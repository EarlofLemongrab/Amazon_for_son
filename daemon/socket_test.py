import socket               # Import socket module
import amazon_pb2
import sys
import io
from messages import *
from google.protobuf.internal import encoder as protobuf_encoder
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint


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
prod = Product(20, "test product20", 20)
prods = [prod, ]
purch = Purchase(prods, 0)
purchs = [purch, ]
command_msg = Commands(purchs, _disconnect=False )


send_msg(sock, command_msg)

rec_msg = read_message_delimited(sock)
Recv_Responses(rec_msg)

sock.close()
