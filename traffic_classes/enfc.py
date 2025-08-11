# enfc.py (Edge Network Flow Classifier / Feature Extractor)

from flow import Flow
from config import TRAFFIC_CLASSES, NETWORK_CONFIG, generate_random_ip # Added generate_random_ip here

class FlowFeatureExtractor:
    """
    Extracts relevant features from a network flow object and potentially
    other network context for use by modules like CNSP or DRO.
    These features can be used for prediction, classification, or load balancing decisions.
    """
    def __init__(self):
        """
        Initializes the feature extractor. No specific parameters needed yet,
        but could be extended for configuration or model loading if using ML.
        """
        pass

    def extract_features(self, flow: Flow, current_time: float) -> dict:
        """
        Extracts a dictionary of features from a given Flow object.

        Args:
            flow (Flow): The Flow object from which to extract features.
            current_time (float): The current simulation time, useful for calculating
                                  dynamic features like elapsed duration.

        Returns:
            dict: A dictionary containing extracted features.
                  Example features include:
                  - 'flow_id'
                  - 'traffic_class_name'
                  - 'priority'
                  - 'latency_sensitivity'
                  - 'dscp'
                  - 'bandwidth_requirement_mbps'
                  - 'total_data_bytes'
                  - 'data_transferred_bytes'
                  - 'remaining_data_bytes'
                  - 'flow_status'
                  - 'elapsed_duration_s'
                  - 'remaining_duration_s'
                  - 'actual_latency_ms' (if available)
                  - 'packets_sent'
                  - 'packets_dropped'
        """
        features = {
            "flow_id": flow.flow_id,
            "source_ip": flow.source_ip,
            "destination_ip": flow.destination_ip,
            "traffic_class_name": flow.traffic_class_name,
            "priority": flow.priority,
            "latency_sensitivity": flow.latency_sensitivity,
            "dscp": flow.dscp,
            "bandwidth_requirement_mbps": flow.bandwidth_requirement_mbps,
            "total_data_bytes": flow.total_data_bytes,
            "data_transferred_bytes": flow.data_transferred_bytes,
            "remaining_data_bytes": flow.get_remaining_data_bytes(),
            "flow_status": flow.status,
            "actual_latency_ms": flow.actual_latency_ms,
            "packets_sent": flow.packets_sent,
            "packets_dropped": flow.packets_dropped,
            "current_path": flow.current_path,
        }

        # Calculate dynamic features based on current time
        features["elapsed_duration_s"] = current_time - flow.start_time
        features["remaining_duration_s"] = max(0, flow.duration_s - features["elapsed_duration_s"])

        # Add specific flags or derived features based on traffic class properties
        features["is_long_living"] = (flow.traffic_class_name == "long_living")
        features["is_short_living"] = (flow.traffic_class_name == "short_living")
        features["is_real_time"] = (flow.traffic_class_name == "low_latency") # Using low_latency for real_time

        return features

    def get_feature_vector(self, flow: Flow, current_time: float) -> list:
        """
        Extracts a numerical feature vector from a given Flow object.
        This is useful for machine learning models that expect numerical inputs.
        The order of features in the vector must be consistent.

        Args:
            flow (Flow): The Flow object from which to extract features.
            current_time (float): The current simulation time.

        Returns:
            list: A list of numerical features.
        """
        features = self.extract_features(flow, current_time)

        # Define the order of numerical features for the vector
        # Ensure this order is consistent if used with a trained ML model
        feature_vector = [
            features["priority"],
            features["latency_sensitivity"],
            features["bandwidth_requirement_mbps"],
            features["total_data_bytes"],
            features["data_transferred_bytes"],
            features["remaining_data_bytes"],
            features["elapsed_duration_s"],
            features["remaining_duration_s"],
            features["actual_latency_ms"],
            features["packets_sent"],
            features["packets_dropped"],
            # Binary flags for traffic classes (one-hot encoding style)
            1 if features["traffic_class_name"] == "low_latency" else 0,
            1 if features["traffic_class_name"] == "critical_signaling" else 0,
            1 if features["traffic_class_name"] == "high_throughput" else 0,
            1 if features["traffic_class_name"] == "long_living" else 0,
            1 if features["traffic_class_name"] == "short_living" else 0,
            1 if features["traffic_class_name"] == "intent_based" else 0,
            1 if features["traffic_class_name"] == "default_flows" else 0,
        ]
        return feature_vector

# Example Usage (for testing purposes)
if __name__ == "__main__":
    import uuid
    import random
    # from config import NETWORK_CONFIG # Import NETWORK_CONFIG for IP generation - no longer needed as generate_random_ip is imported directly

    # Simulate a network environment to generate IPs
    edge_ip_prefix = NETWORK_CONFIG["edge_router_ips"][0].rsplit('.', 1)[0]
    core_ip = NETWORK_CONFIG["core_router_ips"][0]

    # Create a dummy flow- Remeber we can do PCAP later 
    flow_id = str(uuid.uuid4())
    src_ip = generate_random_ip(edge_ip_prefix)
    dst_ip = core_ip
    traffic_class_name = random.choice(list(TRAFFIC_CLASSES.keys()))
    start_time = 0.0
    test_flow = Flow(flow_id, src_ip, dst_ip, traffic_class_name, start_time)

    extractor = FlowFeatureExtractor()

    # Simulate some time passing and flow progress
    current_sim_time = 10.5
    # Manually update flow progress for demonstration (normally done by simulation loop)
    test_flow.update_progress(current_sim_time, test_flow.bandwidth_requirement_mbps * 0.8, 15.0)
    test_flow.packets_sent = 1000
    test_flow.packets_dropped = 5

    print(f"Original Flow: {test_flow}")

    # Extract features
    features = extractor.extract_features(test_flow, current_sim_time)
    print("\nExtracted Features (Dictionary):")
    for key, value in features.items():
        print(f"  {key}: {value}")

    # Get feature vector
    feature_vector = extractor.get_feature_vector(test_flow, current_sim_time)
    print("\nExtracted Feature Vector (List):")
    print(feature_vector)

    # Demonstrate with another flow type
    print("\n--- Testing with another flow type (Short-Living) ---")
    flow_id_2 = str(uuid.uuid4())
    traffic_class_name_2 = "short_living"
    test_flow_2 = Flow(flow_id_2, src_ip, dst_ip, traffic_class_name_2, start_time)
    features_2 = extractor.extract_features(test_flow_2, current_sim_time)
    print(f"Original Flow 2: {test_flow_2}")
    print("\nExtracted Features (Dictionary) for Flow 2:")
    for key, value in features_2.items():
        print(f"  {key}: {value}")
