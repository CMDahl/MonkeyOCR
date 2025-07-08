# README.md

## Note a simple implementation (with codes for the terminal) is given in **README_simple.md**

## Norwegian Biographical Dictionary Processing Pipeline

This pipeline processes Norwegian biographical dictionary pages through OCR, AI-based text extraction, name association, and biographical data extraction. The system handles both text content and portrait images, creating comprehensive biographical datasets.

## Overview

The pipeline transforms raw scanned biographical dictionary pages into structured data containing:
- Extracted biographical text with complete entries
- Name-portrait associations
- Structured biographical information (JSON format)
- Comprehensive CSV datasets for analysis

## Prerequisites

- Python 3.8+
- Azure OCR API access
- Google Gemini API access
- Required Python packages (see requirements.txt)

## Pipeline Steps

### 1. OCR Text and Figure Extraction
**Script:** `AzureOCR_extracting_text_and_figures.py`

Processes raw scanned images using Azure OCR to extract text and identify figures/portraits.

```bash
python AzureOCR_extracting_text_and_figures.py --input "D:/data/HCNC/norway/biographies/raw/corpus/digibok_2007031501007" --start "0057" --end "0494" --output "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json"
```

**Input:** Raw scanned images (JPG/PNG format)
**Output:** 
- Individual markdown files for each page
- Figure markers in format `**[FIGURE: X.Y]**`
- JSON metadata files

### 2. Portrait-Name Association (Initial)
**Script:** `gemini_portrait_name_associator.py`

Uses Google Gemini AI to associate portraits with biographical names by analyzing page content and figure placement.

```bash
python gemini_portrait_name_associator.py "d:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json" "d:\data\HCNC\norway\biographies\storage\AzureOCR\output_portrait_name_associations"
```

**Input:** Markdown files with figure markers
**Output:** JSON files with portrait-name associations

### 3. Markdown Concatenation
**Script:** `concatenate_all_md_files.py`

Combines all individual markdown files into a single concatenated file for comprehensive text processing.

```bash
python concatenate_all_md_files.py "d:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json" "d:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json\concatenated_all.md"
```

**Input:** Individual markdown files
**Output:** Single concatenated markdown file with file boundary markers

### 4. Comprehensive Name Extraction
**Script:** `gemini_all_names.py`

Uses AI to extract all biographical names from the markdown content, creating a comprehensive name database.

```bash
python gemini_all_names.py "d:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_portrait_name_associations"
```

**Input:** Markdown files
**Output:** `all_books_names.json` - comprehensive name database

### 5. Name-Text Chunking and Portrait Association
**Script:** `extract_all_names.py`

**Key Features:**
- **Comprehensive Chunking:** Prioritizes complete biographical information over size limits
- **Smart Boundary Detection:** Uses multiple patterns to find natural biographical entry endings
- **Cross-page Biography Support:** Allows biographical entries to span multiple pages
- **Portrait Association:** Links portraits to biographical subjects based on page positioning

```bash
python extract_all_names.py "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_portrait_name_associations\all_books_names.json" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json\concatenated_all.md" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json\" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\" --portrait-pattern "**[FIGURE:"
```

**Chunking Strategy:**
- Searches for biographical entry patterns: `SURNAME, FirstName, profession, location...`
- Uses multiple ending detection patterns (next entry, figure markers, reference entries)
- Allows chunks up to 15KB to preserve complete biographical narratives
- Provides informational size reporting without artificial restrictions

**Portrait Association Logic:**
- Identifies files starting with `**[FIGURE: X.Y]**` pattern
- Associates portraits with the last name from the previous page
- Generates standardized portrait filenames: `digibok_XXXXXX_XXXX_X.Y.png`

**Input:** 
- `all_books_names.json` (name database)
- `concatenated_all.md` (full text)
- Individual markdown files directory

**Output:**
- `extracted_all_names_with_chunks.csv` - Names with biographical text chunks
- `extracted_all_names_with_chunks_and_portraits.csv` - Complete dataset with portraits
- `files_starting_with_portraits.csv` - Portrait file inventory

### 6. Biographical Data Extraction
**Script:** `biography_extractor.py`

Processes the chunked biographical text to extract structured biographical information.

```bash
python biography_extractor.py "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_with_chunks.csv" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\biographical_data.json" --log-file "D:\data\HCNC\norway\biographies\storage\AzureOCR\log\biography_extraction.log" --log-level "INFO"
```

