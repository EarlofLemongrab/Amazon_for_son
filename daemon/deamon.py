#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import amazon_pb2
#from google.protobuf.internal.decoder import _DecodeVarint32 as decoder
from google.protobuf.internal import encoder as protobuf_encoder
from google.protobuf.internal import decoder as protobuf_decoder
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint
import struct
import io
import sys
import os
import logging
import queue
from messages import *
from random import randint

import _thread
import time
import threading
import json
import psycopg2
import UA_pb2
from threading import Thread, Lock

WH_HOST = '127.0.0.1'
# WH_HOST = '10.236.48.21'
WH_PORT = 23456



UPS_HOST = '127.0.0.1'
UPS_PORT = 9004

SELF_HOST = '127.0.0.1'
# SELF_HOST = '10.190.83.150'
SELF_PORT = 6666


DBhostname = 'localhost'
DBusername = 'herbert'
DBpassword = 'longdong'
DBdatabase = 'amazon'


msg_queue = queue.Queue()
ups_queue = queue.Queue()
mutex_django = threading.Lock()
mutex_ups = threading.Lock()

logging.basicConfig(level = logging.DEBUG,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def wh_receiver(socket):
	print ("Enter WH Receiver")
	myConnection = psycopg2.connect(host=DBhostname, user=DBusername, password=DBpassword, dbname=DBdatabase)

	while True:
		recv_msg = recv_msg_4B(socket)
		print (recv_msg)
		if len(recv_msg)<=1:
			continue
		Recv_Responses(recv_msg, msg_queue, ups_queue, mutex_django, mutex_ups, myConnection)


def django_receiver(socket):
	print ("Enter Django Receiver")
	while True:
		conn, addr = socket.accept()
		data = conn.recv(1024)
		if len(data)<=1:
			continue
		print ("server receive django data ", data)
		msg = json.loads(data.decode())
		# for key,value in msg.items():
		# 	print (key, value)
		#   logger.info(key, value)

		#Contruct Amazon purchase command
		command_msg = amazon_pb2.ACommands()
		command_msg.disconnect = False
		buy = command_msg.buy.add()
		buy.whnum = msg.get('whnum')
		product = buy.things.add()
		product.id = msg.get('pid')
		product.description = msg.get('description')
		product.count = int(msg.get('count'))
		# product = Product(msg.get('pid'), msg.get('description'), int(msg.get('count')))

		#Contruct UPS Message
		ups_command = UA_pb2.AmazonCommands()
		product = ups_command.req_ship.package.things.add()
		product.id = msg.get('pid')
		product.description = msg.get('description')
		product.count = int(msg.get('count'))
		ups_command.req_ship.package.whnum = msg.get('whnum')
		ups_command.req_ship.package.shipid = msg.get('shipid')
		ups_command.req_ship.x = msg.get('address_x')
		ups_command.req_ship.y = msg.get('address_y')
		ups_command.req_ship.upsAccount = '123'



		print("django_sender msg construct finish")
		mutex_ups.acquire()
		ups_queue.put(ups_command)
		mutex_ups.release()

		mutex_django.acquire()
		msg_queue.put(command_msg)
		mutex_django.release()


def ups_sender(ups_socket):
	# get ups_socket output stream
	while True:
		mutex_ups.acquire()
		if not ups_queue.empty():
			msg = ups_queue.get()
			print ("daemon Sending msg to ups")
			send_message_ups(ups_socket, msg)
		mutex_ups.release()

def ups_receiver(ups_socket):
	print ("Enter UPS Receiver")
	myConnection = psycopg2.connect(host=DBhostname, user=DBusername, password=DBpassword, dbname=DBdatabase)
	cur = myConnection.cursor()

	while True:
		# truck arrived
		data = ups_socket.recv(1024)
		if len(data)<=1:
			continue
		response = parse_ups_response(data)
		truck_arrive = response.resp_truck
		truck_id = truck_arrive.truckid
		whnum = truck_arrive.whnum
		ship_id = truck_arrive.shipid
		print("daemon receive ups response, truck "+str(truck_id)+" has arrived at warehouse "+str(whnum)+" for order"+str(ship_id))

		# update database: arrived = True
		cur.execute("update amazon_web_orders set arrive = TRUE where order_id = %s",(ship_id,))
		cur.execute("update amazon_web_orders set truck_id = %s where order_id = %s",(truck_id,ship_id))
		myConnection.commit()


		# if ready == True, create daemon load message
		cur.execute("select ready from amazon_web_orders where order_id = %s", (ship_id,))
		ready_list = cur.fetchall()
		assert (len(ready_list) == 1)
		ready_status = ready_list[0][0]

		if ready_status==True:
			command_msg = amazon_pb2.ACommands()
			to_load = command_msg.load.add()
			to_load.whnum = whnum
			to_load.truckid = truck_id
			to_load.shipid = ship_id
			print("ups ready + arrive => load", command_msg.__str__())

			mutex_django.acquire(1)
			msg_queue.put(command_msg)
			mutex_django.release()




if __name__=="__main__":
	# Create sockets: django, warehouse, UPS
	socket_dj_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket_wh_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket_ups_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# Build up the connection
	socket_wh_client.connect((WH_HOST, WH_PORT))  # Connect
	socket_ups_client.connect((UPS_HOST, UPS_PORT))

	# Connect to warehouse world
	connect_msg = amazon_pb2.AConnect()
	connect_msg.worldid = 1000
	send_msg(socket_wh_client, connect_msg)
	Recv_Connected(recv_msg_4B(socket_wh_client))

	# Send Default simulated speed
	speed = amazon_pb2.ACommands()
	speed.simspeed = 50000
	send_msg(socket_wh_client, speed)
	Recv_Responses(recv_msg_4B(socket_wh_client), msg_queue, ups_queue, mutex_django, mutex_ups)

	# Bind port for django server socket
	try:
		socket_dj_server.bind((SELF_HOST, SELF_PORT))
	except socket.error as msg:
		print ("socket_dj bind error:", msg)
	socket_dj_server.listen(5)

	# Start new threads
	_thread.start_new_thread(django_receiver, (socket_dj_server,))
	_thread.start_new_thread(wh_receiver, (socket_wh_client,))
	_thread.start_new_thread(ups_sender, (socket_ups_client,))
	_thread.start_new_thread(ups_receiver, (socket_ups_client,))

	while True:
		mutex_django.acquire()
		if not msg_queue.empty():
			msg = msg_queue.get()
			print ("daemon Sending msg to warehouse")
			# print (msg.__str__())
			send_msg(socket_wh_client, msg)
		mutex_django.release()

