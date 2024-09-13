#!/usr/bin/env python

ROUTER_LIST = { }

def set_router_params(router_id, address, port):
    ROUTER_LIST.update( { router_id: { 'address': address, 'port': port } } )

def get_router_list():
    return ROUTER_LIST

def get_router_host(router_id):
    rec = ROUTER_LIST.get(router_id, None)
    if rec != None:
        active_router_host = rec.get('address', None)
        if active_router_host != None:
            return active_router_host
    return ''

def get_router_port(router_id):
    rec = ROUTER_LIST.get(router_id, None)
    if rec != None:
        active_router_port = rec.get('port', None)
        if active_router_port != None:
            return active_router_port
    return 23

def del_router(router_id):
    rec = ROUTER_LIST.get(router_id, None)
    if rec != None:
        ROUTER_LIST.pop(router_id)
    return

def router_not_config(router_id):
    return(ROUTER_LIST.get(router_id, None) == None)

def network_id(ip, mask):
    ipv4 = ip.split('.')
    maskv4 = mask.split('.')
    result = []
    for i,m in zip(ipv4, maskv4):
        x = int(i) & int(m)
        result.append(f"{x}")
    return '.'.join(result)
