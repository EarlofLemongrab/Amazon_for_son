import socket               # Import socket module
import amazon_pb2
import sys
import io
from messages import *
from google.protobuf.internal import encoder as protobuf_encoder
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint


def Recv_Responses_aaa(recv_msg):
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
            for product in purchaseMore.things:
                thing = pack.things.add()
                thing.id = product.id
                thing.description = product.description
                thing.count = product.count
            # not included in arrived msg, get from database
            # cannot locate order_id based on returned data, search in database for corresponding orders
            # SELECT order_id form orders where product_id = a.things[0].id AND count = a.things[0].count AND warehouse = whnum
            pack.shipid = randint(1,1000)# should change later
            print("product: id = ", product.id, " description = ", product.description, " count = ", product.count)
        # mutex_django.acquire(1)
        # msg_queue.put(command_msg)
        # mutex_django.release()

    print("Ready List: ", end='')
    for rdy in msg.ready:
        print(rdy, end=', ')
    print('')

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

def read_message_delimited(socket):
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


# Create socket and connect
sock = socket.socket()         # Create a socket object
host = socket.gethostname() # Get local machine name
port = 23456                # Reserve a port for your service.
sock.connect((host, port))
print("successfully connected to simulated world")

# send Connect command
msg = Connect(1000)
send_msg(sock, msg)


# receive message
recv_msg = read_message_delimited(sock)
Recv_Connected(recv_msg)

# Send purchase command
prod = Product(20, "longdong2333", 20)
prods = [prod, ]
purch = Purchase(prods, 0)
purchs = [purch, ]
command_msg = Commands(purchs, _disconnect=False )

send_msg(sock, command_msg)
rec_msg = read_message_delimited(sock)
Recv_Responses_aaa(rec_msg)


rec_msg = read_message_delimited(sock)
Recv_Responses_aaa(rec_msg)

rec_msg = read_message_delimited(sock)
Recv_Responses_aaa(rec_msg)

rec_msg = read_message_delimited(sock)
Recv_Responses_aaa(rec_msg)

sock.close()
