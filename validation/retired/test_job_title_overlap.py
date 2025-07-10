"""
Test script for job title overlap function
"""

import pandas as pd
import numpy as np
from comprehensive_json_extraction import compute_job_title_overlap

def create_test_data():
    """Create test data with job titles"""
    
    # Sample data with job titles
    test_data = {
        'book_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'name_azure': ['Person A', 'Person B', 'Person C', 'Person D', 'Person E', 
                      'Person F', 'Person G', 'Person H', 'Person I', 'Person J'],
        'name_monkey': ['Person A', 'Person B', 'Person C', 'Person D', 'Person E',
                       'Person F', 'Person G', 'Person H', 'Person I', 'Person J'],
        'job1_title_azure': ['Doctor', 'Teacher', 'Engineer', 'Lawyer', 'Nurse',
                            'Architect', 'Writer', 'Artist', 'Scientist', 'Chef'],
        'job1_title_monkey': ['Physician', 'Educator', 'Engineer', 'Attorney', 'Nurse',
                             'Architect', 'Author', 'Painter', 'Researcher', 'Cook'],
        'job2_title_azure': ['Professor', 'Principal', 'Missing', 'Judge', 'Missing',
                            'Designer', 'Editor', 'Missing', 'Professor', 'Missing'],
        'job2_title_monkey': ['Professor', 'Headmaster', 'Missing', 'Judge', 'Missing',
                             'Designer', 'Editor', 'Missing', 'Academic', 'Missing'],
        'job3_title_azure': ['Missing', 'Missing', 'Missing', 'Missing', 'Missing',
                            'Missing', 'Missing', 'Missing', 'Missing', 'Missing'],
        'job3_title_monkey': ['Missing', 'Missing', 'Missing', 'Missing', 'Missing',
                             'Missing', 'Missing', 'Missing', 'Missing', 'Missing']
    }
    
    return pd.DataFrame(test_data)

def test_job_title_overlap():
    """Test the job title overlap function"""
    
    print("Creating test data...")
    test_df = create_test_data()
    
    print("\nTest data:")
    print(test_df[['name_azure', 'job1_title_azure', 'job1_title_monkey', 'job2_title_azure', 'job2_title_monkey']].head())
    
    print("\nTesting job title overlap function...")
    
    # Test with different thresholds
    for threshold in [60, 70, 80, 90]:
        print(f"\n" + "="*60)
        print(f"TESTING WITH THRESHOLD: {threshold}")
        print("="*60)
        
        results = compute_job_title_overlap(
            test_df,
            fuzzy_threshold=threshold,
            missing_value='Missing'
        )
        
        if 'error' not in results:
            print(f"\nSUMMARY FOR THRESHOLD {threshold}:")
            print(f"Azure titles: {results['total_azure_titles']}")
            print(f"Monkey titles: {results['total_monkey_titles']}")
            print(f"Matched pairs: {results['matched_pairs']}")
            print(f"Jaccard similarity: {results['jaccard_similarity']:.3f}")
            print(f"Overlap coefficient: {results['overlap_coefficient']:.3f}")
            print(f"Dice coefficient: {results['dice_coefficient']:.3f}")
        else:
            print(f"Error: {results['error']}")

if __name__ == "__main__":
    test_job_title_overlap()
