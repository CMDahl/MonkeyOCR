#!/usr/bin/env python3
"""
Concatenate all digibok_*.md files in a directory into a single file
"""

import os
import re
import argparse
import sys
from pathlib import Path

def concatenate_md_files_custom(input_directory, output_file_path, file_separator=False, spacing=2):
    """
    Concatenate all digibok_*.md files in a directory into a single file
    
    Args:
        input_directory (str): Directory containing digibok_*.md files
        output_file_path (str): Path for the output concatenated file
    
    Returns:
        tuple: (number of files concatenated, list of small filenames)
    """
    input_dir = Path(input_directory)
    
    # Find all digibok_*.md files and sort them numerically
    digibok_files = list(input_dir.glob("digibok_*.md"))
    
    if not digibok_files:
        print(f"No digibok_*.md files found in {input_directory}")
        return 0, []
    
    # Sort files numerically by extracting the number from filename
    def extract_number(file_path):
        match = re.search(r'digibok_.*?(\d+)\.md', file_path.name)
        return int(match.group(1)) if match else 0
    
    digibok_files.sort(key=extract_number)
    
    print(f"Found {len(digibok_files)} digibok_*.md files")
    print(f"Concatenating files from {digibok_files[0].name} to {digibok_files[-1].name}")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Track small files
    small_files = []
    
    # Concatenate all files
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        for i, md_file in enumerate(digibok_files):
            try:
                with open(md_file, 'r', encoding='utf-8') as input_file:
                    content = input_file.read()
                
                # Check file size and track small files
                file_size = len(content.encode('utf-8'))
                if file_size < 200:
                    small_files.append(md_file.name)
                
                # Add spacing between files
                if i > 0:
                    output_file.write('\n' * spacing)
                
                # Add file marker comment if requested
                if file_separator:
                    output_file.write(f'<!-- File: {md_file.name} -->\n')
                
                output_file.write(content)
                
                print(f"Added {md_file.name} ({len(content):,} characters, {file_size} bytes)")
                
            except Exception as e:
                print(f"Error reading {md_file.name}: {e}")
                continue
    
    # Print small files summary
    if small_files:
        print(f"\n⚠️  Files with size less than 200 bytes ({len(small_files)} files):")
        for filename in small_files:
            print(f"  {filename}")
    else:
        print(f"\n✅ No files found with size less than 200 bytes")
    
    print(f"\nConcatenation complete!")
    print(f"Output saved to: {output_file_path}")
    
    return len(digibok_files), small_files

def main():
    parser = argparse.ArgumentParser(
        description='Concatenate all digibok_*.md files in a directory into a single file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python concatenate_all_md_files.py "D:/data/markdown" "D:/data/concatenated_all.md"
  python concatenate_all_md_files.py ./markdown ./output/combined.md
  python concatenate_all_md_files.py "C:/books/md_files" "C:/books/all_pages.md" --file-separator
        """
    )
    
    parser.add_argument('input_directory', 
                       help='Directory containing digibok_*.md files')
    parser.add_argument('output_file', 
                       help='Output file path for concatenated content')
    parser.add_argument('--file-separator', action='store_true',
                       help='Add file name comments as separators between files')
    parser.add_argument('--spacing', type=int, default=2,
                       help='Number of newlines between files (default: 2)')
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.exists(args.input_directory):
        print(f"Error: Input directory not found: {args.input_directory}")
        sys.exit(1)
    
    if not os.path.isdir(args.input_directory):
        print(f"Error: Input path is not a directory: {args.input_directory}")
        sys.exit(1)
    
    try:
        print(f"Input directory: {args.input_directory}")
        print(f"Output file: {args.output_file}")
        
        if args.file_separator:
            print("File separators: Enabled")
        
        print(f"Spacing between files: {args.spacing} newlines")
        print("-" * 50)
        
        # Run concatenation with custom spacing
        files_processed,small_files = concatenate_md_files_custom(
            args.input_directory, 
            args.output_file,
            file_separator=args.file_separator,
            spacing=args.spacing
        )
        
        if files_processed > 0:
            print(f"\n✅ Successfully concatenated {files_processed} files")
            print(f"📄 Output saved to: {args.output_file}")
            
            # Show file size
            if os.path.exists(args.output_file):
                file_size = os.path.getsize(args.output_file)
                print(f"📊 Output file size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        else:
            print("❌ No files were processed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error during concatenation: {e}")
        sys.exit(1)

    print("this is a list of small files that were found and where the conversion from json to markdown failed:")


if __name__ == "__main__":
    main()

# Basic usage
#python concatenate_all_md_files.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007\" "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007\concatenated_all.md"

# With file separators
#python concatenate_all_md_files.py "D:/data/markdown" "D:/data/concatenated_all.md" --file-separator

# Custom spacing (3 newlines between files)
#python concatenate_all_md_files.py "D:/data/markdown" "D:/data/concatenated_all.md" --spacing 3

# Full example with all options
#python concatenate_all_md_files.py "./markdown_files" "./output/combined.md" --file-separator --spacing 1

# Get help
#python concatenate_all_md_files.py --help    

#python concatenate_all_md_files.py #"d:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json" #"d:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json\concatenate#d_all.md" --file-separator --spacing 2