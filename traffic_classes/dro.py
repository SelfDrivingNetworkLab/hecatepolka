# dro.py ( Dynamic Resource Orchestrator )

import random
import time
from collections import defaultdict

from flow import Flow
from config import TRAFFIC_CLASSES, NETWORK_CONFIG, SIMULATION_PARAMS
from seg_routing import NetworkTopology, PathSelector, SegmentRouter
from cnsp import NetworkStatePredictor
from wrr_manager import WRRManager

class DynamicRoutingOptimizer:
    """
    The core component of the Adaptive Flow Management System (AFMS).
    It makes routing decisions for new and active flows based on:
    - Current network state (from NetworkTopology)
    - Predicted future network state (from CNSP)
    - Traffic class characteristics (from Flow)
    - Dynamic WRR weights (from WRRManager)
    - Shortest path calculations (from PathSelector)
    - Segment routing policies (from SegmentRouter)
    """
    def __init__(self, network_topology: NetworkTopology, path_selector: PathSelector,
                 segment_router: SegmentRouter, cnsp: NetworkStatePredictor,
                 wrr_manager: WRRManager, afms_enabled: bool = True):
        """
        Initializes the DRO with references to all necessary network components.

        Args:
            network_topology (NetworkTopology): The network graph and link states.
            path_selector (PathSelector): For calculating shortest paths.
            segment_router (SegmentRouter): For applying segment routing headers.
            cnsp (NetworkStatePredictor): For receiving predicted network state updates.
            wrr_manager (WRRManager): For dynamic WRR weight management.
            afms_enabled (bool): Flag to enable/disable AFMS logic for comparison.
        """
        self.network = network_topology
        self.path_selector = path_selector
        self.segment_router = segment_router
        self.cnsp = cnsp
        self.wrr_manager = wrr_manager
        self.afms_enabled = afms_enabled

        self.active_flows = {} # {flow_id: Flow_object}
        self.completed_flows = {} # {flow_id: Flow_object}
        self.dropped_flows = {} # {flow_id: Flow_object}

        self.predicted_network_state = None # Stores the last update from CNSP

        # Metrics for load balancing algorithms
        # Track active connections per *actual* path (list of link_ids)
        self.path_active_connections = defaultdict(int) # {tuple(link_ids): num_active_connections}
        self.path_bytes_transferred = defaultdict(float) # {tuple(link_ids): total_bytes}
        self.path_latencies = defaultdict(lambda: {'sum': 0.0, 'count': 0}) # {tuple(link_ids): {'sum': lat, 'count': c}}

        # Metrics for plotting
        self.metrics_history = defaultdict(lambda: defaultdict(list)) # {metric_name: {time: [values]}}
        self.total_bandwidth_utilization = defaultdict(float) # {time: utilization_percentage}
        self.traffic_class_bw_utilization = defaultdict(lambda: defaultdict(float)) # {time: {class_name: bw_mbps}}
        self.flow_completion_times = defaultdict(list) # {traffic_class: [completion_time_s]}

        # Initialize WRR state for round-robin selection
        self.wrr_current_index = 0
        # self.wrr_path_names = list(self.wrr_manager.get_weights().keys()) # Will be dynamically updated

        print(f"Dynamic Routing Optimizer initialized. AFMS Enabled: {self.afms_enabled}")

    def receive_cnsp_update(self, update_message: dict):
        """
        Receives and stores the latest predicted network state from CNSP.
        """
        self.predicted_network_state = update_message['predicted_link_metrics']
        # print(f"DRO received CNSP update at {update_message['timestamp']:.2f}s.")

    def _get_effective_link_metrics(self, use_predicted: bool = False) -> defaultdict:
        """
        Returns link metrics, optionally using predicted values if AFMS is enabled.
        """
        effective_metrics = defaultdict(dict)
        if self.afms_enabled and use_predicted and self.predicted_network_state:
            # Use predicted state if available and enabled
            for link_id, pred_metrics in self.predicted_network_state.items():
                effective_metrics[link_id] = {
                    'latency': pred_metrics['predicted_latency'],
                    'bandwidth': pred_metrics['predicted_bandwidth'],
                    'capacity_used': pred_metrics['predicted_capacity_used'],
                    'utilization': pred_metrics['predicted_utilization'],
                    'available_bandwidth': pred_metrics['predicted_available_bandwidth']
                }
        else:
            # Fallback to current actual state
            for link_id, actual_metrics in self.network.links.items():
                effective_metrics[link_id] = {
                    'latency': actual_metrics['latency'],
                    'bandwidth': actual_metrics['bandwidth'],
                    'capacity_used': actual_metrics['capacity_used'],
                    'utilization': actual_metrics['capacity_used'] / actual_metrics['bandwidth'] if actual_metrics['bandwidth'] > 0 else 0,
                    'available_bandwidth': actual_metrics['bandwidth'] - actual_metrics['capacity_used']
                }
        return effective_metrics

    def _find_path_for_flow(self, flow: Flow, current_time: float) -> tuple:
        """
        Selects the best path for a given flow using one of the load balancing algorithms.
        Returns the chosen path (list of nodes), its cost, and the link IDs in the path.
        """
        source_node = flow.source_ip
        destination_node = flow.destination_ip

        selected_path_nodes = None
        path_cost = float('inf')
        path_link_ids = None
        chosen_algorithm = "Default (Latency Shortest Path)"

        def get_dijkstra_path(src, dst, metric, use_predicted_for_dijkstra=False):
            original_graph = self.network.graph.copy() # Store original graph
            
            # Create a temporary graph for Dijkstra using effective metrics (predicted or actual)
            temp_graph_weights = defaultdict(list)
            effective_link_metrics = self._get_effective_link_metrics(use_predicted=use_predicted_for_dijkstra)

            for u in self.network.nodes: # Iterate over all nodes to ensure all are considered
                for v, original_weight, link_id in original_graph[u]: # Use original graph structure
                    link_info = effective_link_metrics.get(link_id)
                    if not link_info: # Fallback if link not found in effective_link_metrics
                        link_info = self.network.links.get(link_id)
                        if not link_info:
                            continue # Skip if link info is truly missing

                    effective_weight = original_weight # Default to original latency

                    # Use the appropriate metric from link_info (which could be predicted)
                    if metric == 'latency':
                        effective_weight = link_info['latency']
                    elif metric == 'congestion':
                        if link_info['bandwidth'] > 0:
                            congestion_ratio = link_info['utilization'] # Use pre-calculated utilization
                            # More dynamic and aggressive penalty for congestion
                            effective_weight = link_info['latency'] * (1 + congestion_ratio * 20) # Increased multiplier
                        else:
                            effective_weight = float('inf')
                    elif metric == 'available_bandwidth':
                        available_bw = link_info['available_bandwidth']
                        if available_bw > 0:
                            effective_weight = 1.0 / available_bw # Inverse for shortest path
                        else:
                            effective_weight = float('inf')
                    
                    # AFMS Enhancement: Add a small penalty based on active connections on the link
                    # This subtly incorporates load balancing into all AFMS path selections.
                    if self.afms_enabled and use_predicted_for_dijkstra:
                        # Use utilization as a proxy for active connections for this penalty
                        connection_penalty_factor = link_info['utilization'] * 1.0 # Increased penalty factor
                        effective_weight += connection_penalty_factor

                    temp_graph_weights[u].append((v, effective_weight, link_id))

            self.network.graph = temp_graph_weights # Temporarily replace network's graph for path selection
            path, cost, links = self.path_selector.dijkstra(src, dst, metric='latency') # Dijkstra uses its own metric logic based on the graph weights
            self.network.graph = original_graph # Restore original graph

            return path, cost, links


        # --- Load Balancing Algorithm Selection Logic ---
        if self.afms_enabled:
            # AFMS-enabled algorithms leverage predicted state and flow intent
            # 1. Least Response Time (Latency-Optimized) - for low_latency traffic
            if flow.traffic_class_name == "low_latency":
                chosen_algorithm = "AFMS: Least Response Time (Low Latency)"
                selected_path_nodes, path_cost, path_link_ids = get_dijkstra_path(source_node, destination_node, 'latency', use_predicted_for_dijkstra=True)

            # 2. Resource Based (Bandwidth-Optimized) - for high_throughput, intent_based traffic
            elif flow.traffic_class_name in ["high_throughput", "intent_based"]:
                chosen_algorithm = "AFMS: Resource Based (High Throughput/Intent)"
                selected_path_nodes, path_cost, path_link_ids = get_dijkstra_path(source_node, destination_node, 'available_bandwidth', use_predicted_for_dijkstra=True)

            # 3. Weighted Least Connection - for long_living traffic
            elif flow.traffic_class_name == "long_living":
                chosen_algorithm = "AFMS: Weighted Least Connection (Long Living)"
                # Find all relevant logical paths
                relevant_logical_paths = self.wrr_manager.get_paths_for_flow(source_node, destination_node)
                
                best_path_info = (None, float('inf'), None) # (path_nodes, cost, link_ids)
                min_wlc_score = float('inf')

                for path_name, path_nodes_sequence in relevant_logical_paths.items():
                    # Get actual path and links using Dijkstra with predicted congestion
                    current_path_nodes, current_path_cost, current_path_link_ids = get_dijkstra_path(
                        path_nodes_sequence[0], path_nodes_sequence[-1], 'congestion', use_predicted_for_dijkstra=True
                    )
                    if not current_path_link_ids:
                        continue # Skip if no valid path found

                    path_key = tuple(current_path_link_ids)
                    active_connections = self.path_active_connections[path_key]
                    wrr_weight = self.wrr_manager.get_weights().get(path_name, 1) # Get WRR weight for this logical path

                    # Calculate WLC score: (connections / weight) + (predicted_latency_cost_factor)
                    wlc_score = (active_connections / (wrr_weight + 0.001)) + (current_path_cost * 0.1)

                    if wlc_score < min_wlc_score:
                        min_wlc_score = wlc_score
                        best_path_info = (current_path_nodes, current_path_cost, current_path_link_ids)
                
                selected_path_nodes, path_cost, path_link_ids = best_path_info
                
            # 4. Least Connection - for short_living traffic
            elif flow.traffic_class_name == "short_living":
                chosen_algorithm = "AFMS: Least Connection (Short Living)"
                # Find all relevant logical paths
                relevant_logical_paths = self.wrr_manager.get_paths_for_flow(source_node, destination_node)

                best_path_info = (None, float('inf'), None) # (path_nodes, cost, link_ids)
                min_connections = float('inf')

                for path_name, path_nodes_sequence in relevant_logical_paths.items():
                    # Get actual path and links using Dijkstra with predicted latency (for tie-breaking)
                    current_path_nodes, current_path_cost, current_path_link_ids = get_dijkstra_path(
                        path_nodes_sequence[0], path_nodes_sequence[-1], 'latency', use_predicted_for_dijkstra=True
                    )
                    if not current_path_link_ids:
                        continue # Skip if no valid path found

                    path_key = tuple(current_path_link_ids)
                    active_connections = self.path_active_connections[path_key]

                    if active_connections < min_connections:
                        min_connections = active_connections
                        best_path_info = (current_path_nodes, current_path_cost, current_path_link_ids)
                    elif active_connections == min_connections:
                        # Tie-breaker: prefer lower predicted latency
                        if current_path_cost < best_path_info[1]:
                            best_path_info = (current_path_nodes, current_path_cost, current_path_link_ids)
                
                selected_path_nodes, path_cost, path_link_ids = best_path_info

            # Dedicated Path - for critical_signaling traffic
            elif flow.traffic_class_name == "critical_signaling":
                chosen_algorithm = "AFMS: Critical Signaling (Dedicated Path)"
                selected_path_nodes, path_cost, path_link_ids = get_dijkstra_path(source_node, destination_node, 'latency', use_predicted_for_dijkstra=True)

            # Dynamic WRR - for default_flows (and any others not explicitly covered)
            else: # Covers "default_flows"
                chosen_algorithm = "AFMS: Dynamic WRR (General/Default)"
                # For default flows, use a balanced metric that considers both latency and available bandwidth
                selected_path_nodes, path_cost, path_link_ids = self._select_path_dynamic_wrr(flow, use_predicted=True, metric_for_dijkstra='balanced')

        else: # Non-AFMS mode (traditional load balancing) - ALL TRAFFIC CLASSES TREATED AS ONE
            chosen_algorithm = "Non-AFMS: Default Latency Shortest Path"
            selected_path_nodes, path_cost, path_link_ids = get_dijkstra_path(source_node, destination_node, 'latency', use_predicted_for_dijkstra=False)

        if not selected_path_nodes:
            print(f"Warning: No specific path found for {flow.flow_id[:8]} ({flow.traffic_class_name}). Falling back to default latency shortest path.")
            selected_path_nodes, path_cost, path_link_ids = get_dijkstra_path(source_node, destination_node, 'latency', use_predicted_for_dijkstra=self.afms_enabled)
            if not selected_path_nodes:
                print(f"Error: Could not find any path for flow {flow.flow_id[:8]}. Dropping flow.")
                return None, float('inf'), None, "No Path Found"

        # --- Apply Segment Routing ---
        segment_headers = self.segment_router.get_segment_headers(selected_path_nodes)
        flow.segment_headers = segment_headers

        return selected_path_nodes, path_cost, path_link_ids, chosen_algorithm

    def _select_path_dynamic_wrr(self, flow: Flow, use_predicted: bool, metric_for_dijkstra: str = 'latency') -> tuple:
        """
        Selects a path using Dynamic Weighted Round Robin.
        This method now resolves the logical path to an actual network path using Dijkstra.
        Added metric_for_dijkstra parameter for more control.
        """
        weights = self.wrr_manager.get_weights()
        
        # Filter paths relevant to the current flow's source and destination
        relevant_logical_paths = self.wrr_manager.get_paths_for_flow(flow.source_ip, flow.destination_ip)
        
        if not relevant_logical_paths:
            # Fallback if no specific paths are relevant for this flow
            relevant_logical_paths = self.wrr_manager.path_definitions # Fallback to all defined paths

        # Create a weighted list of only the relevant path names for selection
        weighted_path_names = []
        for path_name in relevant_logical_paths.keys():
            if path_name in weights:
                weighted_path_names.extend([path_name] * weights[path_name])
        
        if not weighted_path_names:
            return None, float('inf'), None

        # Select a logical path name based on WRR
        selected_logical_path_name = weighted_path_names[self.wrr_current_index % len(weighted_path_names)]
        self.wrr_current_index = (self.wrr_current_index + 1) % len(weighted_path_names)

        # Get the node sequence for the selected logical path
        selected_path_nodes_sequence = self.wrr_manager.path_definitions[selected_logical_path_name]

        # Now, find the actual shortest path (nodes and links) for this logical path
        # from its start node to its end node, using a metric influenced by AFMS.
        source_node_for_dijkstra = selected_path_nodes_sequence[0]
        destination_node_for_dijkstra = selected_path_nodes_sequence[-1]

        # Temporarily modify NetworkTopology's graph for Dijkstra based on effective metrics
        original_graph = self.network.graph.copy()
        temp_graph_weights = defaultdict(list)
        effective_link_metrics = self._get_effective_link_metrics(use_predicted=use_predicted)

        for u in self.network.nodes:
            for v, original_weight, link_id in original_graph[u]:
                link_info = effective_link_metrics.get(link_id)
                if not link_info: # Fallback if link not found in effective_link_metrics
                    link_info = self.network.links.get(link_id)
                    if not link_info:
                        continue

                effective_weight = original_weight

                if metric_for_dijkstra == 'latency':
                    effective_weight = link_info['latency']
                elif metric_for_dijkstra == 'congestion':
                    if link_info['bandwidth'] > 0:
                        congestion_ratio = link_info['utilization']
                        effective_weight = link_info['latency'] * (1 + congestion_ratio * 10) # Use aggressive penalty
                    else:
                        effective_weight = float('inf')
                elif metric_for_dijkstra == 'available_bandwidth':
                    available_bw = link_info['available_bandwidth']
                    if available_bw > 0:
                        effective_weight = 1.0 / available_bw
                    else:
                        effective_weight = float('inf')
                elif metric_for_dijkstra == 'balanced': # New balanced metric for default flows
                    # Combine latency and inverse of available bandwidth
                    latency_cost = link_info['latency']
                    bandwidth_cost = 0
                    if link_info['available_bandwidth'] > 0:
                        bandwidth_cost = 1.0 / link_info['available_bandwidth']
                    else:
                        bandwidth_cost = float('inf')
                    effective_weight = latency_cost + (bandwidth_cost * 0.1) # Tune this factor

                # AFMS Enhancement: Add a small penalty based on active connections on the link
                if self.afms_enabled and use_predicted:
                    connection_penalty_factor = link_info['utilization'] * 1.0 # Increased penalty factor
                    effective_weight += connection_penalty_factor

                temp_graph_weights[u].append((v, effective_weight, link_id))

        self.network.graph = temp_graph_weights
        path, cost, links = self.path_selector.dijkstra(source_node_for_dijkstra, destination_node_for_dijkstra, metric='latency') # Dijkstra uses its own metric logic
        self.network.graph = original_graph # Restore original graph

        return path, cost, links


    def handle_new_flow(self, flow: Flow, current_time: float):
        """
        Processes a newly arrived flow, selects a path, and assigns it.
        """
        selected_path_nodes, path_cost, path_link_ids, chosen_algorithm = self._find_path_for_flow(flow, current_time)

        if selected_path_nodes:
            flow.current_path = selected_path_nodes
            flow.assigned_path_link_ids = tuple(path_link_ids) # Store link IDs for easier lookup
            flow.path_history.append({'time': current_time, 'path': selected_path_nodes, 'algorithm': chosen_algorithm})
            self.active_flows[flow.flow_id] = flow

            # Update link capacities for chosen path
            if path_link_ids: # Ensure path_link_ids is not None
                for link_id in path_link_ids:
                    self.network.update_link_capacity_used(link_id, flow.bandwidth_requirement_mbps)
            
            # Increment active connections for this path
            # Only increment if path_link_ids is not empty
            if flow.assigned_path_link_ids:
                self.path_active_connections[flow.assigned_path_link_ids] += 1

        else:
            flow.mark_dropped(current_time)
            self.dropped_flows[flow.flow_id] = flow
            # print(f"  Flow {flow.flow_id[:8]} DROPPED (No path found).")


    def update_flow_progress(self, current_time: float):
        """
        Updates the progress of all active flows.
        Removes completed flows and frees up their allocated bandwidth.
        """
        flows_to_remove = []
        for flow_id, flow in list(self.active_flows.items()): # Iterate over a copy
            if flow.current_path and hasattr(flow, 'assigned_path_link_ids') and flow.assigned_path_link_ids:
                effective_link_metrics = self._get_effective_link_metrics(use_predicted=False) # Always use actual for progress
                
                current_path_latency = 0
                current_path_bandwidth = float('inf') # Bottleneck bandwidth

                # Use the stored assigned_path_link_ids directly
                actual_path_link_ids = flow.assigned_path_link_ids

                if actual_path_link_ids:
                    for link_id in actual_path_link_ids:
                        link_info = effective_link_metrics.get(link_id)
                        if link_info:
                            current_path_latency += link_info['latency']
                            # Calculate the *true* available bandwidth on this link for this flow
                            # This link's total capacity - (total capacity used by ALL flows - this flow's own BW)
                            # This gives us the capacity available to *this flow* if it were the only one.
                            # More accurately, it's the link's current available bandwidth.
                            # The flow's rate is limited by the minimum available bandwidth on its path.
                            current_path_bandwidth = min(current_path_bandwidth, link_info['bandwidth'] - (link_info['capacity_used'] - flow.bandwidth_requirement_mbps))
                        else:
                            current_path_bandwidth = 0 # Mark as bottlenecked
                            break
                else:
                    current_path_bandwidth = 0 # No links found for the path

                current_path_bandwidth = max(0, current_path_bandwidth) # Ensure non-negative

                actual_data_rate_mbps = min(flow.bandwidth_requirement_mbps, current_path_bandwidth)

                is_completed = flow.update_progress(current_time, actual_data_rate_mbps, current_path_latency)

                if is_completed:
                    flows_to_remove.append(flow_id)
                    self.completed_flows[flow_id] = flow
                    # Free up bandwidth on the path
                    if actual_path_link_ids:
                        for link_id in actual_path_link_ids:
                            self.network.update_link_capacity_used(link_id, -flow.bandwidth_requirement_mbps)
                    self.flow_completion_times[flow.traffic_class_name].append(current_time - flow.start_time)
                    # Decrement active connections for this path
                    if flow.assigned_path_link_ids:
                        self.path_active_connections[flow.assigned_path_link_ids] -= 1
                elif flow.status == "dropped":
                    flows_to_remove.append(flow_id)
                    self.dropped_flows[flow.flow_id] = flow
                    # If dropped, ensure its bandwidth is freed if it was allocated
                    if actual_path_link_ids:
                        for link_id in actual_path_link_ids:
                            self.network.update_link_capacity_used(link_id, -flow.bandwidth_requirement_mbps)
                    # Decrement active connections for this path
                    if flow.assigned_path_link_ids:
                        self.path_active_connections[flow.assigned_path_link_ids] -= 1


        for flow_id in flows_to_remove:
            if flow_id in self.active_flows:
                del self.active_flows[flow_id]

    def collect_metrics(self, current_time: float):
        """
        Collects network-wide metrics for plotting and analysis.
        """
        total_used_bw = 0
        total_available_bw = 0
        link_utilizations = []
        traffic_class_bw = defaultdict(float)

        for link_id, link_info in self.network.links.items():
            total_used_bw += link_info['capacity_used']
            total_available_bw += link_info['bandwidth']
            if link_info['bandwidth'] > 0:
                link_utilizations.append(link_info['capacity_used'] / link_info['bandwidth'])

        avg_utilization = sum(link_utilizations) / len(link_utilizations) if link_utilizations else 0
        self.total_bandwidth_utilization[current_time] = avg_utilization * 100 # Percentage

        # Calculate bandwidth utilization per traffic class
        # This collection happens for both AFMS and Non-AFMS,
        # as the plotting function will then aggregate for Non-AFMS.
        for flow_id, flow in self.active_flows.items():
            # This is an approximation. A more accurate way would be to track
            # actual data rate for each flow on its assigned path.
            # For simplicity, we'll assume flows are getting their requested BW if active.
            traffic_class_bw[flow.traffic_class_name] += flow.bandwidth_requirement_mbps

        for class_name, bw_mbps in traffic_class_bw.items():
            self.traffic_class_bw_utilization[current_time][class_name] = bw_mbps

        # Store general metrics for plotting
        self.metrics_history['active_flows'][current_time].append(len(self.active_flows))
        self.metrics_history['completed_flows'][current_time].append(len(self.completed_flows))
        # For dropped flows, we should track cumulative drops
        self.metrics_history['dropped_flows'][current_time].append(len(self.dropped_flows))
        self.metrics_history['avg_link_utilization'][current_time].append(avg_utilization)

    def get_simulation_results(self) -> dict:
        """
        Returns all collected simulation results for plotting.
        """
        return {
            "metrics_history": self.metrics_history,
            "total_bandwidth_utilization": self.total_bandwidth_utilization,
            "traffic_class_bw_utilization": self.traffic_class_bw_utilization,
            "flow_completion_times": self.flow_completion_times,
            "afms_enabled": self.afms_enabled,
            "network_config": NETWORK_CONFIG,
            "traffic_classes": TRAFFIC_CLASSES,
            "simulation_params": SIMULATION_PARAMS,
            "completed_flows": self.completed_flows,
            "dropped_flows": self.dropped_flows
        }

