#!/usr/bin/env python3
"""
Cleanup script for MonkeyOCR validation folder
Organizes files into essential vs. retired (development/test) files
"""

import os
import shutil
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_validation_folder():
    """Clean up the validation folder by organizing files"""
    
    base_path = Path("d:/GitHub/MonkeyOCR/validation")
    retired_path = base_path / "retired"
    
    # Create retired folder
    retired_path.mkdir(exist_ok=True)
    
    # Define essential files to keep in main folder
    essential_files = {
        # Core production scripts
        "comprehensive_json_extraction.py",
        "gemini_job_resolver.py",
        "run_gemini_batch_analysis.py",
        "analyze_gemini_results.py",
        
        # Essential data files
        "comprehensive_comparison_dataframe.csv",
        "flagged_job_overlap_records.csv",
        
        # Documentation
        "readme.md",
        "JOB_TITLE_OVERLAP_SUMMARY.md",
        "job_title_overlap_documentation.md",
    }
    
    # Define essential directories to keep
    essential_dirs = {
        "gemini_analysis_complete",  # Main production results
    }
    
    # Define patterns for files/dirs to retire
    test_patterns = [
        "test_",
        "demo_",
        "debug_",
        "verify_",
        "check_",
        "final_test",
        "final_verification",
        "practical_",
        "simple_",
        "_demo",
        "_test",
    ]
    
    # Files to retire (development/testing files)
    files_to_retire = [
        "biography_json_comparisons_retired.py",
        "figure_extraction.py",
        "figure_extraction_usage.py",
        "find_medical_records.py",
        "individual_job_overlap_demo.py",
        "job_comparison_demo.py",
        "job_title_overlap_analysis.py",
        "practical_individual_job_overlap_demo.py",
        "quick_reference_guide.py",
        "similarity_analysis_tool.py",
        "simple_job_comparison_example.py",
        "simple_json_extraction_example.py",
        "usage_examples.py",
        "biography_inspection_demo.py",
        
        # Data files from testing
        "demo_flagged_job_overlap_records.csv",
        "demo_flagged_job_overlap_records_all_results.csv",
        "practical_flagged_job_overlap_records.csv",
        "practical_flagged_job_overlap_records_all_results.csv",
        "test_heggoy_record.csv",
        "test_weider_flagged.csv",
        "flagged_job_overlap_records_all_results.csv",
        
        # Generated analysis files (keep main ones, retire extras)
        "AzureOCR_with_extracted_fields.csv",
        "MonkeyOCR_with_extracted_fields.csv",
        "final_output_with_figures_and_images.csv",
        "output_with_figures_and_images.csv",
        "job_title_matched_pairs.csv",
        "job_title_matched_pairs_enhanced.csv",
        "job_title_unmatched.csv",
        "job_title_unmatched_enhanced.csv",
        "job_title_overlap_summary.csv",
        "similarity_analysis_report.csv",
        
        # Documentation files that are outdated
        "ENHANCED_UNMATCHED_UPDATE.md",
        "gemini_analysis_summary_report.md",
        "gemini_format_improvement_summary.md",
        "INSPECTION_FUNCTIONS_README.md",
    ]
    
    # Process files
    logger.info("Starting cleanup of validation folder...")
    
    moved_files = 0
    moved_dirs = 0
    
    # Move individual files
    for item in base_path.iterdir():
        if item.is_file():
            filename = item.name
            
            # Skip essential files
            if filename in essential_files:
                logger.info(f"Keeping essential file: {filename}")
                continue
            
            # Check if file should be retired
            should_retire = (
                filename in files_to_retire or
                any(pattern in filename for pattern in test_patterns) or
                filename.startswith('__pycache__')
            )
            
            if should_retire:
                try:
                    dest_path = retired_path / filename
                    shutil.move(str(item), str(dest_path))
                    logger.info(f"Moved file: {filename} -> retired/")
                    moved_files += 1
                except Exception as e:
                    logger.error(f"Failed to move {filename}: {e}")
    
    # Move directories
    for item in base_path.iterdir():
        if item.is_dir() and item.name != "retired":
            dirname = item.name
            
            # Skip essential directories
            if dirname in essential_dirs:
                logger.info(f"Keeping essential directory: {dirname}")
                continue
            
            # Check if directory should be retired
            should_retire = (
                any(pattern in dirname for pattern in test_patterns) or
                dirname.startswith('__pycache__') or
                dirname in [
                    "gemini_job_analysis_output",
                    "gemini_job_analysis_extended",
                ]
            )
            
            if should_retire:
                try:
                    dest_path = retired_path / dirname
                    shutil.move(str(item), str(dest_path))
                    logger.info(f"Moved directory: {dirname} -> retired/")
                    moved_dirs += 1
                except Exception as e:
                    logger.error(f"Failed to move {dirname}: {e}")
    
    # Create a clean README for the main folder
    create_clean_readme(base_path)
    
    # Create a retired folder README
    create_retired_readme(retired_path)
    
    logger.info(f"\nCleanup complete!")
    logger.info(f"Moved {moved_files} files and {moved_dirs} directories to retired/")
    
    # Show final structure
    show_clean_structure(base_path)

