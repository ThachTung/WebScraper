def break_lines(file_path):
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Break lines at '/' and remove it
        modified_lines = []
        for line in lines:
            parts = line.split('/')
            for part in parts:
                modified_lines.append(part.strip() + '\n')
        
        # Write the modified lines back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(modified_lines)
        
        print(f"Processed lines in {file_path}")
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def main():
    file_path = r'C:\Users\tungt\Documents\WebScraper\soldprice\soldprice\Panini_player_names.csv'
    break_lines(file_path)

if __name__ == "__main__":
    main() 