#!/usr/bin/env python



import os
import gym
import json
import random
import logging

import numpy as np
import pkg_resources

from gym import spaces
from hecate.gym.envs.network_stat_backend import StatBackEnd
from hecate.gym.envs.utils import read_json_file


class RTEEnv(gym.Env):
    
    
    """Defining the traffic engineering environment"""

    def __init__(self, topology_file):
        self.done = False
        self.max_episodes = 500
    
        #Initialize for topology 
        nodes, edges = read_json_file(topology_file)
        self.backend = StatBackEnd(links = edges, nodes = nodes)
    
        # initialize action based on topology
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

    def get_task(self):

        return self._task
        
    def set_task(self, task):
        self._task = task
        # self.reset()
        
    def sample_tasks(self, num_tasks):
        topology_files = ["topo2.json", "topo2.json"]
        topology_file = np.random.choice(topology_files, num_tasks, replace=True)
        tasks = [{'topo_file': file} for file in topology_file]
        return tasks
        
    def step(self, actions):
        """
        The agent takes a step in the environment.

        Parameters
        ----------
        action : int

        Returns
        -------
        ob, reward, if_done, tasks
        """

        self.take_actions(actions)
        reward = self.get_reward()

            
        ob = self.get_state()
        if self.ticks == self.max_ticks:
            self._done = True
        # print(reward)
        return ob, reward, self._done, self._task

    def take_actions(self, actions):
        
        self.backend.take_actions(actions)
        self.ticks += 1

    def get_reward(self):
        # average utilization
        # effective_links = 0
        # utilization = 0
        # for link in self.backend.links:
        #     # print(self.backend.links_avail[link.name])
        #     if self.backend.links_avail[link.name] > 0.00001:
        #         effective_links += 1
        #         temp = (link.bw - self.backend.links_avail[link.name]) / link.bw
        #         utilization += temp
        # return  utilization / effective_links
        # #maximal utilization
        # max_uti = 0.0
        # for link in self.backend.links:
        #     temp = (link.bw - self.backend.links_avail[link.name]) / link.bw
        #     if temp > max_uti:
        #         max_uti = temp
        # return  1 - max_uti 
        
     
        ## latency
        if self.backend._delivered_flows > 0:
            return - self.backend._delivery_time / self.backend._delivered_flows
        else:
            return 0
            
        


    def reset(self):
        """
        Reset the state of the environment and returns an initial observation.

        Returns
        -------
        observation (object): the initial observation of the space.
        """
        self._done = False
        self.ticks = 0
        _, edges = read_json_file(self._task['topo_file'])

        self.backend.reset_queues_links(edges)

        return self.get_state()

    def render(self, mode='human'):
        self.backend.render()
        return
    

    def get_state(self):
        
        """Get the observation.  it is a tuple """
        ob = []
        ### get link utilization
        for link in self.backend.links:
            ob.append(self.backend.links_avail[link.name])
        ### get current waiting flow size
        for node in self.backend.nodes:
            if len(self.backend.nodes_queues[node.name]) > 0:
                flow = self.backend.nodes_queues[node.name][0]
                ob.append(flow.bw)
            else:
                ob.append(0)
        ## get history
        for node in self.backend.nodes:
            ob.extend(self.backend.nodes_flows_history[node.name][-self.backend._history:])
        for node in self.backend.nodes:
            ob.extend(self.backend.nodes_actions_history[node.name][-self.backend._history:])
            
        return np.array(ob)
        
        
    def seed(self, seed):
        random.seed(seed)
        np.random.seed


    def cleanup(self):
        
        self.backend.cleanup()
        