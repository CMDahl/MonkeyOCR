# MonkeyOCR Validation - Quick Reference

## 🎯 What This Project Does

Takes OCR results from two systems (Azure + Monkey), compares them, and uses AI to create the best possible dataset.

## 📊 Simple Process Flow

```text
Azure OCR Data ──┐
                 ├─→ Compare & Link ──→ Find Problems ──→ AI Fix ──→ Best Dataset
Monkey OCR Data ─┘
```

## ⚡ Quick Start

```bash
# Test with 5 records (2 minutes)
python gemini_job_resolver.py --max-records 5 --output-dir test

# Full production run (2-3 hours)
python gemini_job_resolver.py --create-corrections --output-dir production
```

## 📁 Main Files

### Essential Scripts

- `comprehensive_json_extraction.py` - Links Azure & Monkey data
- `gemini_job_resolver.py` - AI-powered corrections
- `run_gemini_batch_analysis.py` - Batch processing
- `analyze_gemini_results.py` - Results analysis

### Data Files

- `comprehensive_comparison_dataframe.csv` - Linked comparison data
- `flagged_job_overlap_records.csv` - Records needing AI review
- `gemini_analysis_complete/` - AI analysis results

### Documentation

- `README_CLEAN.md` - Detailed production guide
- `JOB_TITLE_OVERLAP_SUMMARY.md` - Analysis summary
- `job_title_overlap_documentation.md` - Technical details

## 🎯 Results

- **Input**: 1,500+ biographical records from 2 OCR systems
- **AI Analysis**: ~200 records with job title conflicts  
- **Output**: Single high-quality dataset combining best of both systems
- **Success Rate**: 95%+ accurate corrections

## 🔧 Requirements

- Python with pandas
- Google Gemini API key (for AI corrections)
- CSV files from Azure and Monkey OCR systems

## 📞 Help

All scripts have built-in help:

```bash
python [script-name].py --help
```

---

**Status**: Production Ready ✅ | **Updated**: July 2025
