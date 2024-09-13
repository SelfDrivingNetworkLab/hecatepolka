#!/usr/bin/env python
import pika
from config_mq import config_rabbitmq, rabbitmq_host, rabbitmq_client_queue

# RabbitMQ setup
if not config_rabbitmq(['CLIENT']):
    print("Error in config file.")
    exit()

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbitmq_host()),
)
channel = connection.channel()

channel.queue_declare(queue=rabbitmq_client_queue(), durable=False)
print(" [*] Waiting for messages on " + rabbitmq_client_queue() + ". To exit press CTRL+C")


def callback(ch, method, properties, body):
    print(f" [x] Received:\n{body.decode()}")
    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue=rabbitmq_client_queue())

channel.start_consuming()
