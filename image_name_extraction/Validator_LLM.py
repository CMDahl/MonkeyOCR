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
df_dolphin = df_dolphin_filtered.copy()

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
merged_df = pd.merge(df_dolphin, df_monkeyocr, on=['name', 'book_id'], how='outer', suffixes=('_dolphin', '_monkeyocr'))
merged_df.head()
merged_df.columns
len(merged_df)
len(df_dolphin)
len(df_monkeyocr)

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
    book_id_positions = [i for i, col in enumerate(result.columns) if col == 'book_id']

    if len(book_id_positions) > 1:
        print(f"Found {len(book_id_positions)} book_id columns at positions: {book_id_positions}")
    
        # Check if they're identical
        col1 = result.iloc[:, book_id_positions[0]]
        col2 = result.iloc[:, book_id_positions[1]]
        
        if col1.equals(col2):
            print("Columns are identical - removing duplicate")
            # Drop the second book_id column
            result = result.iloc[:, [i for i in range(len(result.columns)) if i != book_id_positions[1]]]
            print(f"Fixed! New columns: {result.columns.tolist()}")
        else:
            print("Columns are different - keeping both")
    else:
        print("Only one book_id column found - no action needed")
    
    return result, unmatched_df1, unmatched_df2

# Usage
result_df, unmatched_dolphin, unmatched_monkeyocr = fuzzy_merge_with_book_id_and_report_unmatched(
    df_dolphin, df_monkeyocr, 'name', 'book_id', threshold=90
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

def detailed_unmatched_by_book_dataframe(unmatched_df1, unmatched_df2, name_key, book_id_key, df1_name="Dolphin", df2_name="MonkeyOCR"):
    """
    Create a DataFrame with unmatched names by book_id, storing actual names in dictionaries
    instead of just counts.
    
    Args:
        unmatched_df1 (pd.DataFrame): First unmatched dataframe
        unmatched_df2 (pd.DataFrame): Second unmatched dataframe
        name_key (str): Column name containing the names
        book_id_key (str): Column name containing the book_id
        df1_name (str): Name for first dataframe (default: "Dolphin")
        df2_name (str): Name for second dataframe (default: "MonkeyOCR")
    
    Returns:
        pd.DataFrame: DataFrame with book_id and dictionaries of unmatched names
    """
    # Get counts and names by book_id for df1
    df1_grouped = unmatched_df1.groupby(book_id_key)[name_key].apply(list)
    df1_counts = unmatched_df1.groupby(book_id_key)[name_key].count()
    
    # Get counts and names by book_id for df2
    df2_grouped = unmatched_df2.groupby(book_id_key)[name_key].apply(list)
    df2_counts = unmatched_df2.groupby(book_id_key)[name_key].count()
    
    # Combine all book_ids
    all_books = set(df1_grouped.index) | set(df2_grouped.index)
    
    # Create the data for DataFrame
    data = []
    for book_id in sorted(all_books):
        # Get lists of names (empty list if book_id not in that dataframe)
        df1_names = df1_grouped.get(book_id, [])
        df2_names = df2_grouped.get(book_id, [])
        
        # Get counts
        df1_count = df1_counts.get(book_id, 0)
        df2_count = df2_counts.get(book_id, 0)
        total_count = df1_count + df2_count
        
        # Create dictionaries with names and counts
        df1_dict = {
            "count": df1_count,
            "names": df1_names
        }
        
        df2_dict = {
            "count": df2_count,
            "names": df2_names
        }
        
        data.append({
            'Book_ID': book_id,
            f'Unmatched_{df1_name}': df1_dict,
            f'Unmatched_{df2_name}': df2_dict,
            'Unmatched_Total_Count': total_count
        })
    
    # Create DataFrame
    detailed_df = pd.DataFrame(data)
    return detailed_df


def display_detailed_unmatched_sample(detailed_df, df1_name="Dolphin", df2_name="MonkeyOCR", max_books=5, max_names_per_book=5):
    """
    Display a sample of the detailed unmatched names dataframe in a readable format.
    
    Args:
        detailed_df (pd.DataFrame): DataFrame from detailed_unmatched_by_book_dataframe
        df1_name (str): Name for first dataframe
        df2_name (str): Name for second dataframe
        max_books (int): Maximum number of books to display
        max_names_per_book (int): Maximum number of names to show per book
    """
    print(f"\n{'='*80}")
    print("DETAILED UNMATCHED NAMES SAMPLE")
    print(f"{'='*80}")
    
    for idx, row in detailed_df.head(max_books).iterrows():
        book_id = row['Book_ID']
        df1_data = row[f'Unmatched_{df1_name}']
        df2_data = row[f'Unmatched_{df2_name}']
        
        print(f"\n📚 BOOK_ID: {book_id}")
        print("-" * 70)
        
        # Display counts
        print(f"  {df1_name} unmatched: {df1_data['count']}")
        print(f"  {df2_name} unmatched: {df2_data['count']}")
        print(f"  Total unmatched: {row['Unmatched_Total_Count']}")
        
        # Display sample names
        if df1_data['count'] > 0:
            print(f"\n  Sample {df1_name} names:")
            for name in df1_data['names'][:max_names_per_book]:
                print(f"    • {name}")
            if len(df1_data['names']) > max_names_per_book:
                print(f"    ... and {len(df1_data['names']) - max_names_per_book} more")
        
        if df2_data['count'] > 0:
            print(f"\n  Sample {df2_name} names:")
            for name in df2_data['names'][:max_names_per_book]:
                print(f"    • {name}")
            if len(df2_data['names']) > max_names_per_book:
                print(f"    ... and {len(df2_data['names']) - max_names_per_book} more")


# Usage example:
detailed_df = detailed_unmatched_by_book_dataframe(
    unmatched_dolphin, 
    unmatched_monkeyocr, 
    'name', 
    'book_id'
)

# Display the dataframe structure
print("Detailed DataFrame shape:", detailed_df.shape)
print("\nDataFrame columns:")
print(detailed_df.columns.tolist())

# Display sample in readable format
display_detailed_unmatched_sample(detailed_df)

# Show the actual dataframe (first few rows)
print(f"\n{'='*80}")
print("DATAFRAME PREVIEW")
print(f"{'='*80}")
print(detailed_df.head())

# Access individual book data example
if len(detailed_df) > 0:
    print(f"\n{'='*80}")
    print("EXAMPLE: Accessing data for first book")
    print(f"{'='*80}")
    first_book = detailed_df.iloc[0]
    book_id = first_book['Book_ID']
    dolphin_data = first_book['Unmatched_Dolphin']
    monkeyocr_data = first_book['Unmatched_MonkeyOCR']
    
    print(f"Book ID: {book_id}")
    print(f"Dolphin unmatched count: {dolphin_data['count']}")
    print(f"Dolphin unmatched names: {dolphin_data['names']}")
    print(f"MonkeyOCR unmatched count: {monkeyocr_data['count']}")
    print(f"MonkeyOCR unmatched names: {monkeyocr_data['names']}")
book_data = detailed_df.iloc[0]
dolphin_count = book_data['Unmatched_Dolphin']['count']
dolphin_names = book_data['Unmatched_Dolphin']['names']

monkeyocr_count = book_data['Unmatched_MonkeyOCR']['count']
monkeyocr_names = book_data['Unmatched_MonkeyOCR']['names']

import pandas as pd
import re
import difflib
import os
from pathlib import Path

def compare_ocr_files_batch(file_pairs, engine1_name="Engine1", engine2_name="Engine2"):
    """
    Compares multiple pairs of OCR text files and returns metrics in a DataFrame.
    
    Args:
        file_pairs (list): List of tuples containing (file1_path, file2_path)
        engine1_name (str): Name of the first OCR engine
        engine2_name (str): Name of the second OCR engine
    
    Returns:
        pd.DataFrame: DataFrame with comparison metrics for each file pair
    """
    
    def preprocess_text(text):
        """Normalizes OCR text for comparison with comprehensive LaTeX removal."""
        if pd.isna(text) or text is None:
            return ""
        
        processed_text = str(text)
        
        # Remove LaTeX math environments (display and inline)
        processed_text = re.sub(r'\$\$.*?\$\$', '', processed_text, flags=re.DOTALL)
        processed_text = re.sub(r'\$[^$]*\$', '', processed_text)
        
        # Remove LaTeX environments
        latex_environments = [
            'array', 'align', 'equation', 'eqnarray', 'matrix', 'pmatrix', 
            'bmatrix', 'vmatrix', 'cases', 'split', 'gather', 'multline'
        ]
        
        for env in latex_environments:
            pattern = rf'\\begin\{{{env}\}}.*?\\end\{{{env}\}}'
            processed_text = re.sub(pattern, '', processed_text, flags=re.DOTALL)
        
        # Remove LaTeX commands with arguments
        processed_text = re.sub(r'\\text\{[^}]*\}', '', processed_text)
        processed_text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', processed_text)
        
        # Remove common LaTeX symbols and commands
        latex_commands = [
            r'\\\\', r'\\hline', r'\\newline', r'\\linebreak', r'\\pagebreak',
            r'\\left', r'\\right', r'\\big', r'\\Big', r'\\bigg', r'\\Bigg',
            r'\\quad', r'\\qquad', r'\\,', r'\\:', r'\\;', r'\\!',
            r'\\alpha', r'\\beta', r'\\gamma', r'\\delta', r'\\epsilon',
            r'\\cdot', r'\\times', r'\\div', r'\\pm', r'\\mp',
            r'\\leq', r'\\geq', r'\\neq', r'\\approx', r'\\equiv',
            r'\\sum', r'\\prod', r'\\int', r'\\lim', r'\\infty'
        ]
        
        for cmd in latex_commands:
            processed_text = re.sub(cmd, ' ', processed_text)
        
        # Remove remaining LaTeX commands (backslash followed by letters)
        processed_text = re.sub(r'\\[a-zA-Z]+', '', processed_text)
        
        # Remove LaTeX special characters and brackets
        processed_text = re.sub(r'[{}]', '', processed_text)
        processed_text = re.sub(r'[\[\]]', '', processed_text)
        
        # Remove ampersands used for alignment in LaTeX tables
        processed_text = re.sub(r'&', ' ', processed_text)
        
        # Replace image links with placeholder
        processed_text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '[IMAGE]', processed_text)
        
        # Remove figure references and captions
        processed_text = re.sub(r'!\[Figure\].*?\.png\)', '[IMAGE]', processed_text)
        processed_text = re.sub(r'figures/[^)]*\.png', '[IMAGE]', processed_text)
        
        # Clean up spacing and formatting
        processed_text = re.sub(r'\s+', ' ', processed_text)  # Multiple spaces to single
        processed_text = re.sub(r'\n\s*\n', '\n', processed_text)  # Multiple newlines
        processed_text = re.sub(r'^\s+|\s+$', '', processed_text, flags=re.MULTILINE)  # Trim lines
        
        return processed_text.strip()
    
    def calculate_metrics(text1, text2):
        """Calculate comparison metrics between two texts."""
        if not text1 and not text2:
            return {
                'similarity_ratio': 1.0,
                'character_error_rate': 0.0,
                'word_error_rate': 0.0,
                'edit_distance': 0,
                'text1_length': 0,
                'text2_length': 0,
                'length_difference': 0
            }
        
        # Basic metrics
        text1_length = len(text1)
        text2_length = len(text2)
        length_difference = abs(text1_length - text2_length)
        
        # Similarity ratio using difflib
        matcher = difflib.SequenceMatcher(None, text1, text2)
        similarity_ratio = matcher.ratio()
        
        # Character Error Rate (CER)
        opcodes = matcher.get_opcodes()
        edits = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in opcodes if tag != 'equal')
        cer = (edits / text1_length) if text1_length > 0 else 0
        
        # Word Error Rate (WER)
        words1 = text1.split()
        words2 = text2.split()
        word_matcher = difflib.SequenceMatcher(None, words1, words2)
        word_opcodes = word_matcher.get_opcodes()
        word_edits = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in word_opcodes if tag != 'equal')
        wer = (word_edits / len(words1)) if len(words1) > 0 else 0
        
        return {
            'similarity_ratio': similarity_ratio,
            'character_error_rate': cer,
            'word_error_rate': wer,
            'edit_distance': edits,
            'text1_length': text1_length,
            'text2_length': text2_length,
            'length_difference': length_difference
        }
    
    # Process all file pairs
    results = []
    
    for i, (file1_path, file2_path) in enumerate(file_pairs):
        try:
            # Read files
            with open(file1_path, 'r', encoding='utf-8') as f1:
                text1 = f1.read()
            with open(file2_path, 'r', encoding='utf-8') as f2:
                text2 = f2.read()
            
            # Preprocess texts
            clean_text1 = preprocess_text(text1)
            clean_text2 = preprocess_text(text2)
            
            # Calculate metrics
            metrics = calculate_metrics(clean_text1, clean_text2)
            
            # Create result record
            result = {
                'file_pair_id': i + 1,
                'file1_path': str(file1_path),
                'file2_path': str(file2_path),
                'file1_name': Path(file1_path).name,
                'file2_name': Path(file2_path).name,
                f'{engine1_name}_length': metrics['text1_length'],
                f'{engine2_name}_length': metrics['text2_length'],
                'length_difference': metrics['length_difference'],
                'similarity_ratio': metrics['similarity_ratio'],
                'character_error_rate': metrics['character_error_rate'],
                'word_error_rate': metrics['word_error_rate'],
                'edit_distance': metrics['edit_distance'],
                'status': 'success'
            }
            
        except Exception as e:
            # Handle errors
            result = {
                'file_pair_id': i + 1,
                'file1_path': str(file1_path),
                'file2_path': str(file2_path),
                'file1_name': Path(file1_path).name if file1_path else 'N/A',
                'file2_name': Path(file2_path).name if file2_path else 'N/A',
                f'{engine1_name}_length': 0,
                f'{engine2_name}_length': 0,
                'length_difference': 0,
                'similarity_ratio': 0.0,
                'character_error_rate': 1.0,
                'word_error_rate': 1.0,
                'edit_distance': 0,
                'status': f'error: {str(e)}'
            }
        
        results.append(result)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    return df

