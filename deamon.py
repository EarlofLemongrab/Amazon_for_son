#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import amazon_pb2
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
from Queue import Queue
import thread
import time
import threading
import json
import psycopg2


SIMHOST='10.236.48.21'
SIMPORT=23456

SELFHOST = '10.190.83.150'
SELFPORT = 6666

DBhostname = 'localhost'
DBusername = 'dl208'
DBpassword = 'longdong'
DBdatabase = 'amazon'


msg_queue = Queue()
mutex = threading.Lock()

def send_msg(s,message):
	message_str = message.SerializeToString()
	size = len(message_str)
	variant = protobuf_encoder._VarintBytes(size)
	s.send(variant)
	s.send(message_str)
	return;

def parse_response(response):
	if(len(response)<=1):
		print "not value but "+response
		print "length is "+str(len(response))
		return "";
	print "could be response len is "+str(len(response))
	res = amazon_pb2.AResponses()
	next_pos, pos = 0, 0
	next_pos, pos = protobuf_decoder._DecodeVarint32(response,pos)
	res.ParseFromString(response[pos:pos + next_pos])





	print "parse result "+res.__str__()
	return res;


def wh_receiver(socket):
	print ("Enter WH Receiver")
	myConnection = psycopg2.connect( host=DBhostname, user=DBusername, password=DBpassword, dbname=DBdatabase)
	cur = myConnection.cursor()
	while True:
		data = socket.recv(1024)
		print data
		if len(data)<=1:
			continue;
		print ("Daemon receive WH data"+data)
		response = parse_response(data)

		arrived_list = response.arrived
		ready_list = response.ready
		load_list = response.loaded
		error = response.error

		for a in arrived_list:
			command_msg = amazon_pb2.ACommands();
			pack = command_msg.topack.add()
			pack.whnum =  a.whnum;
			product = pack.things.add()
			product.id = a.things[0].id ##ASSUME buy one kind of item everytime
			product.description = a.things[0].description
			product.count = a.things[0].count
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














def django_receiver(socket):
	print "Enter Django Receiver"
	while True:
		conn, addr = socket.accept()
   		data = conn.recv(1024)
   		if len(data)<=1:
   			continue;
   		print "server receive django data "+data
   		msg = json.loads(data)
   		for key,value in msg.items():
   			print key
   		command_msg = amazon_pb2.ACommands();
		buy = command_msg.buy.add();
		command_msg.disconnect = False
		buy.whnum = msg.get('whnum')
		product = buy.things.add();
		product.id = msg.get('pid');
		product.description = msg.get('description');
		product.count = int(msg.get('count'))

		#MOVE THIS TO UPS RECEIVER AFTER THEY HAVE T_N
		
		mutex.acquire(1)
		msg_queue.put(command_msg)
		mutex.release()





if __name__=="__main__":
	socket_dj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket_wh = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket_wh.connect((SIMHOST,SIMPORT))       #Connect
	# socket_wh_reciver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# socket_wh_reciver.bind((SIMHOST, SIMPORT))
	# socket_wh_reciver.listen(5)


	connect_msg = amazon_pb2.AConnect();
	connect_msg.worldid = 1002;
	send_msg(socket_wh,connect_msg)

	speed = amazon_pb2.ACommands();
	speed.simspeed=50000;
	send_msg(socket_wh,speed)



	socket_dj.bind((SELFHOST, SELFPORT))
	socket_dj.listen(5)
	thread.start_new_thread( django_receiver, (socket_dj, ) )
	thread.start_new_thread( wh_receiver, (socket_wh,) )


	while True:
		if msg_queue.empty():
			continue;
		else:
			msg = msg_queue.get()
			print "Sending msg"
			print msg.__str__()
			send_msg(socket_wh,msg)














