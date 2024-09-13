#!/usr/bin/env python
import asyncio
import re
import telnetlib3
from topology import get_router_list, get_router_host, get_router_port, router_not_config, network_id

### Generic functions

def get_accesslist_tunnels(config):
    accesslist_dict = {}
    tunnel_dict = {}
    tunnel_id = ''
    for line in config:
        rs = line.split()
        if len(rs) > 0:
            if rs[0] == 'access-list':
                if len(rs) > 1:
                    accesslist_dict.update( { rs[1]: { 'seq': 0, 'ip': '' } } )
            if rs[0] == 'ipv4':
                if len(rs) > 1:
                    if rs[1] == 'pbr':
                        pbr = line.split(' ')
                        try:
                            seq = int(pbr[4])
                        except:
                            seq = 0
                        if seq > 0:
                            accesslist_dict.update( { pbr[5]: { 'seq': seq, 'ip': pbr[8] } } )
            if rs[0] == 'interface':
               if len(rs) > 1:
                   tunnel_id = rs[1]
                   route_list = []
            if rs[0] == 'tunnel':
                if len(rs) >= 3:
                    if rs[1] == 'mode' and rs[2] == 'polka':
                        cfg_tunnel = True
                    if rs[1] == 'domain-name':
                        cont_ip = 2
                        while cont_ip < len(rs):
                            route_list.append(rs[cont_ip])
                            cont_ip+=1
            if rs[0] == 'exit':
                cfg_tunnel = False
                tunnel_id = ''
            if rs[0] == 'ipv4':
                if len(rs) >= 3 and cfg_tunnel:
                    if rs[1] == 'address':
                        ip = rs[2]
                        mask = rs[3]
                        tunnel_dict.update( { tunnel_id: { 'ip': ip, 'mask': mask, 'route': '-'.join(route_list) } } )
    return(accesslist_dict, tunnel_dict)

### SET functions

def set_tunnel(router_id, tunnel_id, address, mask, path):
    async def main():
        if router_not_config(router_id):
            return
        reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
        cont = 6 
        end_of_search = False
        ip_array = path.split(',')
        ip_dest = ip_array[len(ip_array)-1]
        ip_array[len(ip_array)-1] = ''
        ip_list = ' '.join(ip_array)
        writer.write(f"delete interface {tunnel_id}\n")
        writer.write( "config\n")
        writer.write(f"interface {tunnel_id}\n")
#        writer.write(f" description {description}\n")
        writer.write( " tunnel vrf v1\n")
        writer.write( " tunnel source loopback0\n")
        writer.write(f" tunnel destination {ip_dest}\n")
        writer.write(f" tunnel domain-name {ip_list}\n")
        writer.write( " tunnel mode polka\n")
        writer.write( " vrf forwarding v1\n")
        writer.write(f" ipv4 address {address} {mask}\n")
        writer.write( " no shutdown\n")
        writer.write( " no log-link-change\n")
        writer.write( " exit\n")
        while not end_of_search:
            resp = await reader.readline()
            response = resp.strip()
            if response[-1:] == '#':
                if cont == 0:
                    end_of_search = True
                    writer.write("exit\n")
                cont = cont-1
    asyncio.run(main())

def set_accesslist(router_id, accesslist_id, protocol, address_in, mask_in, address_out, mask_out, tos):
    async def main():
        if router_not_config(router_id):
            return
        reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
        cfg_tos = ""
        int_tos = 0
        try:
            int_tos = int(tos)
        except:
            int_tos = 0
        if int_tos > 0:
            cfg_tos = " tos " + tos
        protocol_num = protocol
        if protocol_num == 'ICMP':
            protocol_num = '1'
        if protocol_num == 'TCP':
            protocol_num = '6'
        if protocol_num == 'UDP':
            protocol_num = '17'
        writer.write(f"delete access-list {accesslist_id}\n")
        writer.write("config\n")
        writer.write(f"access-list {accesslist_id}\n")
        writer.write(f" sequence 10 permit {protocol_num} {address_in} {mask_in} all {address_out} {mask_out} all{cfg_tos}\n")
        writer.write("exit\n")
        writer.write("exit\n")
    asyncio.run(main())

def set_accesslist_tunnel(router_id, accesslist_id, ip_destiny):
    async def main():
        if router_not_config(router_id):
            return
        reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
        writer.write("terminal length 100000\n")
        writer.write("show running-config\n")
        config = []
        response = ''
        while response != 'end':
            resp = await reader.readline()
            response = resp.strip()
            config.append(response)
        accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
        ip = ''
        seq = 0
        if len(accesslist_dict) > 0:
            accesslist = accesslist_dict.get(accesslist_id, None)
            if accesslist != None:
                seq = accesslist['seq']
            if seq == 0:
                for key, value in accesslist_dict.items():
                    if value['seq'] > seq:
                        seq = value['seq']
                seq = seq + 10
        if seq == 0:
            seq = 10
        writer.write("config\n")
        writer.write(f"ipv4 pbr v1 sequence {seq} {accesslist_id} v1 nexthop {ip_destiny}\n")
        writer.write("exit\n")
        writer.write("exit\n")
    asyncio.run(main())

### DEL functions

