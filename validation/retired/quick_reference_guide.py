"""
COMPREHENSIVE JSON EXTRACTION - QUICK REFERENCE GUIDE
======================================================

This guide shows how to use the three main functions for linking dataframes 
and extracting JSON fields from MonkeyOCR validation data.

FUNCTIONS OVERVIEW:
==================

1. fuzzy_link_dataframes() - Links two dataframes using book_id and fuzzy name matching
2. extract_multiple_json_fields() - Extracts multiple JSON fields from linked dataframes
3. create_comparison_dataframe() - Complete workflow (recommended)

BASIC USAGE:
============
"""

from comprehensive_json_extraction import create_comparison_dataframe
import pandas as pd

# Load your dataframes
AzureOCR_df = pd.read_csv('azure_data.csv')
MonkeyOCR_df = pd.read_csv('monkey_data.csv')

# Define what you want to extract
extraction_list = [
    ["title"],                              # Simple field
    ["educations", "title", "year", 3],     # 3 education titles and years
    ["children", "name", "birth_date", 2]   # 2 children names and birth dates
]

# Create comparison dataframe
result_df = create_comparison_dataframe(
    AzureOCR_df, MonkeyOCR_df, 
    extraction_list=extraction_list,
    fuzzy_threshold=80,
    missing_value='Missing'
)

print("""
EXTRACTION LIST SYNTAX:
=======================

Simple fields:
--------------
["title"]           → title_azure, title_monkey
["birth_date"]      → birth_date_azure, birth_date_monkey
["father_name"]     → father_name_azure, father_name_monkey

Array with single subfield:
---------------------------
["jobs", "title", 3]                    → job1_title_azure, job1_title_monkey, 
                                          job2_title_azure, job2_title_monkey,
                                          job3_title_azure, job3_title_monkey

["children", "name", 2]                 → child1_name_azure, child1_name_monkey,
                                          child2_name_azure, child2_name_monkey

Array with multiple subfields:
------------------------------
["educations", "title", "year", 3]      → education1_title_azure, education1_year_azure,
                                          education2_title_azure, education2_year_azure,
                                          education3_title_azure, education3_year_azure
                                          (same with _monkey suffix)

["children", "name", "birth_date", 2]   → child1_name_azure, child1_birth_date_azure,
                                          child2_name_azure, child2_birth_date_azure
                                          (same with _monkey suffix)

["jobs", "title", "location", "years", 3] → job1_title_azure, job1_location_azure, job1_years_azure,
                                            job2_title_azure, job2_location_azure, job2_years_azure,
                                            job3_title_azure, job3_location_azure, job3_years_azure
                                            (same with _monkey suffix)

EXAMPLE USE CASES:
==================

1. Basic Comparison:
-------------------
extraction_list = [
    ["title"],
    ["birth_date"],
    ["birth_place"]
]

2. Education Focus:
------------------
extraction_list = [
    ["title"],
    ["educations", "title", "institution", "year", 2],
    ["jobs", "title", "location", 3]
]

3. Family Information:
---------------------
extraction_list = [
    ["children", "name", "birth_date", "birth_place", 3],
    ["spouses", "name", "birth_date", 2],
    ["father_name"],
    ["mother_name"]
]

4. Career Timeline:
------------------
extraction_list = [
    ["title"],
    ["jobs", "title", "location", "years", 5],
    ["educations", "title", "year", 3]
]

FUNCTION PARAMETERS:
===================

create_comparison_dataframe():
------------------------------
- df1, df2: Input dataframes
- extraction_list: List of extraction specifications
- book_id_col: Column name for book_id (default: 'book_id')
- name_col: Column name for name (default: 'name')
- fuzzy_threshold: Minimum fuzzy score for matching (default: 80)
- missing_value: Value for missing data (default: 'Missing')

OUTPUT STRUCTURE:
================

The output dataframe will have:
- book_id: Common book identifier
- name_azure, name_monkey: Names from both sources
- fuzzy_score: Similarity score for name matching
- All extracted fields with _azure and _monkey suffixes

EXAMPLE OUTPUT COLUMNS:
======================

For extraction_list = [["title"], ["children", "name", "birth_date", 2]]:

- book_id
- name_azure, name_monkey
- fuzzy_score  
- title_azure, title_monkey
- child1_name_azure, child1_name_monkey
- child1_birth_date_azure, child1_birth_date_monkey
- child2_name_azure, child2_name_monkey
- child2_birth_date_azure, child2_birth_date_monkey

TIPS:
=====

1. Use fuzzy_threshold=80 for good matches, lower for more permissive matching
2. Set missing_value='Missing' or 'N/A' for clear identification of missing data
3. For large datasets, test with smaller samples first
4. The fuzzy_score column helps identify potential matching issues
5. Array fields automatically handle cases where someone has fewer items than max_items

AVAILABLE JSON FIELDS:
=====================

Simple fields: title, birth_date, birth_place, death_date, father_name, mother_name, father_job

Array fields: 
- children (subfields: name, birth_date, birth_place)
- jobs (subfields: title, location, years)
- educations (subfields: title, institution, year)
- spouses (subfields: name, birth_date, birth_place)
- stays_abroad (subfields: location, years, purpose)
""")

# Example of actual usage
if __name__ == "__main__":
    print("Loading example data...")
    
    # Your actual example
    example_extraction = [
        ["title"],
        ["educations", "title", "year", 3],
        ["children", "name", "birth_date", 2]
    ]
    
    print(f"Example extraction specification: {example_extraction}")
    print("\nThis will create columns:")
    print("- title_azure, title_monkey")
    print("- education1_title_azure, education1_year_azure, education1_title_monkey, education1_year_monkey")
    print("- education2_title_azure, education2_year_azure, education2_title_monkey, education2_year_monkey")
    print("- education3_title_azure, education3_year_azure, education3_title_monkey, education3_year_monkey")
    print("- child1_name_azure, child1_birth_date_azure, child1_name_monkey, child1_birth_date_monkey")
    print("- child2_name_azure, child2_birth_date_azure, child2_name_monkey, child2_birth_date_monkey")
