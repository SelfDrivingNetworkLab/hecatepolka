#!/usr/bin/env python
from multiprocessing import Process
import sys
import pika
from config_mq import config_rabbitmq, rabbitmq_host, rabbitmq_router_queue, rabbitmq_client_queue, rabbitmq_telemetry_queue
import os
from flask import Flask, request, render_template

if not config_rabbitmq(['ROUTER','CLIENT','TELEMETRY']):
    print("Error in config file.")
    exit()

CLIENT_QUEUE=rabbitmq_client_queue()
print("RabbitMQ Server: " + rabbitmq_host())

app = Flask(__name__) # Inicializa a aplicação

@app.route('/') # Cria uma rota
def main():
#    var1 = None
#    var1 = request.args.get('var1')
#    if var1:
#        var1 = "(" + var1 + ")"
#    return render_template('index.html', var1=var1)    
     return render_template('index.html')

@app.route('/data-bandwidth')
def data_bandwidth():
    return app.send_static_file('data-bandwidth.txt')

@app.route('/data-latency')
def data_latency():
    return app.send_static_file('data-latency.txt')

@app.route('/table-routers')
def table_routers():
    return app.send_static_file('table-routers.txt')

@app.route('/update-router')
def update_router():
    params=pika.ConnectionParameters(host=rabbitmq_host())
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=rabbitmq_router_queue(), durable=False)
    body = f"list;router;{CLIENT_QUEUE}"
    channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), properties=pika.BasicProperties(expiration='10000',), body=body)
#    router = None
#    router = request.args.get('router')
#    if router:
#        body = f"list;tunnel;{CLIENT_QUEUE};" + router
#        channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), properties=pika.BasicProperties(expiration='10000',), body=body)
#        body = f"list;accesslist;{CLIENT_QUEUE};" + router
#        channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), properties=pika.BasicProperties(expiration='10000',), body=body)
    return ""

@app.route('/table-tunnels')
def table_tunnels():
    router = None
    router = request.args.get('router')
    if router:
        params=pika.ConnectionParameters(host=rabbitmq_host())
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=rabbitmq_router_queue(), durable=False)
        body = f"list;tunnel;{CLIENT_QUEUE};" + router
        channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), properties=pika.BasicProperties(expiration='10000',), body=body)
        filename = 'table-tunnel-' + router + '.txt';
        if os.path.isfile('static/' + filename):
            return app.send_static_file(filename)
        else:
            return '{ "lines": [ ] }'
    else:
        return '{ "lines": [ ] }'

@app.route('/table-accesslist')
def table_accesslist():
    router = None
    router = request.args.get('router')
    if router:
        params=pika.ConnectionParameters(host=rabbitmq_host())
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=rabbitmq_router_queue(), durable=False)
        body = f"list;accesslist;{CLIENT_QUEUE};" + router
        channel.basic_publish(exchange="", routing_key=rabbitmq_router_queue(), properties=pika.BasicProperties(expiration='10000',), body=body)
        filename = 'table-accesslist-' + router + '.txt';
        if os.path.isfile('static/' + filename):
            return app.send_static_file(filename)
        else:
            return '{ "lines": [ ] }'
    else:
        return '{ "lines": [ ] }'

def save_table(tablename, contents):
    f = open("static/" + tablename, "w")
    f.write(contents)
    f.close()
    return

def set_data(datalake, index, value, datatype):
    item = datalake.get(index, None)
    if item == None:
        c = 0
        item = []
        while c < 100:
            item.append('0')
            c=c+1
    c = 0
    while c<99:
        item[c] = item[c+1];
        c = c+1
    item[99] = value;
    datalake.update( { index: item } )
    datakeys = list(datalake.keys())
    datakeys.sort()
    sorted_datalake = {i: datalake[i] for i in datakeys}
    lista = []
    for index, value in sorted_datalake.items():
        datalist = ','.join(value)
        lista.append("{ \"name\": \"" + index + "\", \"data\": [ " + datalist + " ] }")
    contents =  "{ \"lines\": [ " + ','.join(lista) + "] }"
    save_table("data-" + datatype + ".txt", contents)
    return

