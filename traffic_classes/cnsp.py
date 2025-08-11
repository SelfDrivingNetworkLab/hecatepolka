# cnsp.py (Core Network State Predictor/CNP)

import random
from seg_routing import NetworkTopology # Import NetworkTopology to get network state
from enfc import FlowFeatureExtractor # Potentially use flow features for prediction
from config import SIMULATION_PARAMS

class NetworkStatePredictor:
    """
    Predicts future network state (e.g., latency, congestion) based on current
    observations and historical data (simulated).
    In a real system, this would involve sophisticated ML models.
    For this simulation, it will provide a slightly "forward-looking" view
    based on current metrics with some simulated trends or noise.
    """
    def __init__(self, network_topology: NetworkTopology, feature_extractor: FlowFeatureExtractor = None):
        """
        Initializes the Network State Predictor.

        Args:
            network_topology (NetworkTopology): The network topology object to query for current state.
            feature_extractor (FlowFeatureExtractor, optional): An instance of FlowFeatureExtractor
                                                                if flow-specific features are needed for prediction.
        """
        self.network = network_topology
        self.feature_extractor = feature_extractor
        self.history = {} # Stores historical link metrics for simple trend analysis if needed
                          # {link_id: [{'time': t, 'latency': l, 'capacity_used': cu}, ...]}

    def collect_current_state(self, current_time: float) -> dict:
        """
        Collects the current state of all links in the network.

        Args:
            current_time (float): The current simulation time.

        Returns:
            dict: A dictionary where keys are link IDs and values are their current metrics.
        """
        current_metrics = {}
        for link_id, link_info in self.network.links.items():
            current_metrics[link_id] = {
                'source': link_info['source'],
                'dest': link_info['dest'],
                'latency': link_info['latency'],
                'bandwidth': link_info['bandwidth'],
                'capacity_used': link_info['capacity_used'],
                'utilization': link_info['capacity_used'] / link_info['bandwidth'] if link_info['bandwidth'] > 0 else 0,
                'available_bandwidth': link_info['bandwidth'] - link_info['capacity_used']
            }
            # Store in history (simple FIFO, keep last N points)
            if link_id not in self.history:
                self.history[link_id] = []
            self.history[link_id].append({'time': current_time, **current_metrics[link_id]})
            # Keep only the last 10 entries for history
            self.history[link_id] = self.history[link_id][-10:]
        return current_metrics

    def predict_future_state(self, current_time: float, prediction_horizon_s: float) -> dict:
        """
        Predicts the network state at a given prediction horizon.
        For this simulation, it uses a simple heuristic:
        - Latency: Current latency + a small random fluctuation.
        - Congestion: Current utilization + a slight trend based on recent history,
                      plus some random noise to simulate unpredictable bursts.

        Args:
            current_time (float): The current simulation time.
            prediction_horizon_s (float): How far into the future to predict (in seconds).

        Returns:
            dict: A dictionary of predicted link metrics for the future state.
                  Keys are link IDs, values are predicted metrics.
        """
        current_state = self.collect_current_state(current_time)
        predicted_state = {}

        for link_id, metrics in current_state.items():
            predicted_latency = metrics['latency']
            predicted_utilization = metrics['utilization']

            # More intelligent prediction logic:
            # 1. Add some random noise to latency
            predicted_latency += random.uniform(-0.5, 0.5) # +/- 0.5 ms
            predicted_latency = max(0.1, predicted_latency) # Latency cannot be zero or negative

            # 2. Simulate a slight trend for utilization based on recent history
            #    If utilization was increasing, predict it continues to increase slightly, especially if high.
            #    If utilization was decreasing, predict it continues to decrease slightly.
            if link_id in self.history and len(self.history[link_id]) >= 2:
                u_prev = self.history[link_id][-2]['utilization']
                u_curr = self.history[link_id][-1]['utilization']
                
                utilization_change = u_curr - u_prev

                # Trend-based prediction
                if utilization_change > 0: # Utilization is increasing
                    # Predict a further increase, potentially more if already high
                    predicted_utilization += random.uniform(0.01, 0.05) + (utilization_change * 0.5)
                elif utilization_change < 0: # Utilization is decreasing
                    predicted_utilization += random.uniform(-0.01, -0.03) + (utilization_change * 0.5)
                # If no change, slight random fluctuation

            # 3. Add some random noise to utilization prediction
            predicted_utilization += random.uniform(-0.02, 0.02) # +/- 2% noise

            # Clamp utilization between 0 and 1
            predicted_utilization = max(0.0, min(1.0, predicted_utilization))

            predicted_bandwidth = metrics['bandwidth'] # Assume bandwidth capacity doesn't change over short horizon
            predicted_capacity_used = predicted_utilization * predicted_bandwidth
            predicted_available_bandwidth = predicted_bandwidth - predicted_capacity_used

            predicted_state[link_id] = {
                'source': metrics['source'],
                'dest': metrics['dest'],
                'predicted_latency': predicted_latency,
                'predicted_bandwidth': predicted_bandwidth,
                'predicted_capacity_used': predicted_capacity_used,
                'predicted_utilization': predicted_utilization,
                'predicted_available_bandwidth': predicted_available_bandwidth
            }
        return predicted_state

    def generate_update_for_dro(self, current_time: float) -> dict:
        """
        Generates an update message for the Dynamic Routing Optimizer (DRO)
        containing predicted network state.

        Args:
            current_time (float): The current simulation time.

        Returns:
            dict: A dictionary containing the predicted network state for DRO.
        """
        prediction_horizon = SIMULATION_PARAMS["cnsp_update_interval_s"] # Predict for the next update interval
        predicted_state = self.predict_future_state(current_time, prediction_horizon)

        update_message = {
            "timestamp": current_time,
            "prediction_horizon_s": prediction_horizon,
            "predicted_link_metrics": predicted_state
        }
        return update_message

