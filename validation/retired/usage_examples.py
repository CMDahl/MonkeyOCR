"""
Simple usage example for the comprehensive JSON extraction functions
"""
from comprehensive_json_extraction import fuzzy_link_dataframes, extract_multiple_json_fields, create_comparison_dataframe
import pandas as pd

# Load your data
print("Loading data...")
AzureOCR_df = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_portraits_biographies_final.csv')
MonkeyOCR_df = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_csv\extracted_all_names_portraits_biographies_final.csv')

print("="*60)
print("EXAMPLE 1: BASIC LINKING")
print("="*60)

# Example 1: Basic linking with fuzzy matching
linked_df = fuzzy_link_dataframes(
    AzureOCR_df, MonkeyOCR_df,
    book_id_col='book_id',
    name_col='name',
    suffix1='_azure',
    suffix2='_monkey',
    fuzzy_threshold=90
)

print(f"Linked dataframe shape: {linked_df.shape}")
print(f"Sample linked records:")
print(linked_df[['book_id', 'name_azure', 'name_monkey', 'fuzzy_score']].head(3))

print("\n" + "="*60)
print("EXAMPLE 2: CUSTOM EXTRACTION LIST")
print("="*60)

# Example 2: Custom extraction specification
custom_extraction_list = [
    ["title"],  # Simple field
    ["children", "name", "birth_date", 2],  # Children name and birth_date, max 2
    ["jobs", "title", 3]  # Job titles only, max 3
]

comparison_df = create_comparison_dataframe(
    AzureOCR_df, MonkeyOCR_df,
    extraction_list=custom_extraction_list,
    book_id_col='book_id',
    name_col='name',
    fuzzy_threshold=90,
    missing_value='Missing'
)

print(f"Custom comparison dataframe shape: {comparison_df.shape}")
print(f"Columns: {[col for col in comparison_df.columns if 'title' in col or 'child' in col or 'job' in col]}")

print("\n" + "="*60)
print("EXAMPLE 3: DIFFERENT EXTRACTION SPECIFICATIONS")
print("="*60)

# Example 3: Different extraction specifications
examples = [
    {
        "name": "Basic biographical info",
        "extraction_list": [
            ["title"],
            ["birth_date"],
            ["birth_place"],
            ["father_name"],
            ["mother_name"]
        ]
    },
    {
        "name": "Education and career focus",
        "extraction_list": [
            ["title"],
            ["educations", "title", "institution", "year", 2],
            ["jobs", "title", "location", "years", 3]
        ]
    },
    {
        "name": "Family information",
        "extraction_list": [
            ["children", "name", "birth_date", 3],
            ["spouses", "name", "birth_date", 2],
            ["father_name"],
            ["mother_name"]
        ]
    }
]

for example in examples:
    print(f"\n{example['name']}:")
    test_df = create_comparison_dataframe(
        AzureOCR_df.head(50), MonkeyOCR_df.head(50),  # Use smaller sample for demo
        extraction_list=example['extraction_list'],
        missing_value='N/A'
    )
    print(f"  Shape: {test_df.shape}")
    print(f"  Columns: {test_df.columns.tolist()}")
test_df
print("\n" + "="*60)
print("USAGE PATTERNS")
print("="*60)

print("""
EXTRACTION LIST SYNTAX:
=======================

# Simple fields (creates field_azure, field_monkey):
["title"]
["birth_date"]
["father_name"]

# Array with single subfield (creates base1_subfield_azure, base1_subfield_monkey, etc.):
["jobs", "title", 3]                    # job1_title_azure, job1_title_monkey, job2_title_azure, etc.
["children", "name", 2]                 # child1_name_azure, child1_name_monkey, child2_name_azure, etc.

# Array with multiple subfields:
["educations", "title", "year", 3]      # education1_title_azure, education1_year_azure, etc.
["children", "name", "birth_date", 2]   # child1_name_azure, child1_birth_date_azure, etc.
["jobs", "title", "location", "years", 3] # job1_title_azure, job1_location_azure, job1_years_azure, etc.

FUNCTION USAGE:
===============

# 1. Just link dataframes:
linked_df = fuzzy_link_dataframes(df1, df2, book_id_col='book_id', name_col='name')

# 2. Extract from already linked dataframe:
extracted_df = extract_multiple_json_fields(linked_df, extraction_list, 
                                           azure_json_col='biography_json_azure',
                                           monkey_json_col='biography_json_monkey')

# 3. Complete workflow (recommended):
final_df = create_comparison_dataframe(df1, df2, extraction_list, 
                                      fuzzy_threshold=80, missing_value='Missing')
""")
