#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import gym
import os.path
import sys
sys.path.append('/Users/9mk/softwares/GitHub/hecatepolka/hecate/')
#sys.path.append('..\..')

from hecate.gym.envs.rteenv import RTEEnv

EPISODES = 10
total_reward = 0

def test_gym_env():
    print(sys.path)
    topology_file="../hecate/data/topologyzoo/sc24polkatopo.json"
    env = RTEEnv(topology_file)
    
    #env = gym.make('Deeproute-stat-v0')


    print("here")
    observation = env.reset()
    print('Initial State:', observation)
    
    for t in range (EPISODES):
	    action = env.action_space.sample()
	    observation, reward, done = env.step(action)
	    total_reward += reward
	    print('Episode:', t+1)
	    print('Action:', action) 
	    print('Ob:', observation) 
	    print('R:', reward)
	
    print("Episode Finished  after {} timesteps".format(t+1))

    env.cleanup()

if __name__== "__main__":
      test_gym_env()