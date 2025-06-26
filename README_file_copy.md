# File Structure Copy Scripts

This repository contains scripts to copy files from existing file structures to new file structures with customizable mapping rules.

## Files

- `copy_file_structure.py` - Main script with flexible file copying capabilities
- `copy_md_and_figures.py` - Specialized script for copying *.md files and figures
- `structure_mappings.json` - Configuration file with predefined mapping rules

## Your Use Case: Copying *.md Files and Figures

For your specific requirement to copy *.md files from subfolders and all files from 'images' subfolders to an output directory, you have two options:

### Option 1: Use the specialized script (Recommended)

```powershell
# First, do a dry run to see what would be copied
python copy_md_and_figures.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR" --dry-run

# If the dry run looks good, run it for real
python copy_md_and_figures.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR"
```

### Option 2: Use the main script with the specialized option

```powershell
# Dry run
python copy_file_structure.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR" "D:\data\HCNC\norway\biographies\storage\MonkeyOCR" --md-and-figures --dry-run

# Actual copy
python copy_file_structure.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR" "D:\data\HCNC\norway\biographies\storage\MonkeyOCR" --md-and-figures
```

## What the Scripts Do

The specialized functionality (`--md-and-figures` option) will:

1. **Copy *.md files**: Find all `.md` files in immediate subfolders and copy them to the `digibok_2007031501007` directory
2. **Copy images**: Find all `images` subfolders and copy all files from them to the `digibok_2007031501007/figures` directory
3. **Handle naming conflicts**: If files have the same name, they'll be renamed with a number suffix
4. **Respect .gitignore**: Files matching patterns in `.gitignore` will be skipped

## Directory Structure Example

**Before:**
```
MonkeyOCR/
├── subfolder1/
│   ├── document1.md
│   ├── other_file.txt
│   └── images/
│       ├── image1.png
│       └── chart1.jpg
├── subfolder2/
│   ├── document2.md
│   └── images/
│       └── diagram.svg
└── subfolder3/
    └── document3.md
```

**After running the script:**
```
MonkeyOCR/
├── subfolder1/ (unchanged)
├── subfolder2/ (unchanged)
├── subfolder3/ (unchanged)
└── digibok_2007031501007/
    ├── document1.md
    ├── document2.md
    ├── document3.md
    └── figures/
        ├── image1.png
        ├── chart1.jpg
        └── diagram.svg
```

## Other Use Cases

The main script (`copy_file_structure.py`) supports various other copying scenarios:

### Simple directory mapping
```powershell
python copy_file_structure.py . ./reorganized --simple-mapping "magic_pdf:src,projects:apps"
```

### Using JSON configuration
```powershell
python copy_file_structure.py . ./new_structure --mapping-file structure_mappings.json
```

### Copy only specific file types
```powershell
python copy_file_structure.py . ./python_only --simple-mapping ".:backup" --extensions .py .yaml
```

### Custom organization patterns
```powershell
# Organize files by extension
python copy_file_structure.py . ./organized --custom-mapping by_extension

# Flatten all files into one directory
python copy_file_structure.py . ./flattened --custom-mapping flatten
```

## Important Notes

- **Always use `--dry-run` first** to preview what will be copied
- The script respects `.gitignore` patterns to avoid copying unwanted files
- File conflicts are handled by adding number suffixes
- The script preserves file timestamps and metadata
- All operations are logged for tracking

## Troubleshooting

If you encounter issues:

1. Make sure Python 3.6+ is installed
2. Check that the source directory exists and is accessible
3. Verify you have write permissions to the target location
4. Use `--dry-run` to debug without making changes
5. Check the log output for specific error messages
