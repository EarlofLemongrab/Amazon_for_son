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

#WH_HOST = '127.0.0.1'
WH_HOST = '10.236.48.21'
WH_PORT = 23456



UPS_HOST = '127.0.0.1'
UPS_PORT = 9010

SELF_HOST = '127.0.0.1'
# SELF_HOST = '10.190.83.150'
SELF_PORT = 6666


DBhostname = 'localhost'
DBusername = 'dl208'
DBpassword = 'longdong'
DBdatabase = 'amazon'


msg_queue = queue.Queue()
ups_queue = queue.Queue()
mutex_django = threading.Lock()
mutex_ups = threading.Lock()





def wh_receiver(socket):
	print ("Enter WH Receiver")
	myConnection = psycopg2.connect(host=DBhostname, user=DBusername, password=DBpassword, dbname=DBdatabase)
	cur = myConnection.cursor()
	while True:
		recv_msg = recv_msg_4B(socket)
		Recv_Responses (recv_msg)

		data = socket.recv(1024)
		print (data)
		if len(data)<=1:
			continue
		# print ("Daemon receive WH data"+data)
		response = parse_response(data)

		arrived_list = response.arrived
		ready_list = response.ready
		load_list = response.loaded
		error = response.error

		command_msg = amazon_pb2.ACommands()
		for a in arrived_list:
			pack = command_msg.topack.add()
			pack.whnum =  a.whnum
			for product in a.things:
				thing = pack.things.add()
				thing.id = a.things[0].id ##ASSUME buy one kind of item everytime
				thing.description = a.things[0].description
				thing.count = a.things[0].count
				pack.shipid = randint(1,1000)# SQL:SELECT order_id from orders where product_id = a.things[0].id AND count = a.things[0].count AND warehouse = whnum
			mutex_django.acquire()
			msg_queue.put(command_msg)
			mutex_django.release()

		# for r in ready_list:
		# 	cur.execute( "UPDATE amazon_web_orders SET ready=TRUE where tracking_num = %d",r)
		# 	cur.execute("SELECT arrive from amazon_web_orders where tracking_num = %d",r)
		# 	arrive = cur.fetchall()
		# 	if len(arrive)!=1:
		# 		print("tracking_num NOT UNIQUE!")
		# 		continue;
		# 	if arrive[0].equals("False"):
		# 		print("Order "+str(r)+" is not arrived")
		# 		continue;
		# 	cur.execute("SELECT warehouse from amazon_web_orders where tracking_num = %d",r)
		# 	command_msg = amazon_pb2.ACommands();
		# 	load = command_msg.loaded.add()
		# 	load.whnum = cur.fetchall()[0]
		# 	load.truckid = #might need to store truckid in DB



def django_sender(socket):
	print ("Enter Django Receiver")
	while True:
		conn, addr = socket.accept()
		data = conn.recv(1024)
		if len(data)<=1:
			continue
		# print ("server receive django data "+data)
		msg = json.loads(data)
		for key,value in msg.items():
			print (key)
		command_msg = amazon_pb2.ACommands()
		buy = command_msg.buy.add()
		command_msg.disconnect = False
		buy.whnum = msg.get('whnum')
		product = buy.things.add()
		product.id = msg.get('pid')
		product.description = msg.get('description')
		product.count = int(msg.get('count'))


		#Contruct UPS Message
		ups_command = UA_pb2.AmazonCommands()
		ship_request = UA_pb2.UAShipRequest()
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
		print(mutex_ups.acquire())
		ups_queue.put(ups_command)
		mutex_ups.release()

		mutex_django.acquire()
		msg_queue.put(command_msg)
		mutex_django.release()


def ups_sender(ups_socket):
	# get ups_socket output stream
	while True:
		mutex_ups.acquire()
		if ups_queue.empty():
			mutex_ups.release()
			continue
		else:
			msg = ups_queue.get()
			print ("Sending msg")
			send_message(ups_socket, msg)
			mutex_ups.release()

def ups_receiver(ups_socket):
	print ("Enter UPS Receiver")
	while True:
		data = ups_socket.recv(1024)
		if len(data)<=1:
			continue
		response = parse_ups_response(data)
		truck_arrive = response.resp_truck
		truck_id = truck_arrive.truckid
		whnum = truck_arrive.whnum
		ship_id = truck_arrive.shipid
		print("daemon receive ups response, truck "+str(truck_id)+" has arrived at warehouse "+str(whnum)+" for order"+str(ship_id))


		#IMPORTANT:FOR TESTING PURPOSE,ASSUE NOW TRUCK COULD GO DELIVER,NEED TO CHECK DB FIRST,THEN SEND LOAD,GOT LOADED

		ups_command = UA_pb2.AmazonCommands()
		ups_command.req_deliver_truckid = truck_id

		mutex_ups.acquire(1)
		ups_queue.put(ups_command)
		mutex_ups.release()

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
	Recv_Responses(recv_msg_4B(socket_wh_client))

	# Bind port for django server socket
	try:
		socket_dj_server.bind((SELF_HOST, SELF_PORT))
	except socket.error as msg:
		print ("socket_dj bind error:", msg)
	socket_dj_server.listen(5)

	# Start new threads
	_thread.start_new_thread(django_sender, (socket_dj_server,))
	_thread.start_new_thread(wh_receiver, (socket_wh_client,))
	_thread.start_new_thread(ups_sender, (socket_ups_client,))
	_thread.start_new_thread(ups_receiver, (socket_ups_client,))

	while True:
		mutex_django.acquire()
		if msg_queue.empty():
			mutex_django.release()
			continue
		else:
			msg = msg_queue.get()
			print ("Sending msg")
			print (msg.__str__())
			send_msg(socket_wh_client, msg)
			mutex_django.release()

