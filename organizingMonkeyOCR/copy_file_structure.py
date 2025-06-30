#!/usr/bin/env python3
"""
File Structure Copy Script

This script copies files from an existing file structure to a new file structure
with customizable mapping rules and filtering options.
"""

import os
import shutil
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable
import fnmatch
import logging


class FileStructureCopier:
    """
    A flexible file structure copier with customizable mapping rules.
    """
    
    def __init__(self, source_root: str, target_root: str, 
                 gitignore_path: Optional[str] = None,
                 dry_run: bool = False):
        """
        Initialize the file structure copier.
        
        Args:
            source_root: Root directory of source file structure
            target_root: Root directory of target file structure
            gitignore_path: Path to .gitignore file for exclusion patterns
            dry_run: If True, only show what would be copied without actually copying
        """
        self.source_root = Path(source_root).resolve()
        self.target_root = Path(target_root).resolve()
        self.dry_run = dry_run
        self.gitignore_patterns = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Load gitignore patterns if provided
        if gitignore_path and os.path.exists(gitignore_path):
            self._load_gitignore_patterns(gitignore_path)
        
        # Statistics
        self.stats = {
            'files_copied': 0,
            'files_skipped': 0,
            'dirs_created': 0,
            'errors': []
        }
    
    def _load_gitignore_patterns(self, gitignore_path: str):
        """Load patterns from .gitignore file."""
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Convert gitignore patterns to fnmatch patterns
                        if line.endswith('/'):
                            # Directory pattern
                            self.gitignore_patterns.append(line[:-1])
                        else:
                            # File pattern
                            self.gitignore_patterns.append(line)
            
            self.logger.info(f"Loaded {len(self.gitignore_patterns)} patterns from .gitignore")
        except Exception as e:
            self.logger.warning(f"Could not load .gitignore: {e}")
    
    def _should_exclude(self, file_path: Path, relative_path: str) -> bool:
        """Check if file should be excluded based on gitignore patterns."""
        for pattern in self.gitignore_patterns:
            # Check if pattern matches the relative path or filename
            if fnmatch.fnmatch(relative_path, pattern) or \
               fnmatch.fnmatch(file_path.name, pattern) or \
               fnmatch.fnmatch(str(file_path), f"*/{pattern}") or \
               fnmatch.fnmatch(str(file_path), f"*/{pattern}/*"):
                return True
        return False
    
    def copy_with_simple_mapping(self, structure_mapping: Dict[str, str],
                                file_extensions: Optional[List[str]] = None):
        """
        Copy files using simple directory mapping.
        
        Args:
            structure_mapping: Dict mapping source subdirs to target subdirs
                              e.g., {'magic_pdf': 'src', 'projects': 'apps'}
            file_extensions: List of file extensions to copy (e.g., ['.py', '.yaml'])
                           If None, copies all files
        """
        self.logger.info("Starting file copy with simple mapping")
        self.logger.info(f"Source: {self.source_root}")
        self.logger.info(f"Target: {self.target_root}")
        
        if self.dry_run:
            self.logger.info("DRY RUN MODE - No files will actually be copied")
        
        for source_subdir, target_subdir in structure_mapping.items():
            source_path = self.source_root / source_subdir
            target_path = self.target_root / target_subdir
            
            if not source_path.exists():
                self.logger.warning(f"Source directory does not exist: {source_path}")
                continue
            
            self._copy_directory(source_path, target_path, file_extensions)
        
        self._print_statistics()
    
    def copy_with_custom_mapping(self, mapping_function: Callable[[Path], Optional[Path]],
                                file_extensions: Optional[List[str]] = None):
        """
        Copy files using custom mapping function.
        
        Args:
            mapping_function: Function that takes source path and returns target path
                            Return None to skip the file
            file_extensions: List of file extensions to copy
        """
        self.logger.info("Starting file copy with custom mapping")
        
        if self.dry_run:
            self.logger.info("DRY RUN MODE - No files will actually be copied")
        
        for root, dirs, files in os.walk(self.source_root):
            root_path = Path(root)
            
            # Filter files by extension if specified
            if file_extensions:
                files = [f for f in files if any(f.endswith(ext) for ext in file_extensions)]
            
            for file in files:
                source_file = root_path / file
                relative_path = source_file.relative_to(self.source_root)
                
                # Check if file should be excluded
                if self._should_exclude(source_file, str(relative_path)):
                    self.stats['files_skipped'] += 1
                    continue
                
                # Apply custom mapping
                target_file = mapping_function(source_file)
                if target_file is None:
                    self.stats['files_skipped'] += 1
                    continue
                
                self._copy_file(source_file, target_file)
        
        self._print_statistics()
    
    def _copy_directory(self, source_dir: Path, target_dir: Path,
                       file_extensions: Optional[List[str]] = None):
        """Recursively copy directory contents."""
        for root, dirs, files in os.walk(source_dir):
            root_path = Path(root)
            relative_path = root_path.relative_to(source_dir)
            target_subdir = target_dir / relative_path
            
            # Filter files by extension if specified
            if file_extensions:
                files = [f for f in files if any(f.endswith(ext) for ext in file_extensions)]
            
            for file in files:
                source_file = root_path / file
                target_file = target_subdir / file
                
                # Check relative path from source root for gitignore patterns
                relative_from_root = source_file.relative_to(self.source_root)
                
                # Check if file should be excluded
                if self._should_exclude(source_file, str(relative_from_root)):
                    self.stats['files_skipped'] += 1
                    continue
                
                self._copy_file(source_file, target_file)
    
    def _copy_file(self, source_file: Path, target_file: Path):
        """Copy a single file."""
        try:
            if not self.dry_run:
                # Create target directory if it doesn't exist
                target_file.parent.mkdir(parents=True, exist_ok=True)
                if not target_file.parent.exists():
                    self.stats['dirs_created'] += 1
                
                # Copy the file
                shutil.copy2(source_file, target_file)
            
            self.logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Copied: {source_file} -> {target_file}")
            self.stats['files_copied'] += 1
            
        except Exception as e:
            error_msg = f"Error copying {source_file} to {target_file}: {e}"
            self.logger.error(error_msg)
            self.stats['errors'].append(error_msg)
    
    def _print_statistics(self):
        """Print copy statistics."""
        self.logger.info("=" * 50)
        self.logger.info("COPY STATISTICS")
        self.logger.info("=" * 50)
        self.logger.info(f"Files copied: {self.stats['files_copied']}")
        self.logger.info(f"Files skipped: {self.stats['files_skipped']}")
        self.logger.info(f"Directories created: {self.stats['dirs_created']}")
        self.logger.info(f"Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            self.logger.info("\nErrors encountered:")
            for error in self.stats['errors']:
                self.logger.error(f"  - {error}")
    
    def copy_md_and_figures_to_output(self, output_subdir: str = "output"):
        """
        Specialized method to copy *.md files from subfolders and all files 
        from 'images' subfolders to a single output directory.
        
        This method:
        1. Finds all *.md files in immediate subfolders and copies them to output
        2. Finds all files in 'images' subfolders and copies them to output/figures
        
        Args:
            output_subdir: Name of the output subdirectory (default: "output")
        """
        self.logger.info("Starting specialized copy: *.md files and images to output")
        self.logger.info(f"Source: {self.source_root}")
        self.logger.info(f"Target output: {self.source_root / output_subdir}")
        
        if self.dry_run:
            self.logger.info("DRY RUN MODE - No files will actually be copied")
        
        output_path = self.source_root / output_subdir
        
        # Walk through all subdirectories
        for item in self.source_root.iterdir():
            if item.is_dir() and item.name != output_subdir:  # Skip the output dir itself
                self.logger.info(f"Processing subfolder: {item.name}")
                
                # Copy *.md files from this subfolder (not recursive)
                for md_file in item.glob("*.md"):
                    if not self._should_exclude(md_file, str(md_file.relative_to(self.source_root))):
                        target_file = output_path / md_file.name
                        self._copy_file(md_file, target_file)
                    else:
                        self.stats['files_skipped'] += 1
                
                # Look for 'images' subfolder and copy all its contents
                images_path = item / "images"
                self.logger.info(f"Checking for images folder: {images_path}")
                
                if images_path.exists():
                    if images_path.is_dir():
                        self.logger.info(f"Found images folder in: {item.name}")
                        
                        # Create output/figures directory
                        output_figures_path = output_path / "figures"
                        
                        # Copy all files from images folder (recursive)
                        for root, dirs, files in os.walk(images_path):
                            root_path = Path(root)
                            
                            if not files:
                                self.logger.info(f"No files found in images directory: {root_path}")
                                continue
                            
                            self.logger.info(f"Processing {len(files)} files from: {root_path}")
                            
                            for file in files:
                                source_file = root_path / file
                                relative_path = source_file.relative_to(self.source_root)
                                
                                # Check if file should be excluded
                                if self._should_exclude(source_file, str(relative_path)):
                                    self.logger.info(f"Skipping excluded file: {source_file}")
                                    self.stats['files_skipped'] += 1
                                    continue
                                
                                # Preserve the relative structure within images
                                relative_to_images = source_file.relative_to(images_path)
                                target_file = output_figures_path / relative_to_images
                                
                                self._copy_file(source_file, target_file)
                    else:
                        self.logger.info(f"Found 'images' but it's not a directory: {images_path}")
                else:
                    self.logger.info(f"No images folder found in: {item.name}")
        
        self._print_statistics()

def example_structure_mappings():
    """Example structure mappings for common use cases."""
    
    # Example 1: Reorganize a Python project
    python_project_mapping = {
        'magic_pdf': 'src/core',
        'projects/web': 'src/web',
        'projects/web_demo': 'src/demo',
        'tests': 'tests',
        'docs': 'documentation'
    }
    
    # Example 2: Extract specific components
    component_mapping = {
        'magic_pdf/model': 'models',
        'magic_pdf/data': 'data_processing',
        'magic_pdf/utils': 'utilities'
    }
    
    return {
        'python_project': python_project_mapping,
        'components': component_mapping
    }


def custom_mapping_examples():
    """Example custom mapping functions."""
    
    def flatten_structure(source_path: Path) -> Optional[Path]:
        """Flatten all files into a single directory with prefixed names."""
        base_target = Path("flattened_output")
        relative_path = source_path.relative_to(source_path.parts[0])
        
        # Create flattened filename
        flat_name = str(relative_path).replace(os.sep, '_')
        return base_target / flat_name
    
    def organize_by_extension(source_path: Path) -> Optional[Path]:
        """Organize files by their extensions."""
        base_target = Path("organized_output")
        extension = source_path.suffix.lower()
        
        if extension == '.py':
            return base_target / 'python' / source_path.name
        elif extension in ['.yaml', '.yml']:
            return base_target / 'config' / source_path.name
        elif extension in ['.md', '.txt']:
            return base_target / 'docs' / source_path.name
        elif extension in ['.jpg', '.png', '.jpeg']:
            return base_target / 'images' / source_path.name
        else:
            return base_target / 'other' / source_path.name
    
    def selective_copy(source_path: Path) -> Optional[Path]:
        """Only copy specific types of files with custom organization."""
        base_target = Path("selective_output")
        
        # Only copy Python files and config files
        if source_path.suffix not in ['.py', '.yaml', '.yml', '.json']:
            return None
        
        # Preserve relative structure but under new root
        relative_path = source_path.relative_to(source_path.parts[0])
        return base_target / relative_path
    
    return {
        'flatten': flatten_structure,
        'by_extension': organize_by_extension,
        'selective': selective_copy
    }


def main():
    parser = argparse.ArgumentParser(
        description="Copy files from existing structure to new structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple mapping with Python files only
  python copy_file_structure.py /source /target --mapping-file mapping.json --extensions .py .yaml
  
  # Custom mapping with dry run
  python copy_file_structure.py /source /target --custom-mapping flatten --dry-run
  
  # Copy specific directories
  python copy_file_structure.py . ./reorganized --simple-mapping "magic_pdf:src,projects:apps"
  
  # Copy *.md files and figures to output folder (your use case)
  python copy_file_structure.py "D:\\data\\HCNC\\norway\\biographies\\storage\\MonkeyOCR" . --md-and-figures --dry-run
        """
    )
    
    parser.add_argument("source", help="Source directory path")
    parser.add_argument("target", help="Target directory path")
    
    parser.add_argument("--gitignore", help="Path to .gitignore file for exclusion patterns")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without actually copying")
    
    # Mapping options
    mapping_group = parser.add_mutually_exclusive_group(required=True)
    mapping_group.add_argument("--simple-mapping", help="Simple mapping as 'source1:target1,source2:target2'")
    mapping_group.add_argument("--mapping-file", help="JSON file with structure mapping")
    mapping_group.add_argument("--custom-mapping", choices=['flatten', 'by_extension', 'selective'], 
                              help="Use predefined custom mapping function")
    mapping_group.add_argument("--md-and-figures", action="store_true",
                              help="Copy *.md files from subfolders and all files from 'figures' subfolders to output")
    
    parser.add_argument("--extensions", nargs="*", help="File extensions to copy (e.g., .py .yaml)")
    
    args = parser.parse_args()
    
    # Initialize copier
    copier = FileStructureCopier(
        source_root=args.source,
        target_root=args.target,
        gitignore_path=args.gitignore or os.path.join(args.source, '.gitignore'),
        dry_run=args.dry_run
    )
    
    try:
        if args.simple_mapping:
            # Parse simple mapping
            mapping_dict = {}
            for pair in args.simple_mapping.split(','):
                source_dir, target_dir = pair.split(':')
                mapping_dict[source_dir.strip()] = target_dir.strip()
            
            copier.copy_with_simple_mapping(mapping_dict, args.extensions)
            
        elif args.mapping_file:
            # Load mapping from JSON file
            with open(args.mapping_file, 'r') as f:
                mapping_dict = json.load(f)
            
            copier.copy_with_simple_mapping(mapping_dict, args.extensions)
            
        elif args.custom_mapping:
            # Use custom mapping function
            custom_mappings = custom_mapping_examples()
            mapping_func = custom_mappings[args.custom_mapping]
            
            copier.copy_with_custom_mapping(mapping_func, args.extensions)
            
        elif args.md_and_figures:
            # Use specialized method for markdown and figures
            copier.copy_md_and_figures_to_output()
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())