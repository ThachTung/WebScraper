def clean_csv(file_path):
    try:
        print("Starting CSV cleaning process...")
        
        # Step 1: Read the file
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        print("File read successfully")
        
        # Step 2: Break lines at '/' and remove it
        broken_lines = []
        for line in lines:
            parts = line.split('/')
            for part in parts:
                broken_lines.append(part.strip() + '\n')
        print("Split lines at '/' character")
        
        # Step 3: Remove blank lines and lines with only whitespace
        cleaned_lines = [line for line in broken_lines if line.strip()]
        print("Removed blank lines")
        
        # Step 4: Remove commas from each line
        cleaned_lines = [line.replace(',', '') for line in cleaned_lines]
        print("Removed commas")
        
        # Step 5: Remove hyphens from each line
        cleaned_lines = [line.replace('-', '') for line in cleaned_lines]
        print("Removed hyphens")
        
        # Step 6: Remove duplicates while preserving order
        seen = set()
        unique_lines = []
        for line in cleaned_lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        print("Removed duplicates")
        
        # Step 7: Write the cleaned content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(unique_lines)
        
        print(f"\nSummary of changes:")
        print(f"- Original line count: {len(lines)}")
        print(f"- Lines after breaking at '/': {len(broken_lines)}")
        print(f"- Lines after removing blanks: {len(cleaned_lines)}")
        print(f"- Final line count after removing duplicates: {len(unique_lines)}")
        print(f"\nFile has been successfully cleaned: {file_path}")
        
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def main():
    file_path = r'C:\Users\tungt\Documents\WebScraper\soldprice\data\Panini_player_names.csv'
    clean_csv(file_path)

if __name__ == "__main__":
    main() 