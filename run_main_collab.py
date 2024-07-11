#!/usr/bin/env python
# coding: utf-8

import random
import gym
import sys
import yaml
import networkx as nx
import matplotlib.pyplot as plt
import time
import pandas as pd
import numpy as np

#topology_file="examples/networkdatasets/topologies/simpletopo.yaml"
topology_file="../hecate/data/topologyzoo/sc24polkatopo.json"


def find_all_paths(graph, start, end):
    path  = []
    paths = []
    queue = [(start, end, path)]
    """
    while queue:
        start, end, path = queue.pop()
        print('PATH', path)

        path = path + [start]
        if start == end:
            paths.append(path)
        for node in set(graph[start]).difference(path):
            queue.append((node, end, path))
    """
    for path in nx.all_simple_paths(graph, start, end):
        #print(path)
        paths.append(path)
    return paths


def create_topology():
    NetworkDict={}
    with open(topology_file, "r") as stream:
        try:
            NetworkDict=yaml.safe_load(stream)
            #print(NetworkDict)
        except yaml.YAMLError as exc:
            print(exc)
    #print(NetworkDict['links'])
    
    g = nx.DiGraph()

    for i in NetworkDict['nodes']:
        g.add_node(i['name'])


    edge_labels=[]
    for i in NetworkDict['links']:
        src=i['src']
        dst=i['dst']
        g.add_edge(src, dst, weight=2)
        #edge_labels.append(i['name'])

    pos = nx.spring_layout(g)
  
    nx.draw(g,pos,node_size=500, with_labels='True',connectionstyle='arc3, rad = 0.1')
    #edge_labels=dict([((u,v,),d['length'])
     #›       for u,v,d in g.edges(data=True)])

    plt.title("Topology Loaded")
    plt.axis('off')
    plt.show()
    return g


def hecate_polka_collab():
    print("******Starting Scenario...")

    print("*******Topology is created, Polka has developed paths")
    g=create_topology()

    print("******Listing Paths created")
    paths=find_all_paths(g, 'node1', 'node4')
    print(paths)

    print("*************************")
    print("*************************")
    print("*************************")
    print("*************************")
    print("*************************")
    print("Flow Arrives ....... ")
    print("*************************")
    print("*************************")
    
    print("Polka asks Hecate which path to take for this flow.....")
   

    print("Polka calls------------ Ask_Hecate(flowid/flowsize)")
    print("Hecate returns: [path 1- QoS; Path 2- QoS]   OR [PATH1]")
    print("Polka chooses Path1")

Every 10 min() Cron job - new API
 Recall train hecate on new data
 Hecate save new model



hecate_polka_collab()
