import pandas as pd
import numpy as np
import glob
import re
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score, mean_squared_error

def process_files():
    # Get list of all drp.tr files
    file_list = glob.glob('FQCD-bw*-dlay*-drp.tr')

    data_rows = []

    for file_path in file_list:
        # Extract bandwidth and delay from filename
        bw_match = re.search(r'bw([\d]+)', file_path)
        delay_match = re.search(r'dlay([\d]+)', file_path)
        if bw_match and delay_match:
            bandwidth_str = bw_match.group(1).replace('p', '.')
            bandwidth = int(bandwidth_str)
            delay_str = delay_match.group(1).replace('p', '.')
            delay = int(delay_str)
        else:
            continue  # If can't find bandwidth or delay, skip the file

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
            # print(f"Error reading {file_path}: {e}")
            continue

        # Ignore drops before 5 seconds
        df = df[df['timestamp'] >= 5].reset_index(drop=True)

        # If no drops after 5 seconds, skip
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

            # Time difference between batches
            if last_batch_start_time is not None:
                time_between_batches = batch_start_time - last_batch_start_time
                time_diffs_between_batches.append(time_between_batches)
            else:
                # For first batch, set time difference to zero
                time_diffs_between_batches.append(0.0)
            last_batch_start_time = batch_start_time  # Update last_batch_start_time

        # Exclude the first two time differences (first is zero, second is initial gap)
        if len(time_diffs_between_batches) > 2:
            avg_time_diff = np.mean(time_diffs_between_batches[2:])
        else:
            avg_time_diff = np.nan  # Not enough data to compute average

        # Compute average number of drops per batch
        avg_drops_per_batch = np.mean(drops_per_batch) if drops_per_batch else np.nan

        # Skip if avg_time_diff is NaN
        if np.isnan(avg_time_diff):
            continue

        # Append the data to the list
        data_rows.append({
            'bandwidth': bandwidth,
            'delay': delay,
            'avg_time_diff_between_batches': avg_time_diff,
            'avg_drops_per_batch': avg_drops_per_batch
        })

    # Convert the list of dictionaries to a DataFrame
    data_df = pd.DataFrame(data_rows)

    return data_df

def build_function_approximator(data_df, degree=2):
    # Prepare the data for regression
    X = data_df[['bandwidth', 'delay']]
    y = data_df['avg_time_diff_between_batches']
    
    # Generate polynomial features
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X_poly = poly.fit_transform(X)
    
    # Fit a linear regression model on the polynomial features
    model = LinearRegression()
    model.fit(X_poly, y)
    
    # Predict the values
    y_pred = model.predict(X_poly)
    
    # Calculate accuracy metrics
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    
    # Print the function approximation
    feature_names = poly.get_feature_names_out(['bandwidth', 'delay'])
    coefficients = model.coef_
    intercept = model.intercept_
    
    print("Function approximation:")
    equation_terms = [f"{coef:.4f} * {name}" for coef, name in zip(coefficients, feature_names)]
    equation = " + ".join(equation_terms)
    print(f"Average Time Between Batches = {equation} + {intercept:.4f}")
    print(f"R-squared: {r2:.4f}")
    print(f"Mean Squared Error: {mse:.4f}")
    
    # Return the model, polynomial transformer, and accuracy metrics
    return model, poly, r2, mse

def plot_results(data_df, model, poly):
    # Plot the observed vs predicted values
    X = data_df[['bandwidth', 'delay']]
    y = data_df['avg_time_diff_between_batches']
    X_poly = poly.transform(X)
    y_pred = model.predict(X_poly)
    
    plt.figure(figsize=(10, 6))
    plt.scatter(y, y_pred, color='blue')
    plt.plot([y.min(), y.max()], [y.min(), y.max()], 'k--', lw=2)
    plt.xlabel('Observed Average Time Between Batches (s)')
    plt.ylabel('Predicted Average Time Between Batches (s)')
    plt.title('Observed vs Predicted Average Time Between Batches')
    plt.show()
    
    # Optionally, plot residuals
    residuals = y - y_pred
    plt.figure(figsize=(10, 6))
    plt.scatter(y_pred, residuals, color='green')
    plt.hlines(0, y_pred.min(), y_pred.max(), colors='red', linestyles='dashed')
    plt.xlabel('Predicted Values')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Predicted Values')
    plt.show()

def main():
    data_df = process_files()
    
    if data_df.empty:
        print("No data to process.")
        return
    
    # Try polynomial degrees from 2 to 3 (you can adjust as needed)
    for degree in [1, 2, 3]:
        print(f"\nPolynomial Regression with degree {degree}:")
        model, poly, r2, mse = build_function_approximator(data_df, degree=degree)
        plot_results(data_df, model, poly)

if __name__ == '__main__':
        main()