#!/usr/bin/env python
import pika
import sys
from config_mq import config_rabbitmq, rabbitmq_host, rabbitmq_router_queue, rabbitmq_client_queue

def print_help():
    print("Param error, use:")
    print("-l                               # list routers")
    print("-s <router.id> <address> <port>  # set router params")
    print("-d <router.id>                   # delete router")
    print("")
    print("ex:")
    print("-s MIA localhost 2306")
    print("-s AMS localhost 2307")
    exit()
options = '-l0-s3-d1'

# RabbitMQ setup
if not config_rabbitmq(['ROUTER','CLIENT']):
    print("Error in config file.")
    exit()

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbitmq_host()),
)

# at least one option
num_params = len(sys.argv)-2
if num_params < 0:
    print_help()

# sane parameters
param = f"{sys.argv[1]}{num_params}"
if options.find(param) < 0:
    print_help()

# set channel
channel = connection.channel()
channel.queue_declare(queue=rabbitmq_router_queue(), durable=False)
CLIENT_QUEUE=rabbitmq_client_queue()
if sys.argv[1] == '-l':
    command = f"list;router;{CLIENT_QUEUE}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
if sys.argv[1] == '-s':
    router_id = sys.argv[2]
    address = sys.argv[3]
    port = sys.argv[4]
    command = f"set;router;{router_id};{address};{port}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
    print(f" [x] SET Router {router_id} {address}:{port}")
if sys.argv[1] == '-d':
    router_id = sys.argv[2]
    command = f"del;router;{router_id}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)

connection.close()
