#!/usr/bin/env python

# RabbitMQ setup
CONFIG = {}

def config_rabbitmq(config_list):
    f = open('config.txt', 'r')
    for line in f.readlines():
        if line[:1] != '#' and line.strip() != '':
            item, value = line.split('=')
            if item.strip() == 'RABBITMQ_SERVER':
                CONFIG.update( { 'RABBITMQ': value.strip() } )
            if item.strip() == 'ROUTER_QUEUE':
                CONFIG.update( { 'ROUTER': value.strip() } )
            if item.strip() == 'TELEMETRY_QUEUE':
                CONFIG.update( { 'TELEMETRY': value.strip() } )
            if item.strip() == 'CLIENT_QUEUE':
                CONFIG.update( { 'CLIENT': value.strip() } )
    f.close()
    if CONFIG.get('RABBITMQ', None) == None:
        return False
    for config_type in config_list:
        if config_type == 'ROUTER' and CONFIG.get('ROUTER', None) == None:
            return False
        if config_type == 'TELEMETRY' and CONFIG.get('TELEMETRY', None) == None:
            return False
        if config_type == 'CLIENT' and CONFIG.get('CLIENT', None) == None:
            return False
    return True

def rabbitmq_host():
    return CONFIG.get('RABBITMQ', None)

def rabbitmq_router_queue():
    return CONFIG.get('ROUTER', None)

def rabbitmq_telemetry_queue():
    return CONFIG.get('TELEMETRY', None)

def rabbitmq_client_queue():
    return CONFIG.get('CLIENT', None)


