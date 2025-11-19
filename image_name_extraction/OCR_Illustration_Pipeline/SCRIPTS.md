# Python Scripts Documentation

This document provides detailed information about each Python script in the OCR Illustration Pipeline.

## Table of Contents
- [Core Pipeline Scripts](#core-pipeline-scripts)
- [Utility Scripts](#utility-scripts)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)

---

## Core Pipeline Scripts

### 1. gemini_portrait_name_associator.py

**Purpose:** Associate portrait images with person names using Google Gemini AI

**Usage:**
```bash
python gemini_portrait_name_associator.py <input_directory> <output_directory>
```

**Arguments:**
- `input_directory`: Directory containing markdown files
- `output_directory`: Where to save JSON association files

**Process:**
1. Reads each markdown file
2. Identifies portrait references: `<img src="imgs/filename.jpg">`
3. Sends text + portrait list to Gemini AI
4. AI determines which person each portrait depicts
5. Saves associations as JSON

**Output Format:**
```json
{
  "book_id": "digibok_2007031501007_0154",
  "portraits": [
    {
      "filename": "img_in_image_box_173.jpg",
      "person_name": "FLUGE Frithjof"
    }
  ]
}
```

**Key Features:**
- Retry logic (3 attempts with backoff)
- JSON response validation
- Handles multiple portraits per page
- Configurable via `prompt_config.json`

**Dependencies:**
- `google-genai` (Google Gemini SDK)
- `azure-identity`, `azure-keyvault-secrets` (API key management)
- `config_loader` (configuration access)

---

### 2. concatenate_all_md_files.py

**Purpose:** Combine multiple markdown files into a single document

**Usage:**
```bash
python concatenate_all_md_files.py <input_directory> <output_file>
```

**Arguments:**
- `input_directory`: Directory containing .md files
- `output_file`: Path to save concatenated markdown

**Process:**
1. Scans directory for `.md` files
2. Sorts files alphabetically
3. Concatenates with book_id separators

**Output Format:**
```markdown
# === digibok_2007031501007_0154 ===

[Original markdown content]

# === digibok_2007031501007_0155 ===

[Original markdown content]
```

**Key Features:**
- Preserves original formatting
- Adds clear delimiters between documents
- Alphabetical ordering

---

### 3. gemini_all_names.py

**Purpose:** Extract all person names from concatenated biographical text using Gemini AI

**Usage:**
```bash
python gemini_all_names.py <input_markdown> <output_json>
```

**Arguments:**
- `input_markdown`: Concatenated markdown file from Step 2
- `output_json`: Path to save extracted names JSON

**Process:**
1. Reads full concatenated markdown
2. Sends to Gemini with name extraction prompt
3. AI extracts all person names
4. Validates and saves JSON

**Output Format:**
```json
{
  "names": [
    "FLUGE Frithjof",
    "FLØRENES Leif Kristian",
    "FLØRENES Torlaug"
  ]
}
```

**Key Features:**
- Handles Norwegian name formats
- Filters duplicates
- Retry logic for API failures
- Configurable via `prompt_config.json`

---

### 4. extract_all_names.py

**Purpose:** Extract names with surrounding text chunks for context

**Usage:**
```bash
python extract_all_names.py <input_markdown> <names_json> <output_csv>
```

**Arguments:**
- `input_markdown`: Concatenated markdown file
- `names_json`: JSON file from Step 3
- `output_csv`: Path to save CSV with names and chunks

**Process:**
1. Reads names from JSON
2. Searches markdown for each name
3. Extracts surrounding context (configurable length)
4. Associates name with book_id
5. Saves to CSV

**Output Format (CSV):**
```csv
name,book_id,text_chunk
"FLUGE Frithjof","digibok_2007031501007_0154","FLUGE, Frithjof, f. 1940..."
```

**Key Features:**
- Configurable context length (`extraction_rules.context_length_chars`)
- Handles multiple occurrences of same name
- Book ID extraction from delimiters
- Chunk length limits (min/max)

**Configuration:**
See `prompt_config.json` → `extraction_rules`:
```json
{
  "extraction_rules": {
    "min_text_chunk_length": 100,
    "max_text_chunk_length": 3000,
    "context_length_chars": 500
  }
}
```

---

### 5. merge_portraits.py

**Purpose:** Merge portrait associations from JSON into the CSV

**Usage:**
```bash
python merge_portraits.py <csv_file> <json_directory> <output_csv>
```

**Arguments:**
- `csv_file`: CSV from Step 4 (all_names.csv)
- `json_directory`: Directory containing portrait JSON files from Step 1
- `output_csv`: Path to save enhanced CSV

**Process:**
1. Reads all portrait association JSON files
2. Creates mapping: (book_id, name) → portrait_filename
3. Loads CSV
4. Adds `portrait_filename` column
5. Matches based on book_id and name
6. Saves enhanced CSV

**Output:** Adds `portrait_filename` column to CSV

**Key Features:**
- Fuzzy name matching (case-insensitive)
- Handles missing portraits gracefully
- Preserves all original CSV data
- Reports match statistics

---

### 6. biography_extractor.py

**Purpose:** Extract structured biographical data using Gemini AI

**Usage:**
```bash
python biography_extractor.py <input_csv> <output_csv>
```

**Arguments:**
- `input_csv`: CSV with names and text chunks
- `output_csv`: Path to save enhanced CSV with biography fields

**Process:**
1. Reads CSV row by row
2. For each person:
   - Sends name + text_chunk to Gemini
   - AI extracts structured fields
   - Validates JSON response
   - Retries on failure
3. Adds biography columns to CSV
4. Saves enhanced CSV

**Output Columns Added:**
- `birth_year`
- `death_year`
- `birth_place`
- `occupation`
- `education`
- `achievements`
- `family`
- `summary`

**Key Features:**
- Robust retry logic (3 attempts)
- JSON validation
- Error logging
- Progress tracking
- Configurable via `prompt_config.json`

**Typical Runtime:** 5-10 seconds per person (API latency)

---

### 7. collect_data.py

**Purpose:** Generate final dataset and statistics summary

**Usage:**
```bash
python collect_data.py <input_csv> <output_csv>
```

**Arguments:**
- `input_csv`: Enhanced CSV from Step 6
- `output_csv`: Path to save final dataset

**Process:**
1. Reads enhanced CSV
2. Calculates statistics:
   - Total entries
   - Entries with portraits
   - Entries with birth years
   - Entries with occupations
   - etc.
3. Prints summary to console
4. Saves cleaned final dataset

**Output:**
- `final_dataset.csv` - Final cleaned dataset
- Console output with statistics

**Example Output:**
```
Dataset Statistics:
  Total entries: 5
  Entries with portraits: 5 (100.0%)
  Entries with birth years: 4 (80.0%)
  Entries with occupations: 5 (100.0%)
  Average text chunk length: 452 characters
```

---

### 8. visualize_results.py

**Purpose:** Generate quality inspection visualizations

**Usage:**
```bash
python visualize_results.py <csv_file> <original_images_path> <portrait_base_folder> <output_folder>
```

**Arguments:**
- `csv_file`: Final dataset CSV
- `original_images_path`: Corpus folder with full-page images
- `portrait_base_folder`: Base folder for portrait imgs/ subfolders
- `output_folder`: Where to save PNG visualizations

**Process:**
1. Reads final CSV
2. For each entry:
   - Loads full-page image from corpus
   - Loads portrait image
   - Extracts biographical data
   - Creates 3-column visualization
3. Saves PNG files

**Visualization Layout:**
```
┌─────────────┬─────────────┬─────────────┐
│   Full      │  Portrait   │   Text      │
│  Biography  │     +       │   Chunk     │
│    Page     │  Structured │             │
│   (scan)    │    Data     │             │
└─────────────┴─────────────┴─────────────┘
```

**Output Files:**
```
test_images/
├── digibok_2007031501007_0154_01_FLUGE Frithjof.png
├── digibok_2007031501007_0155_01_FLØRENES Leif Kristian.png
└── ...
```

**Key Features:**
- Handles missing images gracefully
- Multiple image format support (jpg, jp2, png)
- Automatic layout sizing
- Text wrapping for long data fields
- High-quality PNG output (20x10 inches)

**Dependencies:**
- `matplotlib` (plotting)
- `pillow` (image loading)
- `pandas` (CSV reading)

---

## Utility Scripts

### config_loader.py

**Purpose:** Centralized configuration loading and access

**Usage:**
```python
from config_loader import load_config

config = load_config()

# Get formatted prompt
prompt = config.get_prompt('biography_extraction', 
                          name="John Doe",
                          text_chunk="...")

# Get system instruction
system_msg = config.get_system_instruction('portrait_association')

# Get Gemini settings
settings = config.get_gemini_settings()
model = settings['model']          # "gemini-2.5-flash"
temp = settings['temperature']     # 0.05

# Get extraction rules
rules = config.get_extraction_rules()
max_chunk = rules['max_text_chunk_length']  # 3000
```

**Features:**
- Lazy loading (configs loaded on first access)
- Caching (configs loaded once)
- Template formatting (supports `{variable}` substitution)
- Handles both string and array formats for prompts
- Error messages for missing configs

**Configuration Files:**
- Loads: `pipeline_config.json`, `prompt_config.json`
- Location: Same directory as the importing script

---

### check_keyvault.py

**Purpose:** Verify Azure Key Vault connection and API key access

**Usage:**
```bash
python check_keyvault.py
```

**Process:**
1. Tests Azure authentication
2. Connects to Key Vault
3. Attempts to retrieve Gemini API key
4. Reports success/failure

**Output:**
```
✓ Azure authentication successful
✓ Connected to Key Vault
✓ Retrieved Gemini API key
✓ All checks passed
```

**Use Case:** Debugging authentication issues before running the pipeline

---

## Common Patterns

### Azure Key Vault Access

All Gemini scripts use this pattern:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Connect to Key Vault
credential = DefaultAzureCredential()
vault_url = "https://llmapikey.vault.azure.net/"
client = SecretClient(vault_url=vault_url, credential=credential)

# Retrieve API key
secret = client.get_secret("Gemini-API-key")
api_key = secret.value

# Configure Gemini client
gemini_client = genai.Client(api_key=api_key)
```

### Gemini API Call with Retry

```python
def call_gemini_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.05,
                    response_mime_type='application/json'
                )
            )
            return json.loads(response.text)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
