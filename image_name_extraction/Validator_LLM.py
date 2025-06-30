import pandas as pd
import json

def check_maidenname(chunk):
    if pd.isna(chunk):
        return 0
    chunk_str = str(chunk)
    first_50 = chunk_str[:50]
    return 1 if ', se ' in first_50.lower() else 0


def check_empty_biography(biography_json_str):
    """
    Check if biography_json has all fields empty except 'name'
    Returns 1 if all fields are empty (except name), 0 otherwise
    """
    if pd.isna(biography_json_str):
        return 0
    
    try:
        # Parse the JSON string
        bio_data = json.loads(str(biography_json_str))
        
        # Check if it's a dictionary
        if not isinstance(bio_data, dict):
            return 0
        
        # Define fields that should be empty
        empty_fields = [
            "birth_date", "birth_place", "death_date", 
            "father_job", "father_name", "mother_name"
        ]
        
        # Define array fields that should be empty lists
        array_fields = ["jobs", "educations", "stays_abroad", "spouses", "children"]
        
        # Check string fields are empty
        for field in empty_fields:
            if field in bio_data and bio_data[field] != "":
                return 0
        
        # Check array fields are empty lists
        for field in array_fields:
            if field in bio_data and bio_data[field] != []:
                return 0
        
        # If we get here, all fields are empty except potentially 'name'
        return 1
        
    except (json.JSONDecodeError, TypeError, KeyError):
        # If JSON parsing fails, return 0
        return 0

# Extract the last 4 digits from book_id and convert to integer for comparison
def extract_last_digits(book_id):
    if pd.isna(book_id):
        return 0
    book_id_str = str(book_id)
    # Extract the last 4 digits after the underscore
    if '_' in book_id_str:
        last_part = book_id_str.split('_')[-1]
        try:
            return int(last_part)
        except ValueError:
            return 0
    return 0


df_dolphin = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\Dolphin\output\extracted_all_names_portraits_biographies_Dolphin_final.csv')
df_dolphin.head()
df_dolphin.columns


df_dolphin['maidenname'] = df_dolphin['markdown_chunk'].apply(check_maidenname)

# Verify the results
print("Maidenname analysis:")
print(f"Total rows: {len(df_dolphin)}")
print(f"Rows with maidenname=1: {df_dolphin['maidenname'].sum()}")
print(f"Rows with maidenname=0: {(df_dolphin['maidenname'] == 0).sum()}")
print(f"Percentage with maidenname: {df_dolphin['maidenname'].mean()*100:.2f}%")

# Show the value counts
print("\nValue counts:")
print(df_dolphin['maidenname'].value_counts())
# delete rows if maidenname is 1
df_dolphin = df_dolphin[df_dolphin['maidenname'] == 0]

# Apply the function to create a new column
df_dolphin['empty_biography'] = df_dolphin['biography_json'].apply(check_empty_biography)

# Check the results
print("Empty biography analysis:")
print(f"Total rows: {len(df_dolphin)}")
print(f"Rows with empty biography (except name): {df_dolphin['empty_biography'].sum()}")
print(f"Rows with non-empty biography data: {(df_dolphin['empty_biography'] == 0).sum()}")
print(f"Percentage with empty biography: {df_dolphin['empty_biography'].mean()*100:.2f}%")

# Show value counts
print("\nValue counts:")
print(df_dolphin['empty_biography'].value_counts())

# Remove rows with empty biography
df_dolphin = df_dolphin[df_dolphin['empty_biography'] == 0]

# Apply the function to extract digits
df_dolphin['last_digits'] = df_dolphin['book_id'].apply(extract_last_digits)

# Check the current distribution
print("Current book_id distribution:")
print(df_dolphin['last_digits'].value_counts().sort_index())

# Filter to keep only rows where last 4 digits <= 494
df_dolphin_filtered = df_dolphin[df_dolphin['last_digits'] <= 494]

# Remove the helper column
df_dolphin_filtered = df_dolphin_filtered.drop('last_digits', axis=1)

