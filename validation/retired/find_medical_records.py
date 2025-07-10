#!/usr/bin/env python3
"""
Find records with medical job titles to understand the confusion
"""

import pandas as pd

# Load comparison dataframe
df = pd.read_csv('comprehensive_comparison_dataframe.csv')

# Look for records with "lege" in job titles
print("Looking for records with 'lege' in job titles...")
lege_records = df[
    (df['job1_title_azure'].str.contains('lege', case=False, na=False)) |
    (df['job2_title_azure'].str.contains('lege', case=False, na=False)) |
    (df['job3_title_azure'].str.contains('lege', case=False, na=False)) |
    (df['job4_title_azure'].str.contains('lege', case=False, na=False)) |
    (df['job5_title_azure'].str.contains('lege', case=False, na=False)) |
    (df['job1_title_monkey'].str.contains('lege', case=False, na=False)) |
    (df['job2_title_monkey'].str.contains('lege', case=False, na=False)) |
    (df['job3_title_monkey'].str.contains('lege', case=False, na=False)) |
    (df['job4_title_monkey'].str.contains('lege', case=False, na=False)) |
    (df['job5_title_monkey'].str.contains('lege', case=False, na=False))
]

print(f"Found {len(lege_records)} records with 'lege' in job titles")

if len(lege_records) > 0:
    print("\nFirst few records with 'lege':")
    for idx, record in lege_records.head(5).iterrows():
        print(f"\nRecord {idx}:")
        print(f"  Book ID: {record['book_id']}")
        print(f"  Name Azure: {record['name_azure']}")
        print(f"  Name Monkey: {record['name_monkey']}")
        print(f"  Job titles:")
        for i in range(1, 6):
            azure_job = record.get(f'job{i}_title_azure', 'Missing')
            monkey_job = record.get(f'job{i}_title_monkey', 'Missing')
            if 'lege' in str(azure_job).lower() or 'lege' in str(monkey_job).lower():
                print(f"    Job {i}: Azure='{azure_job}', Monkey='{monkey_job}'")

# Look for records with "assistent og vikar" in job titles
print("\n\nLooking for records with 'assistent og vikar' in job titles...")
assistent_records = df[
    (df['job1_title_azure'].str.contains('assistent og vikar', case=False, na=False)) |
    (df['job2_title_azure'].str.contains('assistent og vikar', case=False, na=False)) |
    (df['job3_title_azure'].str.contains('assistent og vikar', case=False, na=False)) |
    (df['job4_title_azure'].str.contains('assistent og vikar', case=False, na=False)) |
    (df['job5_title_azure'].str.contains('assistent og vikar', case=False, na=False)) |
    (df['job1_title_monkey'].str.contains('assistent og vikar', case=False, na=False)) |
    (df['job2_title_monkey'].str.contains('assistent og vikar', case=False, na=False)) |
    (df['job3_title_monkey'].str.contains('assistent og vikar', case=False, na=False)) |
    (df['job4_title_monkey'].str.contains('assistent og vikar', case=False, na=False)) |
    (df['job5_title_monkey'].str.contains('assistent og vikar', case=False, na=False))
]

print(f"Found {len(assistent_records)} records with 'assistent og vikar' in job titles")

if len(assistent_records) > 0:
    print("\nFirst few records with 'assistent og vikar':")
    for idx, record in assistent_records.head(3).iterrows():
        print(f"\nRecord {idx}:")
        print(f"  Book ID: {record['book_id']}")
        print(f"  Name Azure: {record['name_azure']}")
        print(f"  Name Monkey: {record['name_monkey']}")
        print(f"  Job titles:")
        for i in range(1, 6):
            azure_job = record.get(f'job{i}_title_azure', 'Missing')
            monkey_job = record.get(f'job{i}_title_monkey', 'Missing')
            print(f"    Job {i}: Azure='{azure_job}', Monkey='{monkey_job}'")
