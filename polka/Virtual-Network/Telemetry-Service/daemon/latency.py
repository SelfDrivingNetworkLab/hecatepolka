#!/usr/bin/python
import sys
import pika
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

if len(sys.argv) < 3:
    print("Informe origem e destino")
    exit()
while True:
    lines = input().split()
    if len(lines) == 2:
        node = sys.argv[1]
        dest = sys.argv[2]
        timestamp = lines[0]
        latency = lines[1]
        body = "telemetry;set;latency;" + node + "-" + dest + ";" + latency + ";" + timestamp
        channel.basic_publish(exchange="", routing_key=rabbitmq_telemetry_queue(), properties=pika.BasicProperties(expiration='10000',), body=body)

