import pandas as pd
import os
import glob

def filter_csv_by_name(csv_file):
    try:
        # Get the base filename without extension and replace underscores with spaces
        player_name = os.path.splitext(os.path.basename(csv_file))[0].replace('_', ' ')
        
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        # Store original length
        original_len = len(df)
        
        # Filter rows that contain the player name (case insensitive)
        filtered_df = df[df['Title'].str.contains(player_name, case=False, na=False)]
        
        # Save the filtered data back to the same file
        filtered_df.to_csv(csv_file, index=False)
        
        print(f"\nProcessed: {os.path.basename(csv_file)}")
        print(f"Removed: {original_len - len(filtered_df)} rows")
        print(f"Kept: {len(filtered_df)} rows")
        
    except Exception as e:
        print(f"\nError processing {os.path.basename(csv_file)}: {e}")

def main():
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all CSV files in the directory
    csv_pattern = os.path.join(script_dir, 'soldprice', '*.csv')
    #csv_pattern = os.path.join('soldprice/soldprice', '*.csv')
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print("No CSV files found in the directory.")
        return
        
    print(f"Found {len(csv_files)} CSV files to process.")
    
    # Process each CSV file
    for csv_file in csv_files:
        filter_csv_by_name(csv_file)
    
    print("\nCompleted processing all CSV files.")

if __name__ == "__main__":
    main() 