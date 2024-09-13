#!/usr/bin/env python
import sys
import pika
from config_mq import config_rabbitmq, rabbitmq_host, rabbitmq_client_queue
import os

def callback(ch, method, properties, body):
    print(f" [x] Received:\n{body.decode()}")
    print(" [x] Done")
    text_line=body.decode()
    itens=text_line.split(";")
    if itens[0]=="list":
        if itens[1]=="router":
            table_router(text_line)
        if itens[1]=="tunnel":
            table_tunnel(text_line)
        if itens[1]=="accesslist":
            table_accesslist(text_line)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def table_router(txt):
    tb_list=[]
    arr_txt=txt.split(";")
    for arr_item in arr_txt[2:]:
        parts=arr_item.split(",")
        address=parts[1].split(":")
        tb_list.append("{ \"router\": \"" + parts[0] + "\", \"address\": \"" + address[0] + "\", \"port\": \"" + address[1] + "\" }")
    tb_list_txt=",".join(tb_list)
    f = open("static/table-routers.txt", "w")
    f.write("{ \"lines\": [" + tb_list_txt + "] }")
    f.close()

def table_tunnel(txt):
    tb_list=[]
    arr_txt=txt.split(";")
    router=arr_txt[2]
    for arr_item in arr_txt[3:]:
        parts=arr_item.split(",")
        mask="255.255.255.252"
        tb_list.append("{ \"router\": \"" + router + "\", \"id\": \"" + parts[0] + "\", \"address\": \"" + parts[1] + "\", \"mask\": \"" + mask + "\", \"path\": \"" + parts[2] + "\" }")
    tb_list_txt=",".join(tb_list)
    f = open("static/table-tunnel-" + router + ".txt", "w")
    f.write("{ \"lines\": [" + tb_list_txt + "] }")
    f.close()

def table_accesslist(txt):
    tb_list=[]
    arr_txt=txt.split(";")
    router=arr_txt[2]
    for arr_item in arr_txt[3:]:
        parts=arr_item.split(",")
        tb_list.append("{ \"router\": \"" + router + "\", \"id\": \"" + parts[0] + "\", \"seq\": \"" + parts[1] + "\", \"address\": \"" + parts[2] + "\" }")
    tb_list_txt=",".join(tb_list)
    f = open("static/table-accesslist-" + router + ".txt", "w")
    f.write("{ \"lines\": [" + tb_list_txt + "] }")
    f.close()

if not config_rabbitmq(['CLIENT']):
    print("Error in config file.")
    exit()

CLIENT_QUEUE=rabbitmq_client_queue()
print("RabbitMQ Server: " + rabbitmq_host())

# Client Channel
connection = pika.BlockingConnection(
pika.ConnectionParameters(host=rabbitmq_host()),
)
channel = connection.channel()
channel.queue_declare(queue=rabbitmq_client_queue(), durable=False)
print(" [*] Waiting for messages on " + rabbitmq_client_queue() + ". To exit press CTRL+C")

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue=rabbitmq_client_queue())
channel.start_consuming()