```

### CSV Processing

```python
import pandas as pd

# Read CSV
df = pd.read_csv('input.csv')

# Add new column
df['new_column'] = df.apply(lambda row: process_row(row), axis=1)

# Save CSV
df.to_csv('output.csv', index=False)
```

---

## Error Handling

### Common Errors

**1. Azure Authentication Failure**
```
azure.core.exceptions.ClientAuthenticationError
```
**Solution:** Run `az login` and verify subscription

**2. Gemini API Errors**
```
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```
**Solution:** Wait and retry, or increase `retry_delay_seconds` in config

**3. JSON Parsing Errors**
```
json.decoder.JSONDecodeError: Expecting value
```
**Solution:** AI didn't return valid JSON. Check prompt clarity or increase retries.

**4. File Not Found**
```
FileNotFoundError: [Errno 2] No such file or directory
```
**Solution:** Verify paths in `pipeline_config.json` are absolute and correct

### Debugging Tips

1. **Enable verbose logging:**
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check intermediate outputs:** Each step saves files - verify they exist and are valid

3. **Test with small dataset:** Run on 1-2 files first to verify setup

4. **Use `check_keyvault.py`:** Verify Azure connection before running full pipeline

5. **Monitor API quotas:** Check Gemini API usage in Google Cloud Console

---

## Performance Optimization

### Parallel Processing (Future Enhancement)

Current pipeline is sequential. For large datasets, consider:

```python
from concurrent.futures import ThreadPoolExecutor

