# Configuration
# --------------------------------------------------
# Load configuration from JSON files
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigPath = Join-Path $ScriptDir "pipeline_config.json"
$PromptConfigPath = Join-Path $ScriptDir "prompt_config.json"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  OCR ILLUSTRATION PIPELINE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Load pipeline configuration
if (-not (Test-Path $ConfigPath)) {
    Write-Error "Configuration file not found: $ConfigPath"
    exit 1
}

Write-Host "`n[Config] Loading pipeline_config.json..." -ForegroundColor Yellow
$Config = Get-Content $ConfigPath -Raw | ConvertFrom-Json

# Load prompt configuration
if (-not (Test-Path $PromptConfigPath)) {
    Write-Warning "Prompt configuration file not found: $PromptConfigPath"
    Write-Warning "Scripts will need to use hardcoded prompts"
    $PromptConfig = $null
} else {
    Write-Host "[Config] Loading prompt_config.json..." -ForegroundColor Yellow
    $PromptConfig = Get-Content $PromptConfigPath -Raw | ConvertFrom-Json
}

# Extract configuration values
$OutputPath = $Config.paths.output_directory
$OriginalImagesPath = $Config.paths.original_images_path
$PythonExe = $Config.paths.python_executable

# Process input configuration
Write-Host "`n[Input] Processing input configuration..." -ForegroundColor Yellow
$InputFiles = @()
$InputMode = $Config.input.mode

switch ($InputMode) {
    "files" {
        # Use specific file list
        $InputFiles = $Config.input.files
        Write-Host "  Mode: Specific files" -ForegroundColor White
    }
    "folders" {
        # Scan folders for files
        Write-Host "  Mode: Folder scanning" -ForegroundColor White
        foreach ($folder in $Config.input.folders) {
            $folderPath = $folder.path
            $pattern = $folder.pattern
            $recursive = $folder.recursive
            
            if (-not (Test-Path $folderPath)) {
                Write-Warning "Folder not found: $folderPath"
                continue
            }
            
            Write-Host "  Scanning: $folderPath" -ForegroundColor Gray
            
            if ($recursive) {
                $files = Get-ChildItem -Path $folderPath -Filter "*.md" -Recurse -File
            } else {
                $files = Get-ChildItem -Path $folderPath -Filter "*.md" -File
            }
            
            $InputFiles += $files.FullName
            Write-Host "    Found: $($files.Count) files" -ForegroundColor Gray
        }
    }
    "mixed" {
        # Combine files and folder scanning
        Write-Host "  Mode: Mixed (files + folders)" -ForegroundColor White
        
        # Add specific files
        if ($Config.input.files) {
            $InputFiles += $Config.input.files
            Write-Host "  Added: $($Config.input.files.Count) specific files" -ForegroundColor Gray
        }
        
        # Scan folders
        foreach ($folder in $Config.input.folders) {
            $folderPath = $folder.path
            $recursive = $folder.recursive
            
            if (-not (Test-Path $folderPath)) {
                Write-Warning "Folder not found: $folderPath"
                continue
            }
            
            Write-Host "  Scanning: $folderPath" -ForegroundColor Gray
            
            if ($recursive) {
                $files = Get-ChildItem -Path $folderPath -Filter "*.md" -Recurse -File
            } else {
                $files = Get-ChildItem -Path $folderPath -Filter "*.md" -File
            }
            
            $InputFiles += $files.FullName
            Write-Host "    Found: $($files.Count) files" -ForegroundColor Gray
        }
    }
    default {
        Write-Error "Invalid input mode: $InputMode. Must be 'files', 'folders', or 'mixed'"
        exit 1
    }
}

# Apply filters
if ($Config.input.filters) {
    $beforeCount = $InputFiles.Count
    
    # Exclude patterns
    if ($Config.input.filters.exclude_patterns) {
        foreach ($pattern in $Config.input.filters.exclude_patterns) {
            $InputFiles = $InputFiles | Where-Object { $_ -notlike $pattern }
        }
    }
    
    # Min file size filter
    if ($Config.input.filters.min_file_size_bytes) {
        $minSize = $Config.input.filters.min_file_size_bytes
        $InputFiles = $InputFiles | Where-Object { 
            (Get-Item $_).Length -ge $minSize 
        }
    }
    
    # Max files limit
    if ($Config.input.filters.max_files -and $Config.input.filters.max_files -gt 0) {
        $InputFiles = $InputFiles | Select-Object -First $Config.input.filters.max_files
    }
    
    $afterCount = $InputFiles.Count
    if ($beforeCount -ne $afterCount) {
        Write-Host "  Filters applied: $beforeCount → $afterCount files" -ForegroundColor Gray
    }
}

