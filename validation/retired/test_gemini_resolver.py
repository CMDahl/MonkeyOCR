#!/usr/bin/env python3
"""
Test the Gemini job resolver extraction functions with the specific WEIDER, Aasta record
"""

import sys
sys.path.append('.')

import pandas as pd
from typing import List, Tuple

# Copy the extraction functions from gemini_job_resolver.py
def extract_job_titles_for_record(comparison_df: pd.DataFrame, book_id: str, name_azure: str, name_monkey: str) -> Tuple[List[str], List[str]]:
    """Extract all job titles for a specific record"""
    # First try to match by book_id and name
    record = comparison_df[
        (comparison_df['book_id'] == book_id) & 
        (comparison_df['name_azure'] == name_azure) & 
        (comparison_df['name_monkey'] == name_monkey)
    ]
    
    if record.empty:
        print(f"No record found for book_id: {book_id}, name_azure: {name_azure}, name_monkey: {name_monkey}")
        return [], []
    
    record = record.iloc[0]  # Take first match
    
    # Extract Azure job titles
    azure_jobs = []
    for i in range(1, 6):  # job1 to job5
        job_col = f'job{i}_title_azure'
        if job_col in record and pd.notna(record[job_col]) and record[job_col] != 'Missing':
            azure_jobs.append(str(record[job_col]))
    
    # Extract Monkey job titles
    monkey_jobs = []
    for i in range(1, 6):  # job1 to job5
        job_col = f'job{i}_title_monkey'
        if job_col in record and pd.notna(record[job_col]) and record[job_col] != 'Missing':
            monkey_jobs.append(str(record[job_col]))
    
    return azure_jobs, monkey_jobs

def get_markdown_content(comparison_df: pd.DataFrame, book_id: str, name_azure: str, name_monkey: str) -> Tuple[str, str]:
    """Get markdown content for Azure and Monkey OCR"""
    # First try to match by book_id and name
    record = comparison_df[
        (comparison_df['book_id'] == book_id) & 
        (comparison_df['name_azure'] == name_azure) & 
        (comparison_df['name_monkey'] == name_monkey)
    ]
    
    if record.empty:
        print(f"No record found for book_id: {book_id}, name_azure: {name_azure}, name_monkey: {name_monkey}")
        return "", ""
    
    record = record.iloc[0]  # Take first match
    
    azure_content = record.get('markdown_chunk_azure', '')
    monkey_content = record.get('markdown_chunk_monkey', '')
    
    # Handle NaN values
    if pd.isna(azure_content):
        azure_content = ""
    if pd.isna(monkey_content):
        monkey_content = ""
    
    return str(azure_content), str(monkey_content)

# Load data
comparison_df = pd.read_csv('comprehensive_comparison_dataframe.csv')

# Test the specific record
book_id = 'digibok_2007031501007_0468'
name_azure = 'WEIDER, Aasta'
name_monkey = 'WEIDER, Aasta'

print(f"Testing job extraction for:")
print(f"Book ID: {book_id}")
print(f"Name Azure: {name_azure}")
print(f"Name Monkey: {name_monkey}")

# Test job extraction
azure_jobs, monkey_jobs = extract_job_titles_for_record(comparison_df, book_id, name_azure, name_monkey)
print(f"\nExtracted jobs:")
print(f"Azure: {azure_jobs}")
print(f"Monkey: {monkey_jobs}")

# Test markdown content extraction
azure_content, monkey_content = get_markdown_content(comparison_df, book_id, name_azure, name_monkey)
print(f"\nMarkdown content (first 100 chars):")
print(f"Azure: {azure_content[:100]}...")
print(f"Monkey: {monkey_content[:100]}...")

# Check if this matches what we expect
expected_azure = ['Husmor og mor', "sporadisk deltagelse i 'arbeidslivet'"]
expected_monkey = []

if azure_jobs == expected_azure and monkey_jobs == expected_monkey:
    print("\n✅ Job extraction is working correctly!")
else:
    print("\n❌ Job extraction is not working correctly!")
    print(f"Expected Azure: {expected_azure}")
    print(f"Expected Monkey: {expected_monkey}")
