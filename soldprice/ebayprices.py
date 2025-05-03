import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime
import re

# Define retry strategy
retry_strategy = Retry(
    total=3,  # number of retries
    backoff_factor=1,  # wait 1, 2, 4 seconds between retries
    status_forcelist=[500, 502, 503, 504]  # HTTP status codes to retry on
)

# Create a thread-local storage for sessions
thread_local = threading.local()

def get_session():
    """Get a thread-local session"""
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
        thread_local.session.mount("http://", adapter)
        thread_local.session.mount("https://", adapter)
    return thread_local.session

def read_player_names():
    """Read player names from player.csv file"""
    try:
        player_df = pd.read_csv('data/combined_athletes.csv', header=None, names=['player_name'])
        return player_df['player_name'].tolist()
    except Exception as e:
        print(f"Error reading player.csv: {e}")
        return []

def extract_item_data(item):
    """Extract data from a single item"""
    try:
        title = item.find('div', class_='s-item__title')
        price = item.find('span', class_='s-item__price')
        link = item.find('a', class_='s-item__link')
        image_div = item.find('div', class_='s-item__image-wrapper image-treatment')
        solddate = item.find('span', class_='s-item__caption--signal POSITIVE')
        
        if all([title, price, link, image_div, solddate]):
            # List of card manufacturers to filter by
            card_manufacturers = ['panini', 'topps', 'merlin', 'leaf', 'pro set', 'donruss', 'kaboom','daka','fansmall','megacracks','match attax','adrenalyn']
            
            # Convert title to lowercase for case-insensitive comparison
            title_lower = title.text.lower()
            
            # Check if any of the manufacturers are in the title
            if any(manufacturer in title_lower for manufacturer in card_manufacturers):
                return {
                    'Title': title.text,
                    'Price': price.text,
                    'Link': link['href'].split('?')[0],
                    'Image Link': image_div.find('img').get('src', 'No image URL'),
                    'Sold Date': solddate.text
                }
    except AttributeError:
        pass
    return None

def scrape_ebay_page(url, params, session):
    """Scrape a single eBay page with optimized performance"""
    try:
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')  # Using lxml parser for better performance
        items = soup.find_all('div', class_='s-item__wrapper clearfix')

        if not items:
            return [], False
        
        # Process items in batch
        items_data = [
            item_data for item in items[1:]  # Skip first item as it's usually an ad
            if (item_data := extract_item_data(item)) is not None
        ]
        
        # Simplified pagination check
        next_button = soup.find('a', {'class': 'pagination__next'})
        has_next = next_button is not None and 'disabled' not in next_button.get('class', [])
        
        return items_data, has_next
    except Exception as e:
        print(f"Error scraping page: {e}")
        return [], False

def scrape_region_pages(player_name, region_name, region_params, session, start_page, end_page):
    """Scrape a range of pages for a region"""
    url = "https://www.ebay.com/sch/i.html"
    params = {
        '_from': 'R40',
        '_nkw': f"{player_name}",
        'LH_Sold': '1',
        'LH_Complete': '1',
        '_ipg': '240',
        'rt': 'nc',
        '_sacat': '0',
        **region_params
    }
    
    items_list = []
    max_retries = 3
    
    for page_number in range(start_page, end_page + 1):
        params['_pgn'] = page_number
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            items_data, has_next = scrape_ebay_page(url, params, session)
            
            if items_data:
                items_list.extend(items_data)
                print(f"Scraped {len(items_data)} cards from page {page_number} for {player_name} in {region_name}")
                success = True
            else:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(1)  # Reduced sleep time
    
    return items_list, has_next

def scrape_region(player_name, region_name, region_params, session):
    """Scrape eBay listings for a specific player in a specific region with parallel page processing"""
    items_list = []
    pages_per_batch = 2  # Number of pages to process in parallel
    current_page = 1
    has_more_pages = True
    
    while has_more_pages:
        with ThreadPoolExecutor(max_workers=pages_per_batch) as page_executor:
            futures = []
            # Process next batch of pages
            end_page = current_page + pages_per_batch - 1
            future = page_executor.submit(
                scrape_region_pages,
                player_name,
                region_name,
                region_params,
                session,
                current_page,
                end_page
            )
            futures.append(future)
            
            for future in as_completed(futures):
                try:
                    page_items, has_next = future.result()
                    items_list.extend(page_items)
                    has_more_pages = has_next
                    if not has_next:
                        print(f"No more pages found for {player_name} in {region_name}")
                except Exception as e:
                    print(f"Error in page batch for {region_name}: {e}")
                    has_more_pages = False
            
            current_page = end_page + 1
            if not has_more_pages:
                break
    
    return items_list

