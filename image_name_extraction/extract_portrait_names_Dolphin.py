import os
import json
import pandas as pd
from pathlib import Path
import re

def extract_names_to_dataframe(json_directory):
    json_dir = Path(json_directory)
    data = []
    
    for json_file in json_dir.glob("digibok_2007031501007*_portrait_associations.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        for association in content.get('associations', []):
            if association.get('associated_person'):
                data.append({
                    'name': association['associated_person'],
                    'image_filename': association.get('image_filename', ''),
                    'page': association.get('image_page', ''),
                    'confidence': association.get('confidence', 0),
                    'book_id': content.get('book_id', '')
                })
    
    df = pd.DataFrame(data)
    
    # Remove consecutive duplicate names
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
    names_list = df['name'].tolist()
    chunks = chunk_markdown_by_names(markdown_file_path, names_list)
    
    # Add chunks as a new column
    df['markdown_chunk'] = chunks
    
    return df

# Usage
json_directory = r"D:\data\HCNC\norway\biographies\storage\Dolphin\output"
markdown_file_path = r"D:\data\HCNC\norway\biographies\storage\Dolphin\markdown\concatenated_all.md"

# Extract names
df = extract_names_to_dataframe(json_directory)

# Add markdown chunks
df = add_chunks_to_dataframe(df, markdown_file_path)
df.head()
# Save to CSV with chunks
output_csv = os.path.join(json_directory, 'extracted_portrait_names_Dolphin_with_chunks_single_page.csv')
df.to_csv(output_csv, index=False)

print(f"Processed {len(df)} names with chunks")
print(f"Saved to: {output_csv}")

# Display sample of results
print("\nSample of first few rows:")
for i in range(min(3, len(df))):
    print(f"\nName: {df.iloc[i]['name']}")
    print(f"Chunk length: {len(df.iloc[i]['markdown_chunk'])} characters")
    print(f"Chunk preview: {df.iloc[i]['markdown_chunk'][:200]}...")