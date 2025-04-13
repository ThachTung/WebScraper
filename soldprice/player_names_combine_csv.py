import pandas as pd
import os
import glob

def combine_csv_files(input_directory, output_file):
    # Define the pattern to match CSV files in the directory
    csv_pattern = os.path.join(input_directory, '*.csv')
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print("No CSV files found in the directory.")
        return
    
    print(f"Found {len(csv_files)} CSV files to combine.")
    
    # List to hold dataframes
    dataframes = []
    
    # Read each CSV file and append to the list
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            dataframes.append(df)
            print(f"Loaded {os.path.basename(csv_file)} with {len(df)} records.")
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
    
    # Concatenate all dataframes
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    # Keep only the 'ATHLETE' column
    athletes_df = combined_df[['ATHLETE']].drop_duplicates().reset_index(drop=True)
    
    # Save the combined dataframe to a new CSV file without the header
    athletes_df.to_csv(output_file, index=False, header=False)
    print(f"Combined CSV with only 'ATHLETE' column saved to {output_file} with {len(athletes_df)} unique records, without header.")

if __name__ == "__main__":
    input_directory = r"C:\Users\tungt\Documents\WebScraper\soldprice\data\basedata\panini"
    output_file = r"C:\Users\tungt\Documents\WebScraper\soldprice\data\combined_athletes.csv"
    combine_csv_files(input_directory, output_file)