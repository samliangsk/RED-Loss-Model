import pandas as pd
import numpy as np
import glob
import os
import re
import matplotlib.pyplot as plt
from collections import Counter

def process_files():
    # Get list of all drp.tr files
    file_list = glob.glob('FQCD-bw*Mb-dlay*-drp.tr')
    
    data = {}

    for file_path in file_list:
        
        # Extract bandwidth from filename
        match = re.search(r'bw([\dp]+)Mb', file_path)
        if match:
            bw_str = match.group(1)
            bw = bw_str.replace('p', '.')
            bandwidth = float(bw)
        else:
            continue  # If can't find bandwidth, skip the file

        # Read the file, handling whether it already has delta_time or not
        try:
            # Try reading with three columns first
            df = pd.read_csv(file_path, sep='\t', header=0)
            if 'delta_time' not in df.columns or df.shape[1] < 3:
                # If delta_time column is missing or only two columns, read again with specified names
                df = pd.read_csv(file_path, sep='\t', header=None, names=['timestamp', 'seq'])
                df = df.sort_values('timestamp').reset_index(drop=True)
                df['delta_time'] = df['timestamp'].diff()
                df['delta_time'].iloc[0] = 0.0
                # Save the DataFrame back to the file with headers
                df.to_csv(file_path, sep='\t', header=True, index=False)
            else:
                # DataFrame already has delta_time
                df = df.sort_values('timestamp').reset_index(drop=True)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

        # Ignore drops before 20 seconds
        df = df[df['timestamp'] >= 20].reset_index(drop=True)

        # If no drops after 20 seconds, skip
        if df.empty:
            continue

        # The delta_time column is already in df
        # No need to recompute it here

        # Group drops into batches where drops within 1 second are in the same batch
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

        # If there are no batches, skip this file
        if not batches:
            continue

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
            avg_time_diff = np.mean(time_diffs_between_batches[1:])
        else:
            avg_time_diff = np.nan  # Not enough data to compute average

        # Compute average number of drops per batch
        avg_drops_per_batch = np.mean(drops_per_batch) if drops_per_batch else np.nan
        # print("Average drop per batch is " , avg_drops_per_batch, "for delay ", delay)
        # Store the collected time differences and drops in the data dictionary
        
        data[bandwidth] = {
            'avg_time_diff_between_batches': avg_time_diff,
            'avg_drops_per_batch': avg_drops_per_batch
        }
        
            
    return data

def plot_data(data):
    # Prepare data for plotting
    bandwidths = sorted(data.keys())
    avg_time_diffs_between_batches = []
    avg_drops_per_batch_list = []

    for bw in bandwidths:
        avg_time_diff = data[bw]['avg_time_diff_between_batches']
        avg_drops_per_batch = data[bw]['avg_drops_per_batch']

        avg_time_diffs_between_batches.append(avg_time_diff)
        avg_drops_per_batch_list.append(avg_drops_per_batch)



        # Plotting
    fig, ax1 = plt.subplots(figsize=(14, 7))

    ind = np.arange(len(bandwidths))
    width = 0.35

    # Plot average time differences between batches
    ax1.bar(ind - width/2, avg_time_diffs_between_batches, width, label='Avg Time Between Batches', color='blue')
    ax1.set_ylabel('Average Time Between Batches (s)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.set_xlabel('Round Trip Time (s)')
    ax1.set_xticks(ind)
    ax1.set_xticklabels([str(bw) for bw in bandwidths], rotation=45)

    # Create a second y-axis for average drops per batch
    ax2 = ax1.twinx()
    ax2.bar(ind + width/2, avg_drops_per_batch_list, width, label='Avg Drops per Batch', color='red')
    ax2.set_ylabel('Average Drops per Batch', color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    # Add title and legend
    fig.suptitle('Average Time Between Batches and Average Drops per Batch for Different RTTs')

    # Combine legends from both axes
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc='upper right')

    plt.tight_layout()
    plt.show()

def main():
    data = process_files()
    plot_data(data)

if __name__ == '__main__':
    main()
