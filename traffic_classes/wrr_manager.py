# wrr_manager.py (Dynamic Weighted Round Robin Manager)

import random
from config import INITIAL_WRR_WEIGHTS, TRAFFIC_CLASSES, SIMULATION_PARAMS, NETWORK_CONFIG
from seg_routing import NetworkTopology # To get current link states

class WRRManager:
    """
    Manages and dynamically adjusts Weighted Round Robin (WRR) weights for network paths.
    Weights are updated based on network conditions (e.g., predicted congestion, latency)
    and potentially traffic class priorities.
    """
    def __init__(self, network_topology: NetworkTopology):
        """
        Initializes the WRR Manager with initial weights and a reference to the network topology.

        Args:
            network_topology (NetworkTopology): The network topology object to query for link states.
        """
        self.network = network_topology
        self.current_weights = INITIAL_WRR_WEIGHTS.copy() # Start with initial weights
        self.path_definitions = self._define_initial_logical_paths() # Define logical paths

    def _define_initial_logical_paths(self) -> dict:
        """
        Defines a set of logical paths in the network. These are conceptual node sequences
        that represent different routing options.

        Returns:
            dict: A dictionary mapping path names to a list of node IPs representing the path.
        """
        core_r1 = NETWORK_CONFIG["core_router_ips"][0]
        core_r2 = NETWORK_CONFIG["core_router_ips"][1]
        edge_r1 = NETWORK_CONFIG["edge_router_ips"][0]
        edge_r2 = NETWORK_CONFIG["edge_router_ips"][1]

        # Define logical paths as node sequences
        # These are examples; in a real system, these would be derived from routing protocols
        # or pre-computed based on topology.
        paths = {
            "path_E1_C1_E2": [edge_r1, core_r1, edge_r2], # Edge1 -> Core1 -> Edge2
            "path_E1_C2_E2": [edge_r1, core_r2, edge_r2], # Edge1 -> Core2 -> Edge2
            "path_E1_C1_C2_E2": [edge_r1, core_r1, core_r2, edge_r2], # Edge1 -> Core1 -> Core2 -> Edge2
            "path_E1_C2_C1_E2": [edge_r1, core_r2, core_r1, edge_r2], # Edge1 -> Core2 -> Core1 -> Edge2
            # Add paths for other source/destination pairs if needed, e.g., E2 to C1
            "path_E2_C1_E1": [edge_r2, core_r1, edge_r1],
            "path_E2_C2_E1": [edge_r2, core_r2, edge_r1],
        }
        return paths

    def get_paths_for_flow(self, source_ip: str, destination_ip: str) -> dict:
        """
        Returns a subset of defined logical paths relevant for a given source-destination pair.
        This is a simplified filter. In a real system, it would be more dynamic.

        Args:
            source_ip (str): The source IP of the flow.
            destination_ip (str): The destination IP of the flow.

        Returns:
            dict: A dictionary of relevant logical paths.
        """
        relevant_paths = {}
        for path_name, path_nodes in self.path_definitions.items():
            # Simple check: if path starts with source_ip and ends with destination_ip
            # This is a simplification; actual routing is more complex.
            if path_nodes[0] == source_ip and path_nodes[-1] == destination_ip:
                 relevant_paths[path_name] = path_nodes
            # Also consider paths that connect an edge router to a core router
            # if the flow destination is a core router.
            elif source_ip in NETWORK_CONFIG["edge_router_ips"] and destination_ip in NETWORK_CONFIG["core_router_ips"]:
                # If flow is from edge to core, any path starting with an edge and containing the core
                # as an intermediate or end node could be relevant.
                # For simplicity, let's assume any path starting with the source edge router
                # and going towards a core router is relevant.
                if path_nodes[0] == source_ip and destination_ip in path_nodes:
                    relevant_paths[path_name] = path_nodes
            # If destination is an edge router, and flow is from a core router
            elif source_ip in NETWORK_CONFIG["core_router_ips"] and destination_ip in NETWORK_CONFIG["edge_router_ips"]:
                if path_nodes[0] == source_ip and destination_ip in path_nodes:
                    relevant_paths[path_name] = path_nodes

        # If no specific path found, return all paths that start with the source edge router
        # and end with any core router, or vice versa.
        if not relevant_paths:
            for path_name, path_nodes in self.path_definitions.items():
                if source_ip in NETWORK_CONFIG["edge_router_ips"] and path_nodes[0] == source_ip and any(node in NETWORK_CONFIG["core_router_ips"] for node in path_nodes):
                    relevant_paths[path_name] = path_nodes
                elif source_ip in NETWORK_CONFIG["core_router_ips"] and path_nodes[0] == source_ip and any(node in NETWORK_CONFIG["edge_router_ips"] for node in path_nodes):
                     relevant_paths[path_name] = path_nodes

        return relevant_paths if relevant_paths else self.path_definitions # Fallback to all if no specific match

    def update_weights(self, current_time: float, predicted_network_state: dict = None, active_flows: dict = None):
        """
        Dynamically updates the WRR weights based on predicted network state
        and/or active flow characteristics.

        Args:
            current_time (float): The current simulation time.
            predicted_network_state (dict, optional): Predicted link metrics from CNSP.
                                                      Keys are link IDs, values are predicted metrics.
            active_flows (dict, optional): Dictionary of active flows.
                                           {flow_id: Flow_object}.
        """
        new_weights = {path_name: 1 for path_name in self.path_definitions} # Start with equal base weight

        if predicted_network_state:
            for path_name, path_nodes in self.path_definitions.items():
                path_predicted_latency_sum = 0
                path_predicted_available_bw_sum = 0 # Corrected variable name
                num_path_links = 0

                # Iterate through pairs of nodes in the logical path to find corresponding links
                for i in range(len(path_nodes) - 1):
                    node1 = path_nodes[i]
                    node2 = path_nodes[i+1]
                    
                    # Find the link_id between node1 and node2
                    found_link = False
                    for neighbor, weight, link_id in self.network.graph[node1]:
                        if neighbor == node2:
                            if link_id in predicted_network_state:
                                pred_metrics = predicted_network_state[link_id]
                                path_predicted_latency_sum += pred_metrics['predicted_latency']
                                path_predicted_available_bw_sum += pred_metrics['predicted_available_bandwidth']
                                num_path_links += 1
                                found_link = True
                                break
                    if not found_link:
                        pass

                if num_path_links > 0:
                    avg_predicted_latency = path_predicted_latency_sum / num_path_links
                    avg_predicted_available_bw = path_predicted_available_bw_sum / num_path_links # Corrected variable name

                    # Calculate a score for the path: higher score is better
                    score = 0
                    if avg_predicted_latency > 0:
                        score += (1000 / avg_predicted_latency) # Scale for impact
                    score += avg_predicted_available_bw # Direct addition

                    new_weights[path_name] = max(1, round(score / 50)) # Scale score to reasonable weight
                else:
                    new_weights[path_name] = 1 # Default if path links not found in predictions

        # If active_flows are provided, consider flow types (e.g., prioritize paths for low_latency flows)
        if active_flows:
            pass

        # Normalize weights if desired (e.g., sum to 100 or a fixed value)
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            for path_name in new_weights:
                new_weights[path_name] = max(1, round(new_weights[path_name] / total_weight * 100)) # Normalize to sum to 100, min 1
        else: # If all weights are zero, reset to equal weights to avoid division by zero
            new_weights = {path_name: 1 for path_name in self.path_definitions}


        self.current_weights = new_weights
        # print(f"WRR Weights updated at {current_time:.2f}s: {self.current_weights}")

    def get_weights(self) -> dict:
        """
        Returns the current dynamic WRR weights.

        Returns:
            dict: A dictionary mapping path names to their current weights.
        """
        return self.current_weights

