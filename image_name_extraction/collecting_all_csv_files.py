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
        data_dir = os.path.join(base_path, 'MonkeyOCR', 'output_csv')
    elif ocr_type == 'AzureOCR':
        data_dir = os.path.join(base_path, 'AzureOCR', 'output_csv')
    elif ocr_type == 'Dolphin':
        data_dir = os.path.join(base_path, 'Dolphin', 'output_csv')
    else:
        raise ValueError(f"Unsupported OCR type: {ocr_type}. Supported types are: 'MonkeyOCR', 'AzureOCR', 'Dolphin'")
    
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

    
        # Clear the image path for AzureOCR
       # Clear the image path for AzureOCR
    elif ocr_type == 'AzureOCR':
        # For AzureOCR, add book_id to image_filename if it's not already present
        def add_book_id_to_filename(row):
            image_filename = row['image_filename']
            book_id = row['book_id']
            
            if pd.isna(image_filename) or image_filename == '':
                return image_filename
            
            # Check if "digibok" is already in the filename to avoid duplicates
            if "digibok" not in str(image_filename).lower():
                # Add book_id to the filename
                # e.g., "1.1.jpg" becomes "digibok_2007031501007_0083_1.1.jpg"
                filename_with_book_id = f"{book_id}_{image_filename}"
            else:
                # "digibok" already present, return as is
                filename_with_book_id = image_filename
            
            # Change file extension from .jpg to .png
            if filename_with_book_id.lower().endswith('.jpg'):
                filename_with_book_id = filename_with_book_id[:-4] + '.png'
            
            return filename_with_book_id
        
        df_merged_portraits['image_filename'] = df_merged_portraits.apply(add_book_id_to_filename, axis=1)
        print("   Added book_id to AzureOCR image filenames where 'digibok' not present.")
        print("   Renamed all .jpg extensions to .png for AzureOCR files.")
        
        df_merged_portraits['image_filename'] = df_merged_portraits.apply(add_book_id_to_filename, axis=1)
        print("   Added book_id to AzureOCR image filenames where 'digibok' not present.")

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
        excluded_books = [
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
    ocr_types = ['MonkeyOCR', 'Dolphin', 'AzureOCR']    
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

def perform_multi_ocr_fuzzy_merge(results_dict, base_path, threshold=85):
    """
    Performs fuzzy merges between multiple OCR results.
    Creates pairwise comparisons and optionally a three-way merge.
    
    Args:
        results_dict (dict): Dictionary containing OCR results with keys like 'MonkeyOCR', 'Dolphin', 'AzureOCR'
        base_path (str): The base path to save the output files
        threshold (int): The similarity threshold for fuzzy matching (0-100)
    """
    try:
        from thefuzz import process, fuzz
    except ImportError:
        print("\n❌ Fuzzy merge skipped. Please install 'thefuzz' and 'python-Levenshtein':")
        print("   pip install thefuzz python-Levenshtein")
        return None

    print(f"\n{'='*60}")
    print(f"Performing Multi-OCR Fuzzy Merge with 'thefuzz' (threshold: {threshold})...")
    print(f"{'='*60}")

    # Load all available dataframes
    ocr_dataframes = {}
    for ocr_type, result in results_dict.items():
        if os.path.exists(result['output_file']):
            ocr_dataframes[ocr_type] = pd.read_csv(result['output_file'])
            print(f"Loaded {ocr_type}: {len(ocr_dataframes[ocr_type])} rows")
    
    if len(ocr_dataframes) < 2:
        print("❌ Need at least 2 OCR results for comparison")
        return None

    # Define all possible pairwise combinations
    ocr_types = list(ocr_dataframes.keys())
    pairwise_results = {}
    
    # Perform pairwise fuzzy merges
    for i in range(len(ocr_types)):
        for j in range(i + 1, len(ocr_types)):
            ocr1, ocr2 = ocr_types[i], ocr_types[j]
            print(f"\n🔄 Performing fuzzy merge: {ocr1} vs {ocr2}")
            
            merge_result = perform_pairwise_fuzzy_merge(
                ocr_dataframes[ocr1], ocr_dataframes[ocr2],
                ocr1, ocr2, base_path, threshold
            )
            
            if merge_result:
                pairwise_results[f"{ocr1}_vs_{ocr2}"] = merge_result

    # If we have all three OCR types, create a three-way merge
    if len(ocr_dataframes) == 3 and 'MonkeyOCR' in ocr_dataframes and 'Dolphin' in ocr_dataframes and 'AzureOCR' in ocr_dataframes:
        print(f"\n🔄 Performing three-way fuzzy merge: MonkeyOCR vs Dolphin vs AzureOCR")
        threeway_result = perform_threeway_fuzzy_merge(
            ocr_dataframes['MonkeyOCR'], 
            ocr_dataframes['Dolphin'], 
            ocr_dataframes['AzureOCR'],
            base_path, threshold
        )
        if threeway_result:
            pairwise_results['threeway_merge'] = threeway_result

    return pairwise_results

def perform_pairwise_fuzzy_merge(df1, df2, ocr1_name, ocr2_name, base_path, threshold=85):
    """
    Performs a fuzzy merge between two specific OCR dataframes.
    """
    try:
        from thefuzz import process, fuzz
    except ImportError:
        print(f"\n❌ Fuzzy merge skipped for {ocr1_name} vs {ocr2_name}. Please install 'thefuzz' and 'python-Levenshtein':")
        print("   pip install thefuzz python-Levenshtein")
        return None
    
    print(f"   Comparing {len(df1)} {ocr1_name} records with {len(df2)} {ocr2_name} records")
    
    all_matches_list = []
    
    common_book_ids = set(df1['book_id'].unique()) & set(df2['book_id'].unique())
    print(f"   Found {len(common_book_ids)} common book_ids")

    for i, book_id in enumerate(sorted(list(common_book_ids))):
        if (i > 0 and i % 100 == 0) or i == len(common_book_ids) - 1:
            print(f"     Processing book_id {i+1}/{len(common_book_ids)}: {book_id}")

        group1 = df1[df1['book_id'] == book_id].copy()
        group2 = df2[df2['book_id'] == book_id].copy()

        if group1.empty or group2.empty:
            continue

        # Create a list of choices for the fuzzy matching
        names1 = group1['name'].tolist()

        # Iterate through each record in group2 to find its best match in group1
        for _, row2 in group2.iterrows():
            name2 = row2['name']
            
            # Find the best match using fuzzy matching
            best_match = process.extractOne(name2, names1, scorer=fuzz.token_sort_ratio)
            
            if best_match and best_match[1] >= threshold:
                # A good match was found
                name1_matched = best_match[0]
                similarity_score = best_match[1]
                
                # Get the full row for the matched name
                row1_matched = group1.loc[group1['name'] == name1_matched].iloc[0]
                
                # Combine the two rows of data, adding suffixes to avoid column name collisions
                combined_row = pd.concat([
                    row1_matched.add_suffix(f'_{ocr1_name.lower()}'),
                    row2.add_suffix(f'_{ocr2_name.lower()}')
                ])
                
                # Add the similarity score and comparison info
                combined_row['similarity'] = similarity_score
                combined_row['comparison'] = f"{ocr1_name}_vs_{ocr2_name}"
                
                all_matches_list.append(combined_row)

    if not all_matches_list:
        print(f"   ❌ No fuzzy matches found for {ocr1_name} vs {ocr2_name}")
        return None

    # Create the final DataFrame from the list of combined rows
    final_df = pd.DataFrame(all_matches_list).reset_index(drop=True)
    
    # Clean up and reorder columns
    book_id_col = f'book_id_{ocr1_name.lower()}'
    if book_id_col in final_df.columns:
        final_df.rename(columns={book_id_col: 'book_id'}, inplace=True)
    
    # Remove duplicate book_id columns
    book_id_cols_to_drop = [col for col in final_df.columns if col.startswith('book_id_') and col != 'book_id']
    final_df.drop(columns=book_id_cols_to_drop, inplace=True)
    
    key_cols = [
        'book_id', 
        f'name_{ocr1_name.lower()}', 
        f'name_{ocr2_name.lower()}', 
        'similarity',
        'comparison'
    ]
    other_cols = sorted([col for col in final_df.columns if col not in key_cols])
    final_df = final_df[key_cols + other_cols]

    # Save the result
    output_file = os.path.join(base_path, f'comparison_{ocr1_name.lower()}_vs_{ocr2_name.lower()}_merged.csv')
    final_df.to_csv(output_file, index=False)
    
    print(f"   ✅ {ocr1_name} vs {ocr2_name} merge complete: {len(final_df)} matches")
    print(f"   💾 Saved to: {os.path.basename(output_file)}")
    return output_file

def perform_threeway_fuzzy_merge(df_monkey, df_dolphin, df_azure, base_path, threshold=85):
    """
    Performs a three-way fuzzy merge between MonkeyOCR, Dolphin, and AzureOCR.
    """
    try:
        from thefuzz import process, fuzz
    except ImportError:
        print(f"\n❌ Three-way fuzzy merge skipped. Please install 'thefuzz' and 'python-Levenshtein':")
        print("   pip install thefuzz python-Levenshtein")
        return None
    
    print(f"   Comparing {len(df_monkey)} MonkeyOCR, {len(df_dolphin)} Dolphin, and {len(df_azure)} AzureOCR records")
    
    all_matches_list = []
    
    # Find common book_ids across all three
    common_book_ids = (set(df_monkey['book_id'].unique()) & 
                      set(df_dolphin['book_id'].unique()) & 
                      set(df_azure['book_id'].unique()))
    print(f"   Found {len(common_book_ids)} common book_ids across all three OCR types")

    for i, book_id in enumerate(sorted(list(common_book_ids))):
        if (i > 0 and i % 50 == 0) or i == len(common_book_ids) - 1:
            print(f"     Processing book_id {i+1}/{len(common_book_ids)}: {book_id}")

        monkey_group = df_monkey[df_monkey['book_id'] == book_id].copy()
        dolphin_group = df_dolphin[df_dolphin['book_id'] == book_id].copy()
        azure_group = df_azure[df_azure['book_id'] == book_id].copy()

        if monkey_group.empty or dolphin_group.empty or azure_group.empty:
            continue

        # Use MonkeyOCR as the base and find matches in both Dolphin and AzureOCR
        dolphin_names = dolphin_group['name'].tolist()
        azure_names = azure_group['name'].tolist()

        for _, monkey_row in monkey_group.iterrows():
            monkey_name = monkey_row['name']
            
            # Find best match in Dolphin
            dolphin_match = process.extractOne(monkey_name, dolphin_names, scorer=fuzz.token_sort_ratio)
            
            # Find best match in AzureOCR
            azure_match = process.extractOne(monkey_name, azure_names, scorer=fuzz.token_sort_ratio)
            
            # Only include if both matches meet the threshold
            if (dolphin_match and dolphin_match[1] >= threshold and 
                azure_match and azure_match[1] >= threshold):
                
                # Get the matched rows
                dolphin_row = dolphin_group.loc[dolphin_group['name'] == dolphin_match[0]].iloc[0]
                azure_row = azure_group.loc[azure_group['name'] == azure_match[0]].iloc[0]
                
                # Combine all three rows
                combined_row = pd.concat([
                    monkey_row.add_suffix('_monkeyocr'),
                    dolphin_row.add_suffix('_dolphin'),
                    azure_row.add_suffix('_azureocr')
                ])
                
                # Add similarity scores
                combined_row['similarity_monkey_dolphin'] = dolphin_match[1]
                combined_row['similarity_monkey_azure'] = azure_match[1]
                combined_row['similarity_average'] = (dolphin_match[1] + azure_match[1]) / 2
                combined_row['comparison'] = 'threeway_merge'
                
                all_matches_list.append(combined_row)

    if not all_matches_list:
        print(f"   ❌ No three-way fuzzy matches found")
        return None

    # Create the final DataFrame
    final_df = pd.DataFrame(all_matches_list).reset_index(drop=True)
    
    # Clean up columns
    final_df.rename(columns={'book_id_monkeyocr': 'book_id'}, inplace=True)
    book_id_cols_to_drop = [col for col in final_df.columns if col.startswith('book_id_') and col != 'book_id']
    final_df.drop(columns=book_id_cols_to_drop, inplace=True)
    
    key_cols = [
        'book_id', 
        'name_monkeyocr', 
        'name_dolphin', 
        'name_azureocr',
        'similarity_monkey_dolphin',
        'similarity_monkey_azure',
        'similarity_average',
        'comparison'
    ]
    other_cols = sorted([col for col in final_df.columns if col not in key_cols])
    final_df = final_df[key_cols + other_cols]

    # Save the result
    output_file = os.path.join(base_path, 'comparison_threeway_merged.csv')
    final_df.to_csv(output_file, index=False)
    
    print(f"   ✅ Three-way merge complete: {len(final_df)} matches")
    print(f"   💾 Saved to: {os.path.basename(output_file)}")
    return output_file
def filter_by_image_agreement_multi_ocr(merged_files_dict, base_path):
    """
    Enhanced image agreement filtering that can handle multiple OCR comparisons.
    """
    print(f"\n{'='*60}")
    print(f"Filtering by Image Presence Agreement (Multi-OCR)...")
    print(f"{'='*60}")

    for comparison_name, file_path in merged_files_dict.items():
        if not file_path or not os.path.exists(file_path):
            continue
            
        print(f"\nProcessing {comparison_name}...")
        
        try:
            df = pd.read_csv(file_path)
            print(f"   Loaded data with {len(df)} rows")

            # Identify image filename columns
            image_cols = [col for col in df.columns if 'image_filename' in col]
            
            if len(image_cols) < 2:
                print(f"   ⚠️  Skipping {comparison_name}: needs at least 2 image columns")
                continue
            
            # Check image presence for each OCR type
            for col in image_cols:
                df[f'has_{col}'] = df[col].notna()
            
            # Check if all image presence columns agree
            has_cols = [f'has_{col}' for col in image_cols]
            
            if comparison_name == 'threeway_merge':
                # For three-way, all three must agree
                df['image_agreement'] = (df[has_cols[0]] == df[has_cols[1]]) & (df[has_cols[1]] == df[has_cols[2]])
            else:
                # For pairwise, both must agree
                df['image_agreement'] = (df[has_cols[0]] == df[has_cols[1]])
            
            # Find disagreement books
            disagreement_books = df[df['image_agreement'] == False]['book_id'].unique()
            print(f"   Found {len(disagreement_books)} book_ids with image disagreements")
            
            # Filter to keep only agreed books
            agreed_df = df[~df['book_id'].isin(disagreement_books)].copy()
            
            # Clean up helper columns
            helper_cols = [col for col in agreed_df.columns if col.startswith('has_') or col == 'image_agreement']
            agreed_df.drop(columns=helper_cols, inplace=True)
            agreed_df.reset_index(drop=True, inplace=True)
            
            # Save filtered result
            output_file = os.path.join(base_path, f'{comparison_name}_image_agreement_only.csv')
            agreed_df.to_csv(output_file, index=False)
            
            print(f"   ✅ Filtered to {len(agreed_df)} rows from {agreed_df['book_id'].nunique()} books")
            print(f"   💾 Saved to: {os.path.basename(output_file)}")

        except Exception as e:
            print(f"   ❌ Error processing {comparison_name}: {e}")

def main_3OCR():
    """Process all OCR types and perform multi-way fuzzy merging"""
    base_path = r'd:\data\HCNC\norway\biographies\storage'
    
    print("🚀 Starting CSV file collection and merging...")
    print(f"Base path: {base_path}")
    
    # Process all OCR types
    ocr_types = ['MonkeyOCR', 'Dolphin', 'AzureOCR']    
    results = {}
    
    for ocr_type in ocr_types:
        result = merge_csv_files(ocr_type, base_path)
        if result:
            results[ocr_type] = result
    
    # Print individual OCR summary
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
    
    # Perform multi-OCR fuzzy merges
    merged_files = None
    if len(results) >= 2:
        merged_files = perform_multi_ocr_fuzzy_merge(results, base_path, threshold=85)
    else:
        print("\nCould not perform fuzzy merge: need at least 2 OCR results.")
    
    # Perform image agreement filtering on all merged files
    if merged_files:
        filter_by_image_agreement_multi_ocr(merged_files, base_path)
    else:
        print("\nCould not perform image agreement filtering: no merged files created.")
    
    print(f"\n🎉 All processing complete!")
    
    # Print final summary of all generated files
    if merged_files:
        print(f"\n📊 Generated comparison files:")
        for comp_name, file_path in merged_files.items():
            if file_path:
                print(f"   {comp_name}: {os.path.basename(file_path)}")

if __name__ == "__main__":
    main_3OCR()

#if __name__ == "__main__":
#    main()