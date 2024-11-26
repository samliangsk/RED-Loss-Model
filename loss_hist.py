import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# This program plots a histogram of the time gaps between consecutive drops for a given flow.

def process_data(drp_file, dest_port):
    # Read the drp.tr file
    df = pd.read_csv(drp_file, sep='\t', header=None, names=['timestamp', 'seq', 'dest_port'])
    
    # Filter for the given dest_port
    df = df[df['dest_port'] == dest_port]
    
    # Check if there are enough data points
    if df.empty or len(df) < 2:
        return np.array([])  # Not enough data to calculate time gaps
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Calculate time differences between consecutive drops
    df['delta_time'] = df['timestamp'].diff().fillna(0)
    
    # Collect time gaps (excluding the first zero value)
    time_gaps = df['delta_time'][1:].values  # Exclude the first zero gap
    
    return time_gaps

def plot_time_gap_distribution(time_gaps, title):
    print(f"Time gaps:\n{time_gaps}\n")
    plt.figure(figsize=(10, 6))
    plt.hist(time_gaps, bins=60, edgecolor='black', alpha=0.7)
    # mean_gap = np.mean(time_gaps)
    # plt.axvline(mean_gap, color='red', linestyle='dashed', linewidth=1)
    min_ylim, max_ylim = plt.ylim()
    # plt.text(mean_gap * 1.05, max_ylim * 0.9, f'Mean: {mean_gap:.4f}s', color='red')
    plt.title(title)
    plt.xlabel('Time Gap Between Drops (s)')
    plt.ylabel('Frequency')
    plt.show()

def main():
    drp_file = 'CD-bursty-drp.tr'  # Replace with your actual drp.tr file path
    dest_port = 50000  # Replace with your desired destination port
    
    time_gaps = process_data(drp_file, dest_port)
    if len(time_gaps) == 0:
        print(f"No time gaps found for flow {dest_port}. Not enough drops to calculate time gaps.")
        return
    title = f'Time Gap Distribution for Flow {dest_port}'
    plot_time_gap_distribution(time_gaps, title)

if __name__ == '__main__':
    main()
