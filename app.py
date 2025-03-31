from flask import Flask, jsonify, render_template
import csv
import os

app = Flask(__name__)

def read_csv():
    cards = []
    # Get the absolute path to the CSV file
    csv_path = os.path.join('soldprice', 'soldprice', 'kevin_agudelo.csv')
    
    try:
        if not os.path.exists(csv_path):
            print(f"CSV file not found at: {csv_path}")
            return []
            
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as file:
            # Read the first line to get headers
            first_line = file.readline().strip()
            headers = first_line.split(',')
            file.seek(0)  # Go back to start of file
            
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                try:
                    card_data = {}
                    for header in headers:
                        # Clean up the header name and get the corresponding value
                        clean_header = header.strip('"').strip()
                        card_data[clean_header] = row[header].strip('"').strip() if header in row else ''
                    
                    cards.append({
                        'Title': card_data.get('Title', ''),
                        'Price': card_data.get('Price', ''),
                        'Link': card_data.get('Link', ''),
                        'Image Link': card_data.get('Image Link', ''),
                        'Sold Date': card_data.get('Sold Date', '')
                    })
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue
        
        print(f"Successfully loaded {len(cards)} cards from CSV")
        return cards
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/cards')
def get_cards():
    cards = read_csv()
    return jsonify(cards)

if __name__ == '__main__':
    app.run(debug=True) 