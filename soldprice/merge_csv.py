import os
import pandas as pd

def merge_csv_files(input_dir, output_file):
    # List all CSV files in the directory
    csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    
    # Initialize a list to hold DataFrames
    dataframes = []
    
    # Read each CSV file and append to the list
    for csv_file in csv_files:
        file_path = os.path.join(input_dir, csv_file)
        df = pd.read_csv(file_path)
        dataframes.append(df)
        print(f"Loaded {csv_file} with {len(df)} records.")
    
    # Concatenate all DataFrames
    merged_df = pd.concat(dataframes, ignore_index=True)
    
    # Save the merged DataFrame to a new CSV file
    merged_df.to_csv(output_file, index=False)
    print(f"Merged {len(csv_files)} files into {output_file} with {len(merged_df)} total records.")

def main():
    input_dir = 'soldprice'
    output_file = 'soldprice/merged_all_players.csv'
    merge_csv_files(input_dir, output_file)

if __name__ == "__main__":
    main() 