# MonkeyOCR Validation Tools

This repository contains validation and processing tools for the MonkeyOCR project, with a particular focus on extracting figure references from OCR-processed text and generating corresponding image filenames.

## 🎯 Main Focus: Figure Extraction (`figure_extraction.py`)

The core functionality of this validation toolkit is the **figure extraction system** that processes OCR text to identify and extract figure references, creating structured metadata for image linking.

### Key Features

- **Figure Reference Extraction**: Automatically identifies figure references in formats like `**[Figure: 1.1]**` and `**[FIGURE: 2.3]**`
- **Case-Insensitive Matching**: Handles both `[Figure:` and `[FIGURE:` while preserving original case
- **Image Filename Generation**: Creates Azure-compatible image filenames by combining book IDs with figure numbers
- **Dual Reference Support**: Extracts first and second figure occurrences per text chunk
- **Robust Error Handling**: Gracefully manages missing values and malformed references
- **Comprehensive Reporting**: Provides detailed statistics and processing summaries

### 📊 Results from Real Data

When tested on the Norwegian biography dataset:

- **Total rows processed**: 1,541
- **Rows with figure references**: 837 (54.3%)
- **Total figure references found**: 9,932
- **First figure references**: 837 rows
- **Second figure references**: 135 rows

## 🔧 Installation & Setup

### Prerequisites

```bash
pip install pandas
```

### Quick Start

```python
import pandas as pd
from figure_extraction import extract_figure_references

# Load your data
df = pd.read_csv('your_data.csv')

# Extract figure references and create image filenames
result = extract_figure_references(df, text_column='markdown_chunk_azureocr')

# Save results
result.to_csv('output_with_figures.csv', index=False)
```

## 📖 Detailed Usage Guide

### Basic Usage

```python
from figure_extraction import extract_figure_references

# Standard usage with default parameters
df_with_figures = extract_figure_references(df)
```

### Advanced Configuration

```python
# Custom configuration
result = extract_figure_references(
    df,
    text_column='your_text_column',           # Column containing text to search
    figure1_column='FirstFigure',             # Name for first figure column
    figure2_column='SecondFigure',            # Name for second figure column
    book_id_column='your_book_id_column',     # Column with book IDs
    missing_value='No Figure Found',          # Value for missing figures
    create_image_columns=True                 # Enable image filename generation
)
```

### Convenience Functions

```python
# Simple integration
from figure_extraction import add_figure_columns_to_dataframe

df_with_figures = add_figure_columns_to_dataframe(df)

# File processing with I/O
from figure_extraction import process_your_data

result = process_your_data(
    'input.csv',
    text_column='markdown_chunk_azureocr',
    output_path='output.csv'
)
```

## 🎮 Function Reference

### `extract_figure_references()`

**Main function for figure extraction and image filename generation.**

#### Parameters

- `df` (pd.DataFrame): DataFrame containing text data
- `text_column` (str): Column name containing text to search (default: 'markdown_chunk_azureocr')
- `figure1_column` (str): Column name for first figure reference (default: 'Figure1')
- `figure2_column` (str): Column name for second figure reference (default: 'Figure2')
- `missing_value` (str): Value for missing references (default: 'Missing value')
- `book_id_column` (str): Column name containing book IDs (default: 'book_id')
- `create_image_columns` (bool): Whether to create image filename columns (default: True)

#### Returns

- `pd.DataFrame`: Original DataFrame with added columns:
  - `Figure1`: First figure reference found
  - `Figure2`: Second figure reference found
  - `azure_image1`: Image filename for first figure
  - `azure_image2`: Image filename for second figure

#### Example Output

```text
book_id: digibok_2007031501007_0057
Figure1: **[FIGURE: 1.2]**
azure_image1: digibok_2007031501007_0057_1.2.png
Figure2: **[FIGURE: 1.3]**
azure_image2: digibok_2007031501007_0057_1.3.png
```

### `find_all_figure_references()`

**Exploratory function to analyze all figure references in your data.**

Returns detailed information about every figure reference found, including position and occurrence number.

### `quick_figure_check()`

**Quick diagnostic function to check if your data contains figure references.**

