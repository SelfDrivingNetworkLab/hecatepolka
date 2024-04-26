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
    
    def __init__(self, flow_lambda, links, nodes, history, seed):

        np.random.seed(seed)
        self.flow_lambda = flow_lambda
        # self.high = high
        self.nodes_queues = {}
        self.active_flows = []
        self._im_pos = []
        self._delivery_time = 0
        self._delivered_flows = 0
        self._generated_flows = 0
        self._history = history
        self.nodes_flows_history = {}
        self.nodes_actions_history = {}
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
        
    def reset_queues_links(self, links):
        self.generate_queues(reset = True, K = 3) ### initial flows at each waiting queue: 3
        
        for node in self.nodes:
            if node.name not in self.nodes_flows_history:
                self.nodes_flows_history[node.name] = []
            if node.name not in self.nodes_actions_history:
                self.nodes_actions_history[node.name] = [] 
            for index in range(self._history):
                new_f_bw = np.random.poisson(self.flow_lambda[0])
                new_f_lat = np.random.randint(1, 4)
                new_f_destination = np.random.choice(self.nodes, 1, replace=False)
                action = np.random.choice(np.arange(len(self.nodes_connected_links[node.name])), 1)
                self.nodes_flows_history[node.name].append(new_f_bw)
                self.nodes_actions_history[node.name].append(action[0])
                # print(action[0])
                to_link, to_node_name = self.nodes_connected_links[node.name][action[0]]
                current_flow = FlowTraffic(new_f_bw, new_f_lat, new_f_destination[0])
                current_flow.counter = index + 1
                if self.links_avail[to_link.name] > new_f_bw:
                    self.links_avail[to_link.name] -= new_f_bw
                    # current_flow.counter += to_link.lat
                    current_flow.to_link = to_link
                    current_flow.lat += to_link.lat
                    current_flow.to_node_name = to_node_name
                    self.active_flows.append(current_flow)
            while len(self.nodes_flows_history[node.name]) < self._history:
                self.nodes_flows_history[node.name].append(0)
            while len(self.nodes_actions_history[node.name]) < self._history:
                self.nodes_actions_history[node.name].append(0)
   
        self.links_utilization_history.append(self.links_avail.copy())
        
        new_linkslist = self.gen_edges(links)
        new_linksnames = []
        for link in new_linkslist:
            new_linksnames.append(link.name)
            
        for link in self.links:
            if link.name not in new_linksnames:
                self.links_avail[link.name] = 0
        
        

            
    def generate_queues(self, reset, K = 1, inflow_rate = False): 
        ## Generate K flows at each node while reset, if inflow_rate is True, the inflow rate satisfy poisson distribution 
        
        for index, node in enumerate(self.nodes):
            current_node_name = node.name
            if reset:
                self.nodes_queues[current_node_name] = []
            if inflow_rate:
                occur_pro = 1 - np.exp(- self.ticks[index] * self.flow_lambda[1]) ### 1 - exp(- lambda t)
                # print(occur_pro)
                if np.random.random() > occur_pro:
                    K = 0
                else:
                    self.ticks[index] = 0
            for _ in range(K):
                self._generated_flows += 1
                new_f_bw = np.random.poisson(self.flow_lambda[0])
                new_f_lat = 0
                new_f_destination = np.random.choice(self.nodes, 1, replace=False)
                while new_f_destination[0].name == current_node_name:
                    new_f_destination = np.random.choice(self.nodes, 1, replace=False)
                self.nodes_queues[current_node_name].append(FlowTraffic(new_f_bw, new_f_lat, new_f_destination[0]))
                

    def cleanup(self):
        pass

    def take_actions(self, actions):
        
        for index in range(len(self.ticks)):
            self.ticks[index] += 1
        
        for flow in self.active_flows:
            flow.counter -= 1
        
        for node in self.nodes:
            for flow in self.nodes_queues[node.name]:
                flow.lat += 1
         
        self.generate_queues(reset = False, inflow_rate = True)

        for index, node in enumerate(self.nodes):

            if len(self.nodes_queues[node.name]) > 0:
                current_flow = self.nodes_queues[node.name][0]
                to_link, to_node_name = self.nodes_connected_links[node.name][actions[index]] 
            
                if self.links_avail[to_link.name] > current_flow.bw:
                    self.nodes_queues[node.name].pop(0)
                    current_flow.counter += to_link.lat
                    current_flow.lat += to_link.lat
                    current_flow.to_link = to_link
                    current_flow.to_node_name = to_node_name
                    
                    self.nodes_flows_history[node.name].append(current_flow.bw)
                    self.nodes_actions_history[node.name].append(actions[index])
                    self.links_avail[to_link.name] -= current_flow.bw
                    self.active_flows.append(current_flow)
                    
            while len(self.nodes_flows_history[node.name]) > self._history:
                self.nodes_flows_history[node.name].pop(0)
            while len(self.nodes_actions_history[node.name]) > self._history:
                self.nodes_actions_history[node.name].pop(0)
        
        for flow in self.active_flows:
            if flow.counter <= 0.1:
                self.active_flows.remove(flow)
                if self.links_avail[flow.to_link.name] > 0:
                    self.links_avail[flow.to_link.name] += flow.bw
                if flow.to_node_name != flow.destination.name:
                    self.nodes_queues[flow.to_node_name].append(flow)
                else:
                    self._delivered_flows += 1
                    # print(self._delivered_flows)
                    # print(flow.lat)
                    self._delivery_time += flow.lat
                    
        self.links_utilization_history.append(self.links_avail.copy())

    
    def render(self):
        
        # self._im_pos.clear()
        # fig = plt.figure()
        # # Video
        # for links_utilization in self.links_utilization_history:
        #     # links_utilization = self.links_utilization_history[0]
        #     G = nx.Graph()
        #     for node in self.nodes:
        #         G.add_node(node.name)
        #         G.nodes[node.name]["pos"] = node.pos
        #     for link in self.links:
        #         # print(links_utilization[link.name])
        #         G.add_edge(link.node1,link.node2, weight = link.bw, avail = round(links_utilization[link.name], 1))
  
        #     pos=nx.get_node_attributes(G,'pos')

        #     elarge = []
        #     esmall = []
        #     eaverage = []
            
        #     nodes_labels = {}
        #     for node in G.nodes():
        #         nodes_labels[node] = node
                
        #     # nodes_labels = dict([(node: node) for n in G.nodes()])
            
        #     for u,v,d in G.edges(data=True):
        #         if d['avail'] / d['weight'] < 0.2 and d['avail'] / d['weight'] > 0.01:
        #             elarge.append((u, v))
                    
        #         elif d['avail'] / d['weight'] > 0.8:
        #             esmall.append((u, v))
        #             # esmall_labels.append(((u,v,),d['weight']))
        #         elif d['avail'] / d['weight'] <= 0.8 and d['avail'] / d['weight'] >= 0.2:
        #             eaverage.append((u, v))
    
        #     # node 
    
        #     nodes = nx.draw_networkx_nodes(G, pos, node_size = 300)
            
        #     # edges
        #     if len(eaverage) > 0:
        #         edges1 = nx.draw_networkx_edges(G, pos, edgelist=eaverage, width=2)

        #     if len(esmall) > 0:
        #         edges2 = nx.draw_networkx_edges(G, pos, edgelist=esmall, width=2, alpha=0.5, edge_color=mcolors.CSS4_COLORS["darkgreen"])

        #     if len(elarge) > 0:
        #         edges3 = nx.draw_networkx_edges(G, pos, edgelist=elarge, width=2, alpha=0.5, edge_color=mcolors.CSS4_COLORS["darkred"])
                
        #     labels = nx.draw_networkx_labels(G, pos, labels = nodes_labels,font_size=6)
        #     title = plt.title("Red: UR > 0.8. Green: UR < 0.2.")
        #     self._im_pos.append((nodes, edges1, edges2, edges3, title,))

        # ani = animation.ArtistAnimation(fig, self._im_pos)

      
        # ani.save("network_utilization.mp4")
        
        
        #### figure 
        plt.figure()
        G = nx.Graph()
        
        for link in self.links:
            G.add_edge(link.node1,link.node2, weight = link.bw, avail = round(self.links_avail[link.name], 1))
            
         

        edge_labels =dict([(u,v) for u,v,d in G.edges(data=True)])

        # pos = nx.spring_layout(G) # positions for all nodes
        # node 
        for node in self.nodes:
                G.add_node(node.name)
                G.nodes[node.name]["pos"] = node.pos
        
        pos=nx.get_node_attributes(G,'pos')
        nx.draw_networkx_nodes(G, pos, node_size = 600)
        # edges
        nx.draw_networkx_edges(G, pos, edgelist = G.edges(), width=6)
        
        # labels
        nx.draw_networkx_labels(G, pos, edge_labels = edge_labels, font_size=6, font_family='sans-serif')
        # nx.draw_networkx_edge_labels(G,pos,edge_labels = edge_labels)
        # plt.title("Network with original bandwidth")
        plt.savefig("network.png")
        
        # plt.figure()
        # elarge = []
        # esmall = []
        # eaverage = []
        # edge_labels =dict([((u,v,),d['avail']) for u,v,d in G.edges(data=True)])
        # for u,v,d in G.edges(data=True):
        #     if d['avail'] / d['weight'] < 0.1:
        #         elarge.append((u, v))
                
        #     elif d['avail'] / d['weight'] > 0.9:
        #         esmall.append((u, v))
        #         # esmall_labels.append(((u,v,),d['weight']))
        #     else:
        #         eaverage.append((u, v))

        # # node 

        # nx.draw_networkx_nodes(G, pos, node_size = 1000)
        
        # # edges
        # nx.draw_networkx_edges(G, pos, edgelist=eaverage, width=6)
        # nx.draw_networkx_edges(G, pos, edgelist=esmall, width=6, alpha=0.5, edge_color='g')
        # nx.draw_networkx_edges(G, pos, edgelist=elarge, width=6, alpha=0.5, edge_color='r')
        
        # # labels
        # nx.draw_networkx_labels(G, pos, edge_labels = edge_labels, font_size=10, font_family='sans-serif')
        # nx.draw_networkx_edge_labels(G,pos,edge_labels = edge_labels)
        # # plt.title("Network with current bandwidth")
        # plt.savefig("network_current.png")
      
        plt.show()