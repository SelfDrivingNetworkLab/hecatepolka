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

status = 0
if len(sys.argv) < 3:
    print("Informe origem e destino")
    exit()
try:
    while True:
        lines = input().split()
        if len(lines) > 4:
            node = sys.argv[1]
            dest = sys.argv[2]
            if lines[2] == 'Connecting':
                status = 0
            else:
                if lines[4] == 'Interval' and status == 0:
                    status = 1
                else:
                    if lines[4] == 'Interval' and status == 1:
                        status = 0
                    else:
                        if status == 1 and lines[4] != 'Interval' and lines[4] != '-':
                            dt = lines[0].split('-')
                            hr = lines[1].split(':')
                            timestamp = datetime(int(dt[0]),int(dt[1]),int(dt[2]),int(hr[0]),int(hr[1]),int(hr[2]))
                            flow = lines[8]
                            unixtimestamp = str(datetime.timestamp(timestamp))
                            #[0]telemetry;[1]set;[2]flowrate;[3]<tunnel-name>;[4]<flow-rate>;[5]<timestamp>
                            body = "telemetry;set;flowrate;" + node + "-" + dest + ";" + flow + ";" + unixtimestamp
                            print(body)
                            channel.basic_publish(exchange="", routing_key=rabbitmq_telemetry_queue(), properties=pika.BasicProperties(expiration='10000',), body=body)
except:
    print('<EOF>')
#2024-08-06 13:26:10 Connecting to host thanos, port 5000
#2024-08-06 13:26:10 Reverse mode, remote host thanos is sending
#2024-08-06 13:26:10 [  5] local 192.168.1.28 port 35856 connected to 192.168.1.6 port 5000
#2024-08-06 13:26:11 [ ID] Interval           Transfer     Bitrate
#2024-08-06 13:26:11 [  5]   0.00-1.00   sec  11.0 MBytes  92422 Kbits/sec
#2024-08-06 13:26:12 [  5]   1.00-2.00   sec  23.5 MBytes  197089 Kbits/sec
#2024-08-06 13:26:13 [  5]   2.00-3.00   sec  28.6 MBytes  239532 Kbits/sec
#2024-08-06 13:26:14 [  5]   3.00-4.00   sec  24.8 MBytes  207796 Kbits/sec
#2024-08-06 13:26:15 [  5]   4.00-5.00   sec  28.8 MBytes  241289 Kbits/sec
#2024-08-06 13:26:16 [  5]   5.00-6.00   sec  19.6 MBytes  164474 Kbits/sec
#2024-08-06 13:26:17 [  5]   6.00-7.00   sec  14.0 MBytes  117491 Kbits/sec
#2024-08-06 13:26:18 [  5]   7.00-8.00   sec  25.4 MBytes  213165 Kbits/sec
#2024-08-06 13:26:19 [  5]   8.00-9.00   sec  34.7 MBytes  291311 Kbits/sec
#2024-08-06 13:26:20 [  5]   9.00-10.00  sec  37.5 MBytes  314883 Kbits/sec
#2024-08-06 13:26:20 - - - - - - - - - - - - - - - - - - - - - - - - -
#2024-08-06 13:26:20 [ ID] Interval           Transfer     Bitrate         Retr
#2024-08-06 13:26:20 [  5]   0.00-10.02  sec   251 MBytes  210111 Kbits/sec  1127             sender
#2024-08-06 13:26:20 [  5]   0.00-10.00  sec   248 MBytes  207944 Kbits/sec                  receiver
#2024-08-06 13:26:20
#2024-08-06 13:26:20 iperf Done.