```python
from figure_extraction import quick_figure_check

stats = quick_figure_check(df, text_column='markdown_chunk_azureocr')
```

Returns statistics about figure reference coverage in your dataset.

### `demonstrate_figure_extraction()`

**Built-in demonstration with sample data.**

Run this function to see how the extraction works with test data.

## 🔍 Pattern Recognition

The system recognizes figure references using this regex pattern:

```regex
\*\*\[(?:Figure|FIGURE):\s*(\d+\.\d+)\]\*\*
```

### Supported Formats

- `**[Figure: 1.1]**` (mixed case)
- `**[FIGURE: 2.3]**` (uppercase)
- `**[Figure: 10.25]**` (multi-digit numbers)

### Pattern Components

- `\*\*` - Literal asterisks at start
- `\[` - Opening bracket
- `(?:Figure|FIGURE)` - Case-insensitive figure keyword
- `:\s*` - Colon followed by optional whitespace
- `(\d+\.\d+)` - Captured figure number (e.g., "1.2")
- `\]` - Closing bracket
- `\*\*` - Literal asterisks at end

## 🧪 Testing & Validation

### Test Files Available

1. **`test_figure_extraction_fix.py`** - Integration test with real data
2. **`final_verification.py`** - Comprehensive validation script
3. **`test_image_filename_generation.py`** - Unit tests for filename generation
4. **`final_comprehensive_test.py`** - Complete requirements testing

### Running Tests

```bash
# Run integration test
python test_figure_extraction_fix.py

# Run comprehensive validation
python final_verification.py

# Run built-in demonstration
python figure_extraction.py
```

## 📁 Project Structure

```text
validation/
├── figure_extraction.py              # Main extraction logic
├── test_figure_extraction_fix.py     # Integration tests
├── final_verification.py             # Comprehensive validation
├── test_image_filename_generation.py # Unit tests
├── final_comprehensive_test.py       # Requirements testing
├── verify_azure_columns.py          # Column verification
├── biography_json_comparisons.py    # Biography comparison tools
├── debug_figure_extraction.py       # Debug utilities
└── readme.md                        # This file
```

## 🎯 Real-World Example

Here's how the system was used on the Norwegian biography dataset:

```python
# Load the three-way merged comparison data
df = pd.read_csv('comparison_threeway_merged.csv')

# Extract figure references from Azure OCR text
result = extract_figure_references(df, text_column='markdown_chunk_azureocr')

# Results: 837 rows with figures, 9,932 total references found
# Output includes Figure1, Figure2, azure_image1, azure_image2 columns
```

## 🔧 Technical Details

### Image Filename Generation Logic

```python
def create_image_filename(book_id, figure_number):
    """Create image filename from book_id and figure number"""
    if pd.isna(book_id) or pd.isna(figure_number) or figure_number is None:
        return 'Missing value'
    return f"{book_id}_{figure_number}.png"
```

### Error Handling

- Gracefully handles `NaN` and empty text values
- Preserves original DataFrame structure
- Provides meaningful default values for missing data
- Comprehensive logging and progress reporting

### Performance Considerations

- Processes 1,500+ rows efficiently
- Uses compiled regex patterns for speed
- Minimal memory footprint with in-place operations
- Detailed progress reporting for large datasets

## 📝 Output Format

The system adds four new columns to your DataFrame:

| Column | Description | Example |
|--------|-------------|---------|
| `Figure1` | First figure reference found | `**[FIGURE: 1.2]**` |
| `Figure2` | Second figure reference found | `**[FIGURE: 1.3]**` |
| `azure_image1` | Image filename for first figure | `digibok_2007031501007_0057_1.2.png` |
| `azure_image2` | Image filename for second figure | `digibok_2007031501007_0057_1.3.png` |

## 🤝 Contributing

This is part of the MonkeyOCR validation toolkit. The figure extraction functionality is production-ready and has been tested on real Norwegian biography data.

## 📄 License

Part of the MonkeyOCR project validation tools.

---

**Last Updated**: July 2025  
**Tested On**: Norwegian Biography Dataset (1,541 rows, 9,932 figure references)  
**Status**: Production Ready ✅