# Example Usage (for testing purposes)
if __name__ == "__main__":
    from config import NETWORK_CONFIG
    import time

    # 1. Initialize Network Topology
    topology = NetworkTopology()

    # 2. Initialize Flow Feature Extractor (optional for CNSP, but good practice)
    feature_extractor = FlowFeatureExtractor()

    # 3. Initialize Network State Predictor
    cnsp = NetworkStatePredictor(topology, feature_extractor)

    print("\n--- Simulating CNSP updates over time ---")
    simulation_duration = SIMULATION_PARAMS["simulation_duration_s"]
    cnsp_update_interval = SIMULATION_PARAMS["cnsp_update_interval_s"]

    for t in range(0, simulation_duration + 1, cnsp_update_interval):
        current_time = float(t)
        print(f"\nSimulation Time: {current_time:.2f}s")

        # Simulate some link capacity changes over time
        # In a real simulation, this would be driven by active flows
        if current_time > 0:
            # Randomly pick a few links and increase/decrease their usage
            num_links_to_change = random.randint(1, len(topology.links) // 2 or 1)
            for _ in range(num_links_to_change):
                random_link_id = random.choice(list(topology.links.keys()))
                change_mbps = random.uniform(-100, 100) # +/- 100 Mbps
                topology.update_link_capacity_used(random_link_id, change_mbps)

        # Generate and print CNSP update
        dro_update = cnsp.generate_update_for_dro(current_time)
        print(f"CNSP Update for DRO (at {dro_update['timestamp']:.2f}s, horizon {dro_update['prediction_horizon_s']}s):")
        for link_id, metrics in dro_update['predicted_link_metrics'].items():
            print(f"  Link {link_id} ({metrics['source']}->{metrics['dest']}): "
                  f"Pred Latency={metrics['predicted_latency']:.2f}ms, "
                  f"Pred Util={metrics['predicted_utilization'] * 100:.2f}%, "
                  f"Pred Avail BW={metrics['predicted_available_bandwidth']:.2f}Mbps")

        # In a full simulation, this update would be passed to the DRO module.
        time.sleep(0.1) # Simulate time passing
