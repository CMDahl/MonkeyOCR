#!/usr/bin/env python3
"""
Test the exact matching logic used by gemini_job_resolver
"""

import pandas as pd

# Load comparison dataframe
comparison_df = pd.read_csv('comprehensive_comparison_dataframe.csv')

# Test the matching logic exactly as used in gemini_job_resolver
book_id = 'digibok_2007031501007_0468'
name_azure = 'WEIDER, Aasta'
name_monkey = 'WEIDER, Aasta'

print(f"Testing matching logic:")
print(f"book_id: {book_id}")
print(f"name_azure: {name_azure}")
print(f"name_monkey: {name_monkey}")

# First try to match by book_id and name (exact logic from gemini_job_resolver)
record = comparison_df[
    (comparison_df['book_id'] == book_id) & 
    (comparison_df['name_azure'] == name_azure) & 
    (comparison_df['name_monkey'] == name_monkey)
]

print(f"\nMatching records found: {len(record)}")

if record.empty:
    print("No record found!")
else:
    print(f"Taking first match (iloc[0])...")
    record_used = record.iloc[0]  # This is what gemini_job_resolver does
    print(f"Record index: {record.index[0]}")
    print(f"Name Azure: {record_used['name_azure']}")
    print(f"Name Monkey: {record_used['name_monkey']}")
    
    # Extract Azure job titles (exact logic from gemini_job_resolver)
    azure_jobs = []
    for i in range(1, 6):  # job1 to job5
        job_col = f'job{i}_title_azure'
        if job_col in record_used and pd.notna(record_used[job_col]) and record_used[job_col] != 'Missing':
            azure_jobs.append(str(record_used[job_col]))
    
    # Extract Monkey job titles (exact logic from gemini_job_resolver)
    monkey_jobs = []
    for i in range(1, 6):  # job1 to job5
        job_col = f'job{i}_title_monkey'
        if job_col in record_used and pd.notna(record_used[job_col]) and record_used[job_col] != 'Missing':
            monkey_jobs.append(str(record_used[job_col]))
    
    print(f"\nExtracted Azure jobs: {azure_jobs}")
    print(f"Extracted Monkey jobs: {monkey_jobs}")
    
    # Test markdown content extraction
    azure_content = record_used.get('markdown_chunk_azure', '')
    monkey_content = record_used.get('markdown_chunk_monkey', '')
    
    # Handle NaN values
    if pd.isna(azure_content):
        azure_content = ""
    if pd.isna(monkey_content):
        monkey_content = ""
    
    print(f"\nAzure content (first 100 chars): {str(azure_content)[:100]}...")
    print(f"Monkey content (first 100 chars): {str(monkey_content)[:100]}...")
    
print(f"\nFor comparison, all records with this book_id:")
all_book_records = comparison_df[comparison_df['book_id'] == book_id]
for idx, rec in all_book_records.iterrows():
    print(f"  Record {idx}: {rec['name_azure']} / {rec['name_monkey']}")
