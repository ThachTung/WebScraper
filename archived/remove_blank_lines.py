def remove_blank_lines(file_path):
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Remove blank lines and lines with only whitespace
        cleaned_lines = [line for line in lines if line.strip()]
        
        # Write the cleaned lines back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(cleaned_lines)
        
        print(f"Removed blank lines from {file_path}")
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def main():
    file_path = r'C:\Users\tungt\Documents\WebScraper\soldprice\soldprice\Panini_player_names.csv'
    remove_blank_lines(file_path)

if __name__ == "__main__":
    main() 