#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import amazon_pb2
import UA_pb2
#from google.protobuf.internal.decoder import _DecodeVarint32 as decoder
from google.protobuf.internal import encoder as protobuf_encoder
from google.protobuf.internal import decoder as protobuf_decoder
from google.protobuf.internal.decoder import _DecodeVarint32

from google.protobuf.internal.encoder import _EncodeVarint 
import struct
import io
import sys
import os
from random import randint
import _thread
import time
import threading
import json

import queue
from messages import *


# SIMHOST='10.236.48.21'
SIMHOST='127.0.0.1'
SIMPORT=23456

SELFHOST = '127.0.0.1'
SELFPORT = 9004

DBhostname = 'localhost'
DBusername = 'herbert'
DBpassword = 'longdong'
DBdatabase = 'amazon'


msg_queue = queue.Queue()
mutex = threading.Lock()
amazon_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def send_message(s,message):
    print("start send message to amazon_conn: "+message.__str__())
    message_str = message.SerializeToString()
    size = len(message_str)
    variant = protobuf_encoder._VarintBytes(size)
    s.sendall(variant+message_str)
    return

def parse_response(response):
	if(len(response)<=1):
		print ("not value but "+response)
		print ("length is "+str(len(response)))
		return ""
	print ("could be response len is "+str(len(response)))
	n=0
	next_pos, pos = 0, 0
	res = UA_pb2.AmazonCommands()
	while n<len(response):
		msg_len, new_pos = _DecodeVarint32(response, n)
		n = new_pos
		msg_buf = response[n:n+msg_len]
		n += msg_len
		res.ParseFromString(msg_buf)
	print ("parse result "+res.__str__())
	return res


def amazon_receiver(amazon_socket):
	print ("Enter amazon Receiver")
	global amazon_conn
	amazon_conn, addr = amazon_socket.accept()
	while True:
		
		data = amazon_conn.recv(2048)
		
		if len(data)<=1:
			continue
		print("receive amazon data "+data.__str__())
		# response = UA_pb2.AmazonCommands()
		# response.ParseFromString(data)
		response = parse_response(data)
		UPS_response = UA_pb2.UPSResponses()
		print ("UPS receive amazon data"+data.__str__())
		if response.HasField('req_ship'):
			ship_req = response.req_ship
			x = ship_req.x
			y = ship_req.y
			ups_account = ship_req.upsAccount
			package = ship_req.package
			whnum = package.whnum
			ship_id = package.shipid
			print("address is "+str(x)+" "+str(y))
			print("ups_Account is "+ups_account)
			print("pick up at warehouse "+str(whnum))
			for p in package.things:
				print("package has item "+p.description+" with count "+str(p.count))
			
			UPS_response.resp_truck.truckid = 1
			UPS_response.resp_truck.whnum = whnum
			UPS_response.resp_truck.shipid = ship_id
			mutex.acquire(1)
			msg_queue.put(UPS_response)
			mutex.release()
		if response.HasField('req_deliver_truckid'):
			print("Sending Truck"+str(response.req_deliver_truckid)+" to deliver")

		










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
	amazon_socket_client=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	amazon_socket.bind((SELFHOST, SELFPORT))
	amazon_socket.listen(5)

	_thread.start_new_thread( amazon_receiver, (amazon_socket,) )


	while True:
		if msg_queue.empty():
			continue
		else:
			msg = msg_queue.get()
			print ("Sending msg")
			# print (msg.__str__())
			send_message(amazon_conn, msg)














