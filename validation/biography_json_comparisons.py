# Direct comparison of your pipeline results
import pandas as pd
import json
from difflib import SequenceMatcher
from Levenshtein import distance as levenshtein_distance
from thefuzz import fuzz, process
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

AzureOCR_df = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_portraits_biographies_final.csv')
AzureOCR_df.head()

MonkeyOCR_df = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_csv\extracted_all_names_portraits_biographies_final.csv')
MonkeyOCR_df.head()

AzureOCR_df['biography_json']

# Extract title from biography_json column
def extract_title_from_json(json_str):
    """Extract title from JSON string"""
    try:
        if pd.isna(json_str) or json_str == '':
            return None
        data = json.loads(json_str)
        return data.get('title', None)
    except (json.JSONDecodeError, TypeError):
        return None

# Apply the function to create title column
AzureOCR_df['title'] = AzureOCR_df['biography_json'].apply(extract_title_from_json)

# Display the extracted titles
print("Extracted titles:")
print(AzureOCR_df['title'].head(10))

# Check for any missing titles
missing_titles = AzureOCR_df['title'].isna().sum()
print(f"\nNumber of missing titles: {missing_titles}")

# Show some examples of name and title pairs
print("\nExample name-title pairs:")
print(AzureOCR_df[['biography_json', 'title']].head(5))

# Extract title from MonkeyOCR data as well
if 'biography_json' in MonkeyOCR_df.columns:
    MonkeyOCR_df['title'] = MonkeyOCR_df['biography_json'].apply(extract_title_from_json)
    
    print("\nMonkeyOCR extracted titles:")
    print(MonkeyOCR_df['title'].head(10))
    
    monkey_missing_titles = MonkeyOCR_df['title'].isna().sum()
    print(f"\nNumber of missing titles in MonkeyOCR: {monkey_missing_titles}")
    
    # Compare title extraction between AzureOCR and MonkeyOCR
    print("\nComparison of title extraction:")
    print(f"AzureOCR - Total rows: {len(AzureOCR_df)}, Missing titles: {missing_titles}")
    print(f"MonkeyOCR - Total rows: {len(MonkeyOCR_df)}, Missing titles: {monkey_missing_titles}")
else:
    print("\nNo biography_json column found in MonkeyOCR data")

# Additional utility functions for JSON extraction
def extract_name_from_json(json_str):
    """Extract name from JSON string"""
    try:
        if pd.isna(json_str) or json_str == '':
            return None
        data = json.loads(json_str)
        return data.get('name', None)
    except (json.JSONDecodeError, TypeError):
        return None

def extract_biography_from_json(json_str):
    """Extract biography from JSON string"""
    try:
        if pd.isna(json_str) or json_str == '':
            return None
        data = json.loads(json_str)
        return data.get('biography', None)
    except (json.JSONDecodeError, TypeError):
        return None

def extract_json_field(df, json_column='biography_json', field_name='title', 
                      max_items=None, subfield=None, missing_value=None):
    """
    General function to extract any field from JSON data in a DataFrame.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the JSON data
    json_column : str
        Name of the column containing JSON strings (default: 'biography_json')
    field_name : str
        Name of the field to extract (e.g., 'title', 'name', 'children', 'jobs')
    max_items : int, optional
        For array fields, maximum number of items to extract as separate columns
        (e.g., max_items=5 for 'children' creates child1, child2, child3, child4, child5)
    subfield : str, optional
        For array fields, specific subfield to extract (e.g., 'name' for children names)
    missing_value : str, optional
        Value to use for missing data (default: None)
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with added columns for the extracted field(s)
    
    Examples:
    ---------
    # Extract simple field
    df = extract_json_field(df, field_name='title')
    
    # Extract children names into separate columns
    df = extract_json_field(df, field_name='children', max_items=5, subfield='name')
    
    # Extract job titles
    df = extract_json_field(df, field_name='jobs', max_items=3, subfield='title')
    """
    
    def extract_field(json_str):
        """Extract field from JSON string"""
        try:
            if pd.isna(json_str) or json_str == '':
                return None
            data = json.loads(json_str)
            return data.get(field_name, None)
        except (json.JSONDecodeError, TypeError):
            return None
    
    # Create a copy to avoid modifying the original DataFrame
    result_df = df.copy()
    
    if max_items is None:
        # Simple field extraction
        column_name = field_name
        result_df[column_name] = result_df[json_column].apply(extract_field)
    else:
        # Array field extraction with multiple columns
        # Create better column names (children -> child1, child2, etc.)
        if field_name == 'children':
            base_name = 'child'
        elif field_name == 'jobs':
            base_name = 'job'
        elif field_name == 'educations':
            base_name = 'education'
        elif field_name == 'spouses':
            base_name = 'spouse'
        elif field_name == 'stays_abroad':
            base_name = 'stay_abroad'
        else:
            base_name = field_name[:-1] if field_name.endswith('s') else field_name
        
        for i in range(1, max_items + 1):
            column_name = f"{base_name}{i}"
            result_df[column_name] = missing_value
        
        # Process each row
        for index, row in result_df.iterrows():
            field_data = extract_field(row[json_column])
            
            if field_data and isinstance(field_data, list):
                for i, item in enumerate(field_data[:max_items]):
                    column_name = f"{base_name}{i+1}"
                    
                    if subfield and isinstance(item, dict):
                        # Extract specific subfield from dict
                        value = item.get(subfield, missing_value)
                    else:
                        # Use the item directly
                        value = item
                    
                    result_df.at[index, column_name] = value
    
    return result_df