**Input:** CSV with biographical text chunks
**Output:** 
- Structured JSON with extracted biographical data
- Processing logs

### 7. Portrait Name Extraction
**Script:** `extract_portrait_names.py`

Specialized extraction focused on names associated with portrait images.

```bash
python extract_portrait_names.py "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_portrait_name_associations" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json\concatenated_all.md" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_portrait_names_with_chunks.csv"
```

**Input:** Portrait association data and concatenated text
**Output:** CSV focused on portrait-associated biographical entries

### 8. Data Collection and Consolidation
**Script:** `collecting_all_csv_files.py`

Consolidates all CSV outputs into final datasets for analysis.

```bash
python collecting_all_csv_files.py
```

**Input:** All generated CSV files
**Output:** Consolidated datasets for analysis

## Data Flow Architecture

```
Raw Images → OCR → Individual MD Files → Portrait Association → Concatenated MD
                                     ↓
Name Database ← AI Name Extraction ← Individual MD Files
                                     ↓
Chunked Text + Portraits ← Name-Text Matching ← Concatenated MD + Name Database
                                     ↓
Structured Biographies ← Biographical Extraction ← Chunked Text
                                     ↓
Final Datasets ← Data Consolidation ← All CSV Files
```

## Key Features

### Comprehensive Biographical Chunking
- **Completeness Priority:** Preserves full biographical narratives over size restrictions
- **Smart Boundary Detection:** Uses multiple pattern recognition strategies
- **Cross-page Support:** Biographical entries can span multiple pages naturally
- **Size Flexibility:** Allows chunks from 500 to 15,000+ characters based on content

### Portrait Association System
- **Page-based Logic:** Associates portraits with biographical subjects from previous pages
- **Standardized Naming:** Generates consistent portrait filenames
- **Pattern Recognition:** Handles various figure marker formats

### Robust Name Matching
- **Multiple Strategies:** Exact match, flexible surname matching, simplified matching
- **Norwegian Name Handling:** Specifically designed for Norwegian naming conventions
- **OCR Error Tolerance:** Handles common OCR inconsistencies

## Output Files

### Primary Outputs
1. **`extracted_all_names_with_chunks_and_portraits.csv`** - Complete biographical dataset
2. **`biographical_data.json`** - Structured biographical information
3. **`files_starting_with_portraits.csv`** - Portrait inventory
4. **`extracted_portrait_names_with_chunks.csv`** - Portrait-focused dataset

### Data Structure
Each biographical entry includes:
- **Name:** Full name as extracted
- **Book ID:** Source page identifier
- **Markdown Chunk:** Complete biographical text
- **Portrait Filename:** Associated portrait image (if available)
- **Biographical Data:** Structured information (dates, profession, locations, etc.)

## Error Handling and Logging

- Comprehensive error logging throughout the pipeline
- Progress tracking for long-running operations
- Validation of input/output files
- Graceful handling of missing or corrupted data

## Performance Considerations

- **Memory Management:** Handles large concatenated files efficiently
- **Progress Reporting:** Shows processing status for long operations
- **Chunking Statistics:** Provides detailed information about chunk size distribution
- **Parallel Processing:** Where applicable, uses efficient processing strategies

## Usage Notes

1. **File Paths:** Use absolute paths for reliability
2. **Portrait Pattern:** Adjust `--portrait-pattern` parameter based on OCR system used
3. **Size Monitoring:** Large chunks (>20KB) indicate comprehensive biographical entries
4. **Error Recovery:** Each step can be run independently for debugging

## Troubleshooting

### Common Issues
1. **Large Chunks:** Indicates rich biographical content - generally beneficial
2. **Missing Names:** Check OCR quality and name pattern matching
3. **Portrait Mismatches:** Verify file naming conventions and page sequencing
4. **Memory Issues:** Process in smaller batches if necessary

### Debug Options
- Use `--log-level DEBUG` for detailed processing information
- Check intermediate CSV files for data quality
- Verify file boundary markers in concatenated files

## Future Enhancements

- Support for additional OCR systems
- Enhanced biographical data extraction
- Multi-language support
- Improved portrait-name association algorithms
- Real-time processing capabilities

This pipeline provides a comprehensive solution for processing historical biographical dictionaries, preserving both textual content and visual elements while creating structured, searchable datasets for research and analysis.