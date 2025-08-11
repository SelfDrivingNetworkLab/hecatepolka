# config.py
import random

# --- Network Configuration ---
NETWORK_CONFIG = {
    "num_core_routers": 2,
    "num_edge_routers": 2,
    "core_router_ips": ["10.0.0.1", "10.0.0.2"],
    "edge_router_ips": ["192.168.1.1", "192.168.1.2"],
    "ip_range_start": 100, # For client IPs connected to edge nodes
    "ip_range_end": 254,
    "base_bandwidth_mbps": 1000, # Base bandwidth for links in Mbps
    "base_latency_ms": 5,      # Base latency for links in ms
    "link_capacity_variance": 0.2, # +/- 20% variance for link capacity (Increased from 0.1)
    "link_latency_variance": 0.2,  # +/- 20% variance for link latency
}

# --- Traffic Class Definitions ---
# Each traffic class has specific characteristics that influence its behavior
# and how load balancing algorithms might prioritize it.
TRAFFIC_CLASSES = {
    "low_latency": { # traffic_ID:0 - Low Latency
        "priority": 5, # High priority
        "latency_sensitivity": 0.95, # Highly sensitive to latency
        "bandwidth_requirement_mbps": (0.5, 2), # Typical bandwidth range
        "flow_duration_s": (5, 15), # Shorter duration flows, min 5 sec
        "packet_size_bytes": (60, 200), # Smaller packets
        "description": "Designed to provide a high-priority, low-latency, low-loss, and low-jitter EF",
        "dscp": "EF", # Expedited Forwarding
        "color": "red"
    },
    "critical_signaling": { # traffic_ID:1 - Priority
        "priority": 6, # Even higher priority for critical signaling
        "latency_sensitivity": 0.9,
        "bandwidth_requirement_mbps": (0.1, 0.5), # Very low bandwidth, small total bytes
        "flow_duration_s": (1, 10), # Very short duration
        "packet_size_bytes": (100, 500),
        "description": "Identified by the critical IP address, total bytes are less than 1MB, duration is less than 1 min or very small.",
        "dscp": "CS5", # Control Plane Signaling
        "color": "darkorange"
    },
    "high_throughput": { # traffic_ID:2 - High throughput
        "priority": 3, # Medium-high priority
        "latency_sensitivity": 0.5,
        "bandwidth_requirement_mbps": (20, 200), # High bandwidth bursts
        "flow_duration_s": (60, 300), # Significant duration
        "packet_size_bytes": (1500, 9000), # Larger packets
        "description": "Larger bytes, higher IAT, significant duration, wants higher BW, packet size is more, significant flow duration.",
        "dscp": "AF31", # Assured Forwarding 31
        "color": "green"
    },
    "long_living": { # traffic_ID:3 - Long living
        "priority": 2, # Medium priority
        "latency_sensitivity": 0.2,
        "bandwidth_requirement_mbps": (5, 50),
        "flow_duration_s": (180, 600), # Very long duration
        "packet_size_bytes": (1000, 5000),
        "description": "Data transfer / backup. Long duration and total bytes are more. They maintain state for extended periods of time.",
        "dscp": "AF21", # Assured Forwarding 21
        "color": "blue"
    },
    "short_living": { # traffic_ID:4 - Short-Living
        "priority": 1, # Low priority
        "latency_sensitivity": 0.6,
        "bandwidth_requirement_mbps": (0.1, 1),
        "flow_duration_s": (0.1, 5), # Very short duration
        "packet_size_bytes": (64, 500), # Small byte size
        "description": "DNS, HTTP, HTTPS, NTP. Very Short duration and small byte size. They typically request response interaction.",
        "dscp": "AF11", # Assured Forwarding 11
        "color": "purple"
    },
    "intent_based": { # traffic_ID:5 - Intent-Based
        "priority": 4, # Custom priority
        "latency_sensitivity": 0.8,
        "bandwidth_requirement_mbps": (0.5, 5),
        "flow_duration_s": (10, 60),
        "packet_size_bytes": (100, 1500),
        "description": "DTN server, customer server - dest IP match, small packet size, low IAT.",
        "dscp": "Custom", # Custom DSCP value, can be defined as needed
        "color": "orange"
    },
    "default_flows": { # traffic_ID:6 - Default Flows
        "priority": 0, # Lowest priority
        "latency_sensitivity": 0.1,
        "bandwidth_requirement_mbps": (0.1, 1),
        "flow_duration_s": (20, 90),
        "packet_size_bytes": (200, 1000),
        "description": "Best efforts, when it does match any of the above criteria.",
        "dscp": "BE", # Best Effort (DSCP 0)
        "color": "gray"
    }
}

# --- Simulation / I am nt using CAIDA data ---
SIMULATION_PARAMS = {
    "simulation_duration_s": 300, # Total simulation time in seconds
    "flow_arrival_rate_per_s": 1.5, # Average new flows per second (Increased from 0.5)
    "metrics_collection_interval_s": 1, # How often to collect metrics
    "cnsp_update_interval_s": 5, # How often CNSP provides updates to DRO
    "wrr_update_interval_s": 10, # How often WRR weights are re-evaluated
}

# --- Load Balancing Algorithm Weights/Priorities (Initial) ---
# These can be dynamically adjusted by WRR Manager or DRO
INITIAL_WRR_WEIGHTS = {
    "path_E1_C1_E2": 1,
    "path_E1_C2_E2": 1,
    "path_E1_C1_C2_E2": 1,
    "path_E1_C2_C1_E2": 1,
    "path_E2_C1_E1": 1,
    "path_E2_C2_E1": 1,
}

# ---generating random IPs ---
def generate_random_ip(edge_router_ip_prefix):
    """Generates a random IP address within a specified range for a client connected to an edge router."""
    return f"{edge_router_ip_prefix}.{random.randint(NETWORK_CONFIG['ip_range_start'], NETWORK_CONFIG['ip_range_end'])}"

# Example usage (for testing purposes)
if __name__ == "__main__":
    print("Network Configuration:")
    for key, value in NETWORK_CONFIG.items():
        print(f"  {key}: {value}")

    print("\nTraffic Classes:")
    for name, params in TRAFFIC_CLASSES.items():
        print(f"  {name}:")
        for key, value in params.items():
            print(f"    {key}: {value}")

    print("\nSimulation Parameters:")
    for key, value in SIMULATION_PARAMS.items():
        print(f"  {key}: {value}")

    print("\nExample Generated IP:")
    print(generate_random_ip(NETWORK_CONFIG["edge_router_ips"][0].rsplit('.', 1)[0]))
