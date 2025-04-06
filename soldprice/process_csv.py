import pandas as pd
import os
import glob
from difflib import SequenceMatcher

def string_similarity(a, b):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, a, b).ratio()

def remove_duplicates(df):
    """Remove completely identical rows from the dataframe"""
    original_len = len(df)
    df_no_duplicates = df.drop_duplicates()
    removed_count = original_len - len(df_no_duplicates)
    print(f"Removed {removed_count} exact duplicate lines")
    return df_no_duplicates

def find_similar_groups(df, similarity_threshold=0.8):
    """Find groups of similar titles in the dataframe"""
    titles = df['Title'].tolist()
    similar_groups = []
    processed_indices = set()
    
    for i, title1 in enumerate(titles):
        if i in processed_indices:
            continue
            
        current_group = [i]
        processed_indices.add(i)
        
        for j, title2 in enumerate(titles[i+1:], start=i+1):
            if j in processed_indices:
                continue
                
            similarity = string_similarity(title1, title2)
            if similarity >= similarity_threshold:
                current_group.append(j)
                processed_indices.add(j)
        
        if len(current_group) > 1:
            similar_groups.append(current_group)
    
    return similar_groups

def rearrange_csv(df, similar_groups):
    """Rearrange the dataframe based on similar groups"""
    all_indices = list(range(len(df)))
    
    for group in similar_groups:
        for idx in group:
            if idx in all_indices:
                all_indices.remove(idx)
    
    new_order = []
    for group in similar_groups:
        new_order.extend(group)
    new_order.extend(all_indices)
    
    return df.iloc[new_order]

def process_csv_file(csv_file, similarity_threshold=0.8):
    """Process a single CSV file: filter by name and find similar items"""
    try:
        # Get player name from filename
        player_name = os.path.splitext(os.path.basename(csv_file))[0].replace('_', ' ')
        print(f"\nProcessing: {os.path.basename(csv_file)}")
        print(f"Player name: {player_name}")
        
        # Read the CSV file
        df = pd.read_csv(csv_file)
        original_len = len(df)
        print(f"Original file has {original_len} lines")
        
        # Step 1: Filter by player name
        filtered_df = df[df['Title'].str.contains(player_name, case=False, na=False)]
        filtered_count = original_len - len(filtered_df)
        print(f"Removed {filtered_count} rows not matching player name")
        print(f"Kept {len(filtered_df)} rows after name filtering")
        
        # Step 2: Remove exact duplicates
        filtered_df = remove_duplicates(filtered_df)
        
        # Step 3: Find and group similar items
        similar_groups = find_similar_groups(filtered_df, similarity_threshold)
        
        # Step 4: Rearrange the dataframe
        final_df = rearrange_csv(filtered_df, similar_groups)
        
        # Save results back to original file
        final_df.to_csv(csv_file, index=False)
        
        # Print summary
        print("\nResults Summary:")
        print(f"- Original lines: {original_len}")
        print(f"- Lines after name filtering: {len(filtered_df)}")
        print(f"- Similar groups found: {len(similar_groups)}")
        print(f"- Lines in similar groups: {sum(len(group) for group in similar_groups)}")
        print(f"- Individual unique lines: {len(filtered_df) - sum(len(group) for group in similar_groups)}")
        print(f"Original file has been updated: {os.path.basename(csv_file)}")
        
    except Exception as e:
        print(f"\nError processing {os.path.basename(csv_file)}: {e}")

def main():
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all CSV files in the directory
    csv_pattern = os.path.join(script_dir, 'data','scrapeddata', '*.csv')
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print("No CSV files found in the directory.")
        return
        
    print(f"Found {len(csv_files)} CSV files to process.")
    
    # Process each CSV file
    for csv_file in csv_files:
        process_csv_file(csv_file)
    
    print("\nCompleted processing all CSV files.")

if __name__ == "__main__":
    main() 