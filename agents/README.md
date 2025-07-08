# Azure Document Intelligence OCR Tool

This tool processes document images using Azure Document Intelligence to extract text content and figures, generating markdown files and saving raw JSON results.

## Features

- 📄 **Text Extraction**: Converts document images to structured markdown
- 🖼️ **Figure Extraction**: Saves embedded figures as separate PNG files
- 💾 **JSON Export**: Stores raw Azure Document Intelligence results
- 🔄 **Smart Caching**: Reuses existing JSON files to save processing time and costs
- 📊 **Batch Processing**: Process single files, ranges, or custom lists
- 🎯 **Flexible Input**: Works with numbered document sequences

## Prerequisites

1. **Azure Document Intelligence**: Set up an Azure Document Intelligence resource
2. **Python Environment**: Python 3.8+ with required packages
3. **Key Vault**: Configure `key_vault.py` with your Azure credentials

### Required Python Packages
```bash
pip install azure-ai-documentintelligence azure-core
```

## Configuration

Create a `key_vault.py` file with your Azure credentials:
```python
class KeyVault:
    def get_key(self, key_name):
        keys = {
            "SDUAzureDocIntelligenceEndpoint": "https://your-endpoint.cognitiveservices.azure.com/",
            "SDUAzureDocIntelligenceKey": "your-api-key-here"
        }
        return keys.get(key_name)
```

## Usage

### Basic Syntax
```bash
python AzureOCR_extracting_text_and_figures.py --input <folder_path> [options] --output <output_folder>
```

### Processing Modes

#### 1. Single File Processing
```bash
python AzureOCR_extracting_text_and_figures.py \
  --input "D:/data/corpus/digibok_2007031501007" \
  --single "0115" \
  --output "output_folder" \
  --use-json
```

#### 2. Range Processing
```bash
python AzureOCR_extracting_text_and_figures.py \
  --input "D:/data/corpus/digibok_2007031501007" \
  --start "0057" \
  --end "0494" \
  --output "output_folder" \
  --use-json
```

#### 3. Custom List Processing
```bash
python AzureOCR_extracting_text_and_figures.py \
  --input "D:/data/corpus/digibok_2007031501007" \
  --list "0067,0097,0148,0169" \
  --output "output_folder" \
  --use-json
```

#### 4. Predefined Failed List
```bash
python AzureOCR_extracting_text_and_figures.py \
  --input "D:/data/corpus/digibok_2007031501007" \
  --list "failed" \
  --output "output_folder" \
  --use-json
```

## Arguments

| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--input` | `-i` | Input folder path containing JPG files | ✅ |
| `--output` | `-o` | Output folder for results | ✅ |
| `--single` | | Process single file by 4-digit number | |
| `--start` | `-s` | Starting 4-digit number for range | |
| `--end` | `-e` | Ending 4-digit number for range | |
| `--list` | | Comma-separated list or "failed" | |
| `--use-json` | | Use existing JSON files if available | |

## File Naming Convention

The tool expects files named with this pattern:
```
{folder_name}_{4-digit-number}.jpg
```

**Example:**
- Folder: `digibok_2007031501007`
- Files: `digibok_2007031501007_0057.jpg`, `digibok_2007031501007_0058.jpg`, etc.

## Output Structure

```
output_folder/
├── figures/
│   ├── digibok_2007031501007_0115_figure.0.png
│   ├── digibok_2007031501007_0115_figure.1.png
│   └── ...
├── digibok_2007031501007_0115.md
├── digibok_2007031501007_0115.json
└── ...
```

### Output Files

1. **Markdown Files (`.md`)**: Structured text content with figure placeholders
2. **JSON Files (`.json`)**: Raw Azure Document Intelligence results
3. **Figure Files (`.png`)**: Extracted images in `figures/` subfolder

## Smart Caching Feature

When `--use-json` is enabled:
- ✅ Reuses existing JSON files instead of calling Azure API
- 💰 Saves processing costs and time
- 🔄 Still generates fresh markdown from cached data
- ⚠️ Reports missing figure files

## Example Workflows

### Initial Processing
```bash
# Process all files in range and save JSON for future use
python AzureOCR_extracting_text_and_figures.py \
  --input "D:/data/corpus/digibok_2007031501007" \
  --start "0057" \
  --end "0494" \
  --output "results"
```

### Reprocessing with Cached Data
```bash
# Regenerate markdown from existing JSON (no API calls)
python AzureOCR_extracting_text_and_figures.py \
  --input "D:/data/corpus/digibok_2007031501007" \
  --list "0067,0097,0148" \
  --output "results" \
  --use-json
```

### Processing Failed Files
```bash
# Process predefined list of problematic files
python AzureOCR_extracting_text_and_figures.py \
  --input "D:/data/corpus/digibok_2007031501007" \
  --list "failed" \
  --output "results" \
  --use-json
```

## Figure Placeholders

In the generated markdown, figures appear as:
```markdown
**[FIGURE: figure.0]**
```

These placeholders correspond to saved PNG files in the `figures/` folder.

## Error Handling

- ⚠️ **Missing Files**: Reports files that don't exist and continues processing
- ❌ **Processing Errors**: Logs errors and provides summary statistics
- 🔄 **Fallback**: Falls back to API processing if JSON reading fails

## Predefined Failed List

The tool includes a predefined list of files that had issues during concatenation:
- `digibok_2007031501007_0067.md`
- `digibok_2007031501007_0097.md`
- `digibok_2007031501007_0148.md`
- `digibok_2007031501007_0169.md`
- `digibok_2007031501007_0190.md`
- `digibok_2007031501007_0199.md`
- `digibok_2007031501007_0216.md`
- `digibok_2007031501007_0253.md`
- `digibok_2007031501007_0315.md`
- `digibok_2007031501007_0430.md`
- `digibok_2007031501007_0465.md`

Use `--list "failed"` to reprocess these specific files.

## Troubleshooting

### Common Issues

1. **Missing Azure Credentials**: Ensure `key_vault.py` is properly configured
2. **File Not Found**: Check file naming convention matches expected pattern
3. **JSON Reading Errors**: Script will fallback to API processing automatically
4. **Permission Errors**: Ensure write access to output folder

### Debug Information

The script provides verbose output including:
- Number of sections, paragraphs, and figures found
- Processing status for each file
- Final summary statistics

## Performance Tips

- Use `--use-json` for reprocessing to avoid redundant API calls
- Process files in batches rather than individually
- Monitor Azure usage to manage costs

## Environment

Recommended environment setup:
```bash
# Create virtual environment
python -m venv MonkeyOCR
source MonkeyOCR/bin/activate  # On Windows: MonkeyOCR\Scripts\activate

# Install dependencies
pip install azure-ai-documentintelligence azure-core
```
