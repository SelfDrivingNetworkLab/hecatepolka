# plot.py

import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def plot_traffic_class_bandwidth(afms_results: dict, non_afms_results: dict):
    """
    Plots the bandwidth utilization over time for different traffic classes
    for AFMS, and total bandwidth utilization for Non-AFMS (as it treats all traffic uniformly).

    Args:
        afms_results (dict): Simulation results dictionary from DRO (AFMS enabled).
        non_afms_results (dict): Simulation results dictionary from DRO (AFMS disabled).
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
    fig.suptitle('Traffic Class Bandwidth Utilization Over Time', fontsize=16)

    # --- AFMS Plot ---
    ax1 = axes[0]
    afms_times = sorted(afms_results['traffic_class_bw_utilization'].keys())
    
    # Prepare data for plotting
    afms_class_data = defaultdict(list)
    for t in afms_times:
        for class_name in afms_results['traffic_classes'].keys(): # Ensure all classes are represented
            bw = afms_results['traffic_class_bw_utilization'][t].get(class_name, 0)
            afms_class_data[class_name].append(bw)

    for class_name, bws in afms_class_data.items():
        ax1.plot(afms_times, bws, label=f'{class_name} ({afms_results["traffic_classes"][class_name]["dscp"]})',
                 color=afms_results['traffic_classes'][class_name]['color'], linestyle='-')

    ax1.set_title('Traffic class Enabled (Class-Aware Routing)')
    ax1.set_ylabel('Bandwidth Utilization (Mbps)')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(loc='upper left', bbox_to_anchor=(1, 1))

    # --- Non-AFMS Plot ---
    ax2 = axes[1]
    non_afms_times = sorted(non_afms_results['traffic_class_bw_utilization'].keys())

    # Aggregate total bandwidth for Non-AFMS
    non_afms_total_bw = []
    for t in non_afms_times:
        total_bw_at_t = sum(non_afms_results['traffic_class_bw_utilization'][t].values())
        non_afms_total_bw.append(total_bw_at_t)

    ax2.plot(non_afms_times, non_afms_total_bw, label='Non-AFMS Total Bandwidth',
             color='black', linestyle='--', linewidth=2)

    ax2.set_title('No Application Aware Source Routing (Class-Agnostic Routing)')
    ax2.set_xlabel('Simulation Time (s)')
    ax2.set_ylabel('Total Bandwidth Utilization (Mbps)')
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend(loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout(rect=[0, 0.03, 0.9, 0.96]) # Adjust layout to make room for suptitle and legends
    plt.show()

def plot_bandwidth_increase(afms_results: dict, non_afms_results: dict):
    """
    Plots the percentage increase in total bandwidth utilization with AFMS vs. Non-AFMS.

    Args:
        afms_results (dict): Simulation results dictionary from DRO (AFMS enabled).
        non_afms_results (dict): Simulation results dictionary from DRO (AFMS disabled).
    """
    afms_times = sorted(afms_results['total_bandwidth_utilization'].keys())
    non_afms_times = sorted(non_afms_results['total_bandwidth_utilization'].keys())

    # Ensure both datasets cover the same time range for comparison
    common_times = sorted(list(set(afms_times) & set(non_afms_times)))

    afms_bw_util = [afms_results['total_bandwidth_utilization'].get(t, 0) for t in common_times]
    non_afms_bw_util = [non_afms_results['total_bandwidth_utilization'].get(t, 0) for t in common_times]

    percentage_increase = []
    for afms_val, non_afms_val in zip(afms_bw_util, non_afms_bw_util):
        if non_afms_val > 0:
            increase = ((afms_val - non_afms_val) / non_afms_val) * 100
        else:
            increase = 0 # Or float('nan') if you prefer to show gaps
        percentage_increase.append(increase)

    plt.figure(figsize=(12, 6))
    plt.plot(common_times, percentage_increase, color='teal', linewidth=2)
    plt.axhline(0, color='gray', linestyle='--', linewidth=0.8) # Zero line
    plt.title('Percentage Increase in Total Bandwidth Utilization (Application Aware- Traffic classes vs. Non-AATC)', fontsize=16)
    plt.xlabel('Simulation Time (s)', fontsize=12)
    plt.ylabel('Percentage Increase (%)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.fill_between(common_times, 0, percentage_increase, where=(np.array(percentage_increase) > 0),
                     facecolor='green', alpha=0.1, interpolate=True)
    plt.fill_between(common_times, 0, percentage_increase, where=(np.array(percentage_increase) < 0),
                     facecolor='red', alpha=0.1, interpolate=True)
    plt.tight_layout()
    plt.show()

def plot_flow_completion_times(afms_results: dict, non_afms_results: dict):
    """
    Plots histograms or box plots of flow completion times per traffic class for AFMS,
    and a single aggregated histogram for Non-AFMS (as it treats all traffic uniformly).

    Args:
        afms_results (dict): Simulation results dictionary from DRO (AFMS enabled).
        non_afms_results (dict): Simulation results dictionary from DRO (AFMS disabled).
    """
    traffic_classes = list(afms_results['traffic_classes'].keys())
    
    fig = plt.figure(figsize=(14, 4 * len(traffic_classes) + 4)) # Adjust figure height
    fig.suptitle('Flow Completion Times per Traffic Class (AFMS) vs. Total (Non-AFMS)', fontsize=16)

    gs = fig.add_gridspec(len(traffic_classes) + 1, 2) # +1 for the aggregated non-AFMS plot

    # --- AFMS Plots (per traffic class) ---
    for i, tc_name in enumerate(traffic_classes):
        ax_afms = fig.add_subplot(gs[i, 0])
        afms_times = afms_results['flow_completion_times'].get(tc_name, [])

        if afms_times:
            ax_afms.hist(afms_times, bins=20, color='skyblue', edgecolor='black', alpha=0.7)
            ax_afms.set_title(f'AFMS: {tc_name} (Avg: {np.mean(afms_times):.2f}s)')
        else:
            ax_afms.set_title(f'AFMS: {tc_name} (No completions)')
        ax_afms.set_ylabel('Count')
        ax_afms.grid(axis='y', linestyle='--', alpha=0.7)
        if i == len(traffic_classes) - 1: # Only last AFMS plot needs x-label
            ax_afms.set_xlabel('Completion Time (s)')

    # --- Non-AFMS Plot (aggregated) ---
    ax_non_afms_agg = fig.add_subplot(gs[:, 1]) # Span all rows in the second column

    non_afms_all_completion_times = []
    for tc_name in traffic_classes:
        non_afms_all_completion_times.extend(non_afms_results['flow_completion_times'].get(tc_name, []))

    if non_afms_all_completion_times:
        ax_non_afms_agg.hist(non_afms_all_completion_times, bins=20, color='lightcoral', edgecolor='black', alpha=0.7)
        ax_non_afms_agg.set_title(f'Non-AFMS: All Traffic Classes (Avg: {np.mean(non_afms_all_completion_times):.2f}s)')
    else:
        ax_non_afms_agg.set_title('Non-AFMS: No Completions (All Traffic Classes)')
    ax_non_afms_agg.set_xlabel('Completion Time (s)')
    ax_non_afms_agg.set_ylabel('Count (Aggregated)')
    ax_non_afms_agg.grid(axis='y', linestyle='--', alpha=0.7)


    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    plt.show()

def plot_dropped_flows(afms_results: dict, non_afms_results: dict):
    """
    Plots the number of dropped flows over time for both AFMS and Non-AFMS simulations.

    Args:
        afms_results (dict): Simulation results dictionary from DRO (AFMS enabled).
        non_afms_results (dict): Simulation results dictionary from DRO (AFMS disabled).
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    afms_times = sorted(afms_results['metrics_history']['dropped_flows'].keys())
    non_afms_times = sorted(non_afms_results['metrics_history']['dropped_flows'].keys())

    afms_dropped_counts = [afms_results['metrics_history']['dropped_flows'][t][0] for t in afms_times]
    non_afms_dropped_counts = [non_afms_results['metrics_history']['dropped_flows'][t][0] for t in non_afms_times]

    ax.plot(afms_times, afms_dropped_counts, label='AFMS Dropped Flows', color='red', linewidth=2)
    ax.plot(non_afms_times, non_afms_dropped_counts, label='Non-AFMS Dropped Flows', color='darkred', linestyle='--', linewidth=2)

    ax.set_title('Cumulative Dropped Flows Over Time', fontsize=16)
    ax.set_xlabel('Simulation Time (s)', fontsize=12)
    ax.set_ylabel('Number of Dropped Flows', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()
    plt.tight_layout()
    plt.show()

def plot_total_bandwidth_comparison(afms_results: dict, non_afms_results: dict):
    """
    Plots a bar chart comparing the average total bandwidth utilization
    for AFMS vs. Non-AFMS over the simulation duration.

    Args:
        afms_results (dict): Simulation results dictionary from DRO (AFMS enabled).
        non_afms_results (dict): Simulation results dictionary from DRO (AFMS disabled).
    """
    afms_total_bw_values = list(afms_results['total_bandwidth_utilization'].values())
    non_afms_total_bw_values = list(non_afms_results['total_bandwidth_utilization'].values())

    avg_afms_bw = np.mean(afms_total_bw_values) if afms_total_bw_values else 0
    avg_non_afms_bw = np.mean(non_afms_total_bw_values) if non_afms_total_bw_values else 0

    labels = ['Traffic_Classes-Enabled', 'Traffic_Classes_Disabled']
    avg_bandwidths = [avg_afms_bw, avg_non_afms_bw]
    colors = ['skyblue', 'lightcoral']

    plt.figure(figsize=(8, 6))
    bars = plt.bar(labels, avg_bandwidths, color=colors)
    plt.ylabel('Average Total Bandwidth Utilization (%)', fontsize=12)
    plt.title('Average Total Bandwidth Utilization: Traffic_Classes vs. Without_Traffic_Classes', fontsize=16)
    plt.ylim(0, max(avg_bandwidths) * 1.2) # Set y-limit slightly above max for better visualization
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Add value labels on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 1, round(yval, 2), ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.show()


# TEST TEST TEST 
if __name__ == "__main__":
    # Dummy data structure mimicking---- DRO's get_simulation_results output
    # In a real scenario, you would run main.py and pass its results here,I am adding ploy.py in main.py too

    # Mock TRAFFIC_CLASSES for standalone testing
    mock_traffic_classes = {
        "low_latency": {"priority": 5, "dscp": "EF", "color": "red"},
        "high_throughput": {"priority": 3, "dscp": "AF31", "color": "green"},
        "long_living": {"priority": 2, "dscp": "AF21", "color": "blue"},
        "short_living": {"priority": 1, "dscp": "AF11", "color": "purple"},
        "default_flows": {"priority": 0, "dscp": "BE", "color": "gray"},
        "critical_signaling": {"priority": 6, "dscp": "CS5", "color": "darkorange"},
        "intent_based": {"priority": 4, "dscp": "Custom", "color": "orange"},
    }

    mock_afms_results = {
        "metrics_history": {
            "active_flows": defaultdict(list),
            "completed_flows": defaultdict(list),
            "dropped_flows": defaultdict(list),
            "avg_link_utilization": defaultdict(list),
        },
        "total_bandwidth_utilization": {
            0: 50, 10: 55, 20: 60, 30: 65, 40: 70, 50: 75, 60: 80, 70: 78, 80: 75, 90: 70, 100: 65
        },
        "traffic_class_bw_utilization": {
            0: {"low_latency": 5, "high_throughput": 10, "critical_signaling": 1},
            10: {"low_latency": 7, "high_throughput": 12, "long_living": 5, "critical_signaling": 1.2},
            20: {"low_latency": 8, "high_throughput": 15, "long_living": 8, "short_living": 2, "critical_signaling": 1.5},
            30: {"low_latency": 9, "high_throughput": 18, "long_living": 10, "short_living": 3, "default_flows": 1, "critical_signaling": 1.8},
            40: {"low_latency": 10, "high_throughput": 20, "long_living": 12, "short_living": 4, "default_flows": 2, "critical_signaling": 2.0},
            50: {"low_latency": 11, "high_throughput": 22, "long_living": 15, "short_living": 5, "default_flows": 3, "critical_signaling": 2.2},
            60: {"low_latency": 10, "high_throughput": 20, "long_living": 14, "short_living": 4, "default_flows": 2, "critical_signaling": 2.0},
            70: {"low_latency": 9, "high_throughput": 18, "long_living": 12, "short_living": 3, "default_flows": 1, "critical_signaling": 1.8},
            80: {"low_latency": 8, "high_throughput": 16, "long_living": 10, "short_living": 2, "critical_signaling": 1.5},
            90: {"low_latency": 7, "high_throughput": 14, "long_living": 8, "critical_signaling": 1.2},
            100: {"low_latency": 6, "high_throughput": 12, "critical_signaling": 1.0},
        },
        "flow_completion_times": {
            "low_latency": [5.1, 6.2, 5.5, 7.0, 6.8],
            "high_throughput": [25.3, 30.1, 28.5],
            "long_living": [40.2, 45.0],
            "short_living": [1.2, 0.8, 1.5, 1.0, 2.1],
            "critical_signaling": [0.5, 0.6, 0.4],
            "intent_based": [10.0, 11.5]
        },
        "afms_enabled": True,
        "network_config": {},
        "traffic_classes": mock_traffic_classes,
        "simulation_params": {},
        "completed_flows": {"flow_afms_1": {}, "flow_afms_2": {}}, # Dummy data for count
        "dropped_flows": {"flow_afms_drop_1": {}, "flow_afms_drop_2": {}, "flow_afms_drop_3": {}},
    }

    mock_non_afms_results = {
        "metrics_history": {
            "active_flows": defaultdict(list),
            "completed_flows": defaultdict(list),
            "dropped_flows": defaultdict(list),
            "avg_link_utilization": defaultdict(list),
        },
        "total_bandwidth_utilization": {
            0: 45, 10: 50, 20: 52, 30: 55, 40: 58, 50: 60, 60: 58, 70: 55, 80: 50, 90: 45, 100: 40
        },
        "traffic_class_bw_utilization": { # This will be aggregated in the plot function
            0: {"low_latency": 4, "high_throughput": 8, "critical_signaling": 0.8},
            10: {"low_latency": 6, "high_throughput": 10, "long_living": 4, "critical_signaling": 1.0},
            20: {"low_latency": 7, "high_throughput": 12, "long_living": 6, "short_living": 1, "critical_signaling": 1.2},
            30: {"low_latency": 8, "high_throughput": 14, "long_living": 8, "short_living": 2, "default_flows": 0.5, "critical_signaling": 1.5},
            40: {"low_latency": 9, "high_throughput": 16, "long_living": 10, "short_living": 3, "default_flows": 1, "critical_signaling": 1.8},
            50: {"low_latency": 10, "high_throughput": 18, "long_living": 12, "short_living": 4, "default_flows": 2, "critical_signaling": 2.0},
            60: {"low_latency": 9, "high_throughput": 16, "long_living": 10, "short_living": 3, "default_flows": 1, "critical_signaling": 1.8},
            70: {"low_latency": 8, "high_throughput": 14, "long_living": 8, "short_living": 2, "default_flows": 0.5, "critical_signaling": 1.5},
            80: {"low_latency": 7, "high_throughput": 12, "long_living": 6, "short_living": 1, "critical_signaling": 1.2},
            90: {"low_latency": 6, "high_throughput": 10, "long_living": 4, "critical_signaling": 1.0},
            100: {"low_latency": 5, "high_throughput": 8, "critical_signaling": 0.8},
        },
        "flow_completion_times": {
            "low_latency": [6.5, 7.0, 6.0, 8.2, 7.5],
            "high_throughput": [30.5, 35.0, 32.1],
            "long_living": [50.1, 55.0],
            "short_living": [1.8, 1.5, 2.0, 1.6, 2.5],
            "critical_signaling": [0.8, 0.9, 0.7],
            "intent_based": [12.0, 13.0]
        },
        "afms_enabled": False,
        "network_config": {},
        "traffic_classes": mock_traffic_classes,
        "simulation_params": {},
        "completed_flows": {"flow_non_afms_1": {}, "flow_non_afms_2": {}}, # Dummy data for count
        "dropped_flows": {"flow_non_afms_drop_1": {}, "flow_non_afms_drop_2": {}, "flow_non_afms_drop_3": {}, "flow_non_afms_drop_4": {}},
    }

    print("Plotting Traffic Class Bandwidth Utilization...")
    plot_traffic_class_bandwidth(mock_afms_results, mock_non_afms_results)
    print("\nPlotting Flow Completion Times...")
    plot_flow_completion_times(mock_afms_results, mock_non_afms_results)
    print("\nPlotting Average Total Bandwidth Utilization Comparison...")
    plot_total_bandwidth_comparison(mock_afms_results, mock_non_afms_results)
    print("\nPlotting complete. Please close the plot windows to continue.")
