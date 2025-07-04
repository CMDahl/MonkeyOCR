import pandas as pd
import os

# Note: This script now uses 'thefuzz' instead of 'string_grouper'
# Please install it first: pip install thefuzz python-Levenshtein

def merge_csv_files(ocr_type: str, base_path: str):
    """
    Merge CSV files for a specific OCR type (MonkeyOCR or Dolphin)
    
    Args:
        ocr_type: 'MonkeyOCR' or 'Dolphin'
        base_path: Base directory path
    """
    print(f"\n{'='*60}")
    print(f"Processing {ocr_type} files...")
    print(f"{'='*60}")
    
    # Define paths based on OCR type
    if ocr_type == 'MonkeyOCR':
        data_dir = os.path.join(base_path, 'MonkeyOCR', 'digibok_2007031501007', 'output')
    else:  # Dolphin
        data_dir = os.path.join(base_path, 'Dolphin', 'output')
    
    # Define file paths
    main_file = os.path.join(data_dir, 'extracted_all_names_with_chunks_with_biographies.csv')
    portrait_single_file = os.path.join(data_dir, 'extracted_portrait_names_with_chunks.csv')
    next_page_portraits_file = os.path.join(data_dir, 'extracted_all_names_with_chunks_and_portraits.csv')
    output_file = os.path.join(data_dir, 'extracted_all_names_portraits_biographies_final.csv')
    
    # Check if all required files exist
    files_to_check = [main_file, portrait_single_file, next_page_portraits_file]
    missing_files = [f for f in files_to_check if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Missing files for {ocr_type}:")
        for file in missing_files:
            print(f"   - {file}")
        return None
    
    print(f"📁 Loading files for {ocr_type}...")
    
    # Load main DataFrame
    df_main = pd.read_csv(main_file)
    print(f"   Main file: {len(df_main)} rows")
    
    # Load portrait files
    df_portrait_single = pd.read_csv(portrait_single_file)
    df_next_page_portraits = pd.read_csv(next_page_portraits_file)
    print(f"   Portrait single: {len(df_portrait_single)} rows")
    print(f"   Next page portraits: {len(df_next_page_portraits)} rows")
    
    # Process portrait DataFrames
    df_portrait_single = df_portrait_single[['name', 'book_id', 'image_filename']].copy()
    
    df_next_page_portraits = df_next_page_portraits[['name', 'book_id', 'portrait_filename']].copy()
    df_next_page_portraits.rename(columns={'portrait_filename': 'image_filename'}, inplace=True)
    
    # Filter out null image_filenames from next_page_portraits
    print(f"   Filtering next page portraits: {len(df_next_page_portraits)} -> ", end="")
    df_next_page_portraits = df_next_page_portraits[df_next_page_portraits['image_filename'].notnull()]
    print(f"{len(df_next_page_portraits)} rows")
    
    # Merge portrait DataFrames
    print("🔄 Merging portrait data...")
    df_merged_portraits = pd.merge(
        df_portrait_single, 
        df_next_page_portraits, 
        on=['name', 'book_id'], 
        how='outer', 
        suffixes=('', '_next_page')
    ).reset_index(drop=True)
    
    
    # Use next_page image_filename when available
    df_merged_portraits['image_filename'] = df_merged_portraits['image_filename_next_page'].combine_first(
        df_merged_portraits['image_filename']
    )
    
    # Clean up temporary column
    df_merged_portraits.drop(columns=['image_filename_next_page'], inplace=True)
    
    # Clean the image path specifically for MonkeyOCR
    if ocr_type == 'MonkeyOCR':
        df_merged_portraits['image_filename'] = df_merged_portraits['image_filename'].str.replace('images/', '', regex=False)
        print("   Cleaned 'images/' prefix from MonkeyOCR image filenames.")

    # Sort by book_id and name
    df_merged_portraits.sort_values(by=['book_id', 'name'], inplace=True)       
    
    
    # Prepare main DataFrame for merging
    df_merged = df_main[['name', 'book_id', 'markdown_chunk', 'biography_json']].copy().reset_index(drop=True)
    
    # Final merge
    print("🔄 Creating final merge...")
    df_final = pd.merge(df_merged, df_merged_portraits, on=['name', 'book_id'], how='left')
    
    # Save results
    df_final.to_csv(output_file, index=False)
    
    # Print summary
    rows_with_portraits = df_final['image_filename'].notnull().sum()
    portrait_percentage = (rows_with_portraits / len(df_final)) * 100
    
    print(f"✅ {ocr_type} processing complete!")
    print(f"   📊 Final DataFrame: {len(df_final)} rows")
    print(f"   🖼️  Rows with portraits: {rows_with_portraits} ({portrait_percentage:.1f}%)")
    print(f"   💾 Saved to: {output_file}")
    
    return {
        'ocr_type': ocr_type,
        'total_rows': len(df_final),
        'rows_with_portraits': rows_with_portraits,
        'portrait_percentage': portrait_percentage,
        'output_file': output_file
    }

def perform_fuzzy_merge(df_monkey, df_dolphin, base_path, threshold=85):
    """
    Performs a fuzzy merge on the 'name' column between two dataframes,
    grouped by an exact match on 'book_id', using 'thefuzz'.
    
    Args:
        df_monkey (pd.DataFrame): The MonkeyOCR dataframe.
        df_dolphin (pd.DataFrame): The Dolphin dataframe.
        base_path (str): The base path to save the output file.
        threshold (int): The similarity threshold for fuzzy matching (0-100).
    """
    try:
        from thefuzz import process, fuzz
    except ImportError:
        print("\n❌ Fuzzy merge skipped. Please install 'thefuzz' and 'python-Levenshtein':")
        print("   pip install thefuzz python-Levenshtein")
        return None

    print(f"\n{'='*60}")
    print(f"Performing Fuzzy Merge with 'thefuzz' (threshold: {threshold})...")
    print(f"{'='*60}")

    all_matches_list = []
    
    common_book_ids = set(df_monkey['book_id'].unique()) & set(df_dolphin['book_id'].unique())
    print(f"Found {len(common_book_ids)} common book_ids to process.")

    for i, book_id in enumerate(sorted(list(common_book_ids))):
        if (i > 0 and i % 100 == 0) or i == len(common_book_ids) - 1:
            print(f"  Processing book_id {i+1}/{len(common_book_ids)}: {book_id}")

        dolphin_group = df_dolphin[df_dolphin['book_id'] == book_id].copy()
        monkey_group = df_monkey[df_monkey['book_id'] == book_id].copy()

        if dolphin_group.empty or monkey_group.empty:
            continue

        # Create a list of choices for the fuzzy matching
        monkey_names = monkey_group['name'].tolist()

        # Iterate through each record in the dolphin group to find its best match
        for _, dolphin_row in dolphin_group.iterrows():
            dolphin_name = dolphin_row['name']
            
            # Find the best match from the list of monkey names using a robust scorer
            best_match = process.extractOne(dolphin_name, monkey_names, scorer=fuzz.token_sort_ratio)
            
            if best_match and best_match[1] >= threshold:
                # A good match was found
                monkey_name_matched = best_match[0]
                similarity_score = best_match[1]
                
                # Get the full row for the matched monkey name
                monkey_row_matched = monkey_group.loc[monkey_group['name'] == monkey_name_matched].iloc[0]
                
                # Combine the two rows of data, adding suffixes to avoid column name collisions
                combined_row = pd.concat([
                    dolphin_row.add_suffix('_dolphin'),
                    monkey_row_matched.add_suffix('_monkeyocr')
                ])
                
                # Add the similarity score
                combined_row['similarity'] = similarity_score
                
                all_matches_list.append(combined_row)

    if not all_matches_list:
        print("\n❌ No fuzzy matches found across all books.")
        return None

    # Create the final DataFrame from the list of combined rows
    final_df = pd.DataFrame(all_matches_list).reset_index(drop=True)
    
    # Clean up and reorder columns
    final_df.rename(columns={'book_id_dolphin': 'book_id'}, inplace=True)
    if 'book_id_monkeyocr' in final_df.columns:
        final_df.drop(columns=['book_id_monkeyocr'], inplace=True)
    
    key_cols = [
        'book_id', 
        'name_dolphin', 
        'name_monkeyocr', 
        'similarity'
    ]
    other_cols = sorted([col for col in final_df.columns if col not in key_cols])
    final_df = final_df[key_cols + other_cols]

    # Save the result
    output_file = os.path.join(base_path, 'comparison_final_merged_thefuzz.csv')
    final_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Fuzzy merge complete!")
    print(f"   📊 Final merged DataFrame: {len(final_df)} rows")
    print(f"   💾 Saved to: {output_file}")
    return output_file

def filter_by_image_agreement(merged_df_path: str, base_path: str):
    """
    Filters the merged dataframe to keep only book_ids where there is
    100% agreement on the presence/absence of images.
    
    Args:
        merged_df_path (str): Path to the final merged CSV file.
        base_path (str): The base path to save the output file.
    """
    print(f"\n{'='*60}")
    print(f"Filtering by Image Presence Agreement...")
    print(f"{'='*60}")

    try:
        df = pd.read_csv(merged_df_path)
        print(f"Loaded merged data with {len(df)} rows.")

        # 1. Determine image presence for each OCR
        df['has_image_dolphin'] = df['image_filename_dolphin'].notna()
        df['has_image_monkeyocr'] = df['image_filename_monkeyocr'].notna()
        
        # 2. Check if the presence agrees for each row
        df['image_agreement'] = (df['has_image_dolphin'] == df['has_image_monkeyocr'])
        
        # 3. Find all book_ids that have at least one disagreement
        disagreement_books = df[df['image_agreement'] == False]['book_id'].unique()
        
        print(f"Found {len(disagreement_books)} book_ids with at least one image disagreement.")
        
        # 4. Filter the dataframe to keep only book_ids NOT in the disagreement list
        agreed_df = df[~df['book_id'].isin(disagreement_books)].copy()
        
        # 5. Clean up helper columns
        agreed_df.drop(columns=['has_image_dolphin', 'has_image_monkeyocr', 'image_agreement'], inplace=True)

        
        # Delete row where book_id is in excluded_books (where I have seen errors in potrait extraction)
        excluded_books = [
            'digibok_2007031501007_0103', 'digibok_2007031501007_0115',
            'digibok_2007031501007_0068', 'digibok_2007031501007_0406',
            'digibok_2007031501007_0295',
        ]
        agreed_df = agreed_df[~agreed_df['book_id'].isin(excluded_books)]
        
        # 6. Reset index
        agreed_df.reset_index(drop=True, inplace=True)
        
        # Save the result
        output_file = os.path.join(base_path, 'comparison_image_agreement_only.csv')
        agreed_df.to_csv(output_file, index=False)
        
        print(f"\n✅ Image agreement filtering complete!")
        print(f"   📊 Final agreed DataFrame: {len(agreed_df)} rows from {agreed_df['book_id'].nunique()} books.")
        print(f"   💾 Saved to: {output_file}")

    except FileNotFoundError:
        print(f"❌ Could not perform image agreement filtering: File not found at {merged_df_path}")
    except Exception as e:
        print(f"\n❌ An error occurred during image agreement filtering: {e}")


def main():
    """Process both MonkeyOCR and Dolphin scenarios and then merge them"""
    base_path = r'd:\data\HCNC\norway\biographies\storage'
    
    print("🚀 Starting CSV file collection and merging...")
    print(f"Base path: {base_path}")
    
    # Process both OCR types
    ocr_types = ['MonkeyOCR', 'Dolphin']
    results = {}
    
    for ocr_type in ocr_types:
        result = merge_csv_files(ocr_type, base_path)
        if result:
            results[ocr_type] = result
    
    # Print final summary
    print(f"\n{'='*60}")
    print("INDIVIDUAL OCR SUMMARY")
    print(f"{'='*60}")
    
    if results:
        for ocr_type, result in results.items():
            print(f"{result['ocr_type']:>12}: {result['total_rows']:>6} rows, "
                  f"{result['rows_with_portraits']:>4} portraits ({result['portrait_percentage']:>5.1f}%)")
        
        print(f"\n📁 Output files:")
        for result in results.values():
            print(f"   {result['ocr_type']}: {os.path.basename(result['output_file'])}")
    else:
        print("❌ No files were successfully processed!")
    
    # Perform the final fuzzy merge between the two results
    merged_file_path = None
    if 'MonkeyOCR' in results and 'Dolphin' in results:
        df_monkey = pd.read_csv(results['MonkeyOCR']['output_file'])
        df_dolphin = pd.read_csv(results['Dolphin']['output_file'])
        # The threshold is now 0-100 for thefuzz
        merged_file_path = perform_fuzzy_merge(df_monkey, df_dolphin, base_path, threshold=85)        
    else:
        print("\nCould not perform fuzzy merge: one or both OCR final files are missing.")
    
    # Perform the final image agreement filtering
    if merged_file_path and os.path.exists(merged_file_path):
        filter_by_image_agreement(merged_file_path, base_path)
    else:
        print("\nCould not perform image agreement filtering because the merged file was not created.")
    
    
    
    print(f"\n🎉 All processing complete!")

if __name__ == "__main__":
    main()