def create_clean_readme(base_path: Path):
    """Create a clean README for the main validation folder"""
    
    readme_content = """# MonkeyOCR Validation - Production Tools

This folder contains the essential production tools for OCR validation and job analysis.

## Core Scripts

### Data Processing & Analysis
- `comprehensive_json_extraction.py` - Main tool for extracting, linking, and comparing OCR data
- `gemini_job_resolver.py` - AI-powered job discrepancy resolution using Google Gemini
- `run_gemini_batch_analysis.py` - Batch processing for Gemini analysis
- `analyze_gemini_results.py` - Analysis and reporting of Gemini results

## Essential Data Files

- `comprehensive_comparison_dataframe.csv` - Main merged dataset with Azure and Monkey OCR
- `flagged_job_overlap_records.csv` - Records flagged for manual inspection

## Results

- `gemini_analysis_complete/` - Complete production results from Gemini analysis
  - Individual JSON analysis files for each record
  - Summary CSV and metadata files

## Documentation

- `JOB_TITLE_OVERLAP_SUMMARY.md` - Summary of job title overlap analysis
- `job_title_overlap_documentation.md` - Detailed documentation

## Usage

### Basic Analysis
```bash
python comprehensive_json_extraction.py
```

### Gemini Job Resolution
```bash
# Test with 5 records
python gemini_job_resolver.py --max-records 5 --output-dir test_run

# Full production run with corrections
python gemini_job_resolver.py --output-dir production_run --create-corrections
```

### Batch Analysis
```bash
python run_gemini_batch_analysis.py
```

## Development Files

All development, testing, and experimental files have been moved to the `retired/` subfolder to keep this directory clean and focused on production tools.
"""
    
    readme_path = base_path / "README_CLEAN.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    logger.info("Created clean README_CLEAN.md")

def create_retired_readme(retired_path: Path):
    """Create a README for the retired folder"""
    
    readme_content = """# Retired Development Files

This folder contains all development, testing, and experimental files that were created during the development process but are no longer needed for production use.

## Categories

### Test Scripts
- Files starting with `test_` - Unit tests and integration tests
- Files ending with `_test.py` - Test implementations
- `demo_` files - Demonstration scripts
- `debug_` files - Debugging utilities

### Development Utilities
- `figure_extraction.py` - Figure extraction experiments
- `similarity_analysis_tool.py` - Analysis tools development
- `verify_` and `check_` scripts - Verification utilities
- Various analysis and inspection tools

### Test Data
- `demo_*.csv` - Test datasets
- `practical_*.csv` - Practical testing files
- Various generated CSV files from testing phases

### Documentation Drafts
- Draft documentation and analysis reports
- Outdated README files
- Development notes and summaries

### Test Output Directories
- Various `test_*` directories with experimental results
- Old analysis output folders

## Note

These files are preserved for reference but are not needed for production use. The main validation folder now contains only essential production tools.
"""
    
    readme_path = retired_path / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    logger.info("Created retired/README.md")

def show_clean_structure(base_path: Path):
    """Show the clean folder structure"""
    
    logger.info("\n" + "="*60)
    logger.info("CLEAN FOLDER STRUCTURE")
    logger.info("="*60)
    
    logger.info("\nEssential files in main folder:")
    for item in sorted(base_path.iterdir()):
        if item.is_file() and item.name != "cleanup_validation_folder.py":
            logger.info(f"  📄 {item.name}")
    
    logger.info("\nEssential directories in main folder:")
    for item in sorted(base_path.iterdir()):
        if item.is_dir() and item.name != "retired":
            logger.info(f"  📁 {item.name}/")
    
    # Count retired items
    retired_path = base_path / "retired"
    if retired_path.exists():
        retired_files = len([f for f in retired_path.iterdir() if f.is_file()])
        retired_dirs = len([f for f in retired_path.iterdir() if f.is_dir()])
        logger.info(f"\n📦 retired/ - {retired_files} files, {retired_dirs} directories")
    
    logger.info("\n✅ Validation folder is now clean and organized!")

if __name__ == "__main__":
    cleanup_validation_folder()