# Demonstrate the general function
print("\n" + "="*80)
print("DEMONSTRATING GENERAL JSON EXTRACTION FUNCTION")
print("="*80)

# Example 1: Extract title (simple field)
print("\n1. Extracting title:")
df_with_title = extract_json_field(AzureOCR_df, field_name='title')
print(f"Created column: 'title'")
print(df_with_title['title'].head())

# Example 1: Extract title (simple field)
print("\n1. Extracting title:")
df_with_title = extract_json_field(MonkeyOCR_df, field_name='title')
print(f"Created column: 'title'")
print(df_with_title['title'].head())

# Example 2: Extract children names
print("\n2. Extracting children names (up to 5 children):")
df_with_children = extract_json_field(AzureOCR_df, field_name='children', max_items=5, subfield='name', missing_value='No child')
child_columns = [col for col in df_with_children.columns if col.startswith('child')]
print(f"Created columns: {child_columns}")
print(df_with_children[child_columns].head())

# Example 3: Extract job titles
print("\n3. Extracting job titles (up to 3 jobs):")
df_with_jobs = extract_json_field(AzureOCR_df, field_name='jobs', max_items=3, subfield='title', missing_value='No job')
job_columns = [col for col in df_with_jobs.columns if col.startswith('job')]
print(f"Created columns: {job_columns}")
print(df_with_jobs[job_columns].head())

# Example 3: Extract job titles
print("\n3. Extracting job titles (up to 3 jobs):")
df_with_jobs = extract_json_field(MonkeyOCR_df, field_name='jobs', max_items=3, subfield='title', missing_value='No job')
job_columns = [col for col in df_with_jobs.columns if col.startswith('job')]
print(f"Created columns: {job_columns}")
print(df_with_jobs[job_columns].head())


# Example 4: Extract education titles
print("\n4. Extracting education titles (up to 2 educations):")
df_with_education = extract_json_field(AzureOCR_df, field_name='educations', max_items=2, subfield='title', missing_value='No education')
education_columns = [col for col in df_with_education.columns if col.startswith('education')]
print(f"Created columns: {education_columns}")
print(df_with_education[education_columns].head())

# Example 5: Extract spouse names
print("\n5. Extracting spouse names (up to 2 spouses):")
df_with_spouses = extract_json_field(AzureOCR_df, field_name='spouses', max_items=2, subfield='name', missing_value='No spouse')
spouse_columns = [col for col in df_with_spouses.columns if col.startswith('spouse')]
print(f"Created columns: {spouse_columns}")
print(df_with_spouses[spouse_columns].head())

# Example 6: Extract simple fields
print("\n6. Extracting simple fields:")
simple_fields = ['birth_date', 'birth_place', 'death_date', 'father_name', 'mother_name']
df_enhanced = AzureOCR_df.copy()
for field in simple_fields:
    df_enhanced = extract_json_field(df_enhanced, field_name=field)
    print(f"Extracted: {field}")

print(f"\nSimple fields extracted: {simple_fields}")
print(df_enhanced[simple_fields].head())

print("\n" + "="*80)
print("USAGE EXAMPLES FOR THE GENERAL FUNCTION")
print("="*80)
print("""
# Extract any simple field:
df = extract_json_field(df, field_name='title')
df = extract_json_field(df, field_name='birth_date')
df = extract_json_field(df, field_name='father_name')

# Extract array fields with subfields:
df = extract_json_field(df, field_name='children', max_items=5, subfield='name')
df = extract_json_field(df, field_name='jobs', max_items=3, subfield='title')
df = extract_json_field(df, field_name='educations', max_items=2, subfield='institution')

# Extract with custom missing values:
df = extract_json_field(df, field_name='children', max_items=5, subfield='name', missing_value='Missing')
""")

# Save the enhanced dataframes
AzureOCR_df.to_csv('AzureOCR_with_extracted_fields.csv', index=False)
if 'title' in MonkeyOCR_df.columns:
    MonkeyOCR_df.to_csv('MonkeyOCR_with_extracted_fields.csv', index=False)
    print("\nSaved enhanced dataframes with extracted fields")