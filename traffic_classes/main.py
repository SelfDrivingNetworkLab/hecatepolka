# main.py (Main Simulation)

import uuid
import time
import random
import numpy as np # Added numpy import

# Import all modules
from config import NETWORK_CONFIG, TRAFFIC_CLASSES, SIMULATION_PARAMS, generate_random_ip
from flow import Flow
from enfc import FlowFeatureExtractor
from seg_routing import NetworkTopology, PathSelector, SegmentRouter
from cnsp import NetworkStatePredictor
from wrr_manager import WRRManager
from dro import DynamicRoutingOptimizer
from plot import plot_traffic_class_bandwidth, plot_bandwidth_increase, plot_flow_completion_times, plot_dropped_flows,plot_total_bandwidth_comparison

def run_simulation():
    """
    Orchestrates the entire network simulation, running both AFMS and Non-AFMS scenarios
    and then plotting the results.
    """
    print("--- Initializing Network Components ---")

    # 1. Initialize Network Topology
    topology = NetworkTopology()

    # 2. Initialize Path Selector (uses the topology)
    path_selector = PathSelector(topology)

    # 3. Initialize Segment Router (uses the topology)
    segment_router = SegmentRouter(topology)

    # 4. Initialize Network State Predictor (CNSP)
    #    It needs the topology to observe current state.
    cnsp = NetworkStatePredictor(topology)

    # 5. Initialize WRR Manager
    #    It needs the topology to define paths and potentially get link info.
    wrr_manager = WRRManager(topology)

    # 6. Initialize two DRO instances for comparison
    #    One with AFMS enabled, one with AFMS disabled.
    dro_afms = DynamicRoutingOptimizer(topology, path_selector, segment_router, cnsp, wrr_manager, afms_enabled=True)
    dro_non_afms = DynamicRoutingOptimizer(topology, path_selector, segment_router, cnsp, wrr_manager, afms_enabled=False)

    print("\n--- Starting Simulation ---")
    
    simulation_duration = SIMULATION_PARAMS["simulation_duration_s"]
    metrics_interval = SIMULATION_PARAMS["metrics_collection_interval_s"]
    cnsp_update_interval = SIMULATION_PARAMS["cnsp_update_interval_s"]
    wrr_update_interval = SIMULATION_PARAMS["wrr_update_interval_s"]
    flow_arrival_rate = SIMULATION_PARAMS["flow_arrival_rate_per_s"]

    # Track last update times for CNSP and WRR to control their update frequency
    last_cnsp_update_time = -cnsp_update_interval # Ensures first update happens at t=0
    last_wrr_update_time = -wrr_update_interval # Ensures first update happens at t=0

    # Main simulation loop
    for t in range(0, simulation_duration + 1, metrics_interval):
        current_time = float(t)
        print(f"\n--- Simulation Time: {current_time:.2f}s ---")

        # --- CNSP Update ---
        # CNSP provides predicted network state to DRO (AFMS enabled)
        if current_time - last_cnsp_update_time >= cnsp_update_interval:
            cnsp_update_message = cnsp.generate_update_for_dro(current_time)
            dro_afms.receive_cnsp_update(cnsp_update_message)
            # Non-AFMS DRO does not receive predicted state
            last_cnsp_update_time = current_time
            # print(f"  CNSP updated at {current_time:.2f}s")

        # --- WRR Manager Update ---
        # WRR weights are updated based on predicted state (for AFMS)
        if current_time - last_wrr_update_time >= wrr_update_interval:
            # For AFMS, WRR uses CNSP's prediction to adjust weights
            predicted_state_for_wrr = cnsp.generate_update_for_dro(current_time)['predicted_link_metrics']
            wrr_manager.update_weights(current_time, predicted_network_state=predicted_state_for_wrr, active_flows=dro_afms.active_flows)
            # For Non-AFMS, WRR weights remain static (or based on simpler heuristics)
            # wrr_manager.update_weights(current_time, predicted_network_state=None, active_flows=None) # Can call with None for non-AFMS
            last_wrr_update_time = current_time
            # print(f"  WRR weights updated at {current_time:.2f}s: {wrr_manager.get_weights()}")


        # --- Simulate New Flow Arrivals ---
        # Use Poisson distribution for flow arrivals (average_rate * interval)
        num_new_flows = np.random.poisson(flow_arrival_rate * metrics_interval)
        if num_new_flows == 0 and random.random() < (flow_arrival_rate * metrics_interval) % 1:
            num_new_flows = 1 # Ensure at least one flow if fractional part suggests it

        for _ in range(num_new_flows):
            flow_id = str(uuid.uuid4())
            src_ip = random.choice(NETWORK_CONFIG["edge_router_ips"]) # Random edge router as source
            dst_ip = random.choice(NETWORK_CONFIG["core_router_ips"]) # Random core router as dest
            traffic_class_name = random.choice(list(TRAFFIC_CLASSES.keys()))
            
            # Create two identical flows for both simulation runs
            new_flow_afms = Flow(flow_id + "_afms", src_ip, dst_ip, traffic_class_name, current_time)
            new_flow_non_afms = Flow(flow_id + "_non_afms", src_ip, dst_ip, traffic_class_name, current_time)

            # Handle new flows with respective DRO instances
            dro_afms.handle_new_flow(new_flow_afms, current_time)
            dro_non_afms.handle_new_flow(new_flow_non_afms, current_time)

        # --- Update Existing Flow Progress ---
        dro_afms.update_flow_progress(current_time)
        dro_non_afms.update_flow_progress(current_time)

        # --- Collect Metrics ---
        dro_afms.collect_metrics(current_time)
        dro_non_afms.collect_metrics(current_time)

        # Print summary for current time step
        print(f"  AFMS Active: {len(dro_afms.active_flows)}, Completed: {len(dro_afms.completed_flows)}, Dropped: {len(dro_afms.dropped_flows)}")
        print(f"  Non-AFMS Active: {len(dro_non_afms.active_flows)}, Completed: {len(dro_non_afms.completed_flows)}, Dropped: {len(dro_non_afms.dropped_flows)}")

    print("\n--- Simulation Complete ---")

    # Get final simulation results from both DRO instances
    results_afms = dro_afms.get_simulation_results()
    results_non_afms = dro_non_afms.get_simulation_results()

    print("\n--- Plotting Results ---")
    plot_traffic_class_bandwidth(results_afms, results_non_afms)
    print("\nPlotting complete. Please close the plot windows to continue.")

if __name__ == "__main__":
    run_simulation()
