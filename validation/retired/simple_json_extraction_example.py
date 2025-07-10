"""
Simple usage examples for the general JSON extraction function
"""
import pandas as pd
from biography_json_comparisons import extract_json_field

# Load your data
AzureOCR_df = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_portraits_biographies_final.csv')

print("="*60)
print("GENERAL JSON EXTRACTION FUNCTION USAGE")
print("="*60)

# Example 1: Extract title
print("\n1. Extract title:")
df_with_title = extract_json_field(AzureOCR_df, field_name='title')
print(f"Created column: 'title'")
print(f"Sample values: {df_with_title['title'].head(5).tolist()}")

# Example 2: Extract children names (creates child1, child2, child3, child4, child5)
print("\n2. Extract children names (max 5):")
df_with_children = extract_json_field(AzureOCR_df, field_name='children', max_items=5, subfield='name')
print("Created columns: child1, child2, child3, child4, child5")
print("Sample data:")
print(df_with_children[['child1', 'child2', 'child3', 'child4', 'child5']].head(3))

# Example 3: Extract job titles (creates job1, job2, job3)
print("\n3. Extract job titles (max 3):")
df_with_jobs = extract_json_field(AzureOCR_df, field_name='jobs', max_items=3, subfield='title')
print("Created columns: job1, job2, job3")
print("Sample data:")
print(df_with_jobs[['job1', 'job2', 'job3']].head(3))

# Example 4: Extract birth_date
print("\n4. Extract birth_date:")
df_with_birth = extract_json_field(AzureOCR_df, field_name='birth_date')
print(f"Sample birth dates: {df_with_birth['birth_date'].head(5).tolist()}")

# Example 5: Extract spouse names (creates spouse1, spouse2)
print("\n5. Extract spouse names (max 2):")
df_with_spouses = extract_json_field(AzureOCR_df, field_name='spouses', max_items=2, subfield='name')
print("Created columns: spouse1, spouse2")
print("Sample data:")
print(df_with_spouses[['spouse1', 'spouse2']].head(3))

# Example 6: Extract with custom missing values
print("\n6. Extract with custom missing values:")
df_custom = extract_json_field(AzureOCR_df, field_name='children', max_items=3, subfield='name', missing_value='Missing')
print("Sample data with custom missing value:")
print(df_custom[['child1', 'child2', 'child3']].head(3))

print("\n" + "="*60)
print("QUICK REFERENCE")
print("="*60)
print("""
# Simple fields:
df = extract_json_field(df, field_name='title')
df = extract_json_field(df, field_name='birth_date')
df = extract_json_field(df, field_name='father_name')
df = extract_json_field(df, field_name='mother_name')

# Array fields with subfields:
df = extract_json_field(df, field_name='children', max_items=5, subfield='name')
df = extract_json_field(df, field_name='jobs', max_items=3, subfield='title')
df = extract_json_field(df, field_name='educations', max_items=2, subfield='institution')
df = extract_json_field(df, field_name='spouses', max_items=2, subfield='name')

# Custom missing values:
df = extract_json_field(df, field_name='children', max_items=5, subfield='name', missing_value='No child')
""")
