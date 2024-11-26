import pandas as pd
import numpy as np
import glob
import re
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

def process_files():
    # Get list of all drp.tr files
    file_list = glob.glob('FQCD-bw*Mb-dlay*-drp.tr')

    data = []

    for file_path in file_list:
        # Extract bandwidth and delay from filename
        bw_match = re.search(r'bw([\dp]+)Mb', file_path)
        delay_match = re.search(r'dlay([\d]+)', file_path)
        
        if bw_match and delay_match:
            bw_str = bw_match.group(1).replace('p', '.')
            delay_str = delay_match.group(1).replace('p', '.')
            bandwidth = float(bw_str)
            delay = float(delay_str)
            print(bandwidth, delay, file_path)
            print()
        else:
            continue

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
        data.append({
            'bandwidth': bandwidth,
            'delay': delay,
            'avg_time_diff_between_batches': avg_time_diff,
            'avg_drops_per_batch': avg_drops_per_batch
        })

    return pd.DataFrame(data)

def plot_data(df):
    # Create a pivot table with bandwidth as rows, delay as columns, and delta_time as values
    pivot_table = df.pivot_table(values='avg_time_diff_between_batches', index='bandwidth', columns='delay', aggfunc='mean')

    plt.figure(figsize=(12, 8))
    sns.heatmap(pivot_table, annot=False, fmt=".2f", cmap='viridis')
    plt.title('Average Delta Time Heatmap')
    plt.ylabel('Bandwidth (Mbps)')
    plt.xlabel('Delay (ms)')
    plt.show()


def main():
    df = process_files()
    if df.empty:
        print("No data to plot.")
    else:
        plot_data(df)

if __name__ == '__main__':
    main()
