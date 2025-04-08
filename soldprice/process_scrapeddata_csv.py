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

def check_product_name_similarity_batch(titles, product_names, threshold=0.4):
    """Vectorized check for product name similarity"""
    # Convert titles to lowercase for case-insensitive matching
    titles_lower = [t.lower() for t in titles]
    product_names_lower = [p.lower() for p in product_names]
    
    # Create a boolean mask for matching titles
    matches = np.zeros(len(titles), dtype=bool)
    
    # First try quick substring matching
    for product_name in product_names_lower:
        matches |= np.array([product_name in title for title in titles_lower])
    
    # For unmatched titles, try similarity matching
    unmatched_indices = np.where(~matches)[0]
    if len(unmatched_indices) > 0:
        for i in unmatched_indices:
            title = titles_lower[i]
            for product_name in product_names_lower:
                if string_similarity(title, product_name) >= threshold:
                    matches[i] = True
                    break
    
    return matches

def find_similar_groups(df, product_names, similarity_threshold=0.8, batch_size=1000):
    """Find groups of similar titles using batched processing"""
    titles = df['Title'].tolist()
    similar_groups = []
    processed_indices = set()
    
    # First, filter titles that match product names
    matching_mask = check_product_name_similarity_batch(titles, product_names)
    matching_indices = np.where(matching_mask)[0]
    
    # Process matching titles in batches
    for i in matching_indices:
        if i in processed_indices:
            continue
            
        current_group = [i]
        processed_indices.add(i)
        
        # Compare with remaining unprocessed matching titles
        remaining_indices = [j for j in matching_indices if j > i and j not in processed_indices]
        
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
    csv_file, product_names_file = args
    try:
        player_name = os.path.splitext(os.path.basename(csv_file))[0].replace('_', ' ')
        print(f"\nProcessing: {os.path.basename(csv_file)}")
        print(f"Player name: {player_name}")
        
        # Read CSV files efficiently
        df = pd.read_csv(csv_file, dtype={'Title': str})
        product_names_df = pd.read_csv(product_names_file, dtype={'Filename': str})
        product_names = product_names_df['Filename'].tolist()
        
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
        similar_groups = find_similar_groups(filtered_df, product_names)
        
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
    product_names_file = os.path.join(script_dir, 'data', 'Product_names.csv')
    
    # Check if Product_names.csv exists
    if not os.path.exists(product_names_file):
        print("Product_names.csv not found. Please ensure it exists in the data directory.")
        return
    
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print("No CSV files found in the directory.")
        return
        
    print(f"Found {len(csv_files)} CSV files to process.")
    
    # Process files in parallel
    max_workers = os.cpu_count() or 4  # Use number of CPU cores
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Create tasks for parallel processing
        tasks = [(csv_file, product_names_file) for csv_file in csv_files]
        
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