def remove_duplicates(file_path):
    try:
        # Read the file and get unique lines
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Use a set to track unique lines
        unique_lines = set(lines)
        
        # Write the unique lines back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(unique_lines)
        
        print(f"Removed duplicate lines from {file_path}")
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def main():
    file_path = r'C:\Users\tungt\Documents\WebScraper\soldprice\soldprice\Panini_player_names.csv'
    remove_duplicates(file_path)

if __name__ == "__main__":
    main() 