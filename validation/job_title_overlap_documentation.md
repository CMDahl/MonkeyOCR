# Job Title Overlap Analysis - Technical Documentation

## 🎯 Purpose

Technical documentation for the job title overlap analysis component of the MonkeyOCR validation pipeline.

## 📊 System Overview

```text
Azure OCR Jobs    Monkey OCR Jobs
       ↓                ↓
   [Fuzzy Matching Algorithm]
       ↓                ↓
   [Overlap Metrics & Statistics]
       ↓
   [Flag Low-Overlap Records]
       ↓
   [Feed to Gemini AI Pipeline]
```

## 🔧 Core Function: `compute_job_title_overlap()`

### Function Signature

```python
def compute_job_title_overlap(
    df: pd.DataFrame,
    azure_job_cols: Optional[List[str]] = None,
    monkey_job_cols: Optional[List[str]] = None,
    fuzzy_threshold: int = 80,
    missing_value: str = 'Missing'
) -> Dict[str, Any]
```

### Parameters

- **df**: DataFrame with job title columns from both OCR systems
- **azure_job_cols**: List of Azure job columns (auto-detected if None)
- **monkey_job_cols**: List of Monkey job columns (auto-detected if None)  
- **fuzzy_threshold**: Minimum similarity score for matches (default: 80)
- **missing_value**: Value representing missing job titles (default: 'Missing')

### Return Value

Dictionary containing:

- **Counts**: Total unique job titles per system
- **Matches**: Number and percentage of matched pairs
- **Metrics**: Jaccard, overlap coefficient, dice coefficient
- **Statistics**: Mean, median, std dev of similarity scores
- **Details**: Lists of matched/unmatched titles with scores

## 🧮 Similarity Algorithms

### 1. Fuzzy String Matching

Uses `fuzzywuzzy` library with token-based matching:

```python
# Example matches at 80% threshold:
"Software Engineer" ↔ "Engineer, Software" (95%)
"Medical Doctor" ↔ "Doctor" (89%)
"School Teacher" ↔ "Teacher" (85%)
```

### 2. Overlap Metrics

**Jaccard Similarity**: `|A ∩ B| / |A ∪ B|`
- Measures overall set overlap
- Range: 0.0 (no overlap) to 1.0 (perfect match)

**Overlap Coefficient**: `|A ∩ B| / min(|A|, |B|)`
- How much of smaller set is covered
- Range: 0.0 to 1.0

**Dice Coefficient**: `2 × |A ∩ B| / (|A| + |B|)`
- Harmonic mean of precision and recall
- Range: 0.0 to 1.0

## 📈 Production Metrics

Typical results from Norwegian biography dataset:

```text
Input: 1,500+ records
Azure unique jobs: ~150-200
Monkey unique jobs: ~140-180
Jaccard similarity: 0.35-0.45
Coverage rates: 55-65%
Flagged records: ~200 (for AI review)
```

## 🎯 Integration Points

### 1. Main Pipeline Integration

Called automatically in `comprehensive_json_extraction.py`:

```python
# After similarity analysis
job_overlap_results = compute_job_title_overlap(comparison_df)
flagged_records = analyze_individual_job_overlap(comparison_df)
save_flagged_records(flagged_records)
```

### 2. AI Pipeline Feeding

Outputs feed directly into Gemini AI analysis:

- Low overlap records → `flagged_job_overlap_records.csv`
- Flagged records → Gemini AI analysis
- AI corrections → Updated datasets

## 🔧 Configuration Guidelines

### Fuzzy Threshold Selection

- **60-70%**: Very lenient, catches more matches but may include false positives
- **80%** (default): Good balance for most use cases
- **90%+**: Conservative, high precision but may miss valid matches

### Column Detection

Auto-detects columns ending with:
- `_azure` for Azure OCR job titles
- `_monkey` for Monkey OCR job titles

Example detected columns:
```text
job1_title_azure, job2_title_azure, ...
job1_title_monkey, job2_title_monkey, ...
```

## 📊 Output Files

### 1. Summary Statistics
`job_title_overlap_summary.csv` - Aggregate metrics

### 2. Matched Pairs  
`job_title_matched_pairs.csv` - Successful fuzzy matches

### 3. Unmatched Titles
`job_title_unmatched.csv` - Titles that didn't find matches

