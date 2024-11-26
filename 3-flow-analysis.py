import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Designed for the 3 flow experiment, this program plots histogram of the first in batch time gaps, in 3 phase.
# phase 1 is 1 flow, phase 2 is 2 flow, and phase 3 is three flows.
# The program will output 3 histogram, and 3 means. 
# time gaps here are the difference between 2 consecutive first in batch packets.

def process_interval(drp_file, dest_port, start_time, end_time):
    # Read the drp.tr file
    df = pd.read_csv(drp_file, sep='\t', header=None, names=['timestamp', 'seq', 'dest_port'])
    
    # Filter for the given dest_port and time interval
    if end_time is not None:
        df = df[(df['dest_port'] == dest_port) & (df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)]
    else:
        df = df[(df['dest_port'] == dest_port) & (df['timestamp'] >= start_time)]
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Group drops into batches where drops within 1 second are in the same batch
    df['delta_time'] = df['timestamp'].diff().fillna(0)
    
    # Create a batch_id column
    # batch_id = 0
    # batch_ids = []
    # for delta in df['delta_time']:
    #     if delta > 0.34:
    #         batch_id += 1
    #     batch_ids.append(batch_id)
    # df['batch_id'] = batch_ids
    
    # # For each batch, get the first timestamp
    # batch_times = df.groupby('batch_id')['timestamp'].min().reset_index()
    
    # # Compute time gaps between batches
    # batch_times['time_gap'] = batch_times['timestamp'].diff().fillna(0)
    # # Exclude the first time_gap which is zero
    # time_gaps = batch_times['time_gap'][1:].values  # Exclude first zero gap
    
    batches = []
    current_batch = {'drops': [], 'times': []}
    for idx, row in df.iterrows():
        timestamp = row['timestamp']
        seq = row['seq']
        delta_time = row['delta_time']
        if delta_time > 0.34:
            # Start a new batch, save the old batch if there's things 
            # the decider is currently static, how can we have a dynamic decider for batches?
            # or use a more accurate value?
            if current_batch['drops']:
                batches.append(current_batch)
            current_batch = {'drops': [seq], 'times': [timestamp]}
        else:
            current_batch['drops'].append(seq)
            current_batch['times'].append(timestamp)
    # Append the last batch
    if current_batch['drops']:
        batches.append(current_batch)
    
    # For each batch, collect time differences and number of drops
        time_diffs_between_batches = []  # Time difference between the start of consecutive batches
        drops_per_batch = []  # Number of drops in each batch


    last_batch_start_time = None
    for idx, batch in enumerate(batches):
        times = batch['times']
        if not times:
            continue
        batch_start_time = times[0]
        # Number of drops in this batch
        drops_per_batch.append(len(batch['drops']))

        # checker: per batch drop count
        # if(delay == 4):
            # print("drops_per_batch for ",idx, " is " ,len(batch['drops']))
        
        # Time difference between batches
        if last_batch_start_time is not None:
            time_between_batches = batch_start_time - last_batch_start_time
            time_diffs_between_batches.append(time_between_batches)
        else:
            # For first batch, set time difference to zero but do not include it in average
            time_diffs_between_batches.append(0.0)
        last_batch_start_time = batch_start_time  # Update last_batch_start_time
    # Exclude the first time difference (which is zero) from average calculation
    if len(time_diffs_between_batches) > 1:
        time_gaps= time_diffs_between_batches[1:]
    else:
        time_gaps = []

    return time_gaps

def plot_time_gap_distribution(time_gaps, title):
    print(time_gaps)
    print()
    plt.figure(figsize=(10, 6))
    plt.hist(time_gaps, bins=20, edgecolor='black', alpha=0.7)
    mean_gap = np.mean(time_gaps)
    plt.axvline(mean_gap, color='red', linestyle='dashed', linewidth=1)
    min_ylim, max_ylim = plt.ylim()
    plt.text(mean_gap * 1.05, max_ylim * 0.9, f'Mean: {mean_gap:.2f}s', color='red')
    plt.title(title)
    plt.xlabel('Time Gap Between Batches (s)')
    plt.ylabel('Frequency')
    # plt.tight_layout()
    plt.show()

def main():
    drp_file = 'CD-multiflow-drp.tr'  # Replace with your actual drp.tr file path
    dest_port = 50000
    intervals = [(20, 59.5), (80, 119.5), (140, None)]
    
    for start_time, end_time in intervals:
        time_gaps = process_interval(drp_file, dest_port, start_time, end_time)
        if len(time_gaps) == 0:
            print(f"No time gaps found for flow {dest_port} between {start_time}s and {end_time if end_time else 'end'}s.")
            continue
        title = f'Time Gap Distribution for Flow {dest_port}\nfrom {start_time}s to {end_time if end_time else "end"}s'
        plot_time_gap_distribution(time_gaps, title)

if __name__ == '__main__':
    main()
