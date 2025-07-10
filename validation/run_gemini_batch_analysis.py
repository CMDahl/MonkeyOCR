#!/usr/bin/env python3
"""
Gemini Job Resolver - Batch Processing Script

This script runs the Gemini job resolver on all flagged records in batches
to avoid overwhelming the API and provide progress updates.
"""

import subprocess
import sys
import time
from pathlib import Path

def run_batch_analysis(max_records_per_batch=10, total_batches=5):
    """Run Gemini analysis in batches"""
    
    print("="*60)
    print("GEMINI JOB RESOLVER - BATCH PROCESSING")
    print("="*60)
    
    for batch in range(1, total_batches + 1):
        print(f"\nProcessing Batch {batch}/{total_batches}")
        print("-" * 40)
        
        # Calculate starting record for this batch
        start_record = (batch - 1) * max_records_per_batch + 1
        end_record = batch * max_records_per_batch
        
        print(f"Processing records {start_record}-{end_record}")
        
        # Run the analysis
        cmd = [
            sys.executable, 
            "gemini_job_resolver.py",
            "--max-records", str(max_records_per_batch),
            "--output-dir", f"gemini_job_analysis_batch_{batch:02d}"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ Batch {batch} completed successfully")
                # Extract summary from output
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Success rate:' in line or 'Successful analyses:' in line:
                        print(f"   {line.strip()}")
            else:
                print(f"❌ Batch {batch} failed")
                print(f"Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Batch {batch} timed out (5 minutes)")
        except Exception as e:
            print(f"💥 Batch {batch} error: {e}")
        
        # Wait between batches to avoid rate limiting
        if batch < total_batches:
            print("Waiting 10 seconds before next batch...")
            time.sleep(10)
    
    print(f"\n" + "="*60)
    print("BATCH PROCESSING COMPLETED")
    print("="*60)
    print(f"Results saved in directories: gemini_job_analysis_batch_01 to gemini_job_analysis_batch_{total_batches:02d}")

if __name__ == "__main__":
    # Run with small batches to test
    run_batch_analysis(max_records_per_batch=5, total_batches=3)