print(f"\nFiltering results:")
print(f"Original df_dolphin rows: {len(df_dolphin)}")
print(f"Filtered df_dolphin rows: {len(df_dolphin_filtered)}")
print(f"Removed {len(df_dolphin) - len(df_dolphin_filtered)} rows")

# Update df_dolphin to the filtered version
df_dolphin = df_dolphin_filtered

# Verify the filtering worked
print(f"\nVerification - remaining book_ids:")
remaining_book_ids = df_dolphin['book_id'].unique()
print(f"Number of unique book_ids remaining: {len(remaining_book_ids)}")
print("Sample of remaining book_ids:")
for book_id in sorted(remaining_book_ids)[:10]:
    print(f"  {book_id}")

df_monkeyocr = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007\output\extracted_all_names_portraits_biographies_final.csv')
df_monkeyocr.head()
df_monkeyocr.columns

df_monkeyocr['maidenname'] = df_monkeyocr['markdown_chunk'].apply(check_maidenname)

# Verify the results
print("Maidenname analysis:")
print(f"Total rows: {len(df_monkeyocr)}")
print(f"Rows with maidenname=1: {df_monkeyocr['maidenname'].sum()}")
print(f"Rows with maidenname=0: {(df_monkeyocr['maidenname'] == 0).sum()}")
print(f"Percentage with maidenname: {df_monkeyocr['maidenname'].mean()*100:.2f}%")

# Show the value counts
print("\nValue counts:")
print(df_monkeyocr['maidenname'].value_counts())
# delete rows if maidenname is 1
df_monkeyocr = df_monkeyocr[df_monkeyocr['maidenname'] == 0]

# Apply the function to create a new column
df_monkeyocr['empty_biography'] = df_monkeyocr['biography_json'].apply(check_empty_biography)
# Check the results
print("Empty biography analysis:")
print(f"Total rows: {len(df_monkeyocr)}")
print(f"Rows with empty biography (except name): {df_monkeyocr['empty_biography'].sum()}")
print(f"Rows with non-empty biography data: {(df_monkeyocr['empty_biography'] == 0).sum()}")
print(f"Percentage with empty biography: {df_monkeyocr['empty_biography'].mean()*100:.2f}%")

# Show value counts
print("\nValue counts:")
print(df_monkeyocr['empty_biography'].value_counts())
# Remove rows with empty biography
df_monkeyocr = df_monkeyocr[df_monkeyocr['empty_biography'] == 0]


# Merge the two DataFrames on 'name' and 'book_id'
merged_df = pd.merge(df_dolphin, df_monkeyocr, on=['name', 'book_id'], how='inner', suffixes=('_dolphin', '_monkeyocr'))
merged_df.head()
merged_df.columns
len(merged_df)
len(df_dolphin)
len(df_monkeyocr)


merged_df = pd.merge(df_dolphin, df_monkeyocr, on=['name',], how='inner', suffixes=('_dolphin', '_monkeycor'))
merged_df.head()
merged_df.columns
len(merged_df)
len(df_dolphin)
len(df_monkeyocr)

# Replace this import:
# from fuzzywuzzy import process

# With this:
# With this:
from rapidfuzz import process, fuzz

