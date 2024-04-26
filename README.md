# hecatepolka
This is a joint effort between Hecate and Polka teams.

Background

Prerequisities


Notes - 
5 th april
- how longdoes probing take, can we have time-based one, synchronous every 5 min or on-deman asynchrouns,,,
- asynchronous for link down or not-- not be considered in topology
- mininet to get the data for traffic data- generate experiment 


8th March 2024:
1) discuss what is the optimization function
1b)latency loss and bandwidth - monitoring of links
    Notes: use iperf3 to get link measurements - bandwidth/throughput, estimated latency
    latency small iperf RTT
    calculate estimated bandwidth using iperf
    data intensve science- throughput,bw available
2) add topology simulation that funnels graph, health and flow data for GNN to learn
3) Add GNN model for hecate that produces path predictions
4) produce an API that produces these paths - Do we want optimized per src-dest pair (1 path) or a collection.
Notes: 1 path per src-dest - different flows may get different paths, TCP versus UDP, optimal path plus backup path (also transport layer port+TUPLE+IPDEST+port) use different paths for different applications.. Give individual values for optimization function
application example: high bandwidth, smart grids latency sensitive regardless of bandwidth
5) Polka reads these "paths"
Notes: Polka will have a choice which path for which application

To Do:
how often will hecate and polka talk: Every 2 minutes?
build a cost model for network
router has rest api- to configure path
create a architecture diagram
Investigate which way to integrate - rabbitmq, pyro, microservices