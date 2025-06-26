#!/usr/bin/env python3
"""
Example script for copying *.md files and figures to output directory.

This script demonstrates how to use the FileStructureCopier to:
1. Copy all *.md files from subfolders to an output directory
2. Copy all files from 'figures' subfolders to output/figures directory

Usage:
    python copy_md_and_figures_example.py
"""

from copy_file_structure import FileStructureCopier

def main():
    # Your specific paths
    source_path = r"D:\data\HCNC\norway\biographies\storage\MonkeyOCR"
    
    # Initialize the copier (target_root not used for this method)
    copier = FileStructureCopier(
        source_root=source_path,
        target_root=source_path,  # Not used for md_and_figures method
        dry_run=False  # Set to True to see what would be copied without actually copying
    )
    
    # Copy *.md files and figures to output directory
    # This will create:
    # - D:\data\HCNC\norway\biographies\storage\MonkeyOCR\output\*.md
    # - D:\data\HCNC\norway\biographies\storage\MonkeyOCR\output\figures\*
    copier.copy_md_and_figures_to_output()
    
    print("\nCopy operation completed!")
    print(f"Check the output directory: {source_path}\\output")
    print("- *.md files are in the output folder")
    print("- Figure files are in the output\\figures subfolder")

if __name__ == "__main__":
    main()
