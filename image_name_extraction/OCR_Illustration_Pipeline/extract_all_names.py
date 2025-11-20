import os
import json
import pandas as pd
from pathlib import Path
import re
import argparse
import sys

def extract_names_to_dataframe(json_file_path):
    """
    Extract all names and their associated book-id from all_books_names.json
    """
    data = []
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
    
    # Iterate through all books in the JSON
    for book_id, book_data in content.get('books', {}).items():
        if 'biographical_entries' in book_data:
            for entry in book_data['biographical_entries']:
                # Handle both 'person_name' (old gemini format) and 'name' (portrait association format)
                person_name = entry.get('person_name') or entry.get('name', '')
                
                data.append({
                    'name': person_name,
                    'book_id': book_id,
                    'page_number': entry.get('page_number', ''),
                    'page_directory': entry.get('page_directory', ''),
                    'confidence': entry.get('confidence', 0)
                })
    
    df = pd.DataFrame(data)
    
    # Remove consecutive duplicate names within each book
    if not df.empty:
        df = df.sort_values(['book_id', 'page_number']).reset_index(drop=True)
        df = df[df['name'] != df['name'].shift()]
    
    return df

def chunk_markdown_by_names(markdown_file_path, names_list):
    """
    Chunk markdown content prioritizing complete biographical information
    Allows large chunks to preserve valuable content
    """
    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    chunks = []
    
    def find_name_in_text(name, text, start_from=0):
        """Find a name in text using multiple strategies"""
        search_text = text[start_from:]
        
        # Strategy 1: Exact match
        escaped_name = re.escape(name)
        match = re.search(escaped_name, search_text, re.IGNORECASE)
        if match:
            return start_from + match.start()
        
        # Strategy 2: Flexible surname matching
        name_parts = name.split(',')
        if len(name_parts) >= 2:
            surname = name_parts[0].strip()
            given_names = name_parts[1].strip()
            
            pattern = rf'\b{re.escape(surname)},\s+{re.escape(given_names.split()[0])}'
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                return start_from + match.start()
        
        # Strategy 3: Simplified match
        simplified_name = re.sub(r'[^\w\s]', '', name)
        pattern = re.escape(simplified_name)
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            return start_from + match.start()
        
        return None
    
    def find_complete_biographical_end(text, start_pos, next_name_pos=None, max_search=50000):
        """
        Find the complete end of a biographical entry, prioritizing completeness
        """
        search_end = min(len(text), start_pos + max_search)
        if next_name_pos:
            search_end = min(search_end, next_name_pos + 1000)  # Allow some overlap for safety
        
        search_section = text[start_pos:search_end]
        
        # Look for definitive biographical entry endings in order of confidence
        ending_patterns = [
            # Next biographical entry (strongest indicator)
            r'\n\s*[A-Z][A-Z\s]{3,},\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*,\s+[a-z]',
            
            # Figure marker followed by new entry
            r'\*\*\[FIGURE:[^\]]+\]\*\*\s*\n\s*[A-Z][A-Z\s]+,\s+[A-Z][a-z]+',
            
            # Reference entry (NAME, se OTHER)
            r'\n\s*[A-Z][A-Z\s]+,\s+[A-Z][a-z]+.*?,\s+se\s+[A-Z]',
            
            # Double line breaks followed by new biographical pattern
            r'\n\s*\n\s*[A-Z][A-Z\s]{3,},\s+[A-Z][a-z]+',
        ]
        
        best_end = None
        best_confidence = 0
        
        for confidence, pattern in enumerate(ending_patterns, 1):
            matches = list(re.finditer(pattern, search_section))
            if matches:
                # Take the first match as it represents the next entry
                match_pos = start_pos + matches[0].start()
                if confidence > best_confidence:
                    best_end = match_pos
                    best_confidence = confidence
                break  # Take the first strong pattern we find
        
        # If no strong pattern found, use next name position or extend reasonably
        if best_end is None:
            if next_name_pos:
                best_end = next_name_pos
            else:
                # For last entries or when next name not found, be generous
                # Look for any reasonable stopping point
                fallback_patterns = [
                    r'\n\s*\n\s*[A-Z]',  # Double break + capital
                    r'\*\*\[FIGURE:',     # Any figure marker
                    r'<!-- File:',        # File boundary
                ]
                
                for pattern in fallback_patterns:
                    match = re.search(pattern, search_section[2000:])  # Skip first 2K to avoid cutting short
                    if match:
                        best_end = start_pos + 2000 + match.start()
                        break
                
                # Absolute fallback - generous chunk size
                if best_end is None:
                    best_end = min(start_pos + 15000, len(text))  # 15KB max, but generous
        
        return best_end
    
    print(f"Comprehensive chunking {len(names_list)} names (prioritizing complete biographies)...")
    
    for i, name in enumerate(names_list):
        if i % 100 == 0:
            print(f"  Processing name {i+1}/{len(names_list)}: {name}")
        
        # Find current name position
        start_pos = find_name_in_text(name, markdown_content)
        
        if start_pos is None:
            print(f"  ✗ Could not find: {name}")
            chunks.append("")
            continue
        
        # Find next name to help determine boundaries
        next_name_pos = None
        if i + 1 < len(names_list):
            next_name = names_list[i + 1]
            next_name_pos = find_name_in_text(next_name, markdown_content, start_pos + len(name))
        
        # Find complete biographical end
        end_pos = find_complete_biographical_end(markdown_content, start_pos, next_name_pos)
        
        # Extract chunk
        chunk = markdown_content[start_pos:end_pos].strip()
        
        # Clean up chunk (remove excessive file markers but preserve content)
        chunk = re.sub(r'\n?<!-- File: [^>]+ -->\n?', '\n[PAGE_BREAK]\n', chunk)
        chunk = re.sub(r'\n+', '\n', chunk).strip()
        
        chunks.append(chunk)
        
        # Report on chunk characteristics (informational, not limiting)
        chunk_size = len(chunk)
        if chunk_size > 20000:
            print(f"  📖 Very comprehensive entry ({chunk_size} chars) for: {name}")
        elif chunk_size > 8000:
            print(f"  📄 Substantial entry ({chunk_size} chars) for: {name}")
        elif chunk_size < 500:
            print(f"  📝 Brief entry ({chunk_size} chars) for: {name}")
    
    # Statistics (informational)
    chunk_lengths = [len(c) for c in chunks]
    avg_length = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
    max_length = max(chunk_lengths) if chunk_lengths else 0
    substantial_chunks = len([c for c in chunk_lengths if c > 5000])
    comprehensive_chunks = len([c for c in chunk_lengths if c > 10000])
    
    print(f"\nComprehensive chunking completed!")
    print(f"  Average chunk size: {avg_length:.0f} chars")
    print(f"  Largest chunk size: {max_length} chars")
    print(f"  Substantial entries (>5K chars): {substantial_chunks}")
    print(f"  Comprehensive entries (>10K chars): {comprehensive_chunks}")
    print(f"  Brief entries (<500 chars): {len([c for c in chunk_lengths if c < 500])}")
    print(f"  Empty chunks: {chunk_lengths.count(0)}")
    
    return chunks

