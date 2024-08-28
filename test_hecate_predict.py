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
default_topology_file="../hecate/data/topologyzoo/sc24polkatopo.json"

pathAdata={time= 0,  bw = y, lat = z
           time = 1, bw=ab, lat=z1}
 
pathBdata={time= x, bw = y, lat = z, fct=1
           time = 1, bw=ab, lat=z1, fct=3}
 

def find_all_paths(graph, start, end):
    path  = []
    paths = []
    queue = [(start, end, path)]

    for path in nx.all_simple_paths(graph, start, end):
        #print(path)
        paths.append(path)
    return paths


def create_topology(topology_file):
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

#2 path case simple case here

def test_hecate_predict(topology_file,[path1data,path2data], allocate_flow_size):

    print("*******Topology is created, Polka has developed paths")
    g=create_topology(topology_file)

    allocate_flow_size= (ID, src, dest ,size)

    reward = [network usage utilization (min max, congested links)]
   

    if allocate_flow_size<=path1data.bw:
        print("select path1")
    else:
        print("select path2")

    
   




hecate_polka_collab(default_topology_file,pathAdata, pathBdata,10)