def callback_telemetry(ch, method, properties, body):
    print(f" [#] Received {body.decode()}")
    params = body.decode().split(';')
    if len(params) > 0:
        command = params[0].strip()
        if command == 'telemetry':
            if params[1].strip() == 'latency':
                if len(params) >= 5:
                    #telemetry;latency;<src>;<dst>;<latency>;<timestamp>
                    node = params[2]
                    dest = params[3]
                    ltnc = params[4]
                    tims = params[5]
                    set_data(LATENCY_DATA, node + "-" + dest, ltnc, 'latency')
            if params[1] == 'bandwidth':
                if len(params) >= 5:
                    #telemetry;bandwidth;<node>;<ethernet>;<bps>
                    node = params[2]
                    ethv = params[3]
                    btps = params[4]
                    set_data(FLOW_DATA, node + ":" + ethv, btps, 'bandwidth')
    ch.basic_ack(delivery_tag=method.delivery_tag)

def callback_client(ch, method, properties, body):
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
    lista=[]
    arr_txt=txt.split(";")
    for arr_item in arr_txt[2:]:
        parts=arr_item.split(",")
        address=parts[1].split(":")
        lista.append("{ \"router\": \"" + parts[0] + "\", \"address\": \"" + address[0] + "\", \"port\": \"" + address[1] + "\" }")
    lista_txt=",".join(lista)
    f = open("static/table-routers.txt", "w")
    f.write("{ \"lines\": [" + lista_txt + "] }")
    f.close()

def table_tunnel(txt):
    lista=[]
    arr_txt=txt.split(";")
    router=arr_txt[2]
    for arr_item in arr_txt[3:]:
        parts=arr_item.split(",")
        mask="255.255.255.252"
        lista.append("{ \"router\": \"" + router + "\", \"id\": \"" + parts[0] + "\", \"address\": \"" + parts[1] + "\", \"mask\": \"" + mask + "\", \"path\": \"" + parts[2] + "\" }")
    lista_txt=",".join(lista)
    f = open("static/table-tunnel-" + router + ".txt", "w")
    f.write("{ \"lines\": [" + lista_txt + "] }")
    f.close()

def table_accesslist(txt):
    lista=[]
    arr_txt=txt.split(";")
    router=arr_txt[2]
    for arr_item in arr_txt[3:]:
        parts=arr_item.split(",")
        lista.append("{ \"router\": \"" + router + "\", \"id\": \"" + parts[0] + "\", \"seq\": \"" + parts[1] + "\", \"address\": \"" + parts[2] + "\" }")
    lista_txt=",".join(lista)
    f = open("static/table-accesslist-" + router + ".txt", "w")
    f.write("{ \"lines\": [" + lista_txt + "] }")
    f.close()

def client_update():
    # Client Channel
    connection2 = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitmq_host()),
    )
    channel2 = connection2.channel()
    channel2.queue_declare(queue=rabbitmq_client_queue(), durable=False)
    print(" [*] Waiting for messages on " + rabbitmq_client_queue() + ". To exit press CTRL+C")

    channel2.basic_qos(prefetch_count=1)
    channel2.basic_consume(callback_client, queue=rabbitmq_client_queue())
    channel2.start_consuming()

def telemetry_update():
    # Client Channel
    LATENCY_DATA = {}
    FLOW_DATA = {}
    connection3 = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitmq_host()),
    )
    channel3 = connection3.channel()
    channel3.queue_declare(queue=rabbitmq_telemetry_queue(), durable=False)
    print(" [*] Waiting for messages on " + rabbitmq_telemetry_queue() + ". To exit press CTRL+C")

    channel3.basic_qos(prefetch_count=1)
    channel3.basic_consume(callback_telemetry, queue=rabbitmq_telemetry_queue())
    channel3.start_consuming()

LATENCY_DATA = {}
FLOW_DATA = {}
p1 = Process(target=client_update)
p2 = Process(target=telemetry_update)
p1.start()
p2.start()
app.run(debug=True) # Executa a aplicação Flask
p1.join()
p2.join()

