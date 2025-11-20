# OCR Illustration Pipeline

A comprehensive, AI-powered pipeline for extracting and structuring biographical information from OCR-processed Norwegian biography collections.

## 🎯 Overview

This pipeline processes Norwegian biographical dictionary pages through OCR, AI-based text extraction, portrait association, and biographical data extraction. It transforms raw scanned biographical pages into structured datasets containing complete biographical information, portrait associations, and quality inspection visualizations.

**Key Features:**
- ✨ AI-powered portrait-to-name association with validation
- 📝 Structured biographical data extraction (birth/death dates, occupation, education, family, etc.)
- 🖼️ Automated quality inspection visualizations
- ⚙️ Fully configurable via JSON files (prompts externalized)
- 🔄 Robust retry logic and error handling
- 🎭 Support for multiple portraits per person
- 📊 CSV output for easy data analysis

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Pipeline Architecture](#-pipeline-architecture)
- [Configuration](#-configuration)
- [Input Requirements](#-input-requirements)
- [Output Structure](#-output-structure)
- [Key Features](#-key-features)
- [Troubleshooting](#-troubleshooting)
- [Additional Documentation](#-additional-documentation)

---

## 🚀 Quick Start

### Prerequisites

1. **Python Environment**: OCR-Parser conda environment
   ```powershell
   conda activate OCR-Parser
   pip install google-genai azure-identity azure-keyvault-secrets pandas matplotlib pillow
   ```

2. **Azure Key Vault**: API keys stored securely
   - **Vault URL**: `https://rmaocr.vault.azure.net/`
   - **Gemini API Key Name**: `SDUGeminiAPI`
   - **Authentication**: Requires Azure CLI login (`az login`)

3. **Input Data**: PaddleOCR markdown files with extracted portrait images

### Running the Pipeline

1. **Configure input** in `pipeline_config.json`:
   ```json
   {
     "input": {
       "mode": "files",
       "files": ["path/to/file1.md", "path/to/file2.md"]
     }
   }
   ```

2. **Run the pipeline**:
   ```powershell
   .\run_pipeline.ps1
   ```

3. **Check results** in the output directory:
   - `final_dataset.csv` - Complete structured biographical data
   - `test_images/` - Quality inspection visualizations

---

## 🏗️ Pipeline Architecture

The pipeline executes **8 sequential steps**:

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Portrait Association (Gemini AI)                    │
│ ─────────────────────────────────────────────────────────── │
│ Associates portraits with biographical subjects             │
│ • Analyzes portrait placement relative to headings          │
│ • Excludes deceased persons marked with †                   │
│ • Handles multiple portraits per person                     │
│ Output: JSON files with portrait-name mappings              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 1b: Validate Portrait Associations (Gemini AI)         │
│ ─────────────────────────────────────────────────────────── │
│ Validates portrait associations to catch false positives    │
│ • Checks if names appear as main biographical subjects      │
│ • Detects embedded names vs. actual headings               │
│ • Suggests corrections for misassignments                   │
│ Output: Validated portrait associations                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Concatenate Markdown Files                          │
│ ─────────────────────────────────────────────────────────── │
│ Combines all markdown files into single document            │
│ Output: all_text.md                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Extract Names with Text Chunks                      │
│ ─────────────────────────────────────────────────────────── │
│ • Extracts biographical subject names                       │
│ • Associates each name with surrounding text context        │
│ • Handles cross-page biographical entries                   │
│ Output: extracted_all_names_with_chunks.csv                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Merge Portrait Data                                 │
│ ─────────────────────────────────────────────────────────── │
│ • Merges portrait associations from Step 1                  │
│ • Supports multiple portraits per person (pipe-separated)   │
│ • Deduplicates portrait filenames                          │
│ Output: extracted_all_names_with_chunks_and_portraits.csv   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Extract Biographical Data (Gemini AI)               │
│ ─────────────────────────────────────────────────────────── │
│ Extracts structured biographical information                │
│ • Birth/death dates, places                                 │
│ • Parents, spouses, children                                │
│ • Education, jobs, stays abroad                            │
│ • Retry logic with temperature adjustment                   │
│ Output: biographies.json                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Collect Final Dataset                               │
│ ─────────────────────────────────────────────────────────── │
│ Generates statistics and final CSV                          │
│ Output: final_dataset.csv + statistics summary              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 7: Generate Visualizations                             │
│ ─────────────────────────────────────────────────────────── │
│ Creates quality inspection images                           │
│ • Full-page scan | Portrait + Data | Text chunk            │
│ • Uses only first portrait for visualization               │
│ • All portraits stored in CSV                              │
│ Output: PNG files in test_images/                           │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

The pipeline uses **two JSON configuration files** with all prompts externalized:

### 📄 pipeline_config.json

Controls pipeline behavior, input sources, and step execution.

**Input Modes:**

#### 1. Specific Files Mode
```json
{
  "input": {
    "mode": "files",
    "files": [
      "C:\\path\\to\\file1.md",
      "C:\\path\\to\\file2.md"
    ]
  }
}
```

#### 2. Folder Scanning Mode
```json
{
  "input": {
    "mode": "folders",
    "folders": [
      {
        "path": "C:\\data\\collection1",
        "pattern": "**/*.md",
        "recursive": true
      }
    ]
  }
}
```

#### 3. Mixed Mode
```json
{
  "input": {
    "mode": "mixed",
    "files": ["C:\\important.md"],
    "folders": [{"path": "C:\\data\\collection"}]
  }
}
```

**Portrait Handling:**
```json
{
  "portrait_handling": {
    "multiple_portraits_per_person": "all",
    "separator": "|"
  }
}
```

Options: `"all"` (store all with separator), `"first"`, `"last"`, `"primary"` (highest confidence)

### 📄 prompt_config.json

Contains all AI prompts and model settings. Prompts are stored as arrays for readability:

```json
{
  "gemini_settings": {
    "model": "gemini-2.5-flash",
    "validation_temperature": 0.01,
    "biography_temperatures": [0.01, 0.01, 0.1, 0.2]
  },
  
  "prompts": {
    "portrait_association": {
      "template": [
        "You are analyzing a Norwegian biography...",
        "",
        "CRITICAL EXCLUSION: NEVER pair portraits with deceased persons marked with †",
        "..."
      ]
    },
    "portrait_validation": {
      "template": [...]
    },
    "biography_extraction": {
      "template": [...]
    }
  }
}
```

**Key Features:**
- **Externalized Prompts**: Modify AI behavior without touching Python code
- **Readable Format**: Multi-line arrays for easy editing
- **Temperature Control**: Different temperatures for different tasks
- **Retry Logic**: Biography extraction tries multiple temperatures

See **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)** for detailed documentation.

---

## 📥 Input Requirements

### Expected Input Format

**Markdown files** from PaddleOCR with:
- OCR-extracted biographical text
- Portrait images as HTML tags: `<div style="text-align: center;"><img src="imgs/filename.jpg" /></div>`
- Portrait images stored in `imgs/` subfolder

**Directory Structure:**
```
paddle_output/
└── sample/
    ├── digibok_2011041305069_0048/
    │   ├── digibok_2011041305069_0048.md
    │   └── imgs/
    │       ├── img_in_image_box_428_449_1062_1298.jpg
    │       └── img_in_image_box_401_2340_1042_3197.jpg
    └── digibok_2012110706264_0094/
        ├── digibok_2012110706264_0094.md
        └── imgs/
            ├── img_in_image_box_397_382_873_1017.jpg
            └── img_in_image_box_938_384_1412_1020.jpg
```

**Original Full-Page Images** (for visualization):
```
corpus/
└── digibok_2011041305069/
    ├── digibok_2011041305069_0048.jpg
    └── digibok_2011041305069_0050.jpg
```

---

## 📤 Output Structure

### Output Directory: `test/`

```
test/
├── input_staging/                          # Copied input files
│   ├── digibok_2011041305069_0048.md
│   └── digibok_2012110706264_0094.md
│
├── all_books_portrait_associations.json    # Step 1: Portrait associations
│   {
│     "books": {
│       "digibok_2011041305069_0048": {
│         "biographical_entries": [
│           {
│             "filename": "img_in_image_box_401_2340_1042_3197.jpg",
│             "associated_person": "Bronn, Thorleif",
│             "confidence": 0.95
│           }
│         ]
│       }
│     }
│   }
│
├── all_text.md                             # Step 2: Concatenated text
│
├── extracted_all_names_with_chunks.csv     # Step 3: Names + text
│   Columns: name, book_id, markdown_chunk
│
├── extracted_all_names_with_chunks_and_portraits.csv  # Step 4: + portraits
│   New column: portrait_filename
│   Example: "img_box_382.jpg|img_box_924.jpg"  (multiple portraits)
│
├── biographies.json                        # Step 5: Structured data
│   [
│     {
│       "name": "Bronn, Thorleif",
│       "birth_date": "1893-01-17",
│       "birth_place": "Drammen",
│       "jobs": [...],
│       "educations": [...],
│       "spouses": [...],
│       "children": [...]
│     }
│   ]
│
├── final_dataset.csv                       # Step 6: Final output
│   All previous columns + biography_json
│
└── test_images/                            # Step 7: Visualizations
    ├── digibok_2011041305069_0048_01_Bronn_Thorleif.png
    └── digibok_2012110706264_0094_01_Bugge_Sigrun_Collett.png
```

### Final Dataset CSV Structure

| Column | Description | Example |
|--------|-------------|---------|
| `name` | Person's full name | "Bronn, Thorleif" |
| `book_id` | Source page identifier | "digibok_2011041305069_0048" |
| `markdown_chunk` | Biographical text | "Jeg har sido 1912..." |
| `portrait_filename` | Portrait(s), pipe-separated | "img1.jpg\|img2.jpg" |
| `biography_json` | Structured data (JSON string) | "{\\"birth_date\\": \\"1893-01-17\\"...}" |

**Multiple Portraits**: When a person has multiple portraits, they are stored as pipe-separated values (e.g., `portrait1.jpg|portrait2.jpg`). Visualizations use only the first portrait, but all are preserved in the CSV.

---

## 🔑 Key Features

### 1. AI-Powered Portrait Association

**Smart Portrait Matching:**
- Analyzes portrait placement relative to biographical headings
- Prioritizes portraits appearing BEFORE headings (confidence: 0.95-1.0)
- **Excludes deceased persons** marked with † symbol
- Handles portraits embedded in text vs. between headings

**Validation Layer:**
- Double-checks associations using context windows
- Detects false positives (embedded names, children, spouses)
- Suggests corrections for misassignments
- Validates that names appear as main biographical subjects

### 2. Multiple Portraits Per Person

- **Storage**: All portraits stored in CSV with pipe separator
- **Visualization**: Only first portrait used in quality inspection images
- **Deduplication**: Automatic removal of duplicate portrait references
- **Configuration**: Controllable via `portrait_handling` settings

### 3. Externalized Prompts

All AI prompts are stored in `prompt_config.json` for easy modification:

```json
{
  "prompts": {
    "portrait_association": {
      "template": [
        "Line 1 of prompt",
        "Line 2 of prompt",
        "..."
      ]
    }
  }
}
```

**Benefits:**
- Modify AI behavior without editing Python code
- Easy A/B testing of different prompts
- Version control for prompt changes
- Readable multi-line format

### 4. Robust Error Handling

**Retry Logic:**
- Biography extraction tries multiple temperatures: [0.01, 0.01, 0.1, 0.2]
- Exponential backoff for API failures
- Graceful degradation (continues processing if one entry fails)

**Encoding Support:**
- UTF-8 encoding throughout pipeline
- ASCII replacements for problematic Unicode characters
- Environment variable: `$env:PYTHONIOENCODING = "utf-8"`

### 5. Comprehensive Name Detection

**Pattern Recognition:**
- Detects names starting with "## SURNAME, Given Names"
- Handles single hash "#" or no hash
- **Requires names to start their own line** (not embedded in prose)
- Excludes names starting with em-dash "—" (embedded references)

**Cross-Page Support:**
- Biographical entries can span multiple pages
- Text chunking preserves complete narratives
- Portrait associations work across page boundaries

### 6. Quality Inspection Visualizations

**Three-Panel Layout:**
1. **Full-page scan** (original image from corpus)
2. **Portrait + Structured Data** (first portrait + JSON biography)
3. **Markdown Chunk** (extracted biographical text)

**Features:**
- Automatic image scaling and centering
- Portrait count indicator (e.g., "Portrait 1 of 2")
- Handles missing portraits gracefully
- Cleans up stale visualizations between runs

---

## 🔧 Troubleshooting

### Common Issues

**❌ Azure Key Vault Connection Errors**
```powershell
az login
az account show  # Verify correct subscription
```
Ensure your account has "Get" permissions on secrets in `rmaocr.vault.azure.net`.

**❌ Unicode Encoding Errors**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```
The pipeline sets `$env:PYTHONIOENCODING = "utf-8"` automatically. If issues persist, check PowerShell encoding.

**❌ Wrong Portrait Associations**

Check `prompt_config.json` rules:
- Deceased persons (†) should be excluded
- Names must start their own line
- Portrait should appear BEFORE heading for highest confidence

**❌ Duplicate Portraits in CSV**

Fixed in v1.0 with deduplication logic. If still occurring, check `merge_portraits.py` is using latest version.

**❌ Missing Portraits in Visualization**

Verify:
1. `original_images_path` points to corpus folder in `pipeline_config.json`
2. Portrait files exist in `imgs/` subfolders
3. Filenames match between markdown and filesystem

### Debug Mode

Enable verbose logging:

```json
{
  "pipeline_steps": {
    "1_portrait_association": {
      "suppress_stderr": false
    }
  }
}
```

### Performance Notes

- **Average**: ~5-10 seconds per biography
- **API Calls**: 3 Gemini calls per file (association, validation, biography)
- **Retry Logic**: Automatic retries with exponential backoff
- **Rate Limiting**: Configurable delay (default: 2 seconds)

---

## 📚 Additional Documentation

- **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)** - Comprehensive configuration guide
- **[INPUT_MODES.md](INPUT_MODES.md)** - Detailed input mode examples
- **[SCRIPTS.md](SCRIPTS.md)** - Individual script documentation
- **[MULTIPLE_PORTRAITS.md](MULTIPLE_PORTRAITS.md)** - Multiple portrait handling

---

## 📝 Version History

### Version 1.0 (November 2025)

**Major Features:**
- ✅ Externalized all prompts to `prompt_config.json`
- ✅ Added portrait validation step (Step 1b)
- ✅ Support for multiple portraits per person
- ✅ Deceased person exclusion († symbol)
- ✅ Deduplication of portrait filenames
- ✅ UTF-8 encoding fixes
- ✅ Nested JSON structure support in `merge_portraits.py`
- ✅ Configurable temperature sequences for biography extraction

**Configuration Updates:**
- `ConfigLoader` class for centralized configuration
- Prompts stored as arrays for readability
- Portrait handling modes: all, first, last, primary

---

## 🤝 Contributing

For production use, consider:
1. Adding validation checks between steps
2. Implementing comprehensive unit tests
3. Adding parallel processing for large datasets
4. Implementing file-based logging with rotation
5. Creating monitoring dashboards for long-running jobs

---

## 🙏 Acknowledgments

- **PaddleOCR** for OCR processing
- **Google Gemini AI** for biographical data extraction
- **Azure Key Vault** for secure API key management
- **Norwegian Biography Collections** for source data

---

**Version:** 1.0  
**Last Updated:** November 2025  
**Maintained by:** CMD Team
