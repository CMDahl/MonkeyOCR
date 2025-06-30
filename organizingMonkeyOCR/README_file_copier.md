# File Structure Copy Script

A flexible Python script for copying files from one directory structure to another with customizable mapping rules.

## Features

- **Flexible Mapping**: Define custom source-to-target directory mappings using JSON configuration
- **Gitignore Support**: Automatically exclude files based on .gitignore patterns
- **Dry Run Mode**: Preview what will be copied before actually copying
- **Specialized Copy Modes**: Built-in support for common copy patterns
- **File Filtering**: Include/exclude files based on patterns
- **Detailed Logging**: Track what files are copied, skipped, or failed

## Installation

No additional dependencies required beyond Python 3.6+. Uses only standard library modules.

## Basic Usage

```bash
# Basic copy with mapping configuration
python copy_file_structure.py source_dir target_dir --mapping python_project_reorganization

# Dry run to see what would be copied
python copy_file_structure.py source_dir target_dir --mapping python_project_reorganization --dry-run

# Simple copy (copy everything)
python copy_file_structure.py source_dir target_dir --mapping simple_copy
```

## Configuration

Edit `structure_mappings.json` to define your mapping rules:

```json
{
  "your_mapping_name": {
    "source_folder": "target_folder",
    "another_source": "another_target"
  }
}
```

## Specialized MD and Figures Copy

For collecting markdown files and figures from subfolders:

```bash
# Copy *.md files from subfolders and all files from 'figures' subfolders
# MD files go to: output/*.md
# Figure files go to: output/figures/*
python copy_file_structure.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR" "D:\data\HCNC\norway\biographies\storage\MonkeyOCR" --md-and-figures

# Or use the example script
python copy_md_and_figures_example.py
```

This will:
- Copy all `*.md` files from immediate subfolders to `output/`
- Copy all files from `figures` subfolders to `output/figures/`
- Preserve the directory structure within the figures folder

## Command Line Options

- `--mapping`: Name of mapping configuration to use from JSON file
- `--md-and-figures`: Use specialized mode for collecting MD files and figures
- `--dry-run`: Show what would be copied without actually copying
- `--gitignore`: Path to .gitignore file for exclusion patterns
- `--include`: Include only files matching this pattern
- `--exclude`: Exclude files matching this pattern

## Examples

```bash
# Reorganize a Python project
python copy_file_structure.py ./old_project ./new_project --mapping python_project_reorganization

# Extract specific components
python copy_file_structure.py ./source ./target --mapping component_extraction

# Copy with file filtering
python copy_file_structure.py ./source ./target --mapping simple_copy --include "*.py" --exclude "*test*"

# Dry run with gitignore
python copy_file_structure.py ./source ./target --mapping simple_copy --gitignore .gitignore --dry-run
```
