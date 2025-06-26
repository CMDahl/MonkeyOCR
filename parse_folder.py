#!/usr/bin/env python3
# Copyright (c) Opendatalab. All rights reserved.
import os
# Set backend configurations to avoid triton dependency
os.environ['MAGIC_PDF_BACKEND'] = 'pytorch'
os.environ['LMDEPLOY_USE_TRITON'] = '0'
os.environ['LMDEPLOY_BACKEND'] = 'pytorch'
os.environ['TRANSFORMERS_BACKEND'] = '1'
# Disable FlashAttention2 if not available
os.environ['DISABLE_FLASH_ATTN'] = '1'
# Set CUDA memory allocation configuration
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
import time
import argparse
import sys
from pathlib import Path
import glob
import gc
import torch
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset, ImageDataset
from magic_pdf.model.doc_analyze_by_custom_model_llm import doc_analyze_llm
from magic_pdf.model.custom_model import MonkeyOCR


def clear_cache_memory():
    """Clear GPU cache and run garbage collection without unloading model"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    gc.collect()


def print_memory_stats():
    """Print current GPU memory usage"""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3  # GB
        reserved = torch.cuda.memory_reserved() / 1024**3    # GB
        print(f"GPU Memory - Allocated: {allocated:.2f}GB, Reserved: {reserved:.2f}GB")


def is_already_processed(input_file, output_dir):
    """
    Check if a file has already been processed by looking for output files
    
    Args:
        input_file: Input file path
        output_dir: Output directory
    
    Returns:
        bool: True if already processed, False otherwise
    """
    name_without_suff = os.path.basename(input_file).split(".")[0]
    local_md_dir = os.path.join(output_dir, name_without_suff)
    
    # Check if output directory exists and has expected files
    if os.path.exists(local_md_dir):
        expected_files = [
            f"{name_without_suff}.md",
            f"{name_without_suff}_content_list.json",
            f"{name_without_suff}_middle.json"
        ]
        
        # Check if all expected files exist
        all_exist = all(os.path.exists(os.path.join(local_md_dir, f)) for f in expected_files)
        return all_exist
    
    return False


def parse_single_file(input_file, output_dir, model, file_count, total_files, skip_existing=True, show_memory=False):
    """
    Parse a single file and save results (reuses loaded model)
    
    Args:
        input_file: Input file path
        output_dir: Output directory
        model: Pre-loaded MonkeyOCR model instance
        file_count: Current file number
        total_files: Total number of files
        skip_existing: Skip files that have already been processed
        show_memory: Show memory usage information
    """
    print(f"\n[{file_count}/{total_files}] Processing: {os.path.basename(input_file)}")
    
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
        
        # Prepare output directory
        local_image_dir = os.path.join(output_dir, name_without_suff, "images")
        local_md_dir = os.path.join(output_dir, name_without_suff)
        image_dir = os.path.basename(local_image_dir)
        os.makedirs(local_image_dir, exist_ok=True)
        os.makedirs(local_md_dir, exist_ok=True)
        
        print(f"Output dir: {local_md_dir}")
        image_writer = FileBasedDataWriter(local_image_dir)
        md_writer = FileBasedDataWriter(local_md_dir)
        
        # Read file content
        reader = FileBasedDataReader()
        file_bytes = reader.read(input_file)
        
        # Create dataset instance
        file_extension = input_file.split(".")[-1].lower()
        if file_extension == "pdf":
            ds = PymuDocDataset(file_bytes)
        else:
            ds = ImageDataset(file_bytes)
        
        # Start inference
        print("Performing document parsing...")
        start_time = time.time()
        
        infer_result = ds.apply(doc_analyze_llm, MonkeyOCR_model=model)
        
        # Pipeline processing
        pipe_result = infer_result.pipe_ocr_mode(image_writer, MonkeyOCR_model=model)
        
        parsing_time = time.time() - start_time
        print(f"Parsing time: {parsing_time:.2f}s")

        # Save results
        infer_result.draw_model(os.path.join(local_md_dir, f"{name_without_suff}_model.pdf"))
        pipe_result.draw_layout(os.path.join(local_md_dir, f"{name_without_suff}_layout.pdf"))
        pipe_result.draw_span(os.path.join(local_md_dir, f"{name_without_suff}_spans.pdf"))
        pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)
        pipe_result.dump_content_list(md_writer, f"{name_without_suff}_content_list.json", image_dir)
        pipe_result.dump_middle_json(md_writer, f'{name_without_suff}_middle.json')
        
        print(f"✅ [{file_count}/{total_files}] Successfully processed: {os.path.basename(input_file)} ({parsing_time:.1f}s)")
        
        # Clean up intermediate results but keep model
        del infer_result
        del pipe_result
        del ds
        del file_bytes
        clear_cache_memory()
        
        return True, local_md_dir
        
    except Exception as e:
        print(f"❌ [{file_count}/{total_files}] Failed to process {os.path.basename(input_file)}: {str(e)}")
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
        extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']
    
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


def process_files(input_path, output_dir, config_path, clear_interval=5, skip_existing=True, show_memory=False):
    """
    Process files (single file or directory) with model reuse and memory management
    
    Args:
        input_path: Input file or directory path
        output_dir: Output directory
        config_path: Configuration file path
        clear_interval: Number of files to process before aggressive memory clearing (default: 5)
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
        print("Supported formats: PDF, JPG, JPEG, PNG, TIFF, TIF, BMP")
        return
    
    print(f"Found {len(files_to_process)} file(s) to process")
    if skip_existing:
        print("Will skip files that have already been processed")
    print(f"Will clear GPU cache every {clear_interval} files to manage memory")
    
    # Load model once
    print("\nLoading MonkeyOCR model...")
    model_start_time = time.time()
    try:
        MonkeyOCR_model = MonkeyOCR(config_path)
        model_load_time = time.time() - model_start_time
        print(f"✅ Model loaded successfully in {model_load_time:.2f}s")
        
        if show_memory:
            print_memory_stats()
            
    except Exception as e:
        print(f"❌ Failed to load model: {str(e)}")
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
            success, result_dir = parse_single_file(file_path, output_dir, MonkeyOCR_model, i, len(files_to_process), skip_existing, show_memory)
            file_time = time.time() - file_start_time
            
            if success:
                if result_dir is None:  # File was skipped
                    skipped += 1
                else:
                    successful += 1
                    total_parsing_time += file_time
            else:
                failed += 1
            
            # More aggressive memory clearing at intervals
            if i % clear_interval == 0:
                print(f"🧹 Performing aggressive memory cleanup after {i} files...")
                clear_cache_memory()
                if show_memory:
                    print_memory_stats()
                time.sleep(2)  # Brief pause to ensure cleanup
        
    except KeyboardInterrupt:
        print("\n⚠️ Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Processing error: {str(e)}")
    finally:
        # Clean up model
        print("\nCleaning up model...")
        del MonkeyOCR_model
        clear_cache_memory()
    
    total_time = time.time() - total_start_time
    
    # Summary
    print(f"\n{'='*60}")
    print(f"PROCESSING SUMMARY")
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


