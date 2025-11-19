import os
import json
import pandas as pd
from pathlib import Path
import re
import argparse
import sys

def extract_names_to_dataframe(json_directory):
    json_dir = Path(json_directory)
    data = []
    
    # Look for all JSON files in the directory
    # The pattern might need to be adjusted if the naming convention changes
    # Original: digibok_2007031501007_*_portrait_associations.json
    # We'll make it more generic: *_portrait_associations.json
    for json_file in json_dir.glob("*_portrait_associations.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # Handle both old and new data structures
        entries = []
        
        # Check for new structure with "biographical_entries"
        if 'biographical_entries' in content:
            entries = content['biographical_entries']
        # Check for old structure with "associations"
        elif 'associations' in content:
            entries = content['associations']
        else:
            # If neither key exists, skip this file
            print(f"Warning: No 'biographical_entries' or 'associations' found in {json_file}")
            continue
        
        for association in entries:
            if association.get('associated_person'):
                # Handle different key variations for image filename
                image_filename = ''
                if 'image_filename' in association:
                    image_filename = association['image_filename']
                elif 'filename' in association:
                    image_filename = association['filename']
                
                # Handle different key variations for page
                page = ''
                if 'image_page' in association:
                    page = association['image_page']
                elif 'page' in association:
                    page = association['page']
                elif 'book_id' in association:
                    # Extract page from book_id if available (e.g., "digibok_2007031501007_0057" -> "0057")
                    book_id_parts = association['book_id'].split('_')
                    if len(book_id_parts) >= 3:
                        page = book_id_parts[-1]
                
                # Handle confidence (should be consistent)
                confidence = association.get('confidence', 0)
                
                # Handle book_id - check both association level and content level
                book_id = association.get('book_id', '') or content.get('book_id', '')
                
                data.append({
                    'name': association['associated_person'],
                    'image_filename': image_filename,
                    'page': page,
                    'confidence': confidence,
                    'book_id': book_id
                })
    
    df = pd.DataFrame(data)
    
    # Remove consecutive duplicate names
    if not df.empty:
        df = df[df['name'] != df['name'].shift()]  

    return df  
    

def chunk_markdown_by_names(markdown_file_path, names_list):
    """
    Chunk markdown content by names, where each chunk starts with name[i] 
    and ends before name[i+1]
    """
    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    chunks = []
    
    for i, name in enumerate(names_list):
        # Find the start position of current name
        # Use regex to find the name pattern (case insensitive)
        name_pattern = re.escape(name)
        start_match = re.search(name_pattern, markdown_content, re.IGNORECASE)
        
        if not start_match:
            # If exact match not found, try without special characters
            simplified_name = re.sub(r'[^\w\s]', '', name)
            start_match = re.search(re.escape(simplified_name), markdown_content, re.IGNORECASE)
        
        if start_match:
            start_pos = start_match.start()
            
            # Find the end position (start of next name)
            if i + 1 < len(names_list):
                next_name = names_list[i + 1]
                next_name_pattern = re.escape(next_name)
                end_match = re.search(next_name_pattern, markdown_content[start_pos + len(name):], re.IGNORECASE)
                
                if not end_match:
                    # Try simplified version of next name
                    simplified_next_name = re.sub(r'[^\w\s]', '', next_name)
                    end_match = re.search(re.escape(simplified_next_name), markdown_content[start_pos + len(name):], re.IGNORECASE)
                
                if end_match:
                    end_pos = start_pos + len(name) + end_match.start()
                else:
                    end_pos = len(markdown_content)  # If next name not found, go to end
            else:
                end_pos = len(markdown_content)  # Last name, go to end of file
            
            chunk = markdown_content[start_pos:end_pos].strip()
            chunks.append(chunk)
        else:
            chunks.append("")  # Empty chunk if name not found
    
    return chunks

def add_chunks_to_dataframe(df, markdown_file_path):
    """
    Add markdown chunks to the dataframe
    """
    if df.empty:
        df['markdown_chunk'] = []
        return df
    
    names_list = df['name'].tolist()
    chunks = chunk_markdown_by_names(markdown_file_path, names_list)
    
    # Add chunks as a new column
    df['markdown_chunk'] = chunks
    
    return df

def main():
    parser = argparse.ArgumentParser(description='Extract portrait names from JSON files and add markdown chunks')
    parser.add_argument('json_directory', help='Directory containing JSON files with portrait associations')
    parser.add_argument('markdown_file_path', help='Path to the markdown file to chunk')
    parser.add_argument('output_csv', help='Output CSV file path')
    
    args = parser.parse_args()
    
    # Validate input paths
    if not os.path.exists(args.json_directory):
        print(f"Error: JSON directory not found: {args.json_directory}")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    try:
        print(f"Processing JSON files from: {args.json_directory}")
        
        # Extract names
        df = extract_names_to_dataframe(args.json_directory)
        
        if df.empty:
            print("Warning: No portrait associations found in JSON files")
            # Create empty CSV with headers
            df = pd.DataFrame(columns=['name', 'image_filename', 'page', 'confidence', 'book_id', 'markdown_chunk'])
            df.to_csv(args.output_csv, index=False)
            print(f"Empty CSV saved to: {args.output_csv}")
            return
        
        print(f"Found {len(df)} portrait names")
        
        # Add markdown chunks
        print(f"Adding markdown chunks from: {args.markdown_file_path}")
        df = add_chunks_to_dataframe(df, args.markdown_file_path)
        
        # Save to CSV
        df.to_csv(args.output_csv, index=False)
        
        print(f"\nProcessing complete!")
        print(f"Processed {len(df)} names with chunks")
        print(f"Saved to: {args.output_csv}")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
