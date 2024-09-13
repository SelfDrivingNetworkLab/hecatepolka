#!/usr/bin/env python
import pika
import sys
from config_mq import config_rabbitmq, rabbitmq_host, rabbitmq_router_queue, rabbitmq_client_queue

def print_help():
    print("Param error, use:")
    print("-l <router_id>                                                                                   # access lists")
    print("-s <router_id> <accesslist_id> <protocol> <address_in> <mask_in> <address_out> <mask_out> <tos>  # set parameters")
    print("-d <router_id> <accesslist_id>                                                                   # del access list")
    print("-t <router.id> <accesslist_id>                                                                   # tunnnel assigned")
    print("-a <router_id> <accesslist_id> <ip_destiny>                                                      # assign to next hop")
    print("-u <router_id> <accesslist_id>                                                                   # unassign to tunnel")
    exit()
options = '-l1-s8-d2-t2-a3-u2'

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
    command = f"list;accesslist;{CLIENT_QUEUE};{router_id}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
if sys.argv[1] == '-s':
    accesslist_id = sys.argv[3]
    protocol = sys.argv[4]
    address_in = sys.argv[5]
    mask_in = sys.argv[6]
    address_out = sys.argv[7]
    mask_out = sys.argv[8]
    tos = sys.argv[9]
    command = f"set;accesslist;{router_id};{accesslist_id};{protocol};{address_in};{mask_in};{address_out};{mask_out};{tos}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
    print(f" [x] Router [{router_id}] SET Access List {accesslist_id} Protocol={protocol} In={address_in}/{mask_in} Out={address_out}/{mask_out} ToS={tos}")
if sys.argv[1] == '-d':
    accesslist_id = sys.argv[3]
    command = f"del;accesslist;{router_id};{accesslist_id}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
    print(f" [x] Router [{router_id}] DEL Access List {accesslist_id}")
if sys.argv[1] == '-t':
    accesslist_id = sys.argv[3]
    command = f"list;accesstunnel;{CLIENT_QUEUE};{router_id};{accesslist_id}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
if sys.argv[1] == '-a':
    accesslist_id = sys.argv[3]
    ip_destiny = sys.argv[4]
    command = f"set;accesstunnel;{router_id};{accesslist_id};{ip_destiny}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
    print(f" [x] Router [{router_id}] Assign Access List {accesslist_id} to Next hop {ip_destiny}")
if sys.argv[1] == '-u':
    accesslist_id = sys.argv[3]
    command = f"del;accesstunnel;{router_id};{accesslist_id}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), body=command)
    print(f" [x] Router [{router_id}] Unassign Access List {accesslist_id}")
connection.close()
