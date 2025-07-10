# MonkeyOCR Validation - Production Tools

Essential production tools for OCR validation and job analysis.

## 🎯 What This Does

Compare Azure OCR and Monkey OCR results, identify discrepancies, and use AI to create the most accurate dataset.

## 📊 Simple Workflow

```text
[Azure Data] + [Monkey Data] 
       ↓
   [Compare & Link Records]
       ↓
   [Find Job Title Differences]
       ↓
   [AI Analysis with Gemini]
       ↓
   [Best Combined Dataset]
```

## 🛠️ Essential Tools

| Script | What It Does | How Long |
|--------|--------------|----------|
| `comprehensive_json_extraction.py` | Links and compares Azure/Monkey data | 5-10 min |
| `gemini_job_resolver.py` | AI fixes job title problems | 2-3 hours |
| `run_gemini_batch_analysis.py` | Runs large batches | Variable |
| `analyze_gemini_results.py` | Creates summary reports | 2-3 min |

## 🚀 Quick Commands

### Test Run (5 records)

```bash
python gemini_job_resolver.py --max-records 5 --output-dir test_run
```

### Full Production Run

```bash
# Step 1: Compare data (once)
python comprehensive_json_extraction.py

# Step 2: AI correction with output files
python gemini_job_resolver.py --output-dir production_run --create-corrections
```

## 📁 What You Get

**Input:**

- Azure OCR CSV files
- Monkey OCR CSV files

**Processing:**

- `comprehensive_comparison_dataframe.csv` (merged data)
- `flagged_job_overlap_records.csv` (problems found)

**Results:**

- `gemini_analysis_complete/` (AI analysis details)
- `azure_corrected.csv` (improved Azure data)
- `monkey_corrected.csv` (improved Monkey data)
- `unified_best_of_both.csv` (best combined dataset)

## 🎯 Key Benefits

- **Automated Linking**: Finds matching people across different OCR systems
- **Quality Analysis**: Identifies which OCR system is more accurate for each record
- **AI Correction**: Uses Google AI to resolve job title conflicts
- **Best of Both**: Creates a single dataset with the best elements from each system
- **Full Tracking**: Keeps records of all changes made

## ⚡ Typical Results

- Process 1,500+ biographical records
- Find ~200 records with job title problems
- AI successfully corrects 95%+ of issues
- Final dataset is more accurate than either original

## 🔧 Setup

Requirements:

- Python with pandas
- Google Gemini API key
- Input CSV files from Azure and Monkey OCR

All scripts have built-in help:

```bash
python [script_name].py --help
```