dolphin_md_dir = r"D:\data\HCNC\norway\biographies\storage\Dolphin\markdown"
monkeyocr_md_dir = r"D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007"

def create_file_pairs_from_directories_with_df(df, book_id_column, dir1, dir2, file_extension='.md'):
    """
    Create file pairs from two directories based on book_id values in DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame containing book_id values
        book_id_column (str): Name of the column containing book_id values
        dir1 (str): Path to first directory (e.g., Dolphin markdown)
        dir2 (str): Path to second directory (e.g., MonkeyOCR markdown)
        file_extension (str): File extension to match (default: '.md')
    
    Returns:
        list: List of (file1_path, file2_path) tuples
    """
    dir1_path = Path(dir1)
    dir2_path = Path(dir2)
    
    file_pairs = []
    
    # Get unique book_ids from the DataFrame
    book_ids = df[book_id_column].unique()
    
    for book_id in book_ids:
        # Create filename from book_id
        filename = f"{book_id}{file_extension}"
        
        # Create full file paths
        file1 = dir1_path / filename
        file2 = dir2_path / filename
        
        # Check if both files exist
        if file1.exists() and file2.exists():
            file_pairs.append((str(file1), str(file2)))
        else:
            # Print which files are missing for debugging
            if not file1.exists():
                print(f"Missing in {dir1}: {filename}")
            if not file2.exists():
                print(f"Missing in {dir2}: {filename}")
    
    return file_pairs



