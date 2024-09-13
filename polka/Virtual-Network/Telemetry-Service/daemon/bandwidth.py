#!/usr/bin/python
import sys
import pika
from datetime import datetime
from config_mq import config_rabbitmq, rabbitmq_host, rabbitmq_telemetry_queue

if not config_rabbitmq('TELEMETRY'):
    print("Error in config file.")
    exit()

print("RabbitMQ Server: " + rabbitmq_host())

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbitmq_host()),
)
channel = connection.channel()

channel.queue_declare(queue=rabbitmq_telemetry_queue(), durable=False)

data = {}

while True:
    lines = input().split()
    node_ethv = lines[0] + ";" + lines[1]
    try:
        sent = int(lines[10])
    except:
        sent = 0
    item = data.get(node_ethv, None)
    time_now = datetime.now()
    if item == None:
        data.update( { node_ethv: { 'sent': sent, 'time': time_now } })
    else:
        last_time = item['time']
        item['time'] = time_now
        last_sent = item['sent']
        item['sent'] = sent
        delta_time = (time_now - last_time).total_seconds()
        delta_sent = sent - last_sent
        bps = (delta_sent / delta_time) * 8
        unixtimestamp = datetime.timestamp(datetime.now())
        body = "telemetry;set;bandwidth;" + node_ethv + ';' + str(bps) + ';' + str(unixtimestamp)
        channel.basic_publish(exchange="", routing_key=rabbitmq_telemetry_queue(), properties=pika.BasicProperties(expiration='10000',), body=body)