def fuzzy_merge_with_book_id_and_report_unmatched(df1, df2, name_key, book_id_key, threshold=90):
    """
    Fuzzy merge two dataframes on name with perfect match on book_id
    and report unmatched names from both dataframes
    """
    matches = []
    match_data = []
    matched_df1_indices = set()
    matched_df2_indices = set()
    
    for idx, row in df1.iterrows():
        name = row[name_key]
        book_id = row[book_id_key]
        
        # First filter df2 to only rows with matching book_id
        df2_same_book = df2[df2[book_id_key] == book_id]
        
        if df2_same_book.empty:
            continue  # No matching book_id in df2
        
        # Now do fuzzy matching on names within the same book_id
        match = process.extractOne(name, df2_same_book[name_key])
        
        if match and match[1] >= threshold:
            # Find the actual row in df2 that matches
            matched_name = match[0]
            df2_matched_row = df2_same_book[df2_same_book[name_key] == matched_name].iloc[0]
            
            # Store the match information
            match_data.append({
                'df1_idx': idx,
                'df2_idx': df2_matched_row.name,  # actual index in df2
                'df1_name': name,
                'df2_name': matched_name,
                'book_id': book_id,
                'score': match[1]
            })
            
            # Track matched indices
            matched_df1_indices.add(idx)
            matched_df2_indices.add(df2_matched_row.name)
    
    # Find unmatched names
    unmatched_df1 = df1[~df1.index.isin(matched_df1_indices)]
    unmatched_df2 = df2[~df2.index.isin(matched_df2_indices)]
    
    # Print unmatched names
    print(f"\n{'='*60}")
    print("UNMATCHED NAMES REPORT")
    print(f"{'='*60}")
    
    print(f"\nUnmatched names from df1 (Dolphin): {len(unmatched_df1)}")
    print("-" * 40)
    for idx, row in unmatched_df1.iterrows():
        print(f"  {row[name_key]} (book_id: {row[book_id_key]})")
    
    print(f"\nUnmatched names from df2 (MonkeyOCR): {len(unmatched_df2)}")
    print("-" * 40)
    for idx, row in unmatched_df2.iterrows():
        print(f"  {row[name_key]} (book_id: {row[book_id_key]})")
    
    print(f"\nSUMMARY:")
    print(f"  Total df1 names: {len(df1)}")
    print(f"  Total df2 names: {len(df2)}")
    print(f"  Matched pairs: {len(match_data)}")
    print(f"  Unmatched df1: {len(unmatched_df1)}")
    print(f"  Unmatched df2: {len(unmatched_df2)}")
    print(f"  Match rate df1: {len(match_data)/len(df1)*100:.1f}%")
    print(f"  Match rate df2: {len(match_data)/len(df2)*100:.1f}%")
    
    if not match_data:
        return pd.DataFrame(), unmatched_df1, unmatched_df2
    
    # Create result DataFrame (same as before)
    match_df = pd.DataFrame(match_data)
    
    # Get matched rows from both dataframes
    df1_matched = df1.loc[match_df['df1_idx']].reset_index(drop=True)
    df2_matched = df2.loc[match_df['df2_idx']].reset_index(drop=True)
    
    # Add match info
    df1_matched['match_score'] = match_df['score'].values
    df1_matched['matched_name_df2'] = match_df['df2_name'].values
    
    # Add suffixes to avoid column conflicts
    for col in df1_matched.columns:
        if col in df2_matched.columns and col not in [book_id_key, 'match_score', 'matched_name_df2']:
            df1_matched.rename(columns={col: f"{col}_df1"}, inplace=True)
            df2_matched.rename(columns={col: f"{col}_df2"}, inplace=True)
    
    # Combine the dataframes
    result = pd.concat([df1_matched, df2_matched], axis=1)
    
    return result, unmatched_df1, unmatched_df2

# Usage
result_df, unmatched_dolphin, unmatched_monkeyocr = fuzzy_merge_with_book_id_and_report_unmatched(
    df_dolphin, df_monkeyocr, 'name', 'book_id', threshold=80
)

print(f"Fuzzy merged with book_id match: {len(result_df)} rows")

# Save unmatched names to CSV files for further analysis
if len(unmatched_dolphin) > 0:
    unmatched_dolphin.to_csv('unmatched_dolphin_names.csv', index=False)
    print(f"Saved {len(unmatched_dolphin)} unmatched Dolphin names to 'unmatched_dolphin_names.csv'")

if len(unmatched_monkeyocr) > 0:
    unmatched_monkeyocr.to_csv('unmatched_monkeyocr_names.csv', index=False)
    print(f"Saved {len(unmatched_monkeyocr)} unmatched MonkeyOCR names to 'unmatched_monkeycor_names.csv'")

# Show sample of unmatched names with their book_ids
print("\nSample of unmatched Dolphin names:")
print(unmatched_dolphin[['name', 'book_id']].head(10))

print("\nSample of unmatched MonkeyOCR names:")
print(unmatched_monkeyocr[['name', 'book_id']].head(10))

# Analyze unmatched names by book_id
print("\nUnmatched names by book_id:")
print("\nDolphin unmatched by book_id:")
dolphin_unmatched_by_book = unmatched_dolphin.groupby('book_id')['name'].count().sort_values(ascending=False)
print(dolphin_unmatched_by_book.head(10))

