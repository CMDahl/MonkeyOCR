import re
import pandas as pd

def extract_failed_names(log_file_path):
    """Simple function to extract names with JSON parsing failures and biography extraction errors."""
    json_failed_names = []
    biography_error_names = []
    
    # Try different encodings
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(log_file_path, 'r', encoding=encoding, errors='ignore') as file:
                for line in file:
                    # Check for JSON parsing failures
                    if 'JSON parsing failed for' in line:
                        match = re.search(r'JSON parsing failed for ([^:]+):', line)
                        if match:
                            name = match.group(1).strip()
                            json_failed_names.append(name)
                    
                    # Check for general biography extraction errors
                    elif 'Error extracting biography for' in line:
                        match = re.search(r'Error extracting biography for ([^:]+):', line)
                        if match:
                            name = match.group(1).strip()
                            biography_error_names.append(name)
            
            print(f"Successfully read file with encoding: {encoding}")
            break
        except UnicodeDecodeError:
            print(f"Failed to read with encoding: {encoding}")
            continue
    else:
        print("Could not read file with any encoding, trying with error handling...")
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='replace') as file:
                for line in file:
                    if 'JSON parsing failed for' in line:
                        match = re.search(r'JSON parsing failed for ([^:]+):', line)
                        if match:
                            name = match.group(1).strip()
                            json_failed_names.append(name)
                    elif 'Error extracting biography for' in line:
                        match = re.search(r'Error extracting biography for ([^:]+):', line)
                        if match:
                            name = match.group(1).strip()
                            biography_error_names.append(name)
        except Exception as e:
            print(f"Failed to read file: {e}")
            return [], []
    
    return json_failed_names, biography_error_names

# Usage example:
if __name__ == "__main__":
    log_file = r"d:\data\HCNC\norway\biographies\storage\Dolphin\logs\biography_extractor_Dolphin.log"
    json_failures, bio_errors = extract_failed_names(log_file)
    
    print(f"Found {len(json_failures)} names with JSON parsing failures:")
    for name in json_failures:
        print(f"  - {name}")
    
    print(f"\nFound {len(bio_errors)} names with biography extraction errors:")
    for name in bio_errors:
        print(f"  - {name}")
    
    # Save both to files
    if json_failures:
        with open(r"d:\data\HCNC\norway\biographies\storage\Dolphin\logs\json_failed_names.txt", 'w', encoding='utf-8') as f:
            for name in json_failures:
                f.write(f"{name}\n")
        print(f"\nJSON failures saved to json_failed_names.txt")
    
    if bio_errors:
        with open(r"d:\data\HCNC\norway\biographies\storage\Dolphin\logs\bio_error_names.txt", 'w', encoding='utf-8') as f:
            for name in bio_errors:
                f.write(f"{name}\n")
        print(f"Biography errors saved to bio_error_names.txt")

    df = pd.read_csv(r'D:\data\HCNC\norway\biographies\storage\Dolphin\output\extracted_all_names_Dolphin_with_chunks.csv', encoding='utf-8')

    # Combine both error lists into one set for efficient lookup
    all_failed_names = set(json_failures + bio_errors)

    # Extract rows where the name is in either error list
    failed_rows = df[df['name'].isin(all_failed_names)]

    print(f"Found {len(failed_rows)} rows with failed names out of {len(df)} total rows")

    # Save the failed rows to a new CSV file
    failed_rows.to_csv(r"d:\data\HCNC\norway\biographies\storage\Dolphin\logs\failed_rows.csv", index=False, encoding='utf-8')


#python biography_extractor_Dolphin.py "d:\data\HCNC\norway\biographies\storage\Dolphin\logs\failed_rows.csv" "d:\data\HCNC\norway\biographies\storage\Dolphin\logs\biographical_data_failed_rows.json"