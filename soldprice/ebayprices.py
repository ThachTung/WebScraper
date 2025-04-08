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

# Define soccer card specific keywords (must have at least one from each category)
CARD_KEYWORDS = {
    'card', 'parallel', 'insert', 'rookie', 'rc', 'prizm', 'mosaic', 'select',
    'donruss', 'panini', 'topps', 'chrome', 'refractor', 'auto', 'numbered'
}

SOCCER_KEYWORDS = {
    'soccer', 'football', 'fifa', 'premier league', 'bundesliga', 'la liga',
    'serie a', 'ligue 1', 'uefa', 'champions league', 'world cup'
}

# Define keywords to exclude
EXCLUDE_KEYWORDS = {
    'baseball', 'basketball', 'nfl', 'nba', 'mlb', 'nhl', 'hockey', 'pokemon',
    'magic the gathering', 'yugioh', 'jersey', 'shirt', 'boot', 'cleat', 'ball',
    'video game', 'action figure', 'toy', 'sticker album'
}

def is_soccer_card(title):
    """
    Check if an item is specifically a soccer card
    Returns True if the item is a soccer card, False otherwise
    """
    if not title:
        return False
        
    title_lower = title.lower()
    
    # First check for excluded keywords
    for keyword in EXCLUDE_KEYWORDS:
        if keyword in title_lower:
            return False
    
    # Check if it contains at least one card-related keyword
    has_card_keyword = any(keyword in title_lower for keyword in CARD_KEYWORDS)
    if not has_card_keyword:
        return False
    
    # Check if it contains at least one soccer-related keyword
    has_soccer_keyword = any(keyword in title_lower for keyword in SOCCER_KEYWORDS)
    if not has_soccer_keyword:
        return False
    
    return True

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
        player_df = pd.read_csv('data/Panini_player_names.csv', header=None, names=['player_name'])
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
            title_text = title.text
            # Only return item data if it's specifically a soccer card
            if is_soccer_card(title_text):
                return {
                    'Title': title_text,
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
    
    return items_list

def scrape_region(player_name, region_name, region_params, session):
    """Scrape eBay listings for a specific player in a specific region with parallel page processing"""
    items_list = []
    max_pages = 5  # Limit maximum pages per region for faster scraping
    pages_per_batch = 2  # Number of pages to process in parallel
    
    with ThreadPoolExecutor(max_workers=pages_per_batch) as page_executor:
        futures = []
        for start_page in range(1, max_pages + 1, pages_per_batch):
            end_page = min(start_page + pages_per_batch - 1, max_pages)
            future = page_executor.submit(
                scrape_region_pages,
                player_name,
                region_name,
                region_params,
                session,
                start_page,
                end_page
            )
            futures.append(future)
        
        for future in as_completed(futures):
            try:
                page_items = future.result()
                items_list.extend(page_items)
            except Exception as e:
                print(f"Error in page batch for {region_name}: {e}")
    
    return items_list

def scrape_ebay_listings(player_name):
    """Scrape eBay listings for a specific player across multiple regions with optimized parallel processing"""
    # Define region-specific parameters with rate limiting
    regions = {
        'United States': {'LH_PrefLoc': 1},
        'Europe': {'LH_PrefLoc': 3},
        'United Kingdom': {'LH_PrefLoc': 4},
        'Asia': {'LH_PrefLoc': 5}
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
    
    # Save combined data
    if all_items:
        # Read existing combined file if it exists
        combined_file = 'data/scrapeddata/all_players.csv'
        if os.path.exists(combined_file):
            existing_df = pd.read_csv(combined_file)
            new_df = pd.DataFrame(all_items)
            
            # Combine and remove duplicates
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['Link'], keep='first')
            
            # Save updated combined data
            combined_df.to_csv(combined_file, index=False)
            print(f"\nUpdated combined file with new soccer cards")
            print(f"Total combined cards: {len(combined_df)}")
        else:
            # Create new combined file
            pd.DataFrame(all_items).to_csv(combined_file, index=False)
            print(f"\nCreated new combined file with {len(all_items)} soccer cards")
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\nTotal execution time: {duration}")

if __name__ == "__main__":
    main()
