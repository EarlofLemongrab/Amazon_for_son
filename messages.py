import socket               # Import socket module
import amazon_pb2

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

    for purchaseMore in msg.arrived:
        print("whnum = ", purchaseMore.whnum)
        for product in purchaseMore.things:
            print("product: id = ", product.id, " description = ", product.description, " count = ", product.count)

    for rdy in msg.ready:
        print(rdy, end='')

    for load in msg.loaded:
        print(load, end='')

    if msg.HasField("error"):
        print("\033[31mError: \033[0m", msg.error)
    if msg.HasField("finished"):
        if msg.finished:
            print("\033[32mFinished\033[0m")
        else:
            print("\033[32mNot finish\033[0m")