def main():
    parser = argparse.ArgumentParser(
        description="PDF/Image Document Parsing Tool - Process single file or entire directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  # Process single file
  python parse_folder.py input.pdf
  python parse_folder.py image.jpg
  
  # Process all files in directory
  python parse_folder.py /path/to/directory
  python parse_folder.py D:\\docs\\pdfs
  
  # With custom output directory and skip existing files
  python parse_folder.py /path/to/directory -o ./results
  
  # Force reprocess all files (don't skip existing)
  python parse_folder.py /path/to/directory --no-skip-existing
  
  # With custom config and memory management
  python parse_folder.py /path/to/directory -c model_configs.yaml --clear-interval 3
  
  # Show memory usage information
  python parse_folder.py /path/to/directory --show-memory
        """
    )
    
    parser.add_argument(
        "input",
        help="Input file or directory path"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="./output",
        help="Output directory (default: ./output)"
    )
    
    parser.add_argument(
        "-c", "--config",
        default="model_configs.yaml",
        help="Configuration file path (default: model_configs.yaml)"
    )
    
    parser.add_argument(
        "--clear-interval",
        type=int,
        default=5,
        help="Number of files to process before aggressive memory clearing (default: 5)"
    )
    
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Reprocess files even if they have already been processed"
    )
    
    parser.add_argument(
        "--show-memory",
        action="store_true",
        help="Show GPU memory usage information"
    )
    
    args = parser.parse_args()
    
    try:
        process_files(
            args.input,
            args.output,
            args.config,
            args.clear_interval,
            skip_existing=not args.no_skip_existing,
            show_memory=args.show_memory
        )
        print(f"\n✅ Processing completed!")
        
    except Exception as e:
        print(f"\n❌ Processing failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()