

#!/usr/bin/env python
import sys
sys.path.append('../../')

import json
import csv
import yaml
import networkx as nx
import matplotlib.pyplot as plt
import time
import pandas as pd
import numpy as np
#from networkx import graphviz_layout


import math
import random


networktopo="../hecate/data/topologyzoo/simple.json"

def test_topology():

    print("Testing the topology configuration file....")

    NetworkDict={}
    with open(networktopo, "r") as stream:
        NetworkDict = json.load(stream)
        nodes = NetworkDict['data']['mapTopology']['nodes']
        edges = NetworkDict['data']['mapTopology']['edges']
        print(NetworkDict)
        drawgraph(NetworkDict)


def drawgraph(nDict):
    g = nx.DiGraph()

    for i in nDict['data']['mapTopology']['nodes']:
        g.add_node(i['name'],data=i['name'])
        #labelDic = {n: g.nodes[n]['data'].name for n in g.nodes()}    



    edge_labels=[]
    for i in nDict['data']['mapTopology']['edges']:
        src=i['from']
        dst=i['to']
        bandwidth=i['BW']
        latency=i['Lat']
        
        elabel=str(bandwidth)+","+str(latency)
        print(elabel)
        g.add_edge(src, dst, label=elabel)
        #edgeDic = {e: g.get_edge_data(*e)["label"] for e in g.edges}    
        #edge_labels.append(i['name'])
        #edge_labels.append(src,dst,i['BW'],i['Lat'])
    
    print(g.nodes())
    labelDic = {n: g.nodes[n]["data"] for n in g.nodes()}    
    edgeDic = {e: g.get_edge_data(*e)["label"] for e in g.edges}   

    pos = nx.random_layout(g)
    #edge_labels = {i[0:2]:'${}'.format(i[2]['BW']) for i in g.edges(data=True)}

    nx.draw(g,pos,labels=labelDic, with_labels=True, arrowsize=25)#,connectionstyle='arc3, rad = 0.1')
    nx.draw_networkx_edge_labels(g, pos, edge_labels=edgeDic, label_pos=0.4)

    #edge_labels=dict([((u,v,),d['length'])
     #›       for u,v,d in g.edges(data=True)])
    print(g.edges)
    #edge_labels=dict([((n1, n2), d['weight'])
                  # for n1, n2 in g.edges])
    #nx.draw_networkx_edge_labels(g,pos, edge_labels=edge_labels, font_color='red')
    #edge_labels = dict([((n1, n2), d['weight'])
    #                for n1, n2 in g.edges])
    #nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels)
    #nx.draw_networkx_edge_labels(g, pos=pos, edge_labels=edge_labels)


    plt.title("Topology Loaded")
    plt.axis('off')
    plt.show()

test_topology()
