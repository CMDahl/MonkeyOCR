"""
Individual Job Overlap Analysis Demo

This script demonstrates how to analyze job title overlap for individual records
and flag those with insufficient overlap for manual inspection.
"""

import pandas as pd
import numpy as np
import json
import sys
import os

# Add the current directory to the Python path to import our module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_json_extraction import (
    fuzzy_link_dataframes,
    extract_multiple_json_fields,
    analyze_individual_job_overlap,
    save_flagged_records
)

def create_demo_data_with_varying_overlap():
    """Create demo data with varying job overlap scenarios"""
    
    # Scenarios for demonstration
    scenarios = [
        # Good overlap cases
        {
            'name': 'Lars Hansen',
            'book_id': 'book_001',
            'azure_jobs': ['Lærer', 'Rektor', 'Forfatter'],
            'monkey_jobs': ['Teacher', 'Principal', 'Author']
        },
        {
            'name': 'Anna Olsen',
            'book_id': 'book_002',
            'azure_jobs': ['Sykepleier', 'Avdelingsleder'],
            'monkey_jobs': ['Nurse', 'Department Head']
        },
        # Moderate overlap cases
        {
            'name': 'Erik Nordahl',
            'book_id': 'book_003',
            'azure_jobs': ['Ingeniør', 'Prosjektleder', 'Konsulent'],
            'monkey_jobs': ['Engineer', 'Manager']  # Missing one job
        },
        {
            'name': 'Kari Berg',
            'book_id': 'book_004',
            'azure_jobs': ['Advokat', 'Dommer'],
            'monkey_jobs': ['Lawyer', 'Legal Advisor', 'Judge']  # Extra job
        },
        # Poor overlap cases (should be flagged)
        {
            'name': 'Ole Svendsen',
            'book_id': 'book_005',
            'azure_jobs': ['Lege', 'Kirurg', 'Forsker'],
            'monkey_jobs': ['Baker', 'Chef', 'Restaurant Owner']  # Completely different
        },
        {
            'name': 'Liv Andersen',
            'book_id': 'book_006',
            'azure_jobs': ['Professor', 'Dekan', 'Forsker'],
            'monkey_jobs': []  # No monkey jobs
        },
        # One-sided cases (should be flagged)
        {
            'name': 'Per Kristiansen',
            'book_id': 'book_007',
            'azure_jobs': [],
            'monkey_jobs': ['Architect', 'Urban Planner']  # Only monkey jobs
        },
        # Exact matches
        {
            'name': 'Astrid Haugen',
            'book_id': 'book_008',
            'azure_jobs': ['Journalist', 'Redaktør'],
            'monkey_jobs': ['Journalist', 'Editor']
        },
        # Mixed quality matches
        {
            'name': 'Nils Johansen',
            'book_id': 'book_009',
            'azure_jobs': ['Bonde', 'Gårdbruker', 'Småbruker'],
            'monkey_jobs': ['Farmer', 'Fisherman']  # One good match, one mismatch
        },
        {
            'name': 'Ingrid Larsen',
            'book_id': 'book_010',
            'azure_jobs': ['Fisker', 'Kaptein'],
            'monkey_jobs': ['Fisherman', 'Captain', 'Sailor']  # Good matches with extra
        }
    ]
    
    azure_data = []
    monkey_data = []
    
    for scenario in scenarios:
        # Create Azure jobs structure
        azure_jobs = []
        for i, job_title in enumerate(scenario['azure_jobs']):
            azure_jobs.append({
                'title': job_title,
                'location': f'Oslo {i+1}',
                'years': f'{1980 + i*5}-{1985 + i*5}'
            })
        
        # Create Monkey jobs structure
        monkey_jobs = []
        for i, job_title in enumerate(scenario['monkey_jobs']):
            monkey_jobs.append({
                'title': job_title,
                'location': f'Bergen {i+1}',
                'years': f'{1982 + i*5}-{1987 + i*5}'
            })
        
        # Create biography JSON
        azure_bio = {
            'title': 'Hr./Fru',
            'jobs': azure_jobs,
            'birth_date': '1950',
            'birth_place': 'Norge'
        }
        
        monkey_bio = {
            'title': 'Mr./Mrs.',
            'jobs': monkey_jobs,
            'birth_date': '1950',
            'birth_place': 'Norway'
        }
        
        azure_data.append({
            'book_id': scenario['book_id'],
            'name': scenario['name'],
            'biography_json': json.dumps(azure_bio)
        })
        
        monkey_data.append({
            'book_id': scenario['book_id'],
            'name': scenario['name'],
            'biography_json': json.dumps(monkey_bio)
        })
    
    return pd.DataFrame(azure_data), pd.DataFrame(monkey_data)

