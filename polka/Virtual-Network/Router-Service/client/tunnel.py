#!/usr/bin/env python
import pika
import sys
from config_mq import config_rabbitmq, rabbitmq_host, rabbitmq_router_queue, rabbitmq_client_queue

def print_help():
    print("Param error, use:")
    print("-l <router_id>                                      # list tunnels")
    print("-s <router_id> <tunnel_id> <address> <mask> <path>  # set tunnel parameters")
    print("-d <router_id> <tunnel_id>                          # delete tunnel")
    print("-a <router_id> <tunnel_id>                          # list access lists assign to tunnel")
    print("")
    print("path = nodelist <node>[,<node>]...")
    exit()
options = '-l1-s5-d2-a2'

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


# get router.id and set client channel
router_id = sys.argv[2]
channel = connection.channel()
channel.queue_declare(queue=rabbitmq_router_queue(), durable=False)
CLIENT_QUEUE=rabbitmq_client_queue()

if sys.argv[1] == '-l':
    command = f"list;tunnel;{CLIENT_QUEUE};{router_id}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
if sys.argv[1] == '-a':
    tunnel_id = sys.argv[3]
    command = f"list;tunnelaccess;{CLIENT_QUEUE};{router_id};{tunnel_id}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
if sys.argv[1] == '-s':
    tunnel_id = sys.argv[3]
    address = sys.argv[4]
    mask = sys.argv[5]
    path = sys.argv[6]
    command = f"set;tunnel;{router_id};{tunnel_id};{address};{mask};{path}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
    print(f" [x] Router [{router_id}] SET Tunnel {tunnel_id} {address}/{mask} = {path}")
if sys.argv[1] == '-d':
    tunnel_id = sys.argv[3]
    command = f"del;tunnel;{router_id};{tunnel_id}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
    print(f" [x] Router [{router_od}] DEL Tunnel {tunnel_id}")

connection.close()
