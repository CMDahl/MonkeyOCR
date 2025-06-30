# File Structure Copy Script Usage Examples

## Basic Usage

### 1. Simple Directory Mapping
```bash
# Copy specific directories to new structure
python copy_file_structure.py . ./reorganized --simple-mapping "magic_pdf:src,projects:apps"

# With file extension filtering
python copy_file_structure.py . ./reorganized --simple-mapping "magic_pdf:src,projects:apps" --extensions .py .yaml .md
```

### 2. Using JSON Configuration
```bash
# Use predefined mapping from JSON file
python copy_file_structure.py . ./new_structure --mapping-file structure_mappings.json

# Dry run to preview changes
python copy_file_structure.py . ./new_structure --mapping-file structure_mappings.json --dry-run
```

### 3. Custom Mapping Functions
```bash
# Flatten all files into single directory
python copy_file_structure.py . ./flattened --custom-mapping flatten

# Organize files by extension
python copy_file_structure.py . ./organized --custom-mapping by_extension

# Selective copy (only Python and config files)
python copy_file_structure.py . ./selective --custom-mapping selective
```

### 4. With GitIgnore Integration
```bash
# Automatically exclude files based on .gitignore
python copy_file_structure.py . ./clean_copy --simple-mapping ".:backup" --gitignore .gitignore
```

## Common Scenarios for MonkeyOCR Project

### Scenario 1: Create Clean Project Structure
```bash
# Reorganize current project into standard Python package structure
python copy_file_structure.py . ../MonkeyOCR_Clean --mapping-file structure_mappings.json --extensions .py .yaml .md .json --dry-run

# Remove --dry-run when satisfied with preview
python copy_file_structure.py . ../MonkeyOCR_Clean --mapping-file structure_mappings.json --extensions .py .yaml .md .json
```

### Scenario 2: Extract Components for Distribution
```bash
# Extract only model-related components
python copy_file_structure.py . ./MonkeyOCR_Models --simple-mapping "magic_pdf/model:models,magic_pdf/config:config" --extensions .py .yaml
```

### Scenario 3: Create Development Environment
```bash
# Copy everything except build artifacts and temporary files
python copy_file_structure.py . ../MonkeyOCR_Dev --simple-mapping ".:." --gitignore .gitignore
```

### Scenario 4: Backup Important Files Only
```bash
# Copy only Python source files and configurations
python copy_file_structure.py . ./backup --custom-mapping selective --extensions .py .yaml .json .md
```

## Advanced Custom Mapping

You can extend the script with your own mapping functions. Here's an example:

```python
def my_custom_mapping(source_path: Path) -> Optional[Path]:
    """Custom mapping for specific MonkeyOCR reorganization."""
    base_target = Path("custom_structure")
    
    relative_path = source_path.relative_to(source_path.parts[0])
    
    # Put all models in models/ directory
    if 'model' in str(relative_path):
        return base_target / 'models' / source_path.name
    
    # Put all configs in config/ directory  
    if source_path.suffix in ['.yaml', '.yml', '.json']:
        return base_target / 'config' / source_path.name
    
    # Put scripts in scripts/ directory
    if source_path.name.endswith('.py') and 'script' in source_path.name.lower():
        return base_target / 'scripts' / source_path.name
    
    # Everything else preserves structure
    return base_target / relative_path
```

## Tips

1. **Always use dry-run first** to preview changes
2. **Check the gitignore integration** to avoid copying unwanted files
3. **Use file extension filtering** to copy only relevant files
4. **Monitor the statistics** output to ensure expected number of files are copied
5. **Check the logs** for any errors or skipped files
