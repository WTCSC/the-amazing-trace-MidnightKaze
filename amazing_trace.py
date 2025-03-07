import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.ticker import MaxNLocator
import time
import os
import subprocess
import platform
import re

def execute_traceroute(destination):
    # Depending on what platform is being used, the command will be different for each one
    if platform.system().lower() == "windows":
        command = ["tracert", destination]
    # Most typically Linux is being used if Windows is not, so this is the command
    else:
        command = ["traceroute", "-I", destination]
    
    # Will attempt to run and gather the information from the command above, but will give an error if one occurs
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"There was an error running traceroute o(╥﹏╥)o: {e}"

def parse_traceroute(traceroute_output):
    # Spilts the lines from execute_tracroute so they can be used in regular expession matching
    lines = traceroute_output.splitlines()
    info_list = []

    # A matching pattern to help find the start of a line
    hop_pattern = re.compile(r"^\s*(\d+)")

    for line in lines:
        # Pulls the hop number from the line
        hop_match = re.match(hop_pattern, line)
        if not hop_match:
            continue

        # Important to int it for the tests
        hop_number = int(hop_match.group(1))

        # Prep for hostname and IP Address pulling
        hostname = None
        ip_address = None

        ip_match = re.search(r"([^\s(]+)\s*\((\d+\.\d+\.\d+\.\d+)\)", line)
        # This will basically try to get both the hostname and the IP at once
        if ip_match:
            hostname = ip_match.group(1)
            ip_address = ip_match.group(2)
            # But if they are the same...
            if hostname == ip_address:
                hostname = None
        #... it will then try to get the IP alone
        else:
            ip_only = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
            if ip_only:
                ip_address = ip_only.group(1)

        # Prep for the return time pulling
        return_times = []

        time_match = re.finditer(r'([*]|\d+\.\d+|\d+|\<\d+)\s*ms', line)
        for match in time_match:
            time = match.group(1)
            # If the return time is a * then it will show None-- per assignment request
            if time == "*":
                return_times.append(None)
            else:
                # Accounts for the <1ms if it happens
                if time.startswith('<'):
                    time = time[1:]
                return_times.append(float(time))

        # If theres no value but there's * then we can just assume a timeout occured
        if not return_times and "*" in line:
            timeout_number = line.count('*')
            return_times = [None] * timeout_number

        # Ensures that there's three return times
        while len(return_times) < 3:
            return_times.append(None)

        info_list.append({
            'hop': hop_number,
            'ip': ip_address,
            'hostname': hostname,
            'rtt': return_times
        })
    
    return info_list

# ============================================================================ #
#                    DO NOT MODIFY THE CODE BELOW THIS LINE                    #
# ============================================================================ #
def visualize_traceroute(destination, num_traces=3, interval=5, output_dir='output'):
    """
    Runs multiple traceroutes to a destination and visualizes the results.

    Args:
        destination (str): The hostname or IP address to trace
        num_traces (int): Number of traces to run
        interval (int): Interval between traces in seconds
        output_dir (str): Directory to save the output plot

    Returns:
        tuple: (DataFrame with trace data, path to the saved plot)
    """
    all_hops = []

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    print(f"Running {num_traces} traceroutes to {destination}...")

    for i in range(num_traces):
        if i > 0:
            print(f"Waiting {interval} seconds before next trace...")
            time.sleep(interval)

        print(f"Trace {i+1}/{num_traces}...")
        output = execute_traceroute(destination)
        hops = parse_traceroute(output)

        # Add timestamp and trace number
        timestamp = time.strftime("%H:%M:%S")
        for hop in hops:
            hop['trace_num'] = i + 1
            hop['timestamp'] = timestamp
            all_hops.append(hop)

    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(all_hops)

    # Calculate average RTT for each hop (excluding timeouts)
    df['avg_rtt'] = df['rtt'].apply(lambda x: np.mean([r for r in x if r is not None]) if any(r is not None for r in x) else None)

    # Plot the results
    plt.figure(figsize=(12, 6))

    # Create a subplot for RTT by hop
    ax1 = plt.subplot(1, 1, 1)

    # Group by trace number and hop number
    for trace_num in range(1, num_traces + 1):
        trace_data = df[df['trace_num'] == trace_num]

        # Plot each trace with a different color
        ax1.plot(trace_data['hop'], trace_data['avg_rtt'], 'o-',
                label=f'Trace {trace_num} ({trace_data.iloc[0]["timestamp"]})')

    # Add labels and legend
    ax1.set_xlabel('Hop Number')
    ax1.set_ylabel('Average Round Trip Time (ms)')
    ax1.set_title(f'Traceroute Analysis for {destination}')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend()

    # Make sure hop numbers are integers
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))

    plt.tight_layout()

    # Save the plot to a file instead of displaying it
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    safe_dest = destination.replace('.', '-')
    output_file = os.path.join(output_dir, f"trace_{safe_dest}_{timestamp}.png")
    plt.savefig(output_file)
    plt.close()

    print(f"Plot saved to: {output_file}")

    # Return the dataframe and the path to the saved plot
    return df, output_file

# Test the functions
if __name__ == "__main__":
    # Test destinations
    destinations = [
        "google.com",
        "amazon.com",
        "bbc.co.uk"  # International site
    ]

    for dest in destinations:
        df, plot_path = visualize_traceroute(dest, num_traces=3, interval=5)
        print(f"\nAverage RTT by hop for {dest}:")
        avg_by_hop = df.groupby('hop')['avg_rtt'].mean()
        print(avg_by_hop)
        print("\n" + "-"*50 + "\n")
