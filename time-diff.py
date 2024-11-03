import pandas as pd
import sys
import os

def add_delta_time(file_path):
    try:
        if not os.path.isfile(file_path):
            print(f"Error: The file '{file_path}' does not exist.")
            return

        
        df = pd.read_csv(
            file_path,
            sep='\t',
            header=None,
            names=['timestamp', 'seq'],
            dtype={'timestamp': float, 'seq': int}
        )
        
        # Verify that the DataFrame has the expected columns
        if df.shape[1] != 2:
            print(f"Error: The file '{file_path}' does not have exactly two columns.")
            return

        df = df.sort_values('timestamp').reset_index(drop=True)
        df['delta_time'] = df['timestamp'].diff()
        df['delta_time'].iloc[0] = 0.0 
        

        # df['delta_time'] = df['delta_time'].round(6)
        
        df.to_csv(
            file_path,
            sep='\t',
            header=True,
            index=False
        )
        
        print(f"Successfully updated '{file_path}' with 'delta_time' as the third column.")
    
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{file_path}' is empty.")
    except pd.errors.ParserError:
        print(f"Error: The file '{file_path}' could not be parsed. Please check the file format.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    """
    Main function to execute the delta_time addition.
    """
    file_path = 'CD-bw5Mb-dlay100-b450p-drp.tr'
    
    add_delta_time(file_path)

if __name__ == '__main__':
    main()
