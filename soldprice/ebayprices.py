import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Define retry strategy
retry_strategy = Retry(
    total=3,  # number of retries
    backoff_factor=1,  # wait 1, 2, 4 seconds between retries
    status_forcelist=[500, 502, 503, 504]  # HTTP status codes to retry on
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

# Define the eBay filters dictionary
ebay_filters = {
    "item_conditions": {
        "New": 1000,
        "Open box": 1500,
        "Used": 3000,
        "Certified Refurbished": 2000,
        "Excellent - Refurbished": 2500,
        "Very Good": 3000,
        "Good": 4000,
        "For Parts or Not Working": 7000
    },
    "item_locations": {
        "Domestic": 1,
        "International": 2,
        "Continent": 3,
    },
    "directories": {
        "No Directory": 0,
        "Consumer Electronics": 9355,
        "Clothing, Shoes & Accessories": 11450,
        "Health & Beauty": 26395,
        "Home & Garden": 11700,
        "Sporting Goods": 382,
        "Toys & Hobbies": 220,
        "Books": 267,
        "Video Games & Consoles": 1249,
        "Collectibles": 1,
        "Business & Industrial": 12576,
        "Automotive": 6000, 
    },
    "categories": {
        "No Category": 0,
        "Cell Phones & Smartphones": 9355,
        "Laptops & Netbooks": 175673,
        "Watches": 31387,
        "Furniture": 3197,
        "Action Figures": 2605,
        "Jewelry & Watches": 281,
        "Cameras & Photo": 625,
        "Pet Supplies": 1281,
        "Crafts": 14339,
        "Computers/Tablets & Networking": 58058,
        "Cars & Trucks": 6001,  
        "Motorcycles": 6024,  
        "Car & Truck Parts": 6030,  
        "Motorcycle Parts": 10063,  
        "Automotive Tools & Supplies": 34998,  
    },
    "sort_order": {
        "Best Match": 12,
        "Time: ending soonest": 1,
        "Time: newly listed": 10,
        "Price + Shipping: lowest first": 15,
        "Price + Shipping: highest first": 16,
        "Distance: nearest first": 7
    }
}

def read_player_names():
    """Read player names from player.csv file"""
    try:
        player_df = pd.read_csv('soldprice/Panini_player_names.csv', header=None, names=['player_name'])
        return player_df['player_name'].tolist()
    except Exception as e:
        print(f"Error reading player.csv: {e}")
        return []

def scrape_ebay_listings(player_name):
    """Scrape eBay listings for a specific player"""
    # Define the base URL for the eBay search
    url = "https://www.ebay.com/sch/i.html"
    
    # Define the query parameters for the search request
    params = {
        '_from': 'R40',
        '_nkw': player_name,
        'LH_PrefLoc': ebay_filters["item_locations"]["International"],
        '_sop': ebay_filters["sort_order"]["Time: newly listed"],
        'LH_Sold': '1',
        'LH_Complete': '1',
        '_ipg': '240',
        'rt':'nc',
        '_sacat':'0',
    }
    
    items_list = []
    page_number = 0
    
    while True:
        try:
            page_number += 1
            print(f'Scraping page {page_number} for {player_name}')
            
            params['_pgn'] = page_number
            
            # Add delay between requests
            time.sleep(2)  # Wait 2 seconds between requests
            
            # Make request with increased timeout and session
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            next_button = soup.find('button', class_='pagination__next', type='next')
            items = soup.find_all('div', class_='s-item__wrapper clearfix')
            
            if not items:  # If no items found, break the loop
                print(f"No more items found for {player_name}")
                break
            
            # Extract Listings
            for item in items[2:]:
                try:
                    title = item.find('div', class_='s-item__title')
                    price = item.find('span', class_='s-item__price')
                    link = item.find('a', class_='s-item__link')
                    image_div = item.find('div', class_='s-item__image-wrapper image-treatment')
                    solddate = item.find('span', class_='s-item__caption--signal POSITIVE')
                    
                    # Check if all required elements exist
                    if all([title, price, link, image_div, solddate]):
                        items_list.append({
                            'Title': title.text,
                            'Price': price.text,
                            'Link': link['href'].split('?')[0],
                            'Image Link': image_div.find('img').get('src', 'No image URL'),
                            'Sold Date': solddate.text
                        })
                except AttributeError as e:
                    print(f"Error processing item: {e}")
                    continue
            
            if next_button and next_button.get('aria-disabled') == 'true':
                break
                
        except requests.RequestException as e:
            print(f"Error fetching page {page_number} for {player_name}: {e}")
            if page_number > 1:  # If we've already got some data, continue with what we have
                break
            else:
                time.sleep(5)  # Wait longer before retrying the first page
                continue
    
    return items_list

def main():
    # Read player names from CSV
    player_names = read_player_names()
    if not player_names:
        print("No player names found in player.csv")
        return
    
    # Create directory for individual player files if it doesn't exist
    os.makedirs('soldprice', exist_ok=True)
    
    # Process each player
    all_items = []
    for player_name in player_names:
        try:
            print(f"\nProcessing player: {player_name}")
            player_items = scrape_ebay_listings(player_name)
            
            if player_items:  # Only process if we got some items
                all_items.extend(player_items)
                
                # Save individual player data
                player_df = pd.DataFrame(player_items)
                player_filename = f"soldprice/{player_name.replace(' ', '_').lower()}.csv"
                player_df.to_csv(player_filename, index=False)
                print(f"Saved {len(player_items)} listings for {player_name} to {player_filename}")
            else:
                print(f"No items found for {player_name}")
                
            # Add delay between players
            time.sleep(3)
            
        except Exception as e:
            print(f"Error processing player {player_name}: {e}")
            continue
    
    # Save combined data
    if all_items:
        all_items_df = pd.DataFrame(all_items)
        all_items_df.to_csv('soldprice/all_players.csv', index=False)
        print(f"\nSaved {len(all_items)} total listings to soldprice/all_players.csv")
    else:
        print("No items were collected successfully")

if __name__ == "__main__":
    main()
