"""
Test script to verify enhanced job title unmatched functionality with file creation
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

def test_enhanced_unmatched_with_file_creation():
    """Test the enhanced unmatched job titles functionality with file creation"""
    
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
        
        # Manually create the enhanced unmatched file as done in the main workflow
        print("\nCreating enhanced unmatched file...")
        
        if results['unmatched_azure_titles'] or results['unmatched_monkey_titles']:
            unmatched_data = []
            
            # Add unmatched Azure titles with record details
            for title in results['unmatched_azure_titles']:
                azure_job_cols = [col for col in test_df.columns if 'job' in col.lower() and 'title' in col.lower() and col.endswith('_azure')]
                for col in azure_job_cols:
                    if col in test_df.columns:
                        matching_rows = test_df[test_df[col] == title]
                        for _, row in matching_rows.iterrows():
                            unmatched_data.append({
                                'title': title,
                                'source': 'Azure',
                                'matched': False,
                                'book_id': row['book_id'],
                                'name_azure': row['name_azure'],
                                'name_monkey': row['name_monkey'],
                                'job_column': col
                            })
            
            # Add unmatched Monkey titles with record details
            for title in results['unmatched_monkey_titles']:
                monkey_job_cols = [col for col in test_df.columns if 'job' in col.lower() and 'title' in col.lower() and col.endswith('_monkey')]
                for col in monkey_job_cols:
                    if col in test_df.columns:
                        matching_rows = test_df[test_df[col] == title]
                        for _, row in matching_rows.iterrows():
                            unmatched_data.append({
                                'title': title,
                                'source': 'Monkey',
                                'matched': False,
                                'book_id': row['book_id'],
                                'name_azure': row['name_azure'],
                                'name_monkey': row['name_monkey'],
                                'job_column': col
                            })
            
            if unmatched_data:
                unmatched_df = pd.DataFrame(unmatched_data)
                unmatched_df.to_csv('job_title_unmatched_enhanced.csv', index=False)
                print(f"Saved enhanced unmatched job titles to: job_title_unmatched_enhanced.csv")
                
                # Show sample of enhanced file
                print(f"\nEnhanced unmatched file preview:")
                print(f"Total records: {len(unmatched_df)}")
                print(f"Columns: {unmatched_df.columns.tolist()}")
                print(f"\nSample records:")
                print(unmatched_df.head())
                
                # Show statistics
                print(f"\nStatistics by source:")
                print(unmatched_df['source'].value_counts())
                
                print(f"\nStatistics by job column:")
                print(unmatched_df['job_column'].value_counts())
                
        # Also create the matched pairs file
        if results['matched_pairs_details']:
            matched_pairs_df = pd.DataFrame(results['matched_pairs_details'])
            matched_pairs_df.to_csv('job_title_matched_pairs_enhanced.csv', index=False)
            print(f"\nSaved matched pairs to: job_title_matched_pairs_enhanced.csv")
            print(f"Matched pairs preview:")
            print(matched_pairs_df.head())
        
    else:
        print(f"Error: {results['error']}")

if __name__ == "__main__":
    test_enhanced_unmatched_with_file_creation()