# Example Usage (for testing purposes)
if __name__ == "__main__":
    import uuid
    import time
    from flow import Flow

    # 1. Initialize Network Topology
    topology = NetworkTopology()

    # 2. Initialize Path Selector
    path_selector = PathSelector(topology)

    # 3. Initialize Segment Router
    segment_router = SegmentRouter(topology)

    # 4. Initialize Network State Predictor
    cnsp = NetworkStatePredictor(topology)

    # 5. Initialize WRR Manager
    wrr_manager = WRRManager(topology)

    # 6. Initialize DRO (AFMS enabled)
    dro_afms = DynamicRoutingOptimizer(topology, path_selector, segment_router, cnsp, wrr_manager, afms_enabled=True)
    # 7. Initialize DRO (AFMS disabled for comparison)
    dro_non_afms = DynamicRoutingOptimizer(topology, path_selector, segment_router, cnsp, wrr_manager, afms_enabled=False)


    print("\n--- Simulating DRO behavior with new flows ---")
    simulation_duration = SIMULATION_PARAMS["simulation_duration_s"]
    metrics_interval = SIMULATION_PARAMS["metrics_collection_interval_s"]
    cnsp_update_interval = SIMULATION_PARAMS["cnsp_update_interval_s"]
    wrr_update_interval = SIMULATION_PARAMS["wrr_update_interval_s"]
    flow_arrival_rate = SIMULATION_PARAMS["flow_arrival_rate_per_s"]

    # Store flows for both simulations
    all_flows_afms = []
    all_flows_non_afms = []

    # Simulate time steps
    last_cnsp_update_time = -cnsp_update_interval
    last_wrr_update_time = -wrr_update_interval

    for t in range(0, simulation_duration + 1, metrics_interval):
        current_time = float(t)
        print(f"\n--- Simulation Time: {current_time:.2f}s ---")

        # CNSP Update (less frequent)
        if current_time - last_cnsp_update_time >= cnsp_update_interval:
            cnsp_update = cnsp.generate_update_for_dro(current_time)
            dro_afms.receive_cnsp_update(cnsp_update)
            # Non-AFMS DRO doesn't use predicted state, so no update needed
            last_cnsp_update_time = current_time

        # WRR Manager Update (less frequent)
        if current_time - last_wrr_update_time >= wrr_update_interval:
            # WRR weights are updated based on predicted state for AFMS
            predicted_state = cnsp.generate_update_for_dro(current_time)['predicted_link_metrics']
            wrr_manager.update_weights(current_time, predicted_network_state=predicted_state)
            last_wrr_update_time = current_time

        # Simulate new flow arrivals
        num_new_flows = int(flow_arrival_rate * metrics_interval) + (1 if random.random() < (flow_arrival_rate * metrics_interval) % 1 else 0)
        for _ in range(num_new_flows):
            flow_id = str(uuid.uuid4())
            src_ip = NETWORK_CONFIG["edge_router_ips"][random.randint(0, len(NETWORK_CONFIG["edge_router_ips"]) - 1)] # Random edge router as source
            dst_ip = NETWORK_CONFIG["core_router_ips"][random.randint(0, len(NETWORK_CONFIG["core_router_ips"]) - 1)] # Random core router as dest
            traffic_class_name = random.choice(list(TRAFFIC_CLASSES.keys()))
            
            new_flow_afms = Flow(flow_id + "_afms", src_ip, dst_ip, traffic_class_name, current_time)
            new_flow_non_afms = Flow(flow_id + "_non_afms", src_ip, dst_ip, traffic_class_name, current_time)

            dro_afms.handle_new_flow(new_flow_afms, current_time)
            dro_non_afms.handle_new_flow(new_flow_non_afms, current_time)

            all_flows_afms.append(new_flow_afms)
            all_flows_non_afms.append(new_flow_non_afms)

        # Update flow progress for both DRO instances
        dro_afms.update_flow_progress(current_time)
        dro_non_afms.update_flow_progress(current_time)

        # Collect metrics for both DRO instances
        dro_afms.collect_metrics(current_time)
        dro_non_afms.collect_metrics(current_time)

        # Print some summary for active flows
        print(f"  AFMS Active Flows: {len(dro_afms.active_flows)}, Completed: {len(dro_afms.completed_flows)}, Dropped: {len(dro_afms.dropped_flows)}")
        print(f"  Non-AFMS Active Flows: {len(dro_non_afms.active_flows)}, Completed: {len(dro_non_afms.completed_flows)}, Dropped: {len(dro_non_afms.dropped_flows)}")

    print("\n--- Simulation Complete ---")

    # Get final results
    results_afms = dro_afms.get_simulation_results()
    results_non_afms = dro_non_afms.get_simulation_results()

    # You would pass these results to plot.py
    print("\nAFMS Simulation Results Summary:")
    print(f"  Total Completed Flows: {len(results_afms['completed_flows'])}")
    print(f"  Total Dropped Flows: {len(results_afms['dropped_flows'])}")

    print("\nNon-AFMS Simulation Results Summary:")
    print(f"  Total Completed Flows: {len(results_non_afms['completed_flows'])}")
    print(f"  Total Dropped Flows: {len(results_non_afms['dropped_flows'])}")

#  TEST - Remove it 
    print("\nTraffic-Classes Avg Link Utilization over time:", results_afms['metrics_history']['avg_link_utilization'])
    print("\nNon-Traffic-Classes Avg Link Utilization over time:", results_non_afms['metrics_history']['avg_link_utilization'])