# Usage with your DataFrame
file_pairs = create_file_pairs_from_directories_with_df(
    result_df, 
    'book_id',      
    dolphin_md_dir, 
    monkeyocr_md_dir,
    '.md'
)

print(f"Found {len(file_pairs)} file pairs to compare")

# Show sample of file pairs
if len(file_pairs) > 0:
    print("\nSample file pairs:")
    for i, (file1, file2) in enumerate(file_pairs[:5]):
        print(f"{i+1}. {Path(file1).name} <-> {Path(file2).name}")

# Run the OCR comparison
if len(file_pairs) > 0:
    results_df = compare_ocr_files_batch(file_pairs, "Dolphin", "MonkeyOCR")
    
    # Display results
    print("\n" + "="*80)
    print("OCR COMPARISON RESULTS")
    print("="*80)
    
    # Summary statistics
    print(f"\nSummary Statistics:")
    print(f"Total file pairs processed: {len(results_df)}")
    print(f"Successful comparisons: {(results_df['status'] == 'success').sum()}")
    print(f"Failed comparisons: {(results_df['status'] != 'success').sum()}")
    
    # Show successful comparisons only
    successful_df = results_df[results_df['status'] == 'success'].copy()
    
    if len(successful_df) > 0:
        print(f"\nOverall Statistics (successful comparisons only):")
        print(f"Average similarity ratio: {successful_df['similarity_ratio'].mean():.3f}")
        print(f"Average character error rate: {successful_df['character_error_rate'].mean():.3f}")
        print(f"Average word error rate: {successful_df['word_error_rate'].mean():.3f}")
        print(f"Median similarity ratio: {successful_df['similarity_ratio'].median():.3f}")
        
        # Show top 10 results
        print(f"\nTop 10 results:")
        display_cols = ['file1_name', 'file2_name', 'similarity_ratio', 'character_error_rate', 'word_error_rate']
        print(successful_df[display_cols].head(10).to_string(index=False))
    
    # Save results to CSV
    results_df.to_csv('ocr_comparison_results.csv', index=False)
    print(f"\nResults saved to 'ocr_comparison_results.csv'")
    
    # Show any errors
    error_df = results_df[results_df['status'] != 'success']
    if len(error_df) > 0:
        print(f"\nErrors encountered:")
        for idx, row in error_df.iterrows():
            print(f"  {row['file1_name']} vs {row['file2_name']}: {row['status']}")
    else:
        print("No matching file pairs found!")

# Extract book_id from file1_name by removing .md extension
results_df['Book_ID'] = results_df['file1_name'].str.replace('.md', '')

# Merge detailed_df and results_df based on Book_ID and extracted book_id
merged_analysis_df = pd.merge(
    detailed_df, 
    results_df, 
    on='Book_ID', 
    how='outer'
)

# Clean up - remove the temporary column
merged_analysis_df = merged_analysis_df.drop('book_id_from_file', axis=1)

merged_analysis_df.head(20)
# Save the merged analysis DataFrame to a CSV file
merged_analysis_df.to_csv('merged_biography_analysis.csv', index=False)

