ALGORITHM NetworkSimulationConfiguration
// This algorithm defines network, traffic, simulation, and load balancing settings.
// It also provides a utility for generating random client IPs.

BEGIN
    IMPORT random_module

    // ------------------------------
    // 1. DEFINE NETWORK CONFIGURATION
    // ------------------------------
    SET NETWORK_CONFIG ← DICTIONARY(
        num_core_routers: 2,
        num_edge_routers: 2,
        core_router_ips: ["10.0.0.1", "10.0.0.2"],
        edge_router_ips: ["192.168.1.1", "192.168.1.2"],
        ip_range_start: 100,
        ip_range_end: 254,
        base_bandwidth_mbps: 1000,
        base_latency_ms: 5,
        link_capacity_variance: 0.2,
        link_latency_variance: 0.2
    )

    // ------------------------------
    // 2. DEFINE TRAFFIC CLASSES
    // ------------------------------
    SET TRAFFIC_CLASSES ← DICTIONARY(
        low_latency: { priority: 5, latency_sensitivity: 0.95, bandwidth_range: (0.5, 2), duration_range: (5, 15),
                       packet_size_range: (60, 200), description: "...", dscp: "EF", color: "red" },
        critical_signaling: { priority: 6, latency_sensitivity: 0.9, bandwidth_range: (0.1, 0.5), duration_range: (1, 10),
                              packet_size_range: (100, 500), description: "...", dscp: "CS5", color: "darkorange" },
        high_throughput: { priority: 3, latency_sensitivity: 0.5, bandwidth_range: (20, 200), duration_range: (60, 300),
                           packet_size_range: (1500, 9000), description: "...", dscp: "AF31", color: "green" },
        long_living: { priority: 2, latency_sensitivity: 0.2, bandwidth_range: (5, 50), duration_range: (180, 600),
                       packet_size_range: (1000, 5000), description: "...", dscp: "AF21", color: "blue" },
        short_living: { priority: 1, latency_sensitivity: 0.6, bandwidth_range: (0.1, 1), duration_range: (0.1, 5),
                        packet_size_range: (64, 500), description: "...", dscp: "AF11", color: "purple" },
        intent_based: { priority: 4, latency_sensitivity: 0.8, bandwidth_range: (0.5, 5), duration_range: (10, 60),
                        packet_size_range: (100, 1500), description: "...", dscp: "Custom", color: "orange" },
        default_flows: { priority: 0, latency_sensitivity: 0.1, bandwidth_range: (0.1, 1), duration_range: (20, 90),
                         packet_size_range: (200, 1000), description: "...", dscp: "BE", color: "gray" }
    )

    // ------------------------------
    // 3. DEFINE SIMULATION PARAMETERS
    // ------------------------------
    SET SIMULATION_PARAMS ← DICTIONARY(
        simulation_duration_s: 300,
        flow_arrival_rate_per_s: 1.5,
        metrics_collection_interval_s: 1,
        cnsp_update_interval_s: 5,
        wrr_update_interval_s: 10
    )

    // ------------------------------
    // 4. DEFINE INITIAL LOAD BALANCING WEIGHTS
    // ------------------------------
    SET INITIAL_WRR_WEIGHTS ← DICTIONARY(
        path_E1_C1_E2: 1,
        path_E1_C2_E2: 1,
        path_E1_C1_C2_E2: 1,
        path_E1_C2_C1_E2: 1,
        path_E2_C1_E1: 1,
        path_E2_C2_E1: 1
    )

    // ------------------------------
    // 5. DEFINE RANDOM IP GENERATOR FUNCTION
    // ------------------------------
    FUNCTION GENERATE_RANDOM_IP(edge_router_ip_prefix)
        RETURN CONCAT(edge_router_ip_prefix, ".", RANDOM_INTEGER(
            NETWORK_CONFIG.ip_range_start, NETWORK_CONFIG.ip_range_end))
    END FUNCTION

    // ------------------------------
    // 6. MAIN TEST BLOCK
    // ------------------------------
    IF FILE_IS_EXECUTED_DIRECTLY THEN
        PRINT "Network Configuration:"
        FOR EACH key, value IN NETWORK_CONFIG
            PRINT key, value
        END FOR

        PRINT "Traffic Classes:"
        FOR EACH class_name, parameters IN TRAFFIC_CLASSES
            PRINT class_name
            FOR EACH param_key, param_value IN parameters
                PRINT param_key, param_value
            END FOR
        END FOR

        PRINT "Simulation Parameters:"
        FOR EACH key, value IN SIMULATION_PARAMS
            PRINT key, value
        END FOR

        PRINT "Example Generated IP:"
        SET prefix ← SPLIT_LAST(NETWORK_CONFIG.edge_router_ips[0], ".")[0..-2]
        PRINT GENERATE_RANDOM_IP(prefix)
    END IF
END
