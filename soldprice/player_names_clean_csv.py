import re

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
                broken_lines.append(part.strip())
        print("Split lines at '/' character")
        
        # Step 3: Remove blank lines and lines with only whitespace
        cleaned_lines = [line for line in broken_lines if line.strip()]
        print("Removed blank lines")
        
        # Step 4: Remove commas from each line
        cleaned_lines = [line.replace(',', '') for line in cleaned_lines]
        print("Removed commas")
        
        # Step 5: Remove hyphens from each line
        cleaned_lines = [line.replace('-', ' ') for line in cleaned_lines]
        print("Removed hyphens")
        
        # Step 6: Remove text within parentheses
        cleaned_lines = [re.sub(r'\(.*?\)', '', line) for line in cleaned_lines]
        print("Removed text within parentheses")
        
        # Step 7: Remove country names
        country_names = get_country_names()
        cleaned_lines = [remove_names(line, country_names) for line in cleaned_lines]
        print("Removed country names")
        
        
        # Step 9: Remove duplicates while preserving order
        seen = set()
        unique_lines = []
        for line in cleaned_lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        print("Removed duplicates")
        
        # Step 10: Write the cleaned content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            for line in unique_lines:
                file.write(line + '\n')
        
        print(f"\nSummary of changes:")
        print(f"- Original line count: {len(lines)}")
        print(f"- Lines after breaking at '/': {len(broken_lines)}")
        print(f"- Lines after removing blanks: {len(cleaned_lines)}")
        print(f"- Final line count after removing duplicates: {len(unique_lines)}")
        print(f"\nFile has been successfully cleaned: {file_path}")
        
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def remove_names(line, names):
    """Remove specified names from a line"""
    for name in names:
        line = re.sub(r'\b' + re.escape(name) + r'\b', '', line)
    return line.strip()

def get_country_names():
    """Return a list of all country names"""
    return [
        "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria",
        "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
        "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia",
        "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica",
        "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador",
        "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini (fmr. \"Swaziland\")", "Ethiopia", "Fiji", "Finland", "France",
        "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau",
        "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq",
        "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait",
        "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg",
        "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico",
        "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar (formerly Burma)", "Namibia", "Nauru",
        "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia (formerly Macedonia)", "Norway", "Oman",
        "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal",
        "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe",
        "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia",
        "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
        "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan",
        "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela",
        "Vietnam", "Yemen", "Zambia", "Zimbabwe"
    ]

def main():
    file_path = r'C:\Users\tungt\Documents\WebScraper\soldprice\data\combined_athletes.csv'
    clean_csv(file_path)

if __name__ == "__main__":
    main() 