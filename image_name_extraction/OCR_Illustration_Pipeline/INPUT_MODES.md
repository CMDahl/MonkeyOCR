# Input Configuration Quick Reference

## Overview

The OCR Illustration Pipeline supports three flexible input modes to accommodate different use cases from small samples to production-scale processing.

---

## Input Modes

### 1️⃣ Files Mode

**When to use:** Specific test cases, curated selections, small samples

**Configuration:**
```json
{
  "input": {
    "mode": "files",
    "files": [
      "C:\\path\\to\\file1.md",
      "C:\\path\\to\\file2.md",
      "C:\\path\\to\\file3.md"
    ]
  }
}
```

**Behavior:**
- Processes exactly the files you specify
- No automatic discovery
- Full control over what gets processed

**Example use case:**
- Testing specific problematic files
- Processing a handpicked selection
- Quality checks on sample data

---

### 2️⃣ Folders Mode

**When to use:** Production runs, bulk processing, automated workflows

**Configuration:**
```json
{
  "input": {
    "mode": "folders",
    "folders": [
      {
        "path": "C:\\data\\collection1",
        "pattern": "**/*.md",
        "recursive": true,
        "description": "Main biography collection"
      },
      {
        "path": "C:\\data\\collection2",
        "pattern": "**/*.md",
        "recursive": false,
        "description": "Supplementary biographies (top-level only)"
      }
    ]
  }
}
```

**Folder configuration options:**
- `path` (required): Directory to scan
- `pattern`: File matching pattern (default: `**/*.md`)
- `recursive`: Scan subdirectories (default: `true`)
- `description`: Human-readable note

**Behavior:**
- Automatically discovers all `.md` files
- Scans multiple directories
- Can combine recursive and non-recursive scans

**Example use case:**
- Processing entire book collections
- Nightly batch jobs
- Complete corpus analysis

---

### 3️⃣ Mixed Mode

**When to use:** Priority files + bulk processing

**Configuration:**
```json
{
  "input": {
    "mode": "mixed",
    "files": [
      "C:\\priority\\important_bio.md",
      "C:\\priority\\reference_case.md"
    ],
    "folders": [
      {
        "path": "C:\\data\\main_collection",
        "recursive": true
      }
    ]
  }
}
```

**Behavior:**
- Includes all specified files
- Plus all discovered files from folders
- Deduplicates automatically (if same file listed twice)

**Example use case:**
- Ensure specific files are always included
- Add test cases to production run
- Combine manual curation with automation

---

## Filters

Apply filters to any mode to refine file selection:

```json
{
  "input": {
    "mode": "folders",
    "folders": [...],
    "filters": {
      "exclude_patterns": [
        "*_backup*",
        "*_temp*",
        "*_draft*",
        "*_old_*"
      ],
      "min_file_size_bytes": 100,
      "max_files": 1000
    }
  }
}
```

### Filter Options

| Filter | Type | Description | Default |
|--------|------|-------------|---------|
| `exclude_patterns` | Array of strings | Skip files matching these glob patterns | `[]` |
| `min_file_size_bytes` | Integer | Skip files smaller than this | No limit |
| `max_files` | Integer or null | Limit total files processed (useful for testing) | No limit |

### Exclude Pattern Examples

```json
{
  "exclude_patterns": [
    "*_backup*",        // Skip: bio_backup.md, backup_bio.md
    "*_temp*",          // Skip: temp_file.md, bio_temp_2024.md
    "*test*",           // Skip: test.md, bio_test.md
    "*_draft*",         // Skip: draft_bio.md
    "*.bak",            // Skip: bio.md.bak
    "*_2023_*"          // Skip: bio_2023_old.md
  ]
}
```

---

## Common Scenarios

### Scenario 1: Quick Test (2 files)

```json
{
  "input": {
    "mode": "files",
    "files": [
      "C:\\test\\bio1.md",
      "C:\\test\\bio2.md"
    ]
  }
}
```

### Scenario 2: Process One Collection

```json
{
  "input": {
    "mode": "folders",
    "folders": [
      {
        "path": "V:\\collections\\digibok_2007031501007",
        "recursive": true
      }
    ]
  }
}
```

### Scenario 3: Process Multiple Collections

```json
{
  "input": {
    "mode": "folders",
    "folders": [
      {
        "path": "V:\\collections\\digibok_2007031501007",
        "recursive": true,
        "description": "2007 collection - 1,234 biographies"
      },
      {
        "path": "V:\\collections\\digibok_2011052606015",
        "recursive": true,
        "description": "2011 collection - 856 biographies"
      },
      {
        "path": "V:\\collections\\digibok_2012101206017",
        "recursive": true,
        "description": "2012 collection - 1,045 biographies"
      }
    ]
  }
}
```