def del_tunnel(router_id, tunnel_id):
    async def main():
        if router_not_config(router_id):
            return
        reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
        cont = 1
        end_of_search = False
        writer.write(f"delete interface {tunnel_id}\n")
        while not end_of_search:
            resp = await reader.readline()
            response = resp.strip()
            if response[-1:] == '#':
                if cont == 0:
                    end_of_search = True
                    writer.write("exit\n")
                if cont == 1:
                    cont = 0
    asyncio.run(main())

def del_accesslist(router_id, accesslist_id):
    async def main():
        if router_not_config(router_id):
            return
        reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
        writer.write("terminal length 100000\n")
        writer.write("show running-config\n")
        config = []
        response = ''
        while response != 'end':
            resp = await reader.readline()
            response = resp.strip()
            config.append(response)
        accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
        accesslist = accesslist_dict.get(accesslist_id, None)
        if accesslist != None:
            seq = accesslist['seq']
            writer.write('config\n')
            writer.write(f"no ipv4 pbr v1 sequence {seq} {accesslist_id} v1\n")
            writer.write('exit\n')
        writer.write(f"delete access-list {accesslist_id}\n")
        writer.write('exit\n')
    asyncio.run(main())

def del_accesslist_tunnel(router_id, accesslist_id):
    async def main():
        if router_not_config(router_id):
            return
        reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
        writer.write("terminal length 100000\n")
        writer.write("show running-config\n")
        config = []
        response = ''
        while response != 'end':
            resp = await reader.readline()
            response = resp.strip()
            config.append(response)
        accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
        accesslist = accesslist_dict.get(accesslist_id, None)
        if accesslist != None:
            seq = accesslist['seq']
            writer.write('config\n')
            writer.write(f"no ipv4 pbr v1 sequence {seq} {accesslist_id} v1\n")
            writer.write('exit\n')
            writer.write('exit\n')
    asyncio.run(main())

### LIST functions

def list_tunnel(callback, client_queue, router_id):
    async def main():
        if router_not_config(router_id):
            return
        reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
        writer.write("terminal length 100000\n")
        writer.write("show running-config\n")
        config = []
        response = ''
        while response != 'end':
            resp = await reader.readline()
            response = resp.strip()
            config.append(response)
        accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
        tunnel_list = [ f"list;tunnel;{router_id}" ]
        for tunnel_id, tunnel in tunnel_dict.items():
            tunnel_list.append(f"{tunnel_id},{tunnel['ip']},{tunnel['route']}")
        callback(client_queue, ';'.join(tunnel_list))
    asyncio.run(main())

def list_router(callback, client_queue):
    list_txt = [ "list;router" ]
    router_list = get_router_list()
    if len(router_list) > 0:
        for key, value in router_list.items():
            list_txt.append(key + ',' + value['address'] + ':' + value['port'])
    callback(client_queue, ';'.join(list_txt))

def list_accesslist(callback, client_queue, router_id):
    async def main():
        if router_not_config(router_id):
            return
        reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
        writer.write("terminal length 100000\n")
        writer.write("show running-config\n")
        config = []
        response = ''
        while response != 'end':
            resp = await reader.readline()
            response = resp.strip()
            config.append(response)
        accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
        access_txt = [ f"list;accesslist;{router_id}" ]
        for accesslist_id, accesslist in accesslist_dict.items():
            access_txt.append(f"{accesslist_id},{accesslist['seq']},{accesslist['ip']}")
        callback(client_queue, ';'.join(access_txt))
    asyncio.run(main())

def list_accesstunnel(callback, client_queue, router_id, accesslist_id):
    async def main():
        if router_not_config(router_id):
            return
        tunnel_name = ''
        reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
        writer.write("terminal length 100000\n")
        writer.write("show running-config\n")
        config = []
        response = ''
        while response != 'end':
            resp = await reader.readline()
            response = resp.strip()
            config.append(response)
        accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
        accesslist = accesslist_dict.get(accesslist_id, None)
        if accesslist != None:
            for tunnel_id, tunnel in tunnel_dict.items():
                tunnel_net = network_id(tunnel['ip'], tunnel['mask'])
                accesslist_net = network_id(accesslist['ip'], tunnel['mask'])
                if tunnel_net == accesslist_net:
                    tunnel_name = tunnel_id
        callback(client_queue, f"list;accesstunnel;{router_id};{accesslist_id};{tunnel_name}")
    asyncio.run(main())

def list_tunnelaccess(callback, client_queue, router_id, tunnel_id):
    async def main():
        if router_not_config(router_id):
            return
        reader, writer = await telnetlib3.open_connection(get_router_host(router_id), get_router_port(router_id))
        writer.write("terminal length 100000\n")
        writer.write("show running-config\n")
        config = []
        response = ''
        while response != 'end':
            resp = await reader.readline()
            response = resp.strip()
            config.append(response)
        accesslist_dict, tunnel_dict = get_accesslist_tunnels(config)
        accesslist_list = [ f"list;tunnelaccess;{router_id};{tunnel_id}" ]
        tunnel = tunnel_dict.get(tunnel_id, None)
        if tunnel != None:
            for accesslist_id, accesslist in accesslist_dict.items():
                tunnel_net = network_id(tunnel['ip'], tunnel['mask'])
                accesslist_net = network_id(accesslist['ip'], tunnel['mask'])
                if tunnel_net == accesslist_net:
                    accesslist_list.append(accesslist_id + ',' + accesslist['ip'])
        callback(client_queue, ';'.join(accesslist_list))
    asyncio.run(main())

