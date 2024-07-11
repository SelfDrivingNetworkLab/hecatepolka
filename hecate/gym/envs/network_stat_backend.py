#! /usr/bin/python 

import os
import time
import pylab
import random
import logging
import matplotlib
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors

import json


class NODE(object):
    def __init__(self, name, posx, posy):
        self.name = name
        self.pos = (posx, posy)

class LINK(object):
    def __init__(self, name, bw, lat, node1, node2):
        self.name = name
        self.bw = bw
        self.lat = lat 
        self.node2 = node2
        self.node1 = node1

class FlowTraffic(object):
    def __init__(self, bw, dur, destination):
        self.bw = bw
        self.lat = dur
        self.counter = dur
        self.to_link = None
        self.to_node_name = None
        self.destination = destination

class StatBackEnd(object):
    def __init__(self, links, nodes):

        np.random.seed(seed)
        self.nodes_queues = {}
        self.active_flows = []
        self._im_pos = []
        self._delivery_time = 0
        self._delivered_flows = 0
        self._generated_flows = 0
        self.nodes = self.gen_nodes(nodes)
        self.links = self.gen_edges(links)
        self.links_utilization_history = []
        self.links_avail = self.gen_links_avail()
        self.ticks = [0 for _ in range(len(self.nodes))]
        self.nodes_connected_links = self.gen_nodes_connected_links()

    def gen_nodes_connected_links(self):
        nodes_connected_links = {}
        for node in self.nodes:
            nodes_connected_links[node.name] = []
            for link in self.links:
                if link.node1 == node.name or link.node2 == node.name:
                    if link.node1 == node.name:
                        nodes_connected_links[node.name].append((link, link.node2))
                    else:
                        nodes_connected_links[node.name].append((link, link.node1))
        return nodes_connected_links
                    
        
    def gen_edges(self,links):
        edgelist = []
        for e in links:
            edge_detail = LINK(e["name"], e["BW"], e["Lat"], e["from"], e["to"])
            edgelist.append(edge_detail)
        return edgelist
        
    def gen_nodes(self, nodes):
        nodeslist = []
        for n in nodes:
            # print(n["name"])
            node_detail = NODE(n["name"], n["posx"], n["posy"])
            nodeslist.append(node_detail)
        return nodeslist
        
    def gen_links_avail(self):
        links_avail = {}
        for link in self.links:
            links_avail[link.name] = link.bw
        return links_avail