import os
import json
import pandas as pd
import argparse
import sys
from pathlib import Path

def merge_portrait_data(csv_file, portrait_dir, output_file):
    """
    Merge portrait associations from JSON files into the CSV
    """
    # Load the CSV
    df = pd.read_csv(csv_file)
    
    # Ensure portrait_filename column exists
    if 'portrait_filename' not in df.columns:
        df['portrait_filename'] = ''
    
    # Load all portrait association JSON files
    portrait_data = {}
    
    portrait_files = list(Path(portrait_dir).glob("*_portrait_associations.json"))
    print(f"Found {len(portrait_files)} portrait association files")
    
    for json_file in portrait_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if 'biographical_entries' in data:
            for entry in data['biographical_entries']:
                person_name = entry.get('associated_person')
                filename = entry.get('filename')
                
                if person_name and filename:
                    portrait_data[person_name] = filename
                    print(f"  Mapping: {person_name} -> {filename}")
    
    # Update the DataFrame
    updated_count = 0
    for idx, row in df.iterrows():
        name = row['name']
        if name in portrait_data:
            df.at[idx, 'portrait_filename'] = portrait_data[name]
            updated_count += 1
            print(f"✓ Updated portrait for: {name}")
    
    # Save the updated CSV
    df.to_csv(output_file, index=False)
    
    print(f"\nMerge complete!")
    print(f"Total names in CSV: {len(df)}")
    print(f"Portraits found: {len(portrait_data)}")
    print(f"Names updated with portraits: {updated_count}")
    print(f"Saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Merge portrait associations into CSV')
    parser.add_argument('csv_file', help='Path to CSV file with names')
    parser.add_argument('portrait_dir', help='Directory containing portrait association JSON files')
    parser.add_argument('output_file', help='Output CSV file path')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    if not os.path.exists(args.portrait_dir):
        print(f"Error: Portrait directory not found: {args.portrait_dir}")
        sys.exit(1)
    
    merge_portrait_data(args.csv_file, args.portrait_dir, args.output_file)

if __name__ == "__main__":
    main()
