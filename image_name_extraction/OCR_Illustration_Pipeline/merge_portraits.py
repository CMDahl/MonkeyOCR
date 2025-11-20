import os
import json
import pandas as pd
import argparse
import sys
from pathlib import Path
from collections import defaultdict
import re

def clean_name(name):
    """
    Remove common prefixes/symbols from biographical names
    - † (dagger/cross symbol indicating deceased)
    - * (asterisk)
    - � (replacement character from encoding issues)
    - Leading/trailing whitespace
    """
    if pd.isna(name):
        return name
    
    # Remove leading symbols and whitespace
    cleaned = re.sub(r'^[†*�\s]+', '', str(name))
    # Remove trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned

def normalize_name_for_matching(name):
    """
    Normalize a name for fuzzy matching:
    - Remove trailing periods
    - Remove maiden name parts (", f. ...")
    - Strip whitespace
    """
    if pd.isna(name):
        return ""
    
    normalized = str(name).strip()
    # Remove trailing period
    normalized = normalized.rstrip('.')
    # Remove maiden name part (e.g., ", f. Blackstad")
    normalized = re.sub(r',\s*f\.\s+\w+', '', normalized)
    
    return normalized.strip()

def extract_portraits_from_markdown(markdown_text):
    """
    Extract portrait filenames from markdown text.
    Looks for HTML img tags: <img src="imgs/filename.jpg" ...>
    
    Returns list of filenames found.
    """
    if pd.isna(markdown_text):
        return []
    
    # Pattern to match: <img src="imgs/FILENAME.jpg"
    pattern = r'<img\s+src="imgs/([^"]+)"'
    matches = re.findall(pattern, str(markdown_text))
    
    return matches

def merge_portrait_data(csv_file, portrait_dir, output_file, mode='all', separator='|'):
    """
    Merge portrait associations from JSON files into the CSV
    
    Args:
        csv_file: Path to CSV with names
        portrait_dir: Directory with portrait JSON files
        output_file: Output CSV path
        mode: How to handle multiple portraits ('all', 'first', 'last', 'primary')
        separator: Character to separate multiple filenames (for 'all' mode)
    """
    # Load the CSV
    df = pd.read_csv(csv_file)
    
    # Clean names in the dataframe
    print(f"Cleaning {len(df)} names...")
    df['name'] = df['name'].apply(clean_name)
    
    # Ensure portrait_filename column exists
    if 'portrait_filename' not in df.columns:
        df['portrait_filename'] = ''
    
    # Load all portrait association JSON files
    # Use defaultdict to collect all portraits per person
    portrait_data = defaultdict(list)
    
    portrait_files = list(Path(portrait_dir).glob("*_portrait_associations.json"))
    print(f"Found {len(portrait_files)} portrait association files")
    print(f"Portrait handling mode: {mode}")
    
    for json_file in portrait_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both old flat structure and new nested structure
        entries = []
        if 'biographical_entries' in data:
            # Old flat structure
            entries = data['biographical_entries']
        elif 'books' in data:
            # New nested structure: books -> book_id -> biographical_entries
            for book_id, book_data in data['books'].items():
                if 'biographical_entries' in book_data:
                    entries.extend(book_data['biographical_entries'])
        
        for entry in entries:
            person_name = entry.get('associated_person')
            filename = entry.get('filename')
            confidence = entry.get('confidence', 1.0)
            
            if person_name and filename:
                portrait_data[person_name].append({
                    'filename': filename,
                    'confidence': confidence
                })
    
    # Process portraits based on mode
    final_portraits = {}
    for person, portraits in portrait_data.items():
        if mode == 'all':
            # Remove duplicates while preserving order
            seen = set()
            unique_filenames = []
            for p in portraits:
                if p['filename'] not in seen:
                    seen.add(p['filename'])
                    unique_filenames.append(p['filename'])
            
            final_portraits[person] = separator.join(unique_filenames)
            if len(unique_filenames) > 1:
                print(f"  {person}: {len(unique_filenames)} unique portraits -> {final_portraits[person]}")
            else:
                print(f"  {person} -> {unique_filenames[0]}")
                
        elif mode == 'first':
            # Keep only the first portrait
            final_portraits[person] = portraits[0]['filename']
            if len(portraits) > 1:
                print(f"  {person}: {len(portraits)} portraits, keeping first -> {final_portraits[person]}")
            else:
                print(f"  {person} -> {final_portraits[person]}")
                
        elif mode == 'last':
            # Keep only the last portrait
            final_portraits[person] = portraits[-1]['filename']
            if len(portraits) > 1:
                print(f"  {person}: {len(portraits)} portraits, keeping last -> {final_portraits[person]}")
            else:
                print(f"  {person} -> {final_portraits[person]}")
                
        elif mode == 'primary':
            # Keep portrait with highest confidence
            best = max(portraits, key=lambda p: p['confidence'])
            final_portraits[person] = best['filename']
            if len(portraits) > 1:
                print(f"  {person}: {len(portraits)} portraits, keeping highest confidence ({best['confidence']:.2f}) -> {best['filename']}")
            else:
                print(f"  {person} -> {best['filename']}")
    
    # Update the DataFrame with fuzzy name matching
    updated_count = 0
    
    # Create a mapping of normalized portrait names to original names
    portrait_name_map = {}
    for person in final_portraits.keys():
        normalized = normalize_name_for_matching(person)
        portrait_name_map[normalized] = person
    
    for idx, row in df.iterrows():
        name = row['name']
        
        # Try exact match first
        if name in final_portraits:
            df.at[idx, 'portrait_filename'] = final_portraits[name]
            updated_count += 1
        else:
            # Try normalized match
            normalized_name = normalize_name_for_matching(name)
            if normalized_name in portrait_name_map:
                matched_person = portrait_name_map[normalized_name]
                df.at[idx, 'portrait_filename'] = final_portraits[matched_person]
                updated_count += 1
                print(f"  Fuzzy match: '{name}' matched to '{matched_person}' -> {final_portraits[matched_person]}")
    
    # Save the updated CSV
    df.to_csv(output_file, index=False)
    
    print(f"\nMerge complete!")
    print(f"Total names in CSV: {len(df)}")
    print(f"Unique persons with portraits: {len(final_portraits)}")
    print(f"Names updated with portraits: {updated_count}")
    print(f"Saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Merge portrait associations into CSV')
    parser.add_argument('csv_file', help='Path to CSV file with names')
    parser.add_argument('portrait_dir', help='Directory containing portrait association JSON files')
    parser.add_argument('output_file', help='Output CSV file path')
    parser.add_argument('--mode', default='all', 
                       choices=['all', 'first', 'last', 'primary'],
                       help='How to handle multiple portraits per person (default: all)')
    parser.add_argument('--separator', default='|',
                       help='Separator for multiple filenames in "all" mode (default: |)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    if not os.path.exists(args.portrait_dir):
        print(f"Error: Portrait directory not found: {args.portrait_dir}")
        sys.exit(1)
    
    merge_portrait_data(args.csv_file, args.portrait_dir, args.output_file, 
                       mode=args.mode, separator=args.separator)

if __name__ == "__main__":
    main()
