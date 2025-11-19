# OCR Illustration Pipeline - Configuration Guide

## Overview

The pipeline now uses JSON configuration files for easy customization without modifying code:

- **`pipeline_config.json`** - Pipeline settings, paths, and input files
- **`prompt_config.json`** - AI prompts and model parameters
- **`config_loader.py`** - Python utility to load configurations

## Configuration Files

### pipeline_config.json

Controls pipeline behavior and file locations:

```json
{
  "paths": {
    "output_directory": "...",           // Where results are saved
    "python_executable": "...",          // Python interpreter path
    "original_images_path": "..."       // Corpus folder with original scans
  },
  
  "input_files": [                       // List of markdown files to process
    "path/to/file1.md",
    "path/to/file2.md"
  ],
  
  "pipeline_steps": {                    // Enable/disable individual steps
    "1_portrait_association": {
      "enabled": true,
      "suppress_stderr": true
    },
    ...
  }
}
```

**To customize:**
1. Edit `input_files` array to process different files
2. Change `output_directory` to save results elsewhere
3. Toggle `enabled: false` to skip pipeline steps
4. Set `suppress_stderr: false` to see detailed logs

### prompt_config.json

Controls AI behavior and prompts:

```json
{
  "gemini_settings": {
    "model": "gemini-2.0-flash-exp",    // Gemini model to use
    "temperature": 0.1,                  // Lower = more consistent
    "max_retries": 3                     // Retry failed requests
  },
  
  "prompts": {
    "portrait_association": {
      "system_instruction": "...",       // Role/persona for the AI
      "user_prompt_template": "...",     // Task description with {variables}
      "notes": "..."                     // Documentation
    }
  }
}
```

**To customize:**
1. Edit prompt templates to change AI behavior
2. Adjust `temperature` (0.0-1.0) for creativity vs consistency
3. Modify `system_instruction` to change AI's role
4. Use `{variable_name}` in templates for dynamic values

## Using Configurations in Python Scripts

The `config_loader.py` module provides easy access to configurations:

```python
from config_loader import load_config

# Load configurations
config = load_config()

# Get a formatted prompt
prompt = config.get_prompt('biography_extraction', 
                          name="John Doe",
                          text_chunk="...")

# Get system instruction
system_msg = config.get_system_instruction('portrait_association')

# Get Gemini settings
settings = config.get_gemini_settings()
model_name = settings['model']
temperature = settings['temperature']

# Get extraction rules
rules = config.get_extraction_rules()
max_chunk = rules['max_text_chunk_length']
```

## Running the Pipeline

Simply run the PowerShell script - it automatically loads `pipeline_config.json`:

```powershell
.\run_pipeline.ps1
```

The script will:
1. Load configuration from `pipeline_config.json`
2. Display pipeline name, version, and settings
3. Execute enabled steps in order
4. Save results to the configured output directory

## Quick Customization Examples

### Process Different Files

Edit `pipeline_config.json`:
```json
{
  "input_files": [
    "V:\\path\\to\\new_file1.md",
    "V:\\path\\to\\new_file2.md"
  ]
}
```

### Skip Portrait Association

Edit `pipeline_config.json`:
```json
{
  "pipeline_steps": {
    "1_portrait_association": {
      "enabled": false
    }
  }
}
```

### Change AI Temperature

Edit `prompt_config.json`:
```json
{
  "gemini_settings": {
    "temperature": 0.3
  }
}
```

### Modify Portrait Detection Prompt

Edit `prompt_config.json` and customize the `user_prompt_template`:
```json
{
  "prompts": {
    "portrait_association": {
      "user_prompt_template": "Your custom prompt here with {markdown_content}..."
    }
  }
}
```

## Benefits

✅ **No code changes needed** - Edit JSON files instead  
✅ **Version control friendly** - Track prompt experiments  
✅ **Easy sharing** - Share configs with team members  
✅ **Quick experimentation** - Test different prompts/settings  
✅ **Documentation built-in** - Prompts are self-documenting  

## Next Steps

To integrate config loading into Python scripts:
1. Import `config_loader` module
2. Replace hardcoded prompts with `config.get_prompt()`
3. Replace hardcoded settings with `config.get_gemini_settings()`