print("\nMonkeyOCR unmatched by book_id:")
monkeycor_unmatched_by_book = unmatched_monkeyocr.groupby('book_id')['name'].count().sort_values(ascending=False)
print(monkeycor_unmatched_by_book.head(10))

def analyze_unmatched_by_book_id(unmatched_df1, unmatched_df2, name_key, book_id_key, df1_name="Dolphin", df2_name="MonkeyOCR"):
    """
    Analyze and display unmatched names grouped by book_id
    """
    # Get all book_ids that have unmatched names in either dataframe
    all_unmatched_book_ids = set(unmatched_df1[book_id_key].unique()) | set(unmatched_df2[book_id_key].unique())
    
    print(f"\n{'='*80}")
    print("UNMATCHED NAMES BY BOOK_ID")
    print(f"{'='*80}")
    
    for book_id in sorted(all_unmatched_book_ids):
        print(f"\n📚 BOOK_ID: {book_id}")
        print("-" * 70)
        
        # Get unmatched names for this book_id from both dataframes
        df1_unmatched_book = unmatched_df1[unmatched_df1[book_id_key] == book_id]
        df2_unmatched_book = unmatched_df2[unmatched_df2[book_id_key] == book_id]
        
        # Display side by side
        max_rows = max(len(df1_unmatched_book), len(df2_unmatched_book))
        
        print(f"{'Unmatched ' + df1_name + ' names':<35} | {'Unmatched ' + df2_name + ' names':<35}")
        print(f"{'-'*35}|{'-'*35}")
        
        for i in range(max_rows):
            df1_name_display = ""
            df2_name_display = ""
            
            if i < len(df1_unmatched_book):
                df1_name_display = df1_unmatched_book.iloc[i][name_key][:32] + "..." if len(df1_unmatched_book.iloc[i][name_key]) > 32 else df1_unmatched_book.iloc[i][name_key]
            
            if i < len(df2_unmatched_book):
                df2_name_display = df2_unmatched_book.iloc[i][name_key][:32] + "..." if len(df2_unmatched_book.iloc[i][name_key]) > 32 else df2_unmatched_book.iloc[i][name_key]
            
            print(f"{df1_name_display:<35} | {df2_name_display:<35}")
        
        print(f"\nSummary for {book_id}:")
        print(f"  {df1_name} unmatched: {len(df1_unmatched_book)}")
        print(f"  {df2_name} unmatched: {len(df2_unmatched_book)}")
        print(f"  Total unmatched for this book: {len(df1_unmatched_book) + len(df2_unmatched_book)}")


def quick_unmatched_by_book_dataframe(unmatched_df1, unmatched_df2, name_key, book_id_key):
    """
    Create a DataFrame with unmatched names overview by book_id
    (same data as quick_unmatched_by_book_overview but as DataFrame)
    """
    # Get counts by book_id
    df1_counts = unmatched_df1.groupby(book_id_key)[name_key].count()
    df2_counts = unmatched_df2.groupby(book_id_key)[name_key].count()
    
    # Combine the counts
    all_books = set(df1_counts.index) | set(df2_counts.index)
    
    # Create the data for DataFrame
    data = []
    for book_id in sorted(all_books):
        dolphin_count = df1_counts.get(book_id, 0)
        monkeycor_count = df2_counts.get(book_id, 0)
        total_count = dolphin_count + monkeycor_count
        
        data.append({
            'Book_ID': book_id,
            'Unmatched Dolphin': dolphin_count,
            'Unmatched MonkeyOCR': monkeycor_count,
            'Unmathed Total': total_count
        })
    
    # Create DataFrame
    overview_df = pd.DataFrame(data)
    return overview_df



# Call the function with your unmatched dataframes
analyze_unmatched_by_book_id(unmatched_dolphin, unmatched_monkeyocr, 'name', 'book_id')
# Run the quick overview
df = quick_unmatched_by_book_dataframe(unmatched_dolphin, unmatched_monkeyocr, 'name', 'book_id')
df