def add_chunks_to_dataframe(df, markdown_file_path):
    """
    Add markdown chunks to the dataframe using comprehensive chunking
    """
    if df.empty:
        df['markdown_chunk'] = []
        return df
    
    names_list = df['name'].tolist()
    chunks = chunk_markdown_by_names(markdown_file_path, names_list)
    
    # Add chunks as a new column
    df['markdown_chunk'] = chunks
    
    return df

def find_files_starting_with_figures(markdown_directory, portrait_pattern):
    """
    Scan all digibok*.md files and return those that START with the specified portrait pattern
    """
    markdown_dir = Path(markdown_directory)
    files_starting_with_figures = []
    
    print(f"Scanning directory: {markdown_dir}")
    print(f"Looking for files starting with pattern: {portrait_pattern}")
    
    # Find all digibok markdown files
    digibok_files = list(markdown_dir.glob("digibok*.md"))
    print(f"Found {len(digibok_files)} digibok*.md files")
    
    for md_file in digibok_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()  # Remove leading/trailing whitespace
            
            # Check if file STARTS with the specified portrait pattern
            if content.startswith(portrait_pattern):
                files_starting_with_figures.append({
                    'file_name': md_file.name,
                    'file_path': str(md_file),
                    'first_line': content.split('\n')[0][:100] + '...' if len(content.split('\n')[0]) > 100 else content.split('\n')[0],
                    'file_size': md_file.stat().st_size
                })
                
                print(f"✓ {md_file.name}: Starts with portrait pattern")
        
        except Exception as e:
            print(f"✗ Error reading {md_file.name}: {e}")
    
    return files_starting_with_figures

