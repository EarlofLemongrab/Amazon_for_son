from __future__ import print_function
import socket               # Import socket module
import amazon_pb2
import io
import UA_pb2
from random import randint
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.decoder import _DecodeVarint
from google.protobuf.internal.encoder import _EncodeVarint
# from deamon import mutex_django
from google.protobuf.internal import encoder as protobuf_encoder
from google.protobuf.internal import decoder as protobuf_decoder

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
        print("\033[33mrecv_connect is empty: Connect successfully\033[0m")
    if msg.HasField('error'):
        print("\033[31mError: \033[0m", msg.error)

def Recv_Responses(recv_msg, msg_queue, ups_queue, mutex_django, mutex_ups, connection=None):
    cur = None
    if connection is not None:
        cur = connection.cursor()
    msg = amazon_pb2.AResponses()
    msg.ParseFromString(recv_msg)
    if (not msg) or (not msg.ListFields()):
        print("\033[33mrecv_response is empty\033[0m")
        return

    # receive arrived msg
    if len(msg.arrived) != 0:
        command_msg = amazon_pb2.ACommands()
        for purchaseMore in msg.arrived:
            print("whnum = ", purchaseMore.whnum)
            pack = command_msg.topack.add()
            pack.whnum = purchaseMore.whnum
            order_id = -1
            for product in purchaseMore.things:
                thing = pack.things.add()
                thing.id = product.id
                thing.description = product.description
                thing.count = product.count
                cur.execute("SELECT order_id from amazon_web_orders where product_id = %s AND count = %s AND warehouse = %s AND purchased = False",(product.id,product.count,purchaseMore.whnum))
                order_id_list = cur.fetchall()
                if (len(order_id_list)<1):
                    print("product id ",product.id)
                    print("count ",product.count)
                    print("warehouse ",purchaseMore.whnum)
                    print("length ",len(order_id_list))
                order_id = order_id_list[0]
                cur.execute("update amazon_web_orders set purchased=TRUE where order_id = %s",order_id)
                connection.commit()
                print("purchase update affect row ", cur.rowcount)

            # not included in arrived msg, get from database
            # cannot locate order_id based on returned data, search in database for corresponding orders
            # SELECT order_id form orders where product_id = a.things[0].id AND count = a.things[0].count AND warehouse = whnum
            print("product: id = ", product.id, " description = ", product.description, " count = ", product.count)
            print("create topack command, shipid= ", order_id[0])
            pack.shipid = order_id[0]# should change later

        mutex_django.acquire(1)
        msg_queue.put(command_msg)
        mutex_django.release()

    print("Ready List: ", end='')
    for rdy in msg.ready:     #ship ids
        print(rdy, end=', ')

        # set ready bit for ship ids
        cur.execute("update amazon_web_orders set ready=TRUE where order_id = %s", (rdy,))
        connection.commit()
        print("ready update affect row ",cur.rowcount)
        cur.execute("SELECT arrive,warehouse,truck_id from amazon_web_orders where order_id = %s",(rdy,))

        # In result set (cursor), if truck Arrived, create load message and insert into msq_queue
        status_list = cur.fetchall()
        assert(len(status_list)==1)
        arrive_status = status_list[0][0]
        if arrive_status==False:
            continue
        else:
            command_msg = amazon_pb2.ACommands()
            to_load = command_msg.load.add()
            to_load.whnum = status_list[0][1]
            to_load.truckid = status_list[0][2]
            to_load.shipid = rdy
            print(command_msg.__str__())
            mutex_django.acquire(1)
            msg_queue.put(command_msg)
            mutex_django.release()
    print('')


    print("Loaded List: ")
    for load in msg.loaded:
        print(load, end='')
        # Receive a loaded message, create a to delieve msg into ups queue
        # TODO: update load
        cur.execute("update amazon_web_orders set load=TRUE where order_id = %s", (load,))
        connection.commit()

        # TODO: use shipid to get truckid
        cur.execute("SELECT truck_id from amazon_web_orders where order_id = %s", (load,))
        truck_list = cur.fetchall()
        assert (len(truck_list) == 1)
        ups_command = UA_pb2.AmazonCommands()
        ups_command.req_deliver_truckid = truck_list[0][0]

        mutex_ups.acquire()
        ups_queue.put(ups_command)
        mutex_ups.release()



    if msg.HasField("error"):
        print("\033[31mError: \033[0m", msg.error)

    if msg.HasField("finished"):
        if msg.finished:
            print("\033[32mFinished\033[0m")
        else:
            print("\033[32mNot finish\033[0m")

def send_msg(socket, _message):
    print("start send message: "+_message.__str__())
    msgToSend = _message.SerializeToString()
    _EncodeVarint(socket.sendall, len(msgToSend))
    socket.sendall(msgToSend)

def recv_msg_4B(socket):
    # int length is at most 4 bytes long
    hdr_bytes = socket.recv(4)
    (msg_length, hdr_length) = _DecodeVarint32(hdr_bytes, 0)
    print("msg_length = ", msg_length, ", hdr_length = ", hdr_length)
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


def parse_ups_response(response):
    if(len(response)<=1):
        print ("not value but "+response)
        print ("length is "+str(len(response)))
        return ""
    print ("could be response len is "+str(len(response)))
    message_length, next_pos = _DecodeVarint32(response, 0)
    print(next_pos)                   
    amazoncmd = UA_pb2.UPSResponses()
    amazoncmd.ParseFromString(response[next_pos : next_pos + message_length])  
    print("Req: ") 
    print(amazoncmd.__str__())


    # print ("could be response len is "+str(len(response)))
    # message_length, next_pos = _DecodeVarint32(response, 0)
    # print(next_pos)                   
    # ups_res = UA_pb2.UPSResponses()
    # ups_res.ParseFromString(response[next_pos : next_pos + message_length])  
    # print("Req: ") 
    # print(ups_res.__str__())

    # n=0
    # next_pos, pos = 0, 0
    # res = UA_pb2.UPSResponses()
    # while n<len(response):
    #     msg_len, new_pos = _DecodeVarint32(response, n)
    #     n = new_pos
    #     msg_buf = response[n:n+msg_len]
    #     print("msg length ",msg_len)
    #     print("raw data is ",response)
    #     n += msg_len
    #     res.ParseFromString(msg_buf)
    # print ("parse result "+res.__str__())
    return amazoncmd

def send_message_ups(s, message):
    print("start send message to ups: "+message.__str__())
    message_str = message.SerializeToString()
    size = len(message_str)
    variant = protobuf_encoder._VarintBytes(size)
    s.sendall(variant+message_str)
    return
