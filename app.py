from flask import Flask, jsonify, render_template, request
import csv
import os
import pandas as pd
from datetime import datetime
from functools import lru_cache

app = Flask(__name__)

# Cache for the DataFrame
_df_cache = None
_last_modified = None

def get_file_modified_time(file_path):
    """Get the last modified time of the file"""
    try:
        return os.path.getmtime(file_path)
    except OSError:
        return None

@lru_cache(maxsize=1000)
def parse_price(price_str):
    """Convert price string to numeric value for sorting"""
    try:
        return float(price_str.replace('VND', '').replace(',', '').strip())
    except (ValueError, AttributeError):
        return 0

@lru_cache(maxsize=1000)
def parse_date(date_str):
    """Convert date string to timestamp for sorting"""
    try:
        clean_date = date_str.replace('Sold ', '')
        return datetime.strptime(clean_date, '%b %d, %Y').timestamp()
    except (ValueError, AttributeError):
        return 0

def read_csv():
    """Read all CSV files from the scrapeddata folder into a pandas DataFrame with caching"""
    global _df_cache, _last_modified
    data_dir = os.path.join('soldprice', 'data', 'scrapeddata')
    
    try:
        # Check if directory exists
        if not os.path.exists(data_dir):
            print(f"Directory not found: {data_dir}")
            return pd.DataFrame()
        
        # Get list of all CSV files
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if not csv_files:
            print(f"No CSV files found in: {data_dir}")
            return pd.DataFrame()
            
        # Get latest modification time of any CSV file
        current_modified = max(
            get_file_modified_time(os.path.join(data_dir, f))
            for f in csv_files
        )
        
        # Return cached DataFrame if no files have changed
        if _df_cache is not None and _last_modified == current_modified:
            return _df_cache
            
        # Read and combine all CSV files
        dfs = []
        for csv_file in csv_files:
            file_path = os.path.join(data_dir, csv_file)
            try:
                # Read CSV and add player name column
                df = pd.read_csv(file_path)
                player_name = os.path.splitext(csv_file)[0].replace('_', ' ')
                df['Player'] = player_name
                dfs.append(df)
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
                continue
        
        if not dfs:
            print("No valid CSV files could be read")
            return pd.DataFrame()
        
        # Combine all DataFrames
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Optimize memory usage by converting to categorical where appropriate
        for col in combined_df.select_dtypes(include=['object']):
            if combined_df[col].nunique() / len(combined_df) < 0.5:  # If less than 50% unique values
                combined_df[col] = combined_df[col].astype('category')
        
        # Cache the DataFrame and modification time
        _df_cache = combined_df
        _last_modified = current_modified
        
        return combined_df
        
    except Exception as e:
        print(f"Error reading CSV files: {e}")
        return pd.DataFrame()

def apply_datatables_sorting(df, order):
    """Apply DataTables sorting with optimized algorithm"""
    if not order:
        return df
        
    sort_columns = []
    ascending = []
    
    for sort_col in order:
        column = sort_col['column']
        direction = sort_col['dir']
        
        if column == 'Price':
            # Add temporary sorting column
            df[f'sort_{column}'] = df['Price'].apply(parse_price)
            sort_columns.append(f'sort_{column}')
        elif column == 'Sold Date':
            df[f'sort_{column}'] = df['Sold Date'].apply(parse_date)
            sort_columns.append(f'sort_{column}')
        else:
            sort_columns.append(column)
            
        ascending.append(direction == 'asc')
    
    # Sort once with all columns
    df = df.sort_values(sort_columns, ascending=ascending)
    
    # Drop temporary sorting columns
    for col in sort_columns:
        if col.startswith('sort_'):
            df = df.drop(col, axis=1)
    
    return df

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/cards', methods=['GET', 'POST'])
def get_cards():
    try:
        # Get DataTables parameters
        draw = int(request.values.get('draw', 1))
        start = int(request.values.get('start', 0))
        length = int(request.values.get('length', 10))
        
        # Handle sorting parameters
        order = []
        order_columns = ['Title', 'Price', 'Link', 'Image Link', 'Sold Date']
        i = 0
        while True:
            order_column = request.values.get(f'order[{i}][column]')
            order_dir = request.values.get(f'order[{i}][dir]')
            if order_column is None:
                break
            order.append({
                'column': order_columns[int(order_column)],
                'dir': order_dir
            })
            i += 1
        
        # Read the CSV file
        df = read_csv()
        
        if df.empty:
            return jsonify({
                'draw': draw,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': []
            })
        
        # Store total record count
        total_records = len(df)
        filtered_records = total_records
        
        # Apply sorting
        df = apply_datatables_sorting(df, order)
        
        # Apply pagination
        df = df.iloc[start:start + length]
        
        # Convert DataFrame to list of dictionaries
        data = df.to_dict('records')
        
        return jsonify({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })
        
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({
            'draw': 1,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 