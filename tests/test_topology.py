""" Test file to text the yaml file """

#!/usr/bin/env python
import sys
sys.path.append('../../')
#from ML_model import testnn

import json
import csv
import yaml
import networkx as nx
import matplotlib.pyplot as plt
import time
import pandas as pd
import numpy as np

import math
import random


network_yaml="../datasets/sample_nov2022/exampletopo.yaml"

def test_topology():

    print("Testing the topology configuration file....")

    NetworkDict={}
    with open(network_yaml, "r") as stream:
        try:
            NetworkDict=yaml.safe_load(stream)
            print(NetworkDict)
        except yaml.YAMLError as exc:
            print(exc)
    print(NetworkDict['links'])
    
    g = nx.DiGraph()

    for i in NetworkDict['regions']:
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


test_topology()
