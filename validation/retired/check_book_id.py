#!/usr/bin/env python3
"""
Check for multiple records with the same book_id
"""

import pandas as pd

# Load comparison dataframe
df = pd.read_csv('comprehensive_comparison_dataframe.csv')

# Check for records with book_id digibok_2007031501007_0468
book_id = 'digibok_2007031501007_0468'
matching_records = df[df['book_id'] == book_id]

print(f"Found {len(matching_records)} records with book_id: {book_id}")

for idx, record in matching_records.iterrows():
    print(f"\nRecord {idx}:")
    print(f"  Book ID: {record['book_id']}")
    print(f"  Name Azure: {record['name_azure']}")
    print(f"  Name Monkey: {record['name_monkey']}")
    print(f"  Job titles:")
    for i in range(1, 6):
        azure_job = record.get(f'job{i}_title_azure', 'Missing')
        monkey_job = record.get(f'job{i}_title_monkey', 'Missing')
        print(f"    Job {i}: Azure='{azure_job}', Monkey='{monkey_job}'")
