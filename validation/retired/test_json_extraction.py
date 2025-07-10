"""
Test script for the general JSON extraction function
"""
import pandas as pd
import sys
sys.path.append('.')
from biography_json_comparisons import extract_json_field

# Load sample data
AzureOCR_df = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_portraits_biographies_final.csv')

print("="*80)
print("TESTING GENERAL JSON EXTRACTION FUNCTION")
print("="*80)

# Test 1: Extract simple title field
print("\n1. Testing simple field extraction (title):")
df_test = extract_json_field(AzureOCR_df.head(5), field_name='title')
print(f"Original columns: {list(AzureOCR_df.columns)}")
print(f"New columns: {list(df_test.columns)}")
print(f"Extracted titles: {df_test['title'].tolist()}")

# Test 2: Extract children names (should create child1, child2, etc.)
print("\n2. Testing children extraction (max 5):")
df_children = extract_json_field(AzureOCR_df.head(5), field_name='children', max_items=5, subfield='name', missing_value='Missing')
child_cols = [col for col in df_children.columns if col.startswith('child')]
print(f"Created child columns: {child_cols}")
print("Children data:")
print(df_children[child_cols])

# Test 3: Extract job titles
print("\n3. Testing job extraction (max 3):")
df_jobs = extract_json_field(AzureOCR_df.head(5), field_name='jobs', max_items=3, subfield='title', missing_value='No job')
job_cols = [col for col in df_jobs.columns if col.startswith('job')]
print(f"Created job columns: {job_cols}")
print("Job data:")
print(df_jobs[job_cols])

# Test 4: Extract birth dates
print("\n4. Testing birth_date extraction:")
df_birth = extract_json_field(AzureOCR_df.head(5), field_name='birth_date')
print(f"Birth dates: {df_birth['birth_date'].tolist()}")

# Test 5: Extract spouse names
print("\n5. Testing spouse extraction (max 2):")
df_spouses = extract_json_field(AzureOCR_df.head(5), field_name='spouses', max_items=2, subfield='name', missing_value='No spouse')
spouse_cols = [col for col in df_spouses.columns if col.startswith('spouse')]
print(f"Created spouse columns: {spouse_cols}")
print("Spouse data:")
print(df_spouses[spouse_cols])

print("\n" + "="*80)
print("FUNCTION USAGE EXAMPLES")
print("="*80)
print("""
# Extract any simple field:
df = extract_json_field(df, field_name='title')
df = extract_json_field(df, field_name='birth_date')
df = extract_json_field(df, field_name='father_name')

# Extract children (creates child1, child2, child3, child4, child5):
df = extract_json_field(df, field_name='children', max_items=5, subfield='name')

# Extract jobs (creates job1, job2, job3):
df = extract_json_field(df, field_name='jobs', max_items=3, subfield='title')

# Extract educations (creates education1, education2):
df = extract_json_field(df, field_name='educations', max_items=2, subfield='institution')

# Extract with custom missing values:
df = extract_json_field(df, field_name='children', max_items=5, subfield='name', missing_value='Missing')
""")
