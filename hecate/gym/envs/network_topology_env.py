#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simulate the channel selection  environment.

"""

# core modules

import os
import gym
import json
import random
import logging
import cfg_load
import numpy as np
import pkg_resources


from gym import spaces
from stat_backend import StatBackEnd

#global params
history = 8


Default_task = {'topo_file': "simple.json"}

##### flow size flow latency inflow rate
flow_lambda =[5.0, 0.5]


class NetworkTopologyEnv(gym.Env):
    def __init__(self, Default_task):

        self._done = False
        self.max_ticks = 500
        self._task = task
        nodes, edges = read_json_file(task['topo_file'])
        self.backend = StatBackEnd(flow_lambda = flow_lambda, links = edges, nodes = nodes, history = History, seed = 100)
        
        # action: next hop of current flow at each node
        actions_space = []
        actions_space_ob = []
        for node in self.backend.nodes:
            action_space = len(self.backend.nodes_connected_links[node.name]) 
            actions_space.append(spaces.Discrete(action_space))
            actions_space_ob.extend([action_space - 1 for _ in range(self.backend._history)])
        self.action_space = spaces.Tuple(actions_space)


        # Observation: 1) links available bw 2) nodes current flow size 3) action history and corresponding flow size
        observation_num = len(self.backend.links) + (1 + self.backend._history * 2) * len(self.backend.nodes)
        low = np.array([0 for _ in range(observation_num)])
        temp = []
        for link in self.backend.links:
            temp.append(self.backend.links_avail[link.name])
        temp.extend([100 for _ in range((1 + self.backend._history) * len(self.backend.nodes))])
        temp.extend(actions_space_ob)
        high = np.array(temp)
        self.observation_space = spaces.Box(low, high, dtype=np.float32)
        
        
        # Observation: 1) links available bw 2) nodes current flow size 3) action history and corresponding flow size
        # observation_num = len(self.backend.links) + len(self.backend.nodes)
        # low = np.array([0 for _ in range(observation_num)])
        # temp = []
        # for link in self.backend.links:
        #     temp.append(self.backend.links_avail[link.name])
        # temp.extend([100 for _ in range(len(self.backend.nodes))])

        # high = np.array(temp)
        # self.observation_space = spaces.Box(low, high, dtype=np.float32)