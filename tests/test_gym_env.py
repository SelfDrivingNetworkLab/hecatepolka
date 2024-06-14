#!/usr/bin/env python
# coding: utf-8

import random
import gym
import sys
import gym_deeproute_stat

MAX_TICKS = 10
total_reward = 0

env = gym.make('Deeproute-stat-v0')

observation = env.reset()

print('Initial State:', observation)

# sys.exit()

for t in range (MAX_TICKS):
	action = env.action_space.sample()
	observation, reward, done = env.step(action)
	total_reward += reward
	print('Ticks:', t+1)
	print('Action:', action) 
	print('Ob:', observation) 
	print('R:', reward)




print("Episode Finished  after {} timesteps".format(t+1))

env.cleanup()