# Remove duplicates
$InputFiles = $InputFiles | Select-Object -Unique

# Validate we have files to process
if ($InputFiles.Count -eq 0) {
    Write-Error "No input files found! Check your configuration."
    exit 1
}

Write-Host "  Total files to process: $($InputFiles.Count)" -ForegroundColor Green

# Validate Python executable
if (-not (Test-Path $PythonExe)) {
    Write-Warning "Python executable not found at: $PythonExe"
    Write-Warning "Falling back to 'python' command"
    $PythonExe = "python"
}

# Display configuration summary
Write-Host "`n[Pipeline Settings]" -ForegroundColor Cyan
Write-Host "  Name: $($Config.pipeline_name)" -ForegroundColor White
Write-Host "  Version: $($Config.version)" -ForegroundColor White
Write-Host "  Input files: $($InputFiles.Count)" -ForegroundColor White
Write-Host "  Output: $OutputPath" -ForegroundColor White
Write-Host "  Original images: $OriginalImagesPath" -ForegroundColor White

if ($PromptConfig) {
    Write-Host "`n[AI Settings]" -ForegroundColor Cyan
    Write-Host "  Model: $($PromptConfig.gemini_settings.model)" -ForegroundColor White
    Write-Host "  Temperature: $($PromptConfig.gemini_settings.temperature)" -ForegroundColor White
    Write-Host "  Max retries: $($PromptConfig.gemini_settings.max_retries)" -ForegroundColor White
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
# --------------------------------------------------

$ErrorActionPreference = "Stop"

# Ensure absolute path for OutputPath
$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)

# Create output directory if it doesn't exist
if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    Write-Host "Created output directory: $OutputPath" -ForegroundColor Green
}

# Create staging directory
$StagingDir = Join-Path $OutputPath "input_staging"
if (-not (Test-Path $StagingDir)) {
    New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null
}

# Copy input files to staging with proper naming
Write-Host "Copying input files to staging directory..." -ForegroundColor Cyan
foreach ($file in $InputFiles) {
    if (Test-Path $file) {
        # Extract the parent directory name (e.g., digibok_2007031501007_0154)
        $parentDir = Split-Path (Split-Path $file -Parent) -Leaf
        
        # Create a new filename: parentDirName.md
        $newFileName = "$parentDir.md"
        $destinationPath = Join-Path $StagingDir $newFileName
        
        Copy-Item -Path $file -Destination $destinationPath -Force
        Write-Host "  Copied: $(Split-Path $file -Leaf) -> $newFileName"
    } else {
        Write-Warning "  File not found: $file"
    }
}

# Set InputPath to the staging directory for the rest of the pipeline
$InputPath = $StagingDir

$ScriptDir = $PSScriptRoot

Write-Host "Starting OCR Illustration Pipeline..." -ForegroundColor Cyan
Write-Host "Input Directory (Staging): $InputPath"
Write-Host "Output Directory: $OutputPath"
Write-Host "Script Directory: $ScriptDir"
Write-Host "--------------------------------------------------"

# 1. Run Gemini Portrait Name Associator
Write-Host "`n[1/6] Running Gemini Portrait Name Associator..." -ForegroundColor Yellow
$script = Join-Path $ScriptDir "gemini_portrait_name_associator.py"
& $PythonExe $script "$InputPath" "$OutputPath" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Error "Step 1 failed"; exit 1 }

# 2. Concatenate MD Files
Write-Host "`n[2/6] Concatenating Markdown Files..." -ForegroundColor Yellow
$script = Join-Path $ScriptDir "concatenate_all_md_files.py"
& $PythonExe $script "$InputPath" "$OutputPath"
if ($LASTEXITCODE -ne 0) { Write-Error "Step 2 failed"; exit 1 }

# 3. Run Gemini All Names Extractor
Write-Host "`n[3/6] Extracting All Names (Gemini)..." -ForegroundColor Yellow
$script = Join-Path $ScriptDir "gemini_all_names.py"
& $PythonExe $script "$InputPath" "$OutputPath" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Error "Step 3 failed"; exit 1 }

