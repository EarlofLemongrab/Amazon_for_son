#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import amazon_pb2
import UA_pb2
#from google.protobuf.internal.decoder import _DecodeVarint32 as decoder
from google.protobuf.internal import encoder as protobuf_encoder
from google.protobuf.internal import decoder as protobuf_decoder
# from google.protobuf.internal.decoder import _DecodeVarint32 
# from google.protobuf.internal.encoder import _EncodeVarint 
import struct
import io
import sys
import os
from random import randint
import _thread
import time
import threading
import json
import psycopg2
import queue
from messages import *


SIMHOST='10.236.48.21'
SIMPORT=23456

SELFHOST = '127.0.0.1'
SELFPORT = 45678

DBhostname = 'localhost'
DBusername = 'dl208'
DBpassword = 'longdong'
DBdatabase = 'amazon'


msg_queue = queue.Queue()
mutex = threading.Lock()

def send_msg(s,message):
	message_str = message.SerializeToString()
	size = len(message_str)
	variant = protobuf_encoder._VarintBytes(size)
	s.send(variant)
	s.send(message_str)
	return;

# def parse_response(response):
# 	if(len(response)<=1):
# 		print "not value but "+response
# 		print "length is "+str(len(response))
# 		return "";
# 	print "could be response len is "+str(len(response))

# 	res = UA_pb2.AmazonCommands()
# 	next_pos, pos = 0, 0
# 	next_pos, pos = protobuf_decoder._DecodeVarint32(response,pos)
# 	res.ParseFromString(response[pos:pos + next_pos])
# 	print "parse result "+res.__str__()
# 	return res;


def amazon_receiver(amazon_socket):
	print ("Enter amazon Receiver")
	conn, addr = amazon_socket.accept()
	while True:
		print ('Start connecting')
		
		data = recv_msg_4B(conn)
		
		print("receive data")
		if len(data)<=1:
			continue;
		response = UA_pb2.AmazonCommands()
		response.ParseFromString(data)
		print ("UPS receive amazon data"+data.__str__())
		if response.HasField('req_ship'):
			ship_req = response.req_ship
			x = ship_req.x
			y = ship_req.y
			ups_account = ship_req.ups_Account
			package = ship_req.package
			whnum = package.whnum
			ship_id = package.shipid
			print("address is "+x+" "+y)
			print("ups_Account is "+ups_account)
			print("pick up at warehouse "+whnum)
			for p in package.things:
				print("package has item "+p.description+" with count "+p.count)
			UPS_response = UA_pb2.UPSResponses()
			truckarrive = UPSResponses.UATrackArrive.add()
			truckarrive.truckid = 1;
			truckarrive.whnum = whnum
			truckarrive.shipid = ship_id
			mutex.acquire(1)
			msg_queue.put(UPSResponses)
			mutex.release()
		if response.HasField('req_deliver_truckid'):
			print("Sending Truck"+response.req_deliver_truckid+" to deliver")

		










# def django_receiver(socket):
# 	print "Enter Django Receiver"
# 	while True:
# 		conn, addr = socket.accept()
#    		data = conn.recv(1024)
#    		if len(data)<=1:
#    			continue;
#    		print "server receive django data "+data
#    		msg = json.loads(data)
#    		for key,value in msg.items():
#    			print key
#    		command_msg = amazon_pb2.ACommands();
# 		buy = command_msg.buy.add();
# 		command_msg.disconnect = False
# 		buy.whnum = msg.get('whnum')
# 		product = buy.things.add();
# 		product.id = msg.get('pid');
# 		product.description = msg.get('description');
# 		product.count = int(msg.get('count'))

# 		#MOVE THIS TO UPS RECEIVER AFTER THEY HAVE T_N
		
# 		mutex.acquire(1)
# 		msg_queue.put(command_msg)
# 		mutex.release()





if __name__=="__main__":
	amazon_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	amazon_socket.bind((SELFHOST, SELFPORT))
	amazon_socket.listen(5)

	_thread.start_new_thread( amazon_receiver, (amazon_socket,) )


	while True:
		if msg_queue.empty():
			continue;
		else:
			msg = msg_queue.get()
			print ("Sending msg")
			print (msg.__str__())
			send_msg(s,msg)














