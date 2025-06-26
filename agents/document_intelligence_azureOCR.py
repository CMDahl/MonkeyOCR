#!/usr/bin/env python3
import os
import time
import argparse
import sys
from pathlib import Path
import gc
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, DocumentContentFormat, AnalyzeOutputOption
from azure.core.credentials import AzureKeyCredential
from key_vault import KeyVault


def clear_cache_memory():
    """Clear cache and run garbage collection"""
    gc.collect()


def print_memory_stats():
    """Print current memory usage (placeholder for Azure processing)"""
    print("Processing with Azure Document Intelligence...")


def is_already_processed(input_file, output_dir):
    """
    Check if a file has already been processed by looking for Azure output files
    
    Args:
        input_file: Input file path
        output_dir: Output directory
    
    Returns:
        bool: True if already processed, False otherwise
    """
    name_without_suff = os.path.basename(input_file).split(".")[0]
    local_md_dir = os.path.join(output_dir, name_without_suff)
    
    # Check if output directory exists and has expected Azure files
    if os.path.exists(local_md_dir):
        expected_files = [
            f"{name_without_suff}_azure.md",
        ]
        
        # Check if all expected files exist
        all_exist = all(os.path.exists(os.path.join(local_md_dir, f)) for f in expected_files)
        return all_exist
    
    return False


def get_azure_client():
    """Initialize Azure Document Intelligence client"""
    try:
        # Get credentials from Key Vault
        keyvault = KeyVault()
        endpoint = keyvault.get_key("SDUAzureDocIntelligenceEndpoint")
        key = keyvault.get_key("SDUAzureDocIntelligenceKey")
        
        if not endpoint or not key:
            raise ValueError("Azure Document Intelligence endpoint or key not found in KeyVault")
        
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=endpoint, 
            credential=AzureKeyCredential(key)
        )
        return document_intelligence_client
    except Exception as e:
        print(f"Failed to initialize Azure client: {str(e)}")
        raise

def get_ocr(path, document_intelligence_client):
    """
    Analyze document using Azure Document Intelligence
    
    Args:
        path: Path to the document file
        document_intelligence_client: Azure Document Intelligence client
    
    Returns:
        AnalyzeResult with markdown content
    """
    with open(path, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-layout",
            body=f,        
            output_content_format=DocumentContentFormat.MARKDOWN,             
            output=[AnalyzeOutputOption.FIGURES],
            content_type="application/octet-stream",
        )
    result: AnalyzeResult = poller.result()
    return result


def parse_single_file_azure(input_file, output_dir, client, file_count, total_files, skip_existing=True, show_memory=False):
    """
    Parse a single file using Azure Document Intelligence and save results
    
    Args:
        input_file: Input file path
        output_dir: Output directory
        client: Azure Document Intelligence client
        file_count: Current file number
        total_files: Total number of files
        skip_existing: Skip files that have already been processed
        show_memory: Show memory usage information
    """
    print(f"\n[{file_count}/{total_files}] Processing with Azure: {os.path.basename(input_file)}")
    
    # Check if already processed
    if skip_existing and is_already_processed(input_file, output_dir):
        print(f"⏭️ [{file_count}/{total_files}] Skipping (already processed): {os.path.basename(input_file)}")
        return True, None
    
    # Clear cache before processing each file
    clear_cache_memory()
    
    if show_memory:
        print_memory_stats()
    
    try:
        # Get filename
        name_without_suff = os.path.basename(input_file).split(".")[0]
        
        # Prepare output directory (same structure as MonkeyOCR but with azure suffix)
        local_md_dir = os.path.join(output_dir, name_without_suff)
        os.makedirs(local_md_dir, exist_ok=True)
        
        print(f"Output dir: {local_md_dir}")
        
        # Start inference
        print("Performing Azure document analysis...")
        start_time = time.time()
        
        # Analyze document with Azure using your get_ocr function
        result = get_ocr(input_file, client)
        
        parsing_time = time.time() - start_time
        print(f"Azure parsing time: {parsing_time:.2f}s")

        # Save results with "azure" suffix to avoid overwriting MonkeyOCR results
        # Use result.content directly as it contains the exact markdown content
        azure_md_path = os.path.join(local_md_dir, f"{name_without_suff}_azure.md")
        
        with open(azure_md_path, 'w', encoding='utf-8') as f:
            f.write(result.content)
        
        print(f"✅ [{file_count}/{total_files}] Successfully processed with Azure: {os.path.basename(input_file)} ({parsing_time:.1f}s)")
        
        # Clean up
        del result
        clear_cache_memory()
        
        return True, local_md_dir
        
    except Exception as e:
        print(f"❌ [{file_count}/{total_files}] Failed to process with Azure {os.path.basename(input_file)}: {str(e)}")
        # Clean up on error
        clear_cache_memory()
        return False, None


