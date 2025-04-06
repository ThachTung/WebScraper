def remove_commas(file_path):
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remove all commas
        content = content.replace(',', '')
        
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print(f"Removed all commas from {file_path}")
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def main():
    file_path = r'C:\Users\tungt\Documents\WebScraper\soldprice\soldprice\Panini_player_names.csv'
    remove_commas(file_path)

if __name__ == "__main__":
    main() 