def main():
    """Main demonstration function"""
    
    print("="*80)
    print("INDIVIDUAL JOB OVERLAP ANALYSIS DEMONSTRATION")
    print("="*80)
    
    # Create demo data
    print("\n1. Creating demo data with varying overlap scenarios...")
    azure_df, monkey_df = create_demo_data_with_varying_overlap()
    
    print(f"   Azure dataframe: {azure_df.shape}")
    print(f"   Monkey dataframe: {monkey_df.shape}")
    
    # Link dataframes
    print("\n2. Linking dataframes...")
    linked_df = fuzzy_link_dataframes(
        azure_df, monkey_df,
        book_id_col='book_id',
        name_col='name',
        suffix1='_azure',
        suffix2='_monkey',
        fuzzy_threshold=80
    )
    
    # Extract job fields
    print("\n3. Extracting job titles...")
    extraction_list = [
        ["jobs", "title", 5]  # Extract up to 5 job titles
    ]
    
    final_df = extract_multiple_json_fields(
        linked_df,
        extraction_list,
        azure_json_col='biography_json_azure',
        monkey_json_col='biography_json_monkey',
        missing_value='Missing'
    )
    
    # Show the data before analysis
    print("\n4. Sample data with extracted job titles:")
    print("-" * 100)
    
    # Select relevant columns for display
    display_cols = ['book_id', 'name_azure', 'name_monkey'] + \
                   [col for col in final_df.columns if 'job' in col.lower() and 'title' in col.lower()]
    
    sample_df = final_df[display_cols].head(10)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 20)
    
    print(sample_df.to_string(index=False))
    
    # Analyze individual job overlap
    print("\n5. Analyzing individual job overlap...")
    individual_results = analyze_individual_job_overlap(
        final_df,
        fuzzy_threshold=80,
        min_overlap_threshold=0.5,  # Flag if overlap coefficient < 50%
        missing_value='Missing'
    )
    
    # Save flagged records
    print("\n6. Saving flagged records...")
    save_flagged_records(individual_results, 'demo_flagged_job_overlap_records.csv')
    
    # Show detailed results
    print("\n7. DETAILED INDIVIDUAL RESULTS:")
    print("-" * 100)
    
    # Sort by overlap coefficient to show worst cases first
    sorted_results = individual_results.sort_values('overlap_coefficient')
    
    for i, (_, row) in enumerate(sorted_results.iterrows(), 1):
        status = "🚩 FLAGGED" if row['needs_inspection'] else "✅ GOOD"
        
        print(f"\n{i:2d}. {row['name_azure']} (Book: {row['book_id']}) - {status}")
        print(f"    Overlap coefficient: {row['overlap_coefficient']:.3f}")
        print(f"    Jaccard similarity: {row['jaccard_similarity']:.3f}")
        print(f"    Azure jobs ({row['total_azure_jobs']}): {row['azure_jobs']}")
        print(f"    Monkey jobs ({row['total_monkey_jobs']}): {row['monkey_jobs']}")
        
        if row['matched_pairs_details']:
            print(f"    ✅ Matches: {row['matched_pairs_details']}")
        
        if row['unmatched_azure_jobs']:
            print(f"    ❌ Unmatched Azure: {row['unmatched_azure_jobs']}")
        
        if row['unmatched_monkey_jobs']:
            print(f"    ❌ Unmatched Monkey: {row['unmatched_monkey_jobs']}")
        
        if row['needs_inspection']:
            print(f"    🚩 Reason: {row['inspection_reason']}")
    
    # Summary statistics
    print(f"\n8. SUMMARY STATISTICS:")
    print("-" * 40)
    
    total_records = len(individual_results)
    flagged_records = len(individual_results[individual_results['needs_inspection'] == True])
    good_records = total_records - flagged_records
    
    print(f"Total records: {total_records}")
    print(f"Flagged for inspection: {flagged_records} ({(flagged_records/total_records)*100:.1f}%)")
    print(f"Good overlap: {good_records} ({(good_records/total_records)*100:.1f}%)")
    
    # Show overlap distribution
    print(f"\nOverlap coefficient distribution:")
    print(f"  Mean: {individual_results['overlap_coefficient'].mean():.3f}")
    print(f"  Median: {individual_results['overlap_coefficient'].median():.3f}")
    print(f"  Min: {individual_results['overlap_coefficient'].min():.3f}")
    print(f"  Max: {individual_results['overlap_coefficient'].max():.3f}")
    
    # Show inspection reasons
    if flagged_records > 0:
        print(f"\nInspection reasons:")
        flagged_df = individual_results[individual_results['needs_inspection'] == True]
        reason_counts = flagged_df['inspection_reason'].value_counts()
        for reason, count in reason_counts.items():
            print(f"  {reason}: {count} records")
    
    print(f"\n9. FILES CREATED:")
    print("-" * 30)
    print("📄 demo_flagged_job_overlap_records.csv - Records flagged for inspection")
    print("📄 demo_flagged_job_overlap_records_all_results.csv - All individual results")
    
    print(f"\n" + "="*80)
    print("INDIVIDUAL JOB OVERLAP ANALYSIS COMPLETED")
    print("="*80)
    
    print(f"\nThis analysis helps identify individuals where job title extraction")
    print(f"differs significantly between Azure and Monkey OCR, allowing you to:")
    print(f"• Focus manual inspection on problematic cases")
    print(f"• Understand the quality of job title extraction")
    print(f"• Identify patterns in extraction failures")
    print(f"• Improve OCR processing for specific job title types")
    
    return individual_results

if __name__ == "__main__":
    results = main()