def get_supported_files(input_path, extensions=None):
    """
    Get list of supported files from input path
    
    Args:
        input_path: Input file or directory path
        extensions: List of supported extensions
    """
    if extensions is None:
        # Azure Document Intelligence supported formats
        extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.heif']
    
    files = []
    
    if os.path.isfile(input_path):
        # Single file
        if any(input_path.lower().endswith(ext) for ext in extensions):
            files.append(input_path)
    elif os.path.isdir(input_path):
        # Directory - get all supported files (case-insensitive)
        for file_path in Path(input_path).iterdir():
            if file_path.is_file():
                file_ext = file_path.suffix.lower()
                if file_ext in extensions:
                    files.append(str(file_path))
    
    # Remove duplicates and sort
    files = sorted(list(set(files)))
    return files


def process_files_azure(input_path, output_dir, clear_interval=5, skip_existing=True, show_memory=False):
    """
    Process files using Azure Document Intelligence
    
    Args:
        input_path: Input file or directory path
        output_dir: Output directory
        clear_interval: Number of files to process before memory clearing (default: 5)
        skip_existing: Skip files that have already been processed (default: True)
        show_memory: Show memory usage information
    """
    # Check if input exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input path does not exist: {input_path}")
    
    # Get list of files to process
    files_to_process = get_supported_files(input_path)
    
    if not files_to_process:
        print(f"No supported files found in: {input_path}")
        print("Supported formats: PDF, JPG, JPEG, PNG, TIFF, TIF, BMP, HEIF")
        return
    
    print(f"Found {len(files_to_process)} file(s) to process with Azure Document Intelligence")
    if skip_existing:
        print("Will skip files that have already been processed")
    print(f"Will clear cache every {clear_interval} files to manage memory")
    
    # Initialize Azure client
    print("\nInitializing Azure Document Intelligence client...")
    try:
        azure_client = get_azure_client()
        print("✅ Azure client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Azure client: {str(e)}")
        return
    
    # Process each file
    successful = 0
    failed = 0
    skipped = 0
    total_parsing_time = 0
    total_start_time = time.time()
    
    try:
        for i, file_path in enumerate(files_to_process, 1):
            file_start_time = time.time()
            success, result_dir = parse_single_file_azure(file_path, output_dir, azure_client, i, len(files_to_process), skip_existing, show_memory)
            file_time = time.time() - file_start_time
            
            if success:
                if result_dir is None:  # File was skipped
                    skipped += 1
                else:
                    successful += 1
                    total_parsing_time += file_time
            else:
                failed += 1
            
            # Memory clearing at intervals
            if i % clear_interval == 0:
                print(f"🧹 Performing memory cleanup after {i} files...")
                clear_cache_memory()
                if show_memory:
                    print_memory_stats()
                time.sleep(1)  # Brief pause
        
    except KeyboardInterrupt:
        print("\n⚠️ Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Processing error: {str(e)}")
    
    total_time = time.time() - total_start_time
    
    # Summary
    print(f"\n{'='*60}")
    print(f"AZURE DOCUMENT INTELLIGENCE PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total files: {len(files_to_process)}")
    print(f"Successful: {successful}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Total processing time: {total_time:.2f}s")
    if successful > 0:
        print(f"Average parsing time per successful file: {total_parsing_time/successful:.2f}s")
    if len(files_to_process) > 0:
        print(f"Average total time per file: {total_time/len(files_to_process):.2f}s")
    print(f"Results saved in: {output_dir}")
    print(f"Azure results are saved with '_azure.md' suffix")


def main():
    parser = argparse.ArgumentParser(
        description="Azure Document Intelligence Processing Tool - Process single file or entire directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  # Process single file with Azure
  python document_intelligence_azure.py input.pdf
  python document_intelligence_azure.py image.jpg
  
  # Process all files in directory with Azure
  python document_intelligence_azure.py /path/to/directory
  python document_intelligence_azure.py D:\\docs\\pdfs
  
  # With custom output directory
  python document_intelligence_azure.py /path/to/directory -o ./azure_results
  
  # Force reprocess all files (don't skip existing)
  python document_intelligence_azure.py /path/to/directory --no-skip-existing
  
  # With memory management settings
  python document_intelligence_azure.py /path/to/directory --clear-interval 3
  
  # Show processing information
  python document_intelligence_azure.py /path/to/directory --show-memory
        """
    )
    
    parser.add_argument(
        "input",
        help="Input file or directory path"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=r"D:\data\HCNC\norway\biographies\storage\AzureOCR",
        help="Output directory (default: D:\\data\\HCNC\\norway\\biographies\\storage\\AzureOCR)"
    )
    
    parser.add_argument(
        "--clear-interval",
        type=int,
        default=5,
        help="Number of files to process before memory clearing (default: 5)"
    )
    
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Reprocess files even if they have already been processed"
    )
    
    parser.add_argument(
        "--show-memory",
        action="store_true",
        help="Show processing information"
    )
    
    args = parser.parse_args()
    
    try:
        process_files_azure(
            args.input,
            args.output,
            args.clear_interval,
            skip_existing=not args.no_skip_existing,
            show_memory=args.show_memory
        )
        print(f"\n✅ Azure processing completed!")
        
    except Exception as e:
        print(f"\n❌ Azure processing failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()