def save_figure_starting_files_info(files_starting_with_figures, output_path):
    """
    Save information about files starting with figures to CSV
    """
    if not files_starting_with_figures:
        print("No files starting with portrait pattern found.")
        return
    
    df = pd.DataFrame(files_starting_with_figures)
    df = df.sort_values('file_name')
    
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(files_starting_with_figures)} files starting with portraits to: {output_path}")
    
    # Print summary
    print(f"Total files starting with portrait pattern: {len(files_starting_with_figures)}")


def associate_portraits_with_names(df, files_starting_with_figures, portrait_pattern):
    """
    Associate portraits with names based on files that start with portrait pattern
    If a file starts with a portrait, the last name from the previous file gets that portrait
    """
    # Add portrait column to DataFrame
    df['portrait_filename'] = ''
    
    print("Associating portraits with names...")
    
    # Detect if we're using AzureOCR based on portrait pattern
    is_azure_ocr = portrait_pattern.startswith('**[FIGURE:')
    
    for file_info in files_starting_with_figures:
        file_name = file_info['file_name']
        first_line = file_info['first_line']
        

        # Extract the figure information based on the pattern
        if is_azure_ocr:
            # AzureOCR pattern: **[FIGURE: 1.2]**
            figure_match = re.search(r'\*\*\[FIGURE:\s*([^\]]+)\]\*\*', first_line)
            if figure_match:
                figure_id = figure_match.group(1).strip()
                
                # Extract base filename from the markdown file (e.g., digibok_2007031501007_0057)
                base_name_match = re.search(r'(digibok_\d+_\d+)', file_name)
                if base_name_match:
                    base_name = base_name_match.group(1)
                    portrait_filename = f"{base_name}_{figure_id}.png"
                else:
                    print(f"  ✗ Could not extract base name from: {file_name}")
                    continue
            else:
                print(f"  ✗ Could not extract figure ID from AzureOCR pattern: {first_line}")
                continue

        else:
            # Original patterns for MonkeyOCR and Dolphin
            if portrait_pattern.startswith('![Figure]'):
                # Standard ![Figure](figures/filename.png) pattern
                figure_match = re.search(r'!\[Figure\]\(figures/([^)]+)\)', first_line)
            elif portrait_pattern.startswith('![Figure('):
                # Alternative ![Figure(filename.png) pattern
                figure_match = re.search(r'!\[Figure\(([^)]+)\)', first_line)
            else:
                # Custom pattern - try to extract filename from parentheses
                figure_match = re.search(r'\(([^)]+)\)', first_line)
            
            if not figure_match:
                print(f"  ✗ Could not extract figure filename from: {first_line}")
                continue
                
            portrait_filename = figure_match.group(1)
        
        # Extract the base book_id from current file (e.g., digibok_2007031501007_0060.md)
        # We want to find the previous page: digibok_2007031501007_0059
        current_match = re.search(r'(digibok_\d+_)(\d+)\.md', file_name)
        if not current_match:
            print(f"  ✗ Could not extract book pattern from: {file_name}")
            continue
            
        book_prefix = current_match.group(1)  # "digibok_2007031501007_"
        current_page_num = int(current_match.group(2))  # 60
        previous_page_num = current_page_num - 1  # 59
        
        # Construct the previous book_id
        previous_book_id = f"{book_prefix}{previous_page_num:04d}"  # "digibok_2007031501007_0059"
        
        # Find all names with this book_id in the DataFrame
        previous_page_names = df[df['book_id'] == previous_book_id]
        
        if len(previous_page_names) > 0:
            # Get the last name from the previous page (highest index)
            last_name_idx = previous_page_names.index[-1]
            last_name = df.loc[last_name_idx, 'name']
            
            # Associate the portrait with this name
            df.loc[last_name_idx, 'portrait_filename'] = portrait_filename
            
            print(f"  ✓ Associated '{portrait_filename}' with '{last_name}' (book_id: {previous_book_id})")
        else:
            print(f"  ✗ No names found for book_id {previous_book_id} for figure {portrait_filename}")
    
    # Count how many portraits were associated
    portraits_associated = len(df[df['portrait_filename'] != ''])
    print(f"\nTotal portraits associated: {portraits_associated}")
    
    return df

