import pandas as pd
from difflib import SequenceMatcher
import itertools

def string_similarity(a, b):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, a, b).ratio()

def remove_duplicates(df):
    """Remove completely identical rows from the dataframe"""
    original_len = len(df)
    # Remove duplicates while keeping the first occurrence
    df_no_duplicates = df.drop_duplicates()
    removed_count = original_len - len(df_no_duplicates)
    
    print(f"Removed {removed_count} duplicate lines")
    return df_no_duplicates

def find_similar_groups(df, similarity_threshold=0.8):
    """Find groups of similar titles in the dataframe"""
    # Create a list of all titles
    titles = df['Title'].tolist()
    similar_groups = []
    processed_indices = set()
    
    # Compare each title with every other title
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
        
        if len(current_group) > 1:  # Only add groups with more than one similar title
            similar_groups.append(current_group)
    
    return similar_groups

def rearrange_csv(df, similar_groups):
    """Rearrange the dataframe based on similar groups"""
    # Create a list of all indices
    all_indices = list(range(len(df)))
    
    # Remove indices that are in groups
    for group in similar_groups:
        for idx in group:
            all_indices.remove(idx)
    
    # Create new order: groups first, then remaining items
    new_order = []
    for group in similar_groups:
        new_order.extend(group)
    new_order.extend(all_indices)
    
    # Reorder the dataframe
    return df.iloc[new_order]

def main():
    # Read the CSV file
    csv_file = r"C:\Users\tungt\Documents\WebScraper\soldprice\soldprice\abdou_diallo.csv"
    df = pd.read_csv(csv_file)
    
    print(f"Original file has {len(df)} lines")
    
    # Remove duplicates first
    df = remove_duplicates(df)
    
    # Find similar groups
    similar_groups = find_similar_groups(df)
    
    # Rearrange the dataframe
    rearranged_df = rearrange_csv(df, similar_groups)
    
    # Save the rearranged data back to CSV
    output_file = csv_file.replace('.csv', '_sorted.csv')
    rearranged_df.to_csv(output_file, index=False)
    
    print(f"\nRearranged CSV saved to: {output_file}")
    print(f"Found {len(similar_groups)} groups of similar titles")
    print(f"Total lines after removing duplicates: {len(df)}")
    print(f"Lines in groups: {sum(len(group) for group in similar_groups)}")
    print(f"Individual lines: {len(df) - sum(len(group) for group in similar_groups)}")

if __name__ == "__main__":
    main() 