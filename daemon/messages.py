from __future__ import print_function
import socket               # Import socket module
import amazon_pb2
import io
import mutex
from random import randint
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.decoder import _DecodeVarint
from google.protobuf.internal.encoder import _EncodeVarint


def Connect(_worldid):
    connect = amazon_pb2.AConnect()
    connect.worldid = _worldid
    return connect

def Product(_id, _des, _count):
    product = amazon_pb2.AProduct()
    product.id = _id
    product.description = _des
    product.count = _count
    return product

def Purchase(_products, _whnum):
    purchase = amazon_pb2.APurchaseMore()
    purchase.whnum = _whnum
    purchase.things.extend(_products)
    return purchase

def Commands(_purchases, _simspeed=5000,_disconnect=False):
    command = amazon_pb2.ACommands()
    command.buy.extend(_purchases)
    # command.load.extend(_loads)
    # command.topack.extend(_topacks)
    command.simspeed = _simspeed
    command.disconnect = _disconnect
    return command

def Recv_Connected(recv_msg):
    msg = amazon_pb2.AConnected()
    msg.ParseFromString(recv_msg)
    if (not msg) or (not msg.ListFields()):
        print("\033[33mrecv_msg is empty\033[0m")
    if msg.HasField('error'):
        print("\033[31mError: \033[0m", msg.error)

def Recv_Responses(recv_msg):
    msg = amazon_pb2.AResponses()
    msg.ParseFromString(recv_msg)
    if (not msg) or (not msg.ListFields()):
        print("\033[33mrecv_msg is empty\033[0m")
        return

    command_msg = amazon_pb2.ACommands()
    for purchaseMore in msg.arrived:
        print("whnum = ", purchaseMore.whnum)
        pack = command_msg.topack.add()
        pack.whnum = purchaseMore.whnum
        pack.things = purchaseMore.things
        pack.shipid = randint(1,1000)# should change later
        for product in purchaseMore.things:
            print("product: id = ", product.id, " description = ", product.description, " count = ", product.count)
    mutex.acquire(1)
    msg_queue.put(command_msg)
    mutex.release()



    print("Ready List: ")
    for rdy in msg.ready:
        print(rdy, end='')

    print("Loaded List: ")
    for load in msg.loaded:
        print(load, end='')

    if msg.HasField("error"):
        print("\033[31mError: \033[0m", msg.error)

    if msg.HasField("finished"):
        if msg.finished:
            print("\033[32mFinished\033[0m")
        else:
            print("\033[32mNot finish\033[0m")

def send_msg(socket, _message):
    print(_message)
    msgToSend = _message.SerializeToString()
    _EncodeVarint(socket.sendall, len(msgToSend))
    socket.sendall(msgToSend)

def recv_msg_4B(socket):
    # int length is at most 4 bytes long
    hdr_bytes = socket.recv(4)
    (msg_length, hdr_length) = _DecodeVarint32(hdr_bytes, 0)
    # print("msg_length = ", msg_length, ", hdr_length = ", hdr_length)
    rsp_buffer = io.BytesIO()
    if hdr_length < 4:
        # print("hdr_length < 4, hdr_length = ", hdr_length)
        rsp_buffer.write(hdr_bytes[hdr_length:])
    # read the remaining message bytes
    msg_length = msg_length - (4 - hdr_length)
    print("msg_length = ", msg_length)
    while msg_length > 0:
        rsp_bytes = socket.recv(min(8096, msg_length))
        # print("rsp_bytes: ", rsp_bytes)
        rsp_buffer.write(rsp_bytes)
        msg_length = msg_length - len(rsp_bytes)
    # print(rsp_buffer.getvalue())
    return rsp_buffer.getvalue()

def recv_msg_8B(socket):
    # int length is at most 8 bytes long
    hdr_bytes = socket.recv(8)
    (msg_length, hdr_length) = _DecodeVarint(hdr_bytes, 0)
    # print("msg_length = ", msg_length, ", hdr_length = ", hdr_length)
    rsp_buffer = io.BytesIO()
    if hdr_length < 8:
        # print("hdr_length < 8, hdr_length = ", hdr_length)
        rsp_buffer.write(hdr_bytes[hdr_length:])
    # read the remaining message bytes
    msg_length = msg_length - (8 - hdr_length)
    # print("msg_length = ", msg_length)
    while msg_length > 0:
        rsp_bytes = socket.recv(min(8096, msg_length))
        # print("rsp_bytes: ", rsp_bytes)
        rsp_buffer.write(rsp_bytes)
        msg_length = msg_length - len(rsp_bytes)
    # print(rsp_buffer.getvalue())
    return rsp_buffer.getvalue()

def parse_response(response):
    if(len(response)<=1):
        print ("not value but "+response)
        print ("length is "+str(len(response)))
        return ""
    print ("could be response len is "+str(len(response)))
    res = amazon_pb2.AResponses()
    next_pos, pos = 0, 0
    next_pos, pos = _DecodeVarint32(response,pos)
    res.ParseFromString(response[pos:pos + next_pos])

    print ("parse result "+res.__str__())
    return res