### Scenario 4: Production Run with Safety Limit

```json
{
  "input": {
    "mode": "folders",
    "folders": [
      {
        "path": "V:\\collections",
        "recursive": true
      }
    ],
    "filters": {
      "exclude_patterns": ["*_backup*", "*_temp*"],
      "min_file_size_bytes": 50,
      "max_files": 100
    }
  }
}
```

**Tip:** Test with `max_files: 10`, then remove limit for full run.

### Scenario 5: Include Priority Files + Bulk

```json
{
  "input": {
    "mode": "mixed",
    "files": [
      "C:\\golden_standard\\validated_bio_001.md",
      "C:\\golden_standard\\validated_bio_002.md"
    ],
    "folders": [
      {
        "path": "C:\\new_data",
        "recursive": true
      }
    ],
    "filters": {
      "exclude_patterns": ["*_unverified*"]
    }
  }
}
```

---

## Pipeline Output During Execution

The pipeline shows input processing details:

```
[Input] Processing input configuration...
  Mode: Folder scanning
  Scanning: C:\data\collection1
    Found: 234 files
  Scanning: C:\data\collection2
    Found: 156 files
  Filters applied: 390 → 385 files
  Total files to process: 385
```

**What this tells you:**
- Input mode being used
- Folders scanned and file counts
- Filter effects (before → after)
- Final count of files to process

---

## Best Practices

### ✅ DO

- **Start small:** Use `max_files: 5` for initial testing
- **Use descriptions:** Document what each folder contains
- **Version control configs:** Keep example configs for different scenarios
- **Check counts:** Verify file count before large runs
- **Use filters:** Exclude backups, temps, and drafts
- **Test filters:** Check exclude patterns work as expected

### ❌ DON'T

- **Skip testing:** Always test with small sample first
- **Ignore warnings:** Pipeline warns about missing folders
- **Mix modes carelessly:** Understand which mode fits your use case
- **Forget backups:** Keep original config before major changes
- **Run blind:** Check the "Total files to process" output

---

## Switching Between Modes

You can easily switch modes by changing one line:

```json
// From specific files...
{
  "input": {
    "mode": "files",
    "files": ["C:\\test1.md", "C:\\test2.md"]
  }
}

// To folder scanning...
{
  "input": {
    "mode": "folders",
    "folders": [
      { "path": "C:\\all_data", "recursive": true }
    ]
  }
}

// To both...
{
  "input": {
    "mode": "mixed",
    "files": ["C:\\test1.md"],
    "folders": [
      { "path": "C:\\all_data", "recursive": true }
    ]
  }
}
```

---

## Troubleshooting

### No files found

```
ERROR: No input files found! Check your configuration.
```

**Solutions:**
- Verify folder paths exist
- Check recursive setting matches your directory structure
- Ensure `.md` files exist in specified locations
- Review exclude patterns (might be too aggressive)

### Too many files

Pipeline processes thousands of files unexpectedly.

**Solutions:**
- Add `max_files` limit for testing
- Check `recursive` setting (might be scanning too deep)
- Use more specific folder paths
- Add exclude patterns for unwanted subdirectories

### Duplicates

Same file processed multiple times (if listed in both files and folders).

**Solution:**
Pipeline automatically deduplicates, but check output count to verify.

---

## Configuration Templates

### Quick Start Template (Files Mode)
```json
{
  "input": {
    "mode": "files",
    "files": [
      "REPLACE_WITH_YOUR_FILE_PATH"
    ]
  }
}
```

### Production Template (Folders Mode)
```json
{
  "input": {
    "mode": "folders",
    "folders": [
      {
        "path": "REPLACE_WITH_FOLDER_PATH",
        "recursive": true,
        "description": "Main collection"
      }
    ],
    "filters": {
      "exclude_patterns": ["*_backup*", "*_temp*"],
      "min_file_size_bytes": 100,
      "max_files": null
    }
  }
}
```

---

## Additional Resources

- **[README.md](README.md)** - Full pipeline documentation
- **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)** - Complete configuration guide
- **[pipeline_config_folders_example.json](pipeline_config_folders_example.json)** - Folder mode example
- **[pipeline_config_mixed_example.json](pipeline_config_mixed_example.json)** - Mixed mode example

---

**Last Updated:** November 2025
