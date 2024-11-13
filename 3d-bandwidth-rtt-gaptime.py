import pandas as pd
import numpy as np
import glob
import re
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

def process_files():
    # Get list of all drp.tr files
    file_list = glob.glob('CD-bw*Mb-dlay*-drp.tr')

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
            if delta_time > 1.0:
                # Start a new batch
                if current_batch['drops']:
                    batches.append(current_batch)
                current_batch = {'drops': [seq], 'times': [timestamp]}
            else:
                current_batch['drops'].append(seq)
                current_batch['times'].append(timestamp)
        # Append the last batch
        if current_batch['drops']:
            batches.append(current_batch)

        # Determine the most common batch size
        batch_sizes = [len(batch['drops']) for batch in batches]
        if not batch_sizes:
            continue  # No batches to process
        batch_size_counts = Counter(batch_sizes)
        expected_batch_size = batch_size_counts.most_common(1)[0][0]

        # Prune batches that don't match the expected batch size
        pruned_batches = [batch for batch in batches if len(batch['drops']) == expected_batch_size]

        # If after pruning there are no batches, skip this file
        if not pruned_batches:
            continue

        # For each pruned batch, collect the first delta time (time since last batch)
        time_diffs_1 = []  # Time since last batch (for first drop in batch)

        last_drop_time = None
        for batch in pruned_batches:
            times = batch['times']
            if not times:
                continue
            first_drop_time = times[0]
            # Time since last batch
            if last_drop_time is not None:
                time_since_last_batch = first_drop_time - last_drop_time
                time_diffs_1.append(time_since_last_batch)
            else:
                # For first batch, we don't have last_drop_time
                pass
            last_drop_time = times[-1]  # Update last_drop_time

        # Compute average time since last batch
        if time_diffs_1:
            avg_time_since_last_batch = np.mean(time_diffs_1)
        else:
            avg_time_since_last_batch = np.nan

        # Store the collected time differences in the data list
        data.append({
            'bandwidth': bandwidth,
            'delay': delay,
            'delta_time': avg_time_since_last_batch
        })

    return pd.DataFrame(data)

def plot_data(df):
    # Create a pivot table with bandwidth as rows, delay as columns, and delta_time as values
    pivot_table = df.pivot_table(values='delta_time', index='bandwidth', columns='delay', aggfunc='mean')

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