def process_file(file_path):
    # Process single file
    pass

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_file, file_paths))
```

### Batch API Calls

Instead of one API call per biography, batch multiple requests:

```python
# Current: 1 call per person
for person in people:
    result = call_gemini(person)

# Optimized: Batch processing
batch_prompt = "\n\n".join([format_prompt(p) for p in people[:10]])
batch_result = call_gemini(batch_prompt)
```

### Caching

Cache Gemini responses to avoid re-processing:

```python
import hashlib
import json

def cached_gemini_call(prompt, cache_dir='cache'):
    # Generate cache key
    key = hashlib.md5(prompt.encode()).hexdigest()
    cache_file = f"{cache_dir}/{key}.json"
    
    # Check cache
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f)
    
    # Call API
    result = call_gemini(prompt)
    
    # Save to cache
    with open(cache_file, 'w') as f:
        json.dump(result, f)
    
    return result
```

---

## Script Dependencies

```
gemini_portrait_name_associator.py
├── google-genai
├── azure-identity
├── azure-keyvault-secrets
└── config_loader (optional)

gemini_all_names.py
├── google-genai
├── azure-identity
├── azure-keyvault-secrets
└── config_loader (optional)

biography_extractor.py
├── google-genai
├── azure-identity
├── azure-keyvault-secrets
├── pandas
└── config_loader (optional)

visualize_results.py
├── matplotlib
├── pillow
└── pandas

All other scripts
└── pandas (for CSV processing)
```

---

## Version History

**v1.0** (November 2025)
- Initial release
- Configuration file support
- 8-step pipeline
- Gemini AI integration
- Quality inspection visualizations

---

For more information, see:
- [README.md](README.md) - Main documentation
- [CONFIG_GUIDE.md](CONFIG_GUIDE.md) - Configuration details
- [prompt_config.json](prompt_config.json) - AI prompts
- [pipeline_config.json](pipeline_config.json) - Pipeline settings
