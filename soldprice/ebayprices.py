import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

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
        player_df = pd.read_csv('player.csv', header=None, names=['player_name'])
        return player_df['player_name'].tolist()
    except Exception as e:
        print(f"Error reading player.csv: {e}")
        return []

def scrape_ebay_listings(player_name):
    """Scrape eBay listings for a specific player"""
    # Define the base URL for the eBay search
    url = "https://www.ebay.com/sch/i.html"
    #https://www.ebay.com/sch/i.html?_nkw=soccer+card&_sacat=0&_from=R40&LH_Sold=1&LH_Complete=1&_ipg=240&rt=nc&_pgn=75
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
        page_number += 1
        print(f'Scraping page {page_number} for {player_name}')
        
        params['_pgn'] = page_number
        response = requests.get(url, params=params)
        html_content = response.text
        
        soup = BeautifulSoup(html_content, 'html.parser')
        next_button = soup.find('button', class_='pagination__next', type='next')
        items = soup.find_all('div', class_='s-item__wrapper clearfix')
        
        # Extract Listings
        for item in items[2:]:
            title = item.find('div', class_='s-item__title').text
            price = item.find('span', class_='s-item__price').text
            link = item.find('a', class_='s-item__link')['href'].split('?')[0]
            image_url = item.find('div', class_='s-item__image-wrapper image-treatment').find('img').get('src', 'No image URL')
            solddate = item.find('span', class_='s-item__caption--signal POSITIVE').text
            
            items_list.append({
                'Title': title,
                'Price': price,
                'Link': link,
                'Image Link': image_url,
                'Sold Date': solddate
            })
        
        #if next_button and next_button.get('aria-disabled') == 'true':
            #break
    
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
        print(f"\nProcessing player: {player_name}")
        player_items = scrape_ebay_listings(player_name)
        all_items.extend(player_items)
        
        # Save individual player data
        player_df = pd.DataFrame(player_items)
        player_filename = f"soldprice/{player_name.replace(' ', '_').lower()}.csv"
        player_df.to_csv(player_filename, index=False)
        print(f"Saved {len(player_items)} listings for {player_name} to {player_filename}")
    
    # Save combined data
    all_items_df = pd.DataFrame(all_items)
    all_items_df.to_csv('soldprice/all_players.csv', index=False)
    print(f"\nSaved {len(all_items)} total listings to soldprice/all_players.csv")

if __name__ == "__main__":
    main()
