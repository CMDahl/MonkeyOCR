"""
Practical Individual Job Overlap Analysis Demo

This script demonstrates the individual job overlap analysis with Norwegian data,
using appropriate fuzzy thresholds and showing realistic scenarios.
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

def create_realistic_norwegian_data():
    """Create realistic Norwegian job data with varying overlap scenarios"""
    
    # More realistic scenarios with Norwegian job titles
    scenarios = [
        # Good overlap - similar Norwegian titles
        {
            'name': 'Ola Nordmann',
            'book_id': 'book_001',
            'azure_jobs': ['lærer', 'rektor', 'skolebestyrer'],
            'monkey_jobs': ['lærer', 'rector', 'skolestyrer']
        },
        # Moderate overlap - some matches
        {
            'name': 'Kari Andersen',
            'book_id': 'book_002',
            'azure_jobs': ['sykepleier', 'avdelingsleder'],
            'monkey_jobs': ['sykepleierske', 'avdelingsleder']
        },
        # Good overlap - exact matches
        {
            'name': 'Lars Hansen',
            'book_id': 'book_003',
            'azure_jobs': ['ingeniør', 'prosjektleder'],
            'monkey_jobs': ['ingeniør', 'prosjektleder']
        },
        # Poor overlap - should be flagged
        {
            'name': 'Anna Olsen',
            'book_id': 'book_004',
            'azure_jobs': ['lege', 'kirurg'],
            'monkey_jobs': ['baker', 'konditor']  # Completely different
        },
        # One-sided - should be flagged
        {
            'name': 'Erik Berg',
            'book_id': 'book_005',
            'azure_jobs': ['advokat', 'dommer'],
            'monkey_jobs': []  # No monkey jobs
        },
        # Mixed case - partial matches
        {
            'name': 'Liv Haugen',
            'book_id': 'book_006',
            'azure_jobs': ['journalist', 'redaktør', 'forfatter'],
            'monkey_jobs': ['journalist', 'forlegger']  # 1 match, 1 mismatch each
        },
        # Spelling variations - should match
        {
            'name': 'Per Johansen',
            'book_id': 'book_007',
            'azure_jobs': ['bokholder', 'regnskapsfører'],
            'monkey_jobs': ['bokkholder', 'regnskapsfører']
        },
        # Different but related jobs
        {
            'name': 'Astrid Larsen',
            'book_id': 'book_008',
            'azure_jobs': ['bibliotekar', 'arkivar'],
            'monkey_jobs': ['biblioteksassistent', 'arkivar']
        },
        # Only monkey jobs - should be flagged
        {
            'name': 'Nils Kristiansen',
            'book_id': 'book_009',
            'azure_jobs': [],
            'monkey_jobs': ['fisker', 'kaptein']
        },
        # Perfect overlap
        {
            'name': 'Ingrid Svendsen',
            'book_id': 'book_010',
            'azure_jobs': ['professor', 'forsker'],
            'monkey_jobs': ['professor', 'forsker']
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
                'location': f'Oslo',
                'years': f'{1970 + i*5}-{1980 + i*5}'
            })
        
        # Create Monkey jobs structure
        monkey_jobs = []
        for i, job_title in enumerate(scenario['monkey_jobs']):
            monkey_jobs.append({
                'title': job_title,
                'location': f'Bergen',
                'years': f'{1975 + i*5}-{1985 + i*5}'
            })
        
        # Create biography JSON
        azure_bio = {
            'title': 'Hr./Fru',
            'jobs': azure_jobs,
            'birth_date': '1945',
            'birth_place': 'Norge'
        }
        
        monkey_bio = {
            'title': 'Hr./Fru',
            'jobs': monkey_jobs,
            'birth_date': '1945',
            'birth_place': 'Norge'
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
    print("PRACTICAL INDIVIDUAL JOB OVERLAP ANALYSIS")
    print("="*80)
    
    # Create realistic Norwegian data
    print("\n1. Creating realistic Norwegian job data...")
    azure_df, monkey_df = create_realistic_norwegian_data()
    
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
    
    # Test different fuzzy thresholds
    thresholds = [60, 70, 80, 90]
    
    print("\n4. Testing different fuzzy thresholds...")
    print("-" * 80)
    
    for threshold in thresholds:
        print(f"\n--- FUZZY THRESHOLD: {threshold} ---")
        
        individual_results = analyze_individual_job_overlap(
            final_df,
            fuzzy_threshold=threshold,
            min_overlap_threshold=0.4,  # More lenient for demonstration
            missing_value='Missing'
        )
        
        # Show summary for this threshold
        total_records = len(individual_results)
        flagged_records = len(individual_results[individual_results['needs_inspection'] == True])
        good_records = total_records - flagged_records
        
        print(f"Summary for threshold {threshold}:")
        print(f"  Total records: {total_records}")
        print(f"  Flagged: {flagged_records} ({(flagged_records/total_records)*100:.1f}%)")
        print(f"  Good overlap: {good_records} ({(good_records/total_records)*100:.1f}%)")
        print(f"  Avg overlap coefficient: {individual_results['overlap_coefficient'].mean():.3f}")
        
        # Show top 3 best and worst cases
        sorted_results = individual_results.sort_values('overlap_coefficient', ascending=False)
        
        print(f"  Best overlap cases:")
        for i, (_, row) in enumerate(sorted_results.head(3).iterrows(), 1):
            print(f"    {i}. {row['name_azure']} - {row['overlap_coefficient']:.3f}")
        
        print(f"  Worst overlap cases:")
        for i, (_, row) in enumerate(sorted_results.tail(3).iterrows(), 1):
            print(f"    {i}. {row['name_azure']} - {row['overlap_coefficient']:.3f}")
    
    # Use optimal threshold (70) for detailed analysis
    print("\n5. DETAILED ANALYSIS WITH OPTIMAL THRESHOLD (70):")
    print("-" * 80)
    
    final_results = analyze_individual_job_overlap(
        final_df,
        fuzzy_threshold=70,
        min_overlap_threshold=0.4,
        missing_value='Missing'
    )
    
    # Save results
    save_flagged_records(final_results, 'practical_flagged_job_overlap_records.csv')
    
    # Show detailed individual results
    print("\n6. INDIVIDUAL RESULTS BREAKDOWN:")
    print("-" * 80)
    
    sorted_results = final_results.sort_values('overlap_coefficient', ascending=False)
    
    for i, (_, row) in enumerate(sorted_results.iterrows(), 1):
        status = "✅ GOOD" if not row['needs_inspection'] else "🚩 FLAGGED"
        
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
    
    # Final recommendations
    print(f"\n7. RECOMMENDATIONS:")
    print("-" * 40)
    
    flagged_count = len(final_results[final_results['needs_inspection'] == True])
    total_count = len(final_results)
    
    print(f"• {flagged_count} out of {total_count} records need manual inspection")
    print(f"• Focus on records with 'Jobs in both but no matches' - these may indicate:")
    print(f"  - OCR recognition differences")
    print(f"  - Spelling variations")
    print(f"  - Different job title formats")
    print(f"• Records with only Azure or only Monkey jobs may indicate:")
    print(f"  - Extraction failures")
    print(f"  - Different JSON structure interpretations")
    print(f"• Use the CSV files for systematic manual review")
    
    print(f"\n8. FILES CREATED:")
    print("-" * 30)
    print("📄 practical_flagged_job_overlap_records.csv - Flagged records")
    print("📄 practical_flagged_job_overlap_records_all_results.csv - All results")
    
    print(f"\n" + "="*80)
    print("PRACTICAL ANALYSIS COMPLETED")
    print("="*80)
    
    return final_results

if __name__ == "__main__":
    results = main()
