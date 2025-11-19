# Configuration
# --------------------------------------------------
# Add your list of markdown files here (full paths)
$InputFiles = @(
    "C:\Users\iu2-cmd\GitHub\ocr-pipeline-paddle-deepseek\output_paddleOCR\digibok_2007031501007\digibok_2007031501007_0154\digibok_2007031501007_0154.md"
    "C:\Users\iu2-cmd\GitHub\ocr-pipeline-paddle-deepseek\output_paddleOCR\digibok_2007031501007\digibok_2007031501007_0155\digibok_2007031501007_0155.md"
    # Add more files as needed...
)

# Output directory
$OutputPath = "C:\Users\iu2-cmd\GitHub\MonkeyOCR\image_name_extraction\test"

# Python Executable (OCR-Parser environment)
$PythonExe = "C:\Users\iu2-cmd\AppData\Local\miniconda3\envs\OCR-Parser\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Warning "OCR-Parser python.exe not found at default location. Falling back to 'python'."
    $PythonExe = "python"
}
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

# 7. Collect Final Data
Write-Host "`n[6/7] Finalizing Data Collection..." -ForegroundColor Yellow
$script = Join-Path $ScriptDir "collect_data.py"
& $PythonExe $script "$OutputPath"
if ($LASTEXITCODE -ne 0) { Write-Error "Step 7 failed"; exit 1 }

Write-Host "`n--------------------------------------------------"
Write-Host "Pipeline Completed Successfully!" -ForegroundColor Green
Write-Host "Final dataset available at: $(Join-Path $OutputPath 'final_dataset.csv')"