def main():
    parser = argparse.ArgumentParser(description='Extract names from JSON files, add markdown chunks, and associate portraits')
    parser.add_argument('json_file_path', help='Path to the all_books_names.json file')
    parser.add_argument('markdown_file_path', help='Path to the concatenated markdown file')
    parser.add_argument('markdown_directory', help='Directory containing individual markdown files')
    parser.add_argument('output_directory', help='Directory to save output files')
    parser.add_argument('--portrait-pattern', default='![Figure]', 
                       help='Pattern that defines a portrait at the start of files (default: "![Figure]")')
    
    args = parser.parse_args()
    
    # Validate input paths
    if not os.path.exists(args.json_file_path):
        print(f"Error: JSON file not found: {args.json_file_path}")
        sys.exit(1)
    
    if not os.path.exists(args.markdown_file_path):
        print(f"Error: Markdown file not found: {args.markdown_file_path}")
        sys.exit(1)
    
    if not os.path.exists(args.markdown_directory):
        print(f"Error: Markdown directory not found: {args.markdown_directory}")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)
        print(f"Created output directory: {args.output_directory}")
    
    try:
        print(f"Processing JSON file: {args.json_file_path}")
        print(f"Using portrait pattern: '{args.portrait_pattern}'")
        
        # Extract names from the all_books_names.json file
        df = extract_names_to_dataframe(args.json_file_path)
        
        if df.empty:
            print("Warning: No names found in JSON file")
            sys.exit(1)
        
        print(f"Found {len(df)} names")
        
        # Add markdown chunks using comprehensive chunking
        print(f"Adding comprehensive markdown chunks from: {args.markdown_file_path}")
        df = add_chunks_to_dataframe(df, args.markdown_file_path)
        
        # Save to CSV with chunks
        output_csv = os.path.join(args.output_directory, 'extracted_all_names_with_chunks.csv')
        df.to_csv(output_csv, index=False)
        print(f"Saved names with chunks to: {output_csv}")
        
        # Find files that START with portrait pattern
        print("\n" + "="*60)
        print("SCANNING FOR FILES STARTING WITH PORTRAIT PATTERN")
        print("="*60)
        
        files_starting_with_figures = find_files_starting_with_figures(args.markdown_directory, args.portrait_pattern)
        
        # Save figure files info
        figure_starting_files_csv = os.path.join(args.output_directory, 'files_starting_with_portraits.csv')
        save_figure_starting_files_info(files_starting_with_figures, figure_starting_files_csv)
        
        # Associate portraits with names
        print("\n" + "="*60)
        print("ASSOCIATING PORTRAITS WITH NAMES")
        print("="*60)
        
        df_with_portraits = associate_portraits_with_names(df, files_starting_with_figures, args.portrait_pattern)
        
        # Save updated CSV with portrait associations
        output_csv_with_portraits = os.path.join(args.output_directory, 'extracted_all_names_with_chunks_and_portraits.csv')
        df_with_portraits.to_csv(output_csv_with_portraits, index=False)
        
        print(f"\nSaved DataFrame with portrait associations to: {output_csv_with_portraits}")
        
        # Display sample of names with portraits
        names_with_portraits = df_with_portraits[df_with_portraits['portrait_filename'] != '']
        if len(names_with_portraits) > 0:
            print(f"\nSample names with portraits:")
            for i, (idx, row) in enumerate(names_with_portraits.head(5).iterrows()):
                print(f"  {i+1}. {row['name']} -> {row['portrait_filename']}")
        else:
            print("No portrait associations found.")
        
        # Display summary statistics
        print(f"\nSummary:")
        print(f"  Total names: {len(df_with_portraits)}")
        print(f"  Names with portraits: {len(names_with_portraits)}")
        if len(df_with_portraits) > 0:
            print(f"  Portrait association rate: {len(names_with_portraits)/len(df_with_portraits)*100:.1f}%")
        
        print(f"\nProcessing complete! Files saved to: {args.output_directory}")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