# 4. Extract All Names & Chunks & Associate Portraits
Write-Host "`n[4/6] Processing Names, Chunks, and Portraits..." -ForegroundColor Yellow
$script = Join-Path $ScriptDir "extract_all_names.py"
$jsonFile = Join-Path $OutputPath "all_books_names.json"
$mdFile = Join-Path $OutputPath "all_text.md"
# Note: Using HTML img tag pattern for DeepSeek/Paddle OCR output
# Other patterns: "![Figure]" (MonkeyOCR), "**[FIGURE:" (AzureOCR)
& $PythonExe $script "$jsonFile" "$mdFile" "$InputPath" "$OutputPath" --portrait-pattern '<img src="imgs/'
if ($LASTEXITCODE -ne 0) { Write-Error "Step 4 failed"; exit 1 }

# 4b. Merge portrait associations from Step 1 into the CSV
Write-Host "`n[4b/6] Merging Portrait Associations..." -ForegroundColor Yellow
$script = Join-Path $ScriptDir "merge_portraits.py"
$inputCsv = Join-Path $OutputPath "extracted_all_names_with_chunks.csv"
$outputCsv = Join-Path $OutputPath "extracted_all_names_with_chunks_and_portraits.csv"
& $PythonExe $script "$inputCsv" "$OutputPath" "$outputCsv"
if ($LASTEXITCODE -ne 0) { Write-Error "Step 4b failed"; exit 1 }

# 5. Extract Biographies
Write-Host "`n[5/6] Extracting Structured Biographies..." -ForegroundColor Yellow
$script = Join-Path $ScriptDir "biography_extractor.py"
$inputCsv = Join-Path $OutputPath "extracted_all_names_with_chunks_and_portraits.csv"
$outputJson = Join-Path $OutputPath "biographies.json"
& $PythonExe $script "$inputCsv" "$outputJson" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Error "Step 5 failed"; exit 1 }

# 6. Extract Portrait Names (Alternative/Validation Flow) - SKIPPED
# This step is now redundant since step 4b merges portrait data directly
# Write-Host "`n[6/7] Extracting Portrait Names (Validation Flow)..." -ForegroundColor Yellow
# $script = Join-Path $ScriptDir "extract_portrait_names.py"
# $outputCsv = Join-Path $OutputPath "extracted_portrait_names_with_chunks.csv"
# & $PythonExe $script "$OutputPath" "$mdFile" "$outputCsv"
# if ($LASTEXITCODE -ne 0) { Write-Error "Step 6 failed"; exit 1 }

# 6. Collect Final Data
Write-Host "`n[6/6] Finalizing Data Collection..." -ForegroundColor Yellow
$script = Join-Path $ScriptDir "collect_data.py"
& $PythonExe $script "$OutputPath"
if ($LASTEXITCODE -ne 0) { Write-Error "Step 6 failed"; exit 1 }

# 7. Generate Visualizations
Write-Host "`n[Bonus] Generating Quality Inspection Visualizations..." -ForegroundColor Cyan
$visualScript = Join-Path $ScriptDir "visualize_results.py"
$finalCsv = Join-Path $OutputPath "final_dataset.csv"

# Extract the base directory from the first input file (contains portraits in imgs/ subfolders)
if ($InputFiles.Count -gt 0) {
    $firstFile = $InputFiles[0]
    $portraitBaseFolder = Split-Path (Split-Path $firstFile -Parent) -Parent
    $visualOutputFolder = Join-Path $OutputPath "test_images"
    
    # Check if final CSV exists before visualization
    if (Test-Path $finalCsv) {
        & $PythonExe $visualScript "$finalCsv" "$OriginalImagesPath" "$portraitBaseFolder" "$visualOutputFolder"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Visualizations saved to: $visualOutputFolder" -ForegroundColor Green
        } else {
            Write-Warning "Visualization step encountered errors but pipeline completed"
        }
    } else {
        Write-Warning "Final CSV not found. Skipping visualization step."
    }
} else {
    Write-Warning "No input files specified. Skipping visualization."
}

Write-Host "`n--------------------------------------------------"
Write-Host "Pipeline Completed Successfully!" -ForegroundColor Green
Write-Host "Final dataset available at: $(Join-Path $OutputPath 'final_dataset.csv')"
