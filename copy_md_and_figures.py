#!/usr/bin/env python3
"""
Script to copy *.md files and figures from MonkeyOCR subfolders to output directory.

This script specifically handles the use case of:
1. Copying all *.md files from immediate subfolders to an output directory
2. Copying all files from 'figures' subfolders to the same output directory

Usage:
    python copy_md_and_figures.py [source_path] [--dry-run] [--output-dir output]
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from copy_file_structure import FileStructureCopier


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Copy *.md files and figures from subfolders to output directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  # For your specific use case:
  python copy_md_and_figures.py "D:\\data\\HCNC\\norway\\biographies\\storage\\MonkeyOCR" --dry-run
  
  # Actually perform the copy:
  python copy_md_and_figures.py "D:\\data\\HCNC\\norway\\biographies\\storage\\MonkeyOCR"
        """
    )
    
    parser.add_argument("source_path", 
                       help="Path to the MonkeyOCR directory containing subfolders with *.md files and figures")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be copied without actually copying")
    parser.add_argument("--output-dir", default="digibok_2007031501007",
                       help="Name of the output directory (default: 'digibok_2007031501007')")
    parser.add_argument("--gitignore", 
                       help="Path to .gitignore file for exclusion patterns")
    parser.add_argument("--no-gitignore", action="store_true",
                       help="Disable gitignore pattern matching")
    
    args = parser.parse_args()
    
    # Validate source path
    source_path = Path(args.source_path)
    if not source_path.exists():
        print(f"Error: Source path does not exist: {source_path}")
        return 1
    
    if not source_path.is_dir():
        print(f"Error: Source path is not a directory: {source_path}")
        return 1
    
    print(f"Source directory: {source_path}")
    print(f"Output directory: {source_path / args.output_dir}")
    
    if args.dry_run:
        print("DRY RUN MODE - No files will actually be copied")
    
    print("\nInitializing file copier...")
    
    # Initialize the copier
    copier = FileStructureCopier(
        source_root=str(source_path),
        target_root=str(source_path),  # Target is same as source since we're creating a subfolder
        gitignore_path=None if args.no_gitignore else args.gitignore,
        dry_run=args.dry_run
    )
    
    try:
        # Use the specialized method
        copier.copy_md_and_figures_to_output(args.output_dir)
        
        print("\nOperation completed successfully!")
        
        if not args.dry_run:
            output_path = source_path / args.output_dir
            if output_path.exists():
                file_count = len(list(output_path.glob("*")))
                print(f"Output directory contains {file_count} files: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
