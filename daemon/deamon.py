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

WH_HOST = '127.0.0.1'
# WH_HOST = '10.236.48.21'
WH_PORT =23456

SELF_HOST = '127.0.0.1'
# SELF_HOST = '10.190.83.150'
SELF_PORT = 6666

DBhostname = 'localhost'
DBusername = 'dl208'
DBpassword = 'longdong'
DBdatabase = 'amazon'


msg_queue = queue.Queue()
mutex = threading.Lock()


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
		print ("Daemon receive WH data"+data)
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
				pack.shipid = randint(1,1000)# should change later
			mutex.acquire(1)
			msg_queue.put(command_msg)
			mutex.release()

		for r in ready_list:
			cur.execute( "UPDATE amazon_web_orders SET ready=TRUE where tracking_num = 'Not Ready'" )
			# cur.execute("SELECT warehouse from amazon_web_orders where tracking_num = 'Not Ready'")

			# command_msg = amazon_pb2.ACommands();
			# load = command_msg.loaded.add()
			# load.whnum = cur.fetchall()[0]
			# load.truck



def django_sender(socket):
	print ("Enter Django Receiver")
	while True:
		conn, addr = socket.accept()
		data = conn.recv(1024)
		if len(data)<=1:
			continue
		print ("server receive django data "+data)
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

		#MOVE THIS TO UPS RECEIVER AFTER THEY HAVE T_N
		
		mutex.acquire(1)
		msg_queue.put(command_msg)
		mutex.release()


if __name__=="__main__":
	socket_dj_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket_wh_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket_wh_client.connect((WH_HOST, WH_PORT))       #Connect

	# Connect to warehouse world
	connect_msg = amazon_pb2.AConnect()
	connect_msg.worldid = 1000
	send_msg(socket_wh_client, connect_msg)

	# Send Default simulated speed
	speed = amazon_pb2.ACommands()
	speed.simspeed=50000
	send_msg(socket_wh_client, speed)

	try:
		socket_dj_server.bind((SELF_HOST, SELF_PORT))
	except socket.error as msg:
		print ("socket_dj bind error:", msg)
	socket_dj_server.listen(5)
	_thread.start_new_thread(django_sender, (socket_dj_server,))
    _thread.start_new_thread(wh_receiver, (socket_wh_client,))

    while True:
        mutex.acquire(1)
        if msg_queue.empty():
            continue
        else:
            msg = msg_queue.get()
            print ("Sending msg")
            print (msg.__str__())
            send_msg(socket_wh_client, msg)
        mutex.release()

