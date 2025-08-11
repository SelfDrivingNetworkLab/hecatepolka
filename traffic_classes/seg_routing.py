# seg_routing.py

import heapq
from collections import defaultdict
import random
from config import NETWORK_CONFIG # To use network configuration details

class NetworkTopology:
    """
    Represents the network topology as a graph, including nodes (routers)
    and links with their properties (e.g., latency, bandwidth).
    """
    def __init__(self):
        """
        Initializes the network graph.
        Nodes are routers (core and edge).
        Links are represented as edges with weights (e.g., latency).
        """
        self.graph = defaultdict(list) # Adjacency list: {node: [(neighbor, weight, link_id), ...]}
        self.nodes = set()
        self.links = {} # {link_id: {'source': src, 'dest': dst, 'latency': lat, 'bandwidth': bw, 'capacity_used': 0}}
        self._next_link_id = 0

        self._build_initial_topology()

    def _build_initial_topology(self):
        """
        Builds a simplified mesh topology based on NETWORK_CONFIG.
        Assumes all core routers are connected to each other,
        and all edge routers are connected to all core routers.
        """
        core_routers = NETWORK_CONFIG["core_router_ips"]
        edge_routers = NETWORK_CONFIG["edge_router_ips"]
        base_latency = NETWORK_CONFIG["base_latency_ms"]
        base_bandwidth = NETWORK_CONFIG["base_bandwidth_mbps"]
        latency_variance = NETWORK_CONFIG["link_latency_variance"]
        bandwidth_variance = NETWORK_CONFIG["link_capacity_variance"]

        all_routers = core_routers + edge_routers
        self.nodes.update(all_routers)

        # Connect core routers in a mesh
        for i, r1 in enumerate(core_routers):
            for j, r2 in enumerate(core_routers):
                if i < j: # Avoid duplicate edges and self-loops
                    self.add_link(r1, r2, base_latency, base_bandwidth, latency_variance, bandwidth_variance)

        # Connect edge routers to core routers (full mesh between edge and core)
        for er in edge_routers:
            for cr in core_routers:
                self.add_link(er, cr, base_latency, base_bandwidth, latency_variance, bandwidth_variance)

        # For simplicity, let's assume direct edge-to-edge links are not primary for now,
        # but could be added if needed.

        print("Initial Network Topology Built:")
        for node in self.graph:
            print(f"  {node} -> {[(neighbor, weight, link_id) for neighbor, weight, link_id in self.graph[node]]}")
        print(f"Total links: {len(self.links)}")


    def add_link(self, source, destination, base_latency, base_bandwidth,
                 latency_variance, bandwidth_variance):
        """
        Adds a bidirectional link between two nodes with randomized properties.
        """
        link_latency = base_latency * (1 + random.uniform(-latency_variance, latency_variance))
        link_bandwidth = base_bandwidth * (1 + random.uniform(-bandwidth_variance, bandwidth_variance))

        link_id_fwd = f"link_{self._next_link_id}"
        self._next_link_id += 1
        link_id_bwd = f"link_{self._next_link_id}"
        self._next_link_id += 1

        self.graph[source].append((destination, link_latency, link_id_fwd))
        self.graph[destination].append((source, link_latency, link_id_bwd)) # Bidirectional

        self.links[link_id_fwd] = {
            'source': source, 'dest': destination, 'latency': link_latency,
            'bandwidth': link_bandwidth, 'capacity_used': 0
        }
        self.links[link_id_bwd] = {
            'source': destination, 'dest': source, 'latency': link_latency,
            'bandwidth': link_bandwidth, 'capacity_used': 0
        }

    def update_link_capacity_used(self, link_id, bandwidth_increase_mbps):
        """
        Updates the used capacity of a specific link.
        """
        if link_id in self.links:
            self.links[link_id]['capacity_used'] += bandwidth_increase_mbps
            # Ensure capacity used does not exceed total bandwidth
            self.links[link_id]['capacity_used'] = min(
                self.links[link_id]['capacity_used'], self.links[link_id]['bandwidth']
            )
            # print(f"Link {link_id} capacity used: {self.links[link_id]['capacity_used']:.2f} Mbps")
        else:
            print(f"Warning: Link {link_id} not found for capacity update.")

    def get_link_metrics(self, link_id):
        """Returns current metrics for a given link."""
        return self.links.get(link_id)

    def get_current_link_weights(self, metric='latency'):
        """
        Returns the current weights for all active links based on a specified metric.
        This is crucial for Dijkstra's algorithm to adapt to changing network conditions.
        """
        current_weights = defaultdict(list)
        for u in self.graph:
            for v, original_weight, link_id in self.graph[u]:
                link_info = self.links[link_id]
                effective_weight = original_weight # Default to latency

                if metric == 'latency':
                    effective_weight = link_info['latency']
                elif metric == 'congestion':
                    # A simple congestion metric: higher usage -> higher weight
                    # Avoid division by zero if bandwidth is 0
                    if link_info['bandwidth'] > 0:
                        congestion_ratio = link_info['capacity_used'] / link_info['bandwidth']
                        effective_weight = link_info['latency'] * (1 + congestion_ratio * 5) # Penalize congested links more
                    else:
                        effective_weight = float('inf') # Link is unusable
                elif metric == 'available_bandwidth':
                    # For shortest path, we want to maximize available bandwidth, so weight is inverse
                    available_bw = link_info['bandwidth'] - link_info['capacity_used']
                    if available_bw > 0:
                        effective_weight = 1.0 / available_bw
                    else:
                        effective_weight = float('inf') # Link is fully utilized
                # Add more metrics as needed (e.g., hop count, resource cost)

                current_weights[u].append((v, effective_weight, link_id))
        return current_weights

