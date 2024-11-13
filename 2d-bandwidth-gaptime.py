import pandas as pd
import numpy as np
import glob
import os
import re
import matplotlib.pyplot as plt
from collections import Counter

def process_files():
    # Get list of all drp.tr files
    file_list = glob.glob('CD-bw*p*-drp.tr')

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

        # For each pruned batch, collect time differences
        time_diffs_1 = []  # Time since last batch (for first drop in batch)
        time_diffs_within_batch = []  # Time differences within batch

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

            # Time differences within batch
            within_batch_diffs = []
            for i in range(1, len(times)):
                within_batch_diffs.append(times[i] - times[i - 1])
            time_diffs_within_batch.append(within_batch_diffs)

        # Compute average time differences within batches
        # Transpose the list of lists to get lists of time differences at each position
        time_diffs_within_batch_transposed = list(zip(*time_diffs_within_batch))
        avg_within_batch_diffs = [np.mean(diffs) for diffs in time_diffs_within_batch_transposed]

        # Store the collected time differences in the data dictionary
        data[bandwidth] = {
            'time_diffs_1': time_diffs_1,
            'avg_within_batch_diffs': avg_within_batch_diffs,
            'expected_batch_size': expected_batch_size
        }

    return data

def plot_data(data):
    # Prepare data for plotting
    bandwidths = sorted(data.keys())
    avg_time_diffs_1 = []
    avg_within_batch_diffs = []
    batch_sizes = []

    for bw in bandwidths:
        time_diffs_1 = data[bw]['time_diffs_1']
        within_batch_diffs = data[bw]['avg_within_batch_diffs']
        expected_batch_size = data[bw]['expected_batch_size']

        # Compute average, if the list is empty, set average to NaN
        avg_1 = np.mean(time_diffs_1) if time_diffs_1 else np.nan
        avg_time_diffs_1.append(avg_1)
        batch_sizes.append(expected_batch_size)

        # For within-batch diffs, fill with NaNs if not enough data
        while len(within_batch_diffs) < expected_batch_size - 1:
            within_batch_diffs.append(np.nan)
        avg_within_batch_diffs.append(within_batch_diffs[:expected_batch_size - 1])

    # Number of bandwidths
    N = len(bandwidths)
    ind = np.arange(N)  # the x locations for the groups
    width = 0.2  # the width of the bars

    fig, ax = plt.subplots(figsize=(14, 7))

    # Extract within-batch diffs
    avg_time_diffs_list = [list(diffs) for diffs in avg_within_batch_diffs]
    max_diffs = max(len(diffs) for diffs in avg_time_diffs_list)

    # Stack the bars for each time difference
    bar_positions = [ind + i * width - width for i in range(max_diffs + 1)]
    labels = ['Time since last batch'] + [f'Within-batch time diff {i+1}' for i in range(max_diffs)]

    rects = []
    rects.append(ax.bar(bar_positions[0], avg_time_diffs_1, width, label=labels[0]))
    for i in range(max_diffs):
        avg_diffs_i = [diffs[i] if i < len(diffs) else np.nan for diffs in avg_time_diffs_list]
        rects.append(ax.bar(bar_positions[i + 1], avg_diffs_i, width, label=labels[i + 1]))

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Time differences (s)')
    ax.set_xlabel('Bandwidth (Mbps)')
    ax.set_title('Time Differences between Drops for Different Bandwidths')
    ax.set_xticks(ind)
    ax.set_xticklabels([str(bw) for bw in bandwidths], rotation=45)
    ax.legend()

    plt.tight_layout()
    plt.show()

def main():
    data = process_files()
    plot_data(data)

if __name__ == '__main__':
    main()