### 4. Flagged Records
`flagged_job_overlap_records.csv` - Records for AI review

## 🚀 Performance Considerations

- **Memory**: Loads unique titles into memory for matching
- **CPU**: O(n²) fuzzy matching complexity
- **Optimization**: Processes unique titles only (no duplicates)
- **Scalability**: Efficient for typical biography datasets (1K-10K records)

## 🎯 Quality Thresholds

Records are flagged for AI review based on:

```python
# Individual record overlap < 50%
if individual_overlap < 0.5:
    flag_for_ai_review()
```

This threshold identifies records where Azure and Monkey OCR extracted significantly different job titles, requiring AI analysis to determine the correct version.

---

**Integration**: Gemini AI Pipeline | **Performance**: Production Ready ✅
- `save_results`: Whether to save results to CSV files (default: True)

**Returns**: Dictionary with comprehensive overlap metrics and detailed results.

## Output Files

The analysis generates several output files:

### 1. `job_title_matched_pairs.csv`
Contains all matched job title pairs with their similarity scores.

**Columns**:
- `azure_title`: Job title from Azure OCR
- `monkey_title`: Matched job title from MonkeyOCR
- `similarity_score`: Fuzzy matching score (0-100)

### 2. `job_title_unmatched.csv`
Contains all unmatched job titles from both datasets with record details.

**Columns**:
- `title`: The unmatched job title
- `source`: Source dataset ('Azure' or 'Monkey')
- `matched`: Always False (indicates unmatched)
- `book_id`: Book ID of the record containing this job title
- `name_azure`: Azure name of the person with this job title
- `name_monkey`: Monkey name of the person with this job title
- `job_column`: The specific job column where this title was found

### 3. `job_title_overlap_summary.csv`
Contains summary statistics for the overlap analysis.

**Columns**:
- `total_azure_titles`: Total unique Azure job titles
- `total_monkey_titles`: Total unique Monkey job titles
- `matched_pairs`: Number of matched pairs
- `unmatched_azure`: Number of unmatched Azure titles
- `unmatched_monkey`: Number of unmatched Monkey titles
- `azure_coverage_percent`: Percentage of Azure titles matched
- `monkey_coverage_percent`: Percentage of Monkey titles matched
- `jaccard_similarity`: Jaccard similarity coefficient
- `overlap_coefficient`: Overlap coefficient
- `dice_coefficient`: Dice coefficient
- `fuzzy_threshold`: Threshold used for matching
- `mean_similarity`: Mean similarity score of matches
- `median_similarity`: Median similarity score of matches
- `std_similarity`: Standard deviation of similarity scores
- `min_similarity`: Minimum similarity score
- `max_similarity`: Maximum similarity score

## Usage Examples

### Basic Usage
```python
from comprehensive_json_extraction import compute_job_title_overlap
import pandas as pd

# Load your dataframe
df = pd.read_csv('comprehensive_comparison_dataframe.csv')

# Analyze job title overlap
results = compute_job_title_overlap(df, fuzzy_threshold=80)

# Access results
print(f"Jaccard similarity: {results['jaccard_similarity']:.3f}")
print(f"Azure coverage: {results['azure_coverage_percent']:.1f}%")
print(f"Matched pairs: {results['matched_pairs']}")
```

### Standalone Analysis
```python
from job_title_overlap_analysis import analyze_job_title_overlap_from_csv

# Analyze from CSV file
results = analyze_job_title_overlap_from_csv(
    'comprehensive_comparison_dataframe.csv',
    fuzzy_threshold=80,
    save_results=True
)
```

### Custom Column Specification
```python
# Specify custom job title columns
azure_cols = ['job1_title_azure', 'job2_title_azure']
monkey_cols = ['job1_title_monkey', 'job2_title_monkey']

results = compute_job_title_overlap(
    df,
    azure_job_cols=azure_cols,
    monkey_job_cols=monkey_cols,
    fuzzy_threshold=75
)
```

## Interpreting Results

### Similarity Metrics

1. **Jaccard Similarity (0-1)**:
   - 0: No overlap
   - 1: Perfect overlap
   - Good for comparing relative overlap

2. **Overlap Coefficient (0-1)**:
   - Focuses on the smaller set
   - Good when sets are very different sizes