def scrape_ebay_listings(player_name):
    """Scrape eBay listings for a specific player across multiple regions with optimized parallel processing"""
    # Define region-specific parameters with rate limiting
    regions = {
        'United States': {'LH_PrefLoc': 4},
        'Domestic': {'LH_PrefLoc': 1},
        'International': {'LH_PrefLoc': 2},
        'Continent': {'LH_PrefLoc': 3}
    }
    
    items_list = []
    session = get_session()  # Create a single session for all regions
    
    # Process regions in parallel with optimized thread count
    with ThreadPoolExecutor(max_workers=min(len(regions), 4)) as executor:
        future_to_region = {
            executor.submit(
                scrape_region,
                player_name,
                region_name,
                region_params,
                session
            ): region_name
            for region_name, region_params in regions.items()
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_region):
            region_name = future_to_region[future]
            try:
                region_items = future.result()
                if region_items:
                    items_list.extend(region_items)
                    print(f"Completed scraping {len(region_items)} items for {player_name} in {region_name}")
            except Exception as e:
                print(f"Error scraping {region_name} for {player_name}: {e}")
    
    return items_list

def save_player_data(player_name, player_items):
    """Save player data to CSV, appending if file exists"""
    if not player_items:
        return []
    
    new_df = pd.DataFrame(player_items)
    player_filename = f"data/scrapeddata/{player_name.replace(' ', '_').lower()}.csv"
    
    try:
        # If file exists, read it and append new data
        if os.path.exists(player_filename):
            existing_df = pd.read_csv(player_filename)
            
            # Remove duplicates based on Link (which should be unique for each item)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['Link'], keep='first')

            # Save combined data
            combined_df.to_csv(player_filename, index=False)
            print(f"Updated {player_filename} with {len(new_df)} new soccer cards")
            print(f"Total cards: {len(combined_df)} (Added: {len(new_df)}, Existing: {len(existing_df)})")
            return combined_df.to_dict('records')

        # If file doesn't exist, save new data
        new_df.to_csv(player_filename, index=False)
        print(f"Created new file {player_filename} with {len(new_df)} soccer cards")
        return player_items
    except Exception as e:
        print(f"Error saving data for {player_name}: {e}")
        return []

def process_player(player_name):
    """Process a single player"""
    try:
        print(f"\nProcessing player: {player_name}")
        player_items = scrape_ebay_listings(player_name)
        return save_player_data(player_name, player_items)
    except Exception as e:
        print(f"Error processing player {player_name}: {e}")
        return []

def main():
    start_time = datetime.now()
    
    # Read player names from CSV
    player_names = read_player_names()
    if not player_names:
        print("No player names found in player.csv")
        return
    
    # Create directory for individual player files
    os.makedirs('data/scrapeddata', exist_ok=True)
    
    # Process players concurrently
    all_items = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_player = {executor.submit(process_player, name): name for name in player_names}
        
        for future in as_completed(future_to_player):
            player_name = future_to_player[future]
            try:
                player_items = future.result()
                all_items.extend(player_items)
            except Exception as e:
                print(f"Error processing {player_name}: {e}")

    # Remove duplicates from all scraped files
    remove_duplicates_from_all_files()
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\nTotal execution time: {duration}")

def remove_duplicates_from_all_files():
    """Removes duplicate rows based on 'Link' column from all CSV files in the scrapeddata directory."""
    directory = 'data/scrapeddata'
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            filepath = os.path.join(directory, filename)
            try:
                df = pd.read_csv(filepath)
                initial_len = len(df)
                df = df.drop_duplicates(subset=['Link'], keep='first')
                final_len = len(df)
                df.to_csv(filepath, index=False)
                print(f"Removed {initial_len - final_len} duplicate rows from {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    main()
