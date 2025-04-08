import pandas as pd
import os
import glob
from difflib import SequenceMatcher
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
from functools import lru_cache
import re

@lru_cache(maxsize=10000)
def string_similarity(a, b):
    """Calculate similarity ratio between two strings with caching"""
    # Quick check for exact match or completely different
    if a == b:
        return 1.0
    if not bool(set(a) & set(b)):
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

def remove_duplicates(df):
    """Remove completely identical rows from the dataframe using vectorized operations"""
    original_len = len(df)
    df_no_duplicates = df.drop_duplicates()
    removed_count = original_len - len(df_no_duplicates)
    print(f"Removed {removed_count} exact duplicate lines")
    return df_no_duplicates

def find_similar_groups(df, similarity_threshold=0.8, batch_size=1000):
    """Find groups of similar titles using batched processing"""
    titles = df['Title'].tolist()
    similar_groups = []
    processed_indices = set()
    
    # Process all titles in batches
    for i in range(len(titles)):
        if i in processed_indices:
            continue
            
        current_group = [i]
        processed_indices.add(i)
        
        # Compare with remaining unprocessed titles
        remaining_indices = [j for j in range(i + 1, len(titles)) if j not in processed_indices]
        
        # Process in batches
        for j in range(0, len(remaining_indices), batch_size):
            batch_indices = remaining_indices[j:j + batch_size]
            batch_titles = [titles[idx] for idx in batch_indices]
            
            # Calculate similarities in batch
            similarities = np.array([string_similarity(titles[i], title) for title in batch_titles])
            matching_batch_indices = np.where(similarities >= similarity_threshold)[0]
            
            for match_idx in matching_batch_indices:
                current_group.append(batch_indices[match_idx])
                processed_indices.add(batch_indices[match_idx])
        
        if len(current_group) > 1:
            similar_groups.append(current_group)
    
    return similar_groups

def rearrange_csv(df, similar_groups):
    """Rearrange the dataframe based on similar groups using efficient numpy operations"""
    if not similar_groups:
        return df
        
    all_indices = np.arange(len(df))
    grouped_indices = np.concatenate([np.array(group) for group in similar_groups])
    ungrouped_mask = ~np.isin(all_indices, grouped_indices)
    ungrouped_indices = all_indices[ungrouped_mask]
    
    new_order = np.concatenate([grouped_indices, ungrouped_indices])
    return df.iloc[new_order]

def process_csv_file(args):
    """Process a single CSV file with optimized operations"""
    csv_file, _ = args
    try:
        player_name = os.path.splitext(os.path.basename(csv_file))[0].replace('_', ' ')
        print(f"\nProcessing: {os.path.basename(csv_file)}")
        print(f"Player name: {player_name}")
        
        # Read CSV file efficiently
        df = pd.read_csv(csv_file, dtype={'Title': str})
        
        original_len = len(df)
        print(f"Original file has {original_len} lines")
        
        # Vectorized player name filtering
        name_pattern = re.compile(player_name, re.IGNORECASE)
        filtered_df = df[df['Title'].str.contains(name_pattern, na=False)]
        filtered_count = original_len - len(filtered_df)
        print(f"Removed {filtered_count} rows not matching player name")
        print(f"Kept {len(filtered_df)} rows after name filtering")
        
        # Remove duplicates
        filtered_df = remove_duplicates(filtered_df)
        
        # Find and group similar items
        similar_groups = find_similar_groups(filtered_df)
        
        # Rearrange and save
        final_df = rearrange_csv(filtered_df, similar_groups)
        final_df.to_csv(csv_file, index=False)
        
        # Print summary
        print("\nResults Summary:")
        print(f"- Original lines: {original_len}")
        print(f"- Lines after name filtering: {len(filtered_df)}")
        print(f"- Similar groups found: {len(similar_groups)}")
        print(f"- Lines in similar groups: {sum(len(group) for group in similar_groups)}")
        print(f"- Individual unique lines: {len(filtered_df) - sum(len(group) for group in similar_groups)}")
        print(f"Original file has been updated: {os.path.basename(csv_file)}")
        
        return True
        
    except Exception as e:
        print(f"\nError processing {os.path.basename(csv_file)}: {e}")
        return False

def main():
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths for CSV files
    csv_pattern = os.path.join(script_dir, 'data', 'scrapeddata', '*.csv')
    
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print("No CSV files found in the directory.")
        return
        
    print(f"Found {len(csv_files)} CSV files to process.")
    
    # Process files in parallel
    max_workers = os.cpu_count() or 4  # Use number of CPU cores
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Create tasks for parallel processing
        tasks = [(csv_file, None) for csv_file in csv_files]
        
        # Submit all tasks and process them in parallel
        futures = [executor.submit(process_csv_file, task) for task in tasks]
        
        # Wait for all tasks to complete
        completed = 0
        for future in as_completed(futures):
            completed += 1
            print(f"\nProgress: {completed}/{len(csv_files)} files processed")
    
    print("\nCompleted processing all CSV files.")

if __name__ == "__main__":
    main() 