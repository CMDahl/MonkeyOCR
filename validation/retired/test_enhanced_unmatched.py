"""
Test script to verify the enhanced job title unmatched functionality
"""

import pandas as pd
import numpy as np
from comprehensive_json_extraction import compute_job_title_overlap

def create_test_data_with_ids():
    """Create test data with book_id and name information"""
    
    # Sample data with job titles and identity information
    test_data = {
        'book_id': ['book1', 'book2', 'book3', 'book4', 'book5', 'book6', 'book7', 'book8', 'book9', 'book10'],
        'name_azure': ['John Smith', 'Jane Doe', 'Bob Johnson', 'Alice Brown', 'Charlie Davis', 
                      'Diana Wilson', 'Frank Miller', 'Grace Lee', 'Henry Taylor', 'Ivy Anderson'],
        'name_monkey': ['John Smith', 'Jane Doe', 'Bob Johnson', 'Alice Brown', 'Charlie Davis',
                       'Diana Wilson', 'Frank Miller', 'Grace Lee', 'Henry Taylor', 'Ivy Anderson'],
        'job1_title_azure': ['Doctor', 'Teacher', 'Engineer', 'Lawyer', 'Nurse',
                            'Architect', 'Writer', 'Artist', 'Scientist', 'Chef'],
        'job1_title_monkey': ['Physician', 'Educator', 'Engineer', 'Attorney', 'Nurse',
                             'Architect', 'Author', 'Painter', 'Researcher', 'Cook'],
        'job2_title_azure': ['Professor', 'Principal', 'Missing', 'Judge', 'Missing',
                            'Designer', 'Editor', 'Missing', 'Professor', 'Missing'],
        'job2_title_monkey': ['Professor', 'Headmaster', 'Missing', 'Judge', 'Missing',
                             'Designer', 'Editor', 'Missing', 'Academic', 'Missing'],
        'job3_title_azure': ['Consultant', 'Missing', 'Missing', 'Missing', 'Missing',
                            'Missing', 'Missing', 'Missing', 'Missing', 'Missing'],
        'job3_title_monkey': ['Advisor', 'Missing', 'Missing', 'Missing', 'Missing',
                             'Missing', 'Missing', 'Missing', 'Missing', 'Missing']
    }
    
    return pd.DataFrame(test_data)

def test_enhanced_unmatched_functionality():
    """Test the enhanced unmatched job titles functionality"""
    
    print("Creating test data with book_id and name information...")
    test_df = create_test_data_with_ids()
    
    print("\nTest data preview:")
    print(test_df[['book_id', 'name_azure', 'job1_title_azure', 'job1_title_monkey', 'job2_title_azure', 'job2_title_monkey']].head())
    
    print("\nTesting enhanced job title overlap function...")
    
    # Test with a threshold that will create some unmatched titles
    results = compute_job_title_overlap(
        test_df,
        fuzzy_threshold=85,  # Higher threshold to create more unmatched titles
        missing_value='Missing'
    )
    
    if 'error' not in results:
        print(f"\nResults summary:")
        print(f"Azure titles: {results['total_azure_titles']}")
        print(f"Monkey titles: {results['total_monkey_titles']}")
        print(f"Matched pairs: {results['matched_pairs']}")
        print(f"Unmatched Azure titles: {len(results['unmatched_azure_titles'])}")
        print(f"Unmatched Monkey titles: {len(results['unmatched_monkey_titles'])}")
        
        # Check if files were created
        import os
        files_to_check = ['job_title_matched_pairs.csv', 'job_title_unmatched.csv', 'job_title_overlap_summary.csv']
        
        print(f"\nChecking output files:")
        for file in files_to_check:
            if os.path.exists(file):
                print(f"✓ {file} exists")
                if file == 'job_title_unmatched.csv':
                    # Check the content of the unmatched file
                    unmatched_df = pd.read_csv(file)
                    print(f"  - Contains {len(unmatched_df)} records")
                    print(f"  - Columns: {unmatched_df.columns.tolist()}")
                    if not unmatched_df.empty:
                        print(f"  - Sample record:")
                        print(f"    {unmatched_df.iloc[0].to_dict()}")
            else:
                print(f"✗ {file} not found")
    else:
        print(f"Error: {results['error']}")

if __name__ == "__main__":
    test_enhanced_unmatched_functionality()
