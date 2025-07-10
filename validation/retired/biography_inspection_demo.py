"""
Example script demonstrating the new biography inspection functions.

This script shows how to use the new functions added to biography_json_comparisons.py:
1. inspect_individual_matching() - Detailed inspection of a single individual
2. quick_inspect() - Quick inspection by name  
3. print_individual_inspection() - Pretty print inspection results

These functions are particularly useful for examining cases where "jobs" and 
"educations" element matching has low similarity scores.
"""

import pandas as pd
import sys
import os

# Add the directory containing the comparison script to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from biography_json_comparisons import (
    compare_ocr_pipeline_results_detailed_filtered,
    inspect_individual_matching,
    quick_inspect,
    print_individual_inspection
)

def demo_inspection_functions():
    """
    Demonstration of the new inspection functions.
    
    This function shows how to use the inspection tools to examine
    individual biographical comparisons, especially for cases with
    low similarity in jobs and educations.
    """
    
    print("=" * 80)
    print("BIOGRAPHY INSPECTION FUNCTIONS DEMO")
    print("=" * 80)
    
    print("""
This script demonstrates the new functions for inspecting individual
biographical element matching results:

1. inspect_individual_matching() - Returns detailed comparison data for a single person
2. quick_inspect() - Quick command-line inspection tool
3. print_individual_inspection() - Pretty prints the inspection results

These functions are designed to help you examine cases where biographical
elements (especially 'jobs' and 'educations') have low similarity scores
between the two OCR pipelines.

TYPICAL WORKFLOW:
================

1. Run the main comparison:
   matched_pairs, comparison_results, summary = compare_ocr_pipeline_results_detailed_filtered(
       dolphin_csv_path="path/to/monkeyocr.csv",
       azureocr_csv_path="path/to/azureocr.csv"
   )

2. Find individuals with low jobs/educations similarity:
   low_jobs_edu = comparison_results[
       (comparison_results['element'].isin(['jobs', 'educations'])) &
       (comparison_results['similarity_score'] < 0.7)
   ]

3. Inspect specific individuals:
   # Quick inspection by name (supports partial matching)
   quick_inspect(matched_pairs, comparison_results, "Anderson")
   
   # Detailed inspection with specific criteria
   result = inspect_individual_matching(
       matched_pairs, comparison_results,
       name="John Smith",
       book_id="2007031501007"
   )
   
   # Pretty print the results
   print_individual_inspection(result, verbose=True)

FUNCTION PARAMETERS:
===================

inspect_individual_matching():
  - matched_pairs: DataFrame from fuzzy name matching
  - comparison_results: DataFrame from element comparison
  - name: Name to search (partial match on either df1 or df2 name)
  - book_id: Filter by specific book ID
  - name_df1, name_df2: Exact names if you want precise matching
  - low_similarity_threshold: Threshold for "low" similarity (default: 0.7)
  - focus_elements: Elements to highlight (default: ['jobs', 'educations'])

quick_inspect():
  - Same as above but simplified interface
  - search_name: Name to search for
  - book_id: Optional book ID filter
  - verbose: Whether to show detailed output

RETURN DATA STRUCTURE:
=====================

The inspect_individual_matching() function returns a dictionary with:
  - individual_info: Basic info about the matched pair
  - element_comparisons: Detailed comparison for each biographical element
  - low_similarity_elements: List of elements with similarity < threshold
  - focus_elements_analysis: Special analysis for jobs/educations
  - summary: Counts of exact matches, high/medium/low similarity

This is especially useful for debugging cases where biographical data
extraction differs significantly between the two OCR pipelines.
""")

def example_usage_code():
    """
    Print example code that users can copy and modify.
    """
    
    print("=" * 80)
    print("EXAMPLE CODE TO COPY AND MODIFY:")
    print("=" * 80)
    
    example_code = '''
# Example 1: Run comparison and find problematic cases
matched_pairs, comparison_results, summary = compare_ocr_pipeline_results_detailed_filtered(
    dolphin_csv_path=r"path/to/your/monkeyocr_results.csv",
    azureocr_csv_path=r"path/to/your/azureocr_results.csv",
    output_path=r"path/to/output/directory",
    name_similarity_threshold=80.0
)

# Example 2: Find individuals with low jobs/educations similarity
problematic_cases = comparison_results[
    (comparison_results['element'].isin(['jobs', 'educations'])) &
    (comparison_results['similarity_score'] < 0.7)
].drop_duplicates(subset=['book_id', 'name_df1', 'name_df2'])

print(f"Found {len(problematic_cases)} individuals with low jobs/educations similarity")

# Example 3: Quick inspection of a specific person
quick_inspect(matched_pairs, comparison_results, "Anderson", verbose=True)

# Example 4: Detailed inspection with custom threshold
result = inspect_individual_matching(
    matched_pairs, comparison_results,
    name="John Smith",
    book_id="2007031501007",
    low_similarity_threshold=0.8  # More strict threshold
)

# Example 5: Examine the first problematic case
if not problematic_cases.empty:
    first_case = problematic_cases.iloc[0]
    print(f"Inspecting: {first_case['name_df1']} from book {first_case['book_id']}")
    
    detailed_result = inspect_individual_matching(
        matched_pairs, comparison_results,
        name_df1=first_case['name_df1'],
        name_df2=first_case['name_df2'],
        book_id=first_case['book_id']
    )
    
    print_individual_inspection(detailed_result, verbose=True)

# Example 6: Focus on specific elements only
result = inspect_individual_matching(
    matched_pairs, comparison_results,
    name="Anderson",
    focus_elements=['jobs', 'educations', 'spouses']  # Custom focus elements
)
'''
    
    print(example_code)

if __name__ == "__main__":
    demo_inspection_functions()
    example_usage_code()
    
    print("=" * 80)
    print("To use these functions with your data:")
    print("1. Update the file paths in the example code above")
    print("2. Run the comparison to get matched_pairs and comparison_results")
    print("3. Use the inspection functions to examine specific individuals")
    print("4. Focus on cases where jobs/educations similarity is low")
    print("=" * 80)