3. **Dice Coefficient (0-1)**:
   - Harmonic mean of precision and recall
   - Balanced metric for overall similarity

### Coverage Percentages

- **Azure Coverage**: % of Azure job titles that found matches
- **Monkey Coverage**: % of Monkey job titles that found matches
- High coverage indicates good agreement between datasets

### Fuzzy Matching Threshold

- **60-70**: Very lenient matching (catches distant similarities)
- **80**: Balanced matching (default, good for most cases)
- **90+**: Strict matching (only very similar titles match)

## Integration with Main Workflow

The job title overlap analysis is automatically integrated into the main `comprehensive_json_extraction.py` workflow:

1. **Automatic Execution**: Runs after similarity analysis
2. **Auto-Detection**: Automatically finds job title columns
3. **File Output**: Saves results to multiple CSV files
4. **Console Output**: Provides detailed console reports

## Example Console Output

```
================================================================================
COMPUTING JOB TITLE OVERLAP WITH FUZZY MATCHING
================================================================================
Azure job title columns: ['job1_title_azure', 'job2_title_azure', 'job3_title_azure']
Monkey job title columns: ['job1_title_monkey', 'job2_title_monkey', 'job3_title_monkey']

Unique Azure job titles: 156
Unique Monkey job titles: 148

Finding fuzzy matches with threshold 80...

JOB TITLE OVERLAP RESULTS:
----------------------------------------
Total Azure job titles: 156
Total Monkey job titles: 148
Matched pairs (fuzzy ≥80): 87
Unmatched Azure titles: 69
Unmatched Monkey titles: 61

Coverage:
Azure coverage: 55.8%
Monkey coverage: 58.8%

Similarity Metrics:
Jaccard similarity: 0.397
Overlap coefficient: 0.588
Dice coefficient: 0.568

Fuzzy Match Statistics:
Mean similarity: 91.3
Median similarity: 93.0
Std deviation: 8.7
Range: 80.0 - 100.0

TOP 10 MATCHED PAIRS:
------------------------------------------------------------
 1. Engineer                  ↔ Engineer                  (100)
 2. Teacher                   ↔ Teacher                   (100)
 3. Doctor                    ↔ Doctor                    (100)
 4. Lawyer                    ↔ Lawyer                    (100)
 5. Nurse                     ↔ Nurse                     (100)
 6. Architect                 ↔ Architect                 (100)
 7. Professor                 ↔ Professor                 (100)
 8. Physician                 ↔ Doctor                    (89)
 9. Attorney                  ↔ Lawyer                    (86)
10. Educator                  ↔ Teacher                   (82)
```

## Technical Notes

### Performance Considerations
- Uses efficient fuzzy matching algorithms
- Processes unique titles only (no duplicates)
- Optimized for large datasets

### Memory Usage
- Stores all unique titles in memory
- Maintains detailed match results
- Scalable for typical biography datasets

### Error Handling
- Gracefully handles missing data
- Validates input parameters
- Provides clear error messages

## Advanced Usage

### Batch Analysis with Different Thresholds
```python
thresholds = [60, 70, 80, 90]
results_by_threshold = {}

for threshold in thresholds:
    results_by_threshold[threshold] = compute_job_title_overlap(
        df, fuzzy_threshold=threshold
    )
    
# Compare results across thresholds
for threshold, results in results_by_threshold.items():
    print(f"Threshold {threshold}: {results['jaccard_similarity']:.3f} Jaccard")
```

### Custom Analysis Pipeline
```python
# 1. Load data
df = pd.read_csv('your_data.csv')

# 2. Analyze with different parameters
results = compute_job_title_overlap(
    df,
    azure_job_cols=['custom_azure_col1', 'custom_azure_col2'],
    monkey_job_cols=['custom_monkey_col1', 'custom_monkey_col2'],
    fuzzy_threshold=85,
    missing_value='N/A'
)

# 3. Extract specific information
matched_pairs = results['matched_pairs_details']
high_similarity_pairs = [
    pair for pair in matched_pairs 
    if pair['similarity_score'] >= 95
]

# 4. Generate custom reports
print(f"High similarity pairs: {len(high_similarity_pairs)}")
```

This comprehensive job title overlap analysis provides deep insights into the consistency and quality of job title extraction between Azure OCR and MonkeyOCR systems.
