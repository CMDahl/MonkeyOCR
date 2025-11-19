# OCR Illustration Pipeline

A comprehensive, AI-powered pipeline for extracting and structuring biographical information from OCR-processed Norwegian biography collections.

## 🎯 Overview

This pipeline demonstrates the complete workflow for processing OCR results from PaddleOCR, extracting biographical data using Google Gemini AI, associating portraits with individuals, and generating quality inspection visualizations.

**Key Features:**
- ✨ AI-powered portrait-to-name association
- 📝 Structured biographical data extraction (birth/death dates, occupation, education, etc.)
- 🖼️ Automated quality inspection visualizations
- ⚙️ Fully configurable via JSON files
- 🔄 Robust retry logic and error handling
- 📊 CSV output for easy data analysis

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Pipeline Architecture](#pipeline-architecture)
- [Configuration](#configuration)
- [Input Requirements](#input-requirements)
- [Output Structure](#output-structure)
- [Python Scripts](#python-scripts)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

1. **Python Environment**: OCR-Parser conda environment with required packages:
   ```powershell
   conda activate OCR-Parser
   pip install google-genai azure-identity azure-keyvault-secrets pandas matplotlib pillow
   ```

2. **Azure Key Vault**: API keys stored in Azure Key Vault (configured in parent project)

3. **Input Data**: PaddleOCR markdown files with extracted portrait images

### Running the Pipeline

1. **Configure input files** in `pipeline_config.json`:
   ```json
   {
     "input_files": [
       "C:\\path\\to\\file1.md",
       "C:\\path\\to\\file2.md"
     ]
   }
   ```

2. **Run the pipeline**:
   ```powershell
   .\run_pipeline.ps1
   ```

3. **Check results** in the output directory (default: `test/`):
   - `final_dataset.csv` - Complete structured biographical data
   - `test_images/` - Quality inspection visualizations

---

## 🏗️ Pipeline Architecture

The pipeline executes **8 sequential steps**:

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Portrait Association (Gemini AI)                    │
│ ─────────────────────────────────────────────────────────── │
│ Input:  Individual markdown files                           │
│ Output: JSON files mapping portraits to person names        │
│ AI Model: Gemini 2.5 Flash                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Concatenate Markdown Files                          │
│ ─────────────────────────────────────────────────────────── │
│ Combines all markdown files into single document            │
│ Output: all_biographies.md                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Extract Names (Gemini AI)                           │
│ ─────────────────────────────────────────────────────────── │
│ Extracts all person names from concatenated text            │
│ Output: gemini_all_names.json                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Extract Names with Text Chunks                      │
│ ─────────────────────────────────────────────────────────── │
│ Associates each name with surrounding text context          │
│ Output: all_names.csv (name, book_id, text_chunk)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Merge Portrait Data                                 │
│ ─────────────────────────────────────────────────────────── │
│ Adds portrait_filename column from Step 1 JSON files        │
│ Output: Enhanced all_names.csv                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Extract Biographical Data (Gemini AI)               │
│ ─────────────────────────────────────────────────────────── │
│ Extracts structured data: birth/death, occupation, etc.     │
│ Output: CSV with biography columns added                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 7: Collect Final Dataset                               │
│ ─────────────────────────────────────────────────────────── │
│ Generates statistics and final CSV                          │
│ Output: final_dataset.csv + stats summary                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 8: Generate Visualizations (Bonus)                     │
│ ─────────────────────────────────────────────────────────── │
│ Creates quality inspection images                           │
│ Output: PNG files in test_images/                           │
│ Layout: Full page | Portrait + Data | Text chunk            │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

The pipeline uses **two JSON configuration files**:

### 📄 pipeline_config.json

Controls pipeline behavior, paths, and enabled steps.

```json
{
  "pipeline_name": "OCR Illustration Pipeline",
  "version": "1.0",
  
  "paths": {
    "output_directory": "C:\\...\\test",
    "python_executable": "C:\\...\\python.exe",
    "original_images_path": "V:\\...\\corpus"
  },
  
  "input_files": [
    "path/to/file1.md",
    "path/to/file2.md"
  ],
  
  "pipeline_steps": {
    "1_portrait_association": {
      "enabled": true,
      "suppress_stderr": true,
      "description": "Associate portraits with names using Gemini AI"
    }
    // ... more steps
  }
}
```

**Key Settings:**
- `input_files`: Array of markdown files to process
- `output_directory`: Where results are saved
- `original_images_path`: Corpus folder with full-page scans
- `pipeline_steps.*.enabled`: Toggle individual steps on/off
- `pipeline_steps.*.suppress_stderr`: Hide Azure KeyVault logging

### 📄 prompt_config.json

Controls AI prompts, model settings, and extraction rules.

```json
{
  "gemini_settings": {
    "model": "gemini-2.5-flash",
    "temperature": 0.05,
    "max_retries": 3,
    "retry_delay_seconds": 2
  },
  
  "prompts": {
    "portrait_association": {
      "system_instruction": [...],
      "user_prompt_template": [...]
    }
    // ... more prompts
  },
  
  "extraction_rules": {
    "min_text_chunk_length": 100,
    "max_text_chunk_length": 3000,
    "context_length_chars": 500
  }
}
```

**Key Settings:**
- `model`: Gemini model to use
- `temperature`: Lower = more consistent (0.0-1.0)
- `max_retries`: Retry failed API calls
- `prompts.*`: Customizable AI instructions
- `extraction_rules`: Text chunking parameters

See **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)** for detailed configuration documentation.

---

## 📥 Input Requirements

### Expected Input Format

**Markdown files** from PaddleOCR with:
- OCR-extracted biographical text
- Portrait image references as HTML tags: `<img src="imgs/filename.jpg">`
- Portrait images stored in `imgs/` subfolder

**Directory Structure:**
```
output_paddleOCR/
└── digibok_2007031501007/
    ├── digibok_2007031501007_0154/
    │   ├── digibok_2007031501007_0154.md
    │   └── imgs/
    │       ├── img_in_image_box_173_357_600_930.jpg
    │       └── img_in_image_box_415_1065_1072_1445.jpg
    └── digibok_2007031501007_0155/
        ├── digibok_2007031501007_0155.md
        └── imgs/
            └── ...
```

**Original Full-Page Images:**
```
corpus/
└── digibok_2007031501007/
    ├── digibok_2007031501007_0154.jpg
    ├── digibok_2007031501007_0155.jpg
    └── ...
```

---

## 📤 Output Structure

### Output Directory: `test/`

```
test/
├── input_staging/                          # Copied & renamed input files
│   ├── digibok_2007031501007_0154.md
│   └── digibok_2007031501007_0155.md
│
├── all_biographies.md                      # Step 2: Concatenated markdown
│
├── digibok_*_portrait_associations.json    # Step 1: Portrait mappings
│
├── gemini_all_names.json                   # Step 3: Extracted names
│
├── all_names.csv                           # Step 4-6: Names + biographies
│   Columns: name, book_id, text_chunk, portrait_filename,
│            birth_year, death_year, occupation, etc.
│
├── final_dataset.csv                       # Step 7: Final output
│   Complete structured biographical data
│
└── test_images/                            # Step 8: Visualizations
    ├── digibok_2007031501007_0154_01_PERSON_NAME.png
    ├── digibok_2007031501007_0154_02_PERSON_NAME.png
    └── ...
```

### Final Dataset CSV Columns

| Column | Description | Example |
|--------|-------------|---------|
| `name` | Person's full name | "FLUGE Frithjof" |
| `book_id` | Source page identifier | "digibok_2007031501007_0154" |
| `text_chunk` | Biographical text context | "FLUGE, Frithjof, f. 1940..." |
| `portrait_filename` | Associated portrait image | "img_in_image_box_173.jpg" |
| `birth_year` | Year of birth | "1940" |
| `death_year` | Year of death | "" (if living) |
| `birth_place` | Place of birth | "Oslo" |
| `occupation` | Primary occupation | "Professor" |
| `education` | Educational background | "Cand.med. 1965, Dr.med. 1972" |
| `achievements` | Notable achievements | "Developed new surgical technique" |
| `family` | Family information | "Married to Anne, 3 children" |
| `summary` | 2-3 sentence summary | "Norwegian surgeon who..." |

---

## 🐍 Python Scripts

### Core Pipeline Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `gemini_portrait_name_associator.py` | Associate portraits with names using AI | .md files | JSON files |
| `concatenate_all_md_files.py` | Combine all markdown files | .md files | all_biographies.md |
| `gemini_all_names.py` | Extract person names using AI | all_biographies.md | gemini_all_names.json |
| `extract_all_names.py` | Extract names with text chunks | all_biographies.md + JSON | all_names.csv |
| `merge_portraits.py` | Add portrait filenames to CSV | CSV + JSON files | Enhanced CSV |
| `biography_extractor.py` | Extract structured biographical data | CSV | CSV with bio columns |
| `collect_data.py` | Generate final dataset & stats | CSV | final_dataset.csv |
| `visualize_results.py` | Create quality inspection images | CSV + images | PNG files |

### Utility Scripts

| Script | Purpose |
|--------|---------|
| `config_loader.py` | Load and access JSON configurations |
| `check_keyvault.py` | Verify Azure Key Vault connection |

### Configuration Integration

Python scripts can use the `config_loader` module:

```python
from config_loader import load_config

config = load_config()

# Get AI prompt
prompt = config.get_prompt('portrait_association', 
                          markdown_content=md_text)

# Get Gemini settings
settings = config.get_gemini_settings()
model = settings['model']
temperature = settings['temperature']
```

---

## 🔧 Troubleshooting

### Common Issues

**❌ Azure Key Vault Connection Errors**
```
ERROR: Unable to connect to Azure Key Vault
```
**Solution:** Ensure you're logged into Azure CLI and have proper permissions:
```powershell
az login
az account show  # Verify correct subscription
```

**❌ Import Error: No module named 'google.genai'**
```
ModuleNotFoundError: No module named 'google'
```
**Solution:** Install the correct Google Gemini package:
```powershell
conda activate OCR-Parser
pip install google-genai  # NOT google-generativeai
```

**❌ Images Not Showing in Visualizations**

**Solution:** Verify paths in `pipeline_config.json`:
- `original_images_path` should point to corpus folder
- Portraits should be in `imgs/` subfolders within PaddleOCR output

**❌ JSON Decode Errors from Gemini**

**Solution:** 
1. Check `prompt_config.json` - ensure prompts clearly request JSON output
2. Increase `max_retries` in Gemini settings
3. Lower `temperature` for more consistent responses

**❌ Pipeline Hangs on Specific Step**

**Solution:**
1. Set `suppress_stderr: false` for that step in `pipeline_config.json`
2. Check logs for detailed error messages
3. Verify input files are valid and accessible

### Debug Mode

Enable verbose logging by setting `suppress_stderr: false` for all steps:

```json
{
  "pipeline_steps": {
    "1_portrait_association": {
      "enabled": true,
      "suppress_stderr": false  // Shows full Azure KeyVault logs
    }
  }
}
```

### Checking Intermediate Outputs

Monitor progress by checking intermediate files:
1. After Step 1: Check `*_portrait_associations.json` files
2. After Step 3: Check `gemini_all_names.json`
3. After Step 4: Check `all_names.csv` has names and chunks
4. After Step 6: Check CSV has biography columns filled

---

## 📚 Additional Documentation

- **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)** - Comprehensive configuration guide with examples
- **[prompt_config.json](prompt_config.json)** - View/edit AI prompts directly
- **[pipeline_config.json](pipeline_config.json)** - View/edit pipeline settings

---

## 🎓 Example Use Cases

### Processing a Small Sample

Test the pipeline on 2-3 files first:

```json
{
  "input_files": [
    "path/to/sample1.md",
    "path/to/sample2.md"
  ]
}
```

### Experimenting with Prompts

Edit `prompt_config.json` to test different AI instructions without modifying code. Lower temperature for consistency or raise it for more creative interpretations.

### Skipping Steps

Disable visualization if you only need CSV output:

```json
{
  "pipeline_steps": {
    "8_visualize": {
      "enabled": false
    }
  }
}
```

### Batch Processing Different Collections

Create multiple config files:
- `pipeline_config_collection1.json`
- `pipeline_config_collection2.json`

Then modify `run_pipeline.ps1` to load the specific config.

---

## 📊 Performance Notes

- **Average Processing Time:** ~5-10 seconds per biography (depends on Gemini API latency)
- **API Calls:** 3 Gemini API calls per input file (portrait association, name extraction, biography extraction)
- **Retry Logic:** Automatic retries with exponential backoff on API failures
- **Rate Limiting:** Configurable delay between retries (default: 2 seconds)

---

## 🤝 Contributing

This is an illustration pipeline. For production use:
1. Consider adding validation checks between steps
2. Implement more robust error handling
3. Add unit tests for each script
4. Consider parallel processing for large datasets
5. Add logging to file for audit trails

---

## 📝 License

Part of the MonkeyOCR project. See main repository for license details.

---

## 🙏 Acknowledgments

- **PaddleOCR** for initial OCR processing
- **Google Gemini AI** for biographical data extraction
- **Azure Key Vault** for secure API key management
- **Norwegian Biography Collections** for source data

---

**Version:** 1.0  
**Last Updated:** November 2025  
**Maintained by:** MonkeyOCR Team
