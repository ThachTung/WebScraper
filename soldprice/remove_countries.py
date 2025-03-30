import re

def remove_countries(file_path):
    try:
        # Define a list of country names to remove
        countries = [
            'Netherlands', 'Germany', 'France', 'Spain', 'Italy', 'Brazil', 'Argentina',
            'England', 'Portugal', 'Belgium', 'Mexico', 'USA', 'Canada', 'Australia',
            'Japan', 'South Korea', 'China', 'Russia', 'India', 'Nigeria', 'Egypt'
        ]
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Remove country names
        cleaned_lines = []
        for line in lines:
            for country in countries:
                line = re.sub(rf'\b{country}\b', '', line)
            cleaned_lines.append(line)
        
        # Write the cleaned lines back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(cleaned_lines)
        
        print(f"Removed country names from {file_path}")
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def main():
    file_path = r'C:\Users\tungt\Documents\WebScraper\soldprice\soldprice\Panini_player_names.csv'
    remove_countries(file_path)

if __name__ == "__main__":
    main() 