class PathSelector:
    """
    Selects the shortest path using Dijkstra's algorithm based on current network state.
    """
    def __init__(self, network_topology: NetworkTopology):
        self.network = network_topology

    def dijkstra(self, start_node, end_node, metric='latency'):
        """
        Finds the shortest path between a start and end node using Dijkstra's algorithm.

        Args:
            start_node (str): The starting node (router IP).
            end_node (str): The destination node (router IP).
            metric (str): The metric to optimize for ('latency', 'congestion', 'available_bandwidth').

        Returns:
            tuple: A tuple containing:
                - list: The shortest path as a list of nodes (IPs).
                - float: The total cost (e.g., latency) of the shortest path.
                - list: A list of link IDs used in the shortest path.
                Returns (None, float('inf'), None) if no path is found.
        """
        if start_node not in self.network.nodes or end_node not in self.network.nodes:
            print(f"Error: Start node {start_node} or end node {end_node} not in network.")
            return None, float('inf'), None

        distances = {node: float('inf') for node in self.network.nodes}
        distances[start_node] = 0
        previous_nodes = {node: None for node in self.network.nodes}
        previous_links = {node: None for node in self.network.nodes} # To store the link_id used to reach this node

        priority_queue = [(0, start_node)] # (distance, node)

        current_graph_weights = self.network.get_current_link_weights(metric)

        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)

            # If we've already found a shorter path to current_node, skip
            if current_distance > distances[current_node]:
                continue

            # If we reached the end node, reconstruct the path
            if current_node == end_node:
                path = []
                path_links = []
                temp_node = end_node
                while temp_node is not None:
                    path.insert(0, temp_node)
                    if previous_links[temp_node]:
                        path_links.insert(0, previous_links[temp_node])
                    temp_node = previous_nodes[temp_node]
                return path, distances[end_node], path_links

            for neighbor, weight, link_id in current_graph_weights[current_node]:
                distance = current_distance + weight

                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_nodes[neighbor] = current_node
                    previous_links[neighbor] = link_id
                    heapq.heappush(priority_queue, (distance, neighbor))

        return None, float('inf'), None # No path found

class SegmentRouter:
    """
    Manages Segment Routing policies and translates paths into Segment IDs (SIDs).
    """
    def __init__(self, network_topology: NetworkTopology):
        self.network = network_topology
        # Simple SID mapping: each router IP is its Node SID
        self.node_sids = {node_ip: node_ip for node_ip in network_topology.nodes}
        # Adjacency SIDs could be more complex, e.g., (src_ip, dest_ip) -> unique_sid
        self.adjacency_sids = {} # For now, we'll just use Node SIDs

    def get_segment_headers(self, path: list) -> list:
        """
        Translates a given path (list of node IPs) into a list of Segment IDs (SIDs)
        that would be used as segment routing headers.
        For simplicity, we'll use Node SIDs for each hop in the path.
        In a real SR deployment, this would involve more complex SID types (e.g., Adjacency SIDs).

        Args:
            path (list): A list of node IPs representing the chosen path.

        Returns:
            list: A list of SIDs (strings) representing the segment routing header.
                  Returns an empty list if the path is invalid or empty.
        """
        if not path or len(path) < 1:
            return []

        sids = []
        for node_ip in path:
            if node_ip in self.node_sids:
                sids.append(self.node_sids[node_ip])
            else:
                print(f"Warning: Node {node_ip} not found in Node SIDs. Skipping.")
        return sids

# Example Usage (for testing purposes)
if __name__ == "__main__":
    # 1. Initialize Network Topology
    topology = NetworkTopology()

    # 2. Initialize Path Selector
    path_selector = PathSelector(topology)

    # 3. Initialize Segment Router
    segment_router = SegmentRouter(topology)

    # Define some source and destination nodes from the config
    source_node = NETWORK_CONFIG["edge_router_ips"][0]
    destination_node = NETWORK_CONFIG["core_router_ips"][1]

    print(f"\n--- Finding shortest path from {source_node} to {destination_node} (metric: latency) ---")
    path, cost, links_in_path = path_selector.dijkstra(source_node, destination_node, metric='latency')

    if path:
        print(f"Shortest Path: {path}")
        print(f"Total Latency Cost: {cost:.2f} ms")
        print(f"Links in Path: {links_in_path}")

        # Get segment routing headers
        sids = segment_router.get_segment_headers(path)
        print(f"Segment Routing Headers (SIDs): {sids}")

        # Simulate some traffic on the links
        if links_in_path:
            print("\n--- Simulating traffic increasing congestion on path links ---")
            for link_id in links_in_path:
                topology.update_link_capacity_used(link_id, 500) # Add 500 Mbps to each link

            # Try finding path again with 'congestion' metric
            print(f"\n--- Finding shortest path from {source_node} to {destination_node} (metric: congestion) ---")
            path_congestion, cost_congestion, links_congestion = path_selector.dijkstra(source_node, destination_node, metric='congestion')

            if path_congestion:
                print(f"Shortest Path (Congestion-aware): {path_congestion}")
                print(f"Total Congestion Cost: {cost_congestion:.2f}")
                print(f"Links in Path (Congestion-aware): {links_congestion}")
            else:
                print("No congestion-aware path found.")

    else:
        print(f"No path found from {source_node} to {destination_node}.")

    # Test ONLY -SHASH
    print("\n--- Testing with a non-existent node ---")
    path, cost, _ = path_selector.dijkstra("1.1.1.1", destination_node)
    print(f"Path from non-existent node: {path}, Cost: {cost}")