# TESTING 
if __name__ == "__main__":
    from seg_routing import NetworkTopology
    from cnsp import NetworkStatePredictor
    import time

    # 1. Initialize Network Topology
    topology = NetworkTopology()

    # 2. Initialize Network State Predictor (to provide predicted_network_state)
    cnsp = NetworkStatePredictor(topology)

    # 3. Initialize WRR Manager
    wrr_manager = WRRManager(topology)

    print("Initial WRR Weights:", wrr_manager.get_weights())

    print("\n--- Simulating WRR weight updates over time ---")
    simulation_duration = SIMULATION_PARAMS["simulation_duration_s"]
    wrr_update_interval = SIMULATION_PARAMS["wrr_update_interval_s"]
    cnsp_update_interval = SIMULATION_PARAMS["cnsp_update_interval_s"]

    for t in range(0, simulation_duration + 1, wrr_update_interval):
        current_time = float(t)
        print(f"\nSimulation Time: {current_time:.2f}s")

        # Simulate some link capacity changes to affect network state
        if current_time > 0:
            num_links_to_change = random.randint(1, len(topology.links) // 2 or 1)
            for _ in range(num_links_to_change):
                random_link_id = random.choice(list(topology.links.keys()))
                change_mbps = random.uniform(-200, 200) # Simulate more significant changes
                topology.update_link_capacity_used(random_link_id, change_mbps)

        # Get predicted network state from CNSP
        # Note: CNSP's update interval might be different from WRR's
        # For this example, we'll just call CNSP directly. In main.py, it will be orchestrated.
        predicted_state_from_cnsp = cnsp.generate_update_for_dro(current_time)['predicted_link_metrics']

        # Update WRR weights
        wrr_manager.update_weights(current_time, predicted_network_state=predicted_state_from_cnsp)

        print(f"Current WRR Weights at {current_time:.2f}s: {wrr_manager.get_weights()}")

        time.sleep(0.1) # Simulate time passing
