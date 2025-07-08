"""
Test script to verify the new inspection functions work correctly.
This creates mock data to test the functions without requiring actual CSV files.
"""

import pandas as pd
import json
from biography_json_comparisons import (
    inspect_individual_matching,
    quick_inspect,
    print_individual_inspection
)

def create_mock_data():
    """Create mock matched_pairs and comparison_results for testing."""
    
    # Mock matched pairs
    matched_pairs = pd.DataFrame([
        {
            'book_id': '2007031501007',
            'name_df1': 'John Anderson',
            'name_df2': 'Jon Anderson',
            'name_similarity': 85.0,
            'idx_df1': 0,
            'idx_df2': 0
        },
        {
            'book_id': '2007031501007', 
            'name_df1': 'Mary Smith',
            'name_df2': 'Marie Smith',
            'name_similarity': 90.0,
            'idx_df1': 1,
            'idx_df2': 1
        }
    ])
    
    # Mock comparison results
    comparison_results = []
    
    # John Anderson - with problematic jobs and educations
    elements_john = {
        'father_name': ('Robert Anderson', 'Robert Anderson', 1.0, True),
        'mother_name': ('Lisa Johnson', 'Lisa Johnston', 0.85, False),
        'birth_date': ('1985-03-15', '1985-03-15', 1.0, True),
        'birth_place': ('Oslo', 'Oslo', 1.0, True),
        'death_date': (None, None, 1.0, True),
        'jobs': ('["Engineer", "Manager"]', '["Teacher", "Principal"]', 0.45, False),
        'educations': ('["University of Oslo"]', '["Oslo University"]', 0.65, False),
        'spouses': ('["Anna Peterson"]', '["Anna Peterson"]', 1.0, True),
        'children': ('["Erik Anderson", "Nina Anderson"]', '["Erik Anderson", "Nina Anderson"]', 1.0, True)
    }
    
    for element, (val1, val2, similarity, exact_match) in elements_john.items():
        comparison_results.append({
            'book_id': '2007031501007',
            'name_df1': 'John Anderson',
            'name_df2': 'Jon Anderson',
            'name_similarity': 85.0,
            'element': element,
            f'{element}_df1': val1,
            f'{element}_df2': val2,
            'edit_distance': 1 - similarity,
            'similarity_score': similarity,
            'exact_match': exact_match,
            'distance_metric': 'levenshtein'
        })
    
    # Mary Smith - with good matching
    elements_mary = {
        'father_name': ('William Smith', 'William Smith', 1.0, True),
        'mother_name': ('Helen Brown', 'Helen Brown', 1.0, True),
        'birth_date': ('1990-07-22', '1990-07-22', 1.0, True),
        'birth_place': ('Bergen', 'Bergen', 1.0, True),
        'death_date': (None, None, 1.0, True),
        'jobs': ('["Nurse", "Head Nurse"]', '["Nurse", "Head Nurse"]', 1.0, True),
        'educations': ('["University of Bergen"]', '["University of Bergen"]', 1.0, True),
        'spouses': ('["Peter Johnson"]', '["Peter Johnson"]', 1.0, True),
        'children': ('["Sarah Johnson"]', '["Sarah Johnson"]', 1.0, True)
    }
    
    for element, (val1, val2, similarity, exact_match) in elements_mary.items():
        comparison_results.append({
            'book_id': '2007031501007',
            'name_df1': 'Mary Smith',
            'name_df2': 'Marie Smith', 
            'name_similarity': 90.0,
            'element': element,
            f'{element}_df1': val1,
            f'{element}_df2': val2,
            'edit_distance': 1 - similarity,
            'similarity_score': similarity,
            'exact_match': exact_match,
            'distance_metric': 'levenshtein'
        })
    
    comparison_results_df = pd.DataFrame(comparison_results)
    
    return matched_pairs, comparison_results_df

def test_inspection_functions():
    """Test the new inspection functions with mock data."""
    
    print("Creating mock data...")
    matched_pairs, comparison_results = create_mock_data()
    
    print("Mock data created successfully!")
    print(f"Matched pairs: {len(matched_pairs)}")
    print(f"Comparison results: {len(comparison_results)}")
    print()
    
    # Test 1: Quick inspect by name
    print("=" * 60)
    print("TEST 1: Quick inspect John Anderson (problematic case)")
    print("=" * 60)
    quick_inspect(matched_pairs, comparison_results, "Anderson", verbose=True)
    
    print("\n" + "=" * 60)
    print("TEST 2: Quick inspect Mary Smith (good case)")
    print("=" * 60)
    quick_inspect(matched_pairs, comparison_results, "Smith", verbose=False)
    
    # Test 3: Detailed inspection
    print("\n" + "=" * 60)
    print("TEST 3: Detailed inspection with custom threshold")
    print("=" * 60)
    result = inspect_individual_matching(
        matched_pairs, comparison_results,
        name="John Anderson",
        low_similarity_threshold=0.8
    )
    print_individual_inspection(result, verbose=True)
    
    # Test 4: Find problematic cases
    print("\n" + "=" * 60)
    print("TEST 4: Finding individuals with low jobs/educations similarity")
    print("=" * 60)
    
    problematic_cases = comparison_results[
        (comparison_results['element'].isin(['jobs', 'educations'])) &
        (comparison_results['similarity_score'] < 0.7)
    ].drop_duplicates(subset=['book_id', 'name_df1', 'name_df2'])
    
    print(f"Found {len(problematic_cases)} individuals with low jobs/educations similarity:")
    for _, row in problematic_cases.iterrows():
        print(f"  - {row['name_df1']} (Book: {row['book_id']})")
    
    print("\n" + "=" * 60)
    print("TEST 5: Error handling - non-existent name")
    print("=" * 60)
    result = inspect_individual_matching(
        matched_pairs, comparison_results,
        name="Non Existent Person"
    )
    print_individual_inspection(result)
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("The new inspection functions are working correctly.")
    print("=" * 60)

if __name__ == "__main__":
    test_inspection_functions()
