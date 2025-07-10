"""
Advanced JSON Extraction and DataFrame Linking for MonkeyOCR Validation

This script provides functions to:
1. Link two dataframes using book_id and fuzzy matching on names
2. Extract multiple JSON fields from both dataframes with proper suffixes
3. Create a comprehensive comparison dataframe
"""

import pandas as pd
import json
from thefuzz import fuzz, process
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

def fuzzy_link_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, 
                         book_id_col: str = 'book_id',
                         name_col: str = 'name',
                         suffix1: str = '_azure',
                         suffix2: str = '_monkey',
                         fuzzy_threshold: int = 80) -> pd.DataFrame:
    """
    Link two dataframes using book_id blocking and fuzzy matching on names.
    
    Parameters:
    -----------
    df1 : pd.DataFrame
        First dataframe (e.g., AzureOCR_df)
    df2 : pd.DataFrame
        Second dataframe (e.g., MonkeyOCR_df)
    book_id_col : str
        Column name for book_id (default: 'book_id')
    name_col : str
        Column name for name (default: 'name')
    suffix1 : str
        Suffix for first dataframe columns (default: '_azure')
    suffix2 : str
        Suffix for second dataframe columns (default: '_monkey')
    fuzzy_threshold : int
        Minimum fuzzy matching score (default: 80)
    
    Returns:
    --------
    pd.DataFrame
        Merged dataframe with proper suffixes
    """
    
    print(f"Linking dataframes...")
    print(f"DF1 shape: {df1.shape}")
    print(f"DF2 shape: {df2.shape}")
    
    # Get unique book_ids from both dataframes
    book_ids_1 = set(df1[book_id_col].unique())
    book_ids_2 = set(df2[book_id_col].unique())
    common_book_ids = book_ids_1.intersection(book_ids_2)
    
    print(f"Common book_ids: {len(common_book_ids)}")
    
    linked_records = []
    
    # Process each common book_id
    for book_id in common_book_ids:
        # Get records for this book_id from both dataframes
        df1_records = df1[df1[book_id_col] == book_id]
        df2_records = df2[df2[book_id_col] == book_id]
        
        # For each record in df1, find best match in df2
        for idx1, row1 in df1_records.iterrows():
            name1 = str(row1[name_col]) if pd.notna(row1[name_col]) else ""
            best_match = None
            best_score = 0
            
            for idx2, row2 in df2_records.iterrows():
                name2 = str(row2[name_col]) if pd.notna(row2[name_col]) else ""
                score = fuzz.ratio(name1, name2)
                
                if score > best_score and score >= fuzzy_threshold:
                    best_score = score
                    best_match = row2
            
            if best_match is not None:
                # Create merged record
                merged_record = {
                    book_id_col: book_id,
                    f'{name_col}{suffix1}': name1,
                    f'{name_col}{suffix2}': best_match[name_col],
                    'fuzzy_score': best_score
                }
                
                # Add all columns from df1 with suffix1
                for col in df1.columns:
                    if col not in [book_id_col, name_col]:
                        merged_record[f'{col}{suffix1}'] = row1[col]
                
                # Add all columns from df2 with suffix2
                for col in df2.columns:
                    if col not in [book_id_col, name_col]:
                        merged_record[f'{col}{suffix2}'] = best_match[col]
                
                linked_records.append(merged_record)
    
    linked_df = pd.DataFrame(linked_records)
    
    print(f"Linked records: {len(linked_df)}")
    print(f"Average fuzzy score: {linked_df['fuzzy_score'].mean():.2f}")
    
    return linked_df

def extract_multiple_json_fields(df: pd.DataFrame, 
                                extraction_list: List[List],
                                azure_json_col: str = 'biography_json_azure',
                                monkey_json_col: str = 'biography_json_monkey',
                                missing_value: str = 'Missing') -> pd.DataFrame:
    """
    Extract multiple JSON fields from both Azure and Monkey JSON columns.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with JSON columns
    extraction_list : List[List]
        List of extraction specifications. Each item can be:
        - [field_name] for simple field
        - [field_name, subfield1, subfield2, max_items] for array with multiple subfields
        - [field_name, subfield, max_items] for array with single subfield
    azure_json_col : str
        Column name for Azure JSON data (default: 'biography_json_azure')
    monkey_json_col : str
        Column name for Monkey JSON data (default: 'biography_json_monkey')
    missing_value : str
        Value for missing data (default: 'Missing')
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with extracted fields
    
    Example extraction_list:
    -----------------------
    [
        ["title"],  # Simple field
        ["educations", "title", "year", 3],  # Array with 2 subfields, max 3 items
        ["children", "name", "birth_date", 2],  # Array with 2 subfields, max 2 items
        ["jobs", "title", 3]  # Array with 1 subfield, max 3 items
    ]
    """
    
    def extract_field_from_json(json_str, field_name):
        """Extract field from JSON string"""
        try:
            if pd.isna(json_str) or json_str == '':
                return None
            data = json.loads(json_str)
            return data.get(field_name, None)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def get_base_name(field_name):
        """Get base name for column naming"""
        if field_name == 'children':
            return 'child'
        elif field_name == 'jobs':
            return 'job'
        elif field_name == 'educations':
            return 'education'
        elif field_name == 'spouses':
            return 'spouse'
        elif field_name == 'stays_abroad':
            return 'stay_abroad'
        else:
            return field_name[:-1] if field_name.endswith('s') else field_name
    
    result_df = df.copy()
    
    print(f"Extracting fields from {len(extraction_list)} specifications...")
    
    for spec in extraction_list:
        field_name = spec[0]
        
        if len(spec) == 1:
            # Simple field extraction
            print(f"Extracting simple field: {field_name}")
            
            # Extract from Azure JSON
            azure_values = []
            for _, row in result_df.iterrows():
                value = extract_field_from_json(row[azure_json_col], field_name)
                azure_values.append(value if value is not None else missing_value)
            result_df[f'{field_name}_azure'] = azure_values
            
            # Extract from Monkey JSON
            monkey_values = []
            for _, row in result_df.iterrows():
                value = extract_field_from_json(row[monkey_json_col], field_name)
                monkey_values.append(value if value is not None else missing_value)
            result_df[f'{field_name}_monkey'] = monkey_values
            
        else:
            # Array field extraction
            if len(spec) == 3:
                # Single subfield: [field_name, subfield, max_items]
                subfield = spec[1]
                max_items = spec[2]
                subfields = [subfield]
            else:
                # Multiple subfields: [field_name, subfield1, subfield2, max_items]
                subfields = spec[1:-1]  # All middle elements are subfields
                max_items = spec[-1]    # Last element is max_items
            
            base_name = get_base_name(field_name)
            print(f"Extracting array field: {field_name} with subfields {subfields}, max_items: {max_items}")
            
            # Initialize columns for both Azure and Monkey
            for i in range(1, max_items + 1):
                for subfield in subfields:
                    result_df[f'{base_name}{i}_{subfield}_azure'] = missing_value
                    result_df[f'{base_name}{i}_{subfield}_monkey'] = missing_value
            
            # Extract data for each row
            for index, row in result_df.iterrows():
                # Extract from Azure JSON
                azure_data = extract_field_from_json(row[azure_json_col], field_name)
                if azure_data and isinstance(azure_data, list):
                    for i, item in enumerate(azure_data[:max_items]):
                        if isinstance(item, dict):
                            for subfield in subfields:
                                col_name = f'{base_name}{i+1}_{subfield}_azure'
                                value = item.get(subfield, missing_value)
                                result_df.at[index, col_name] = value
                
                # Extract from Monkey JSON
                monkey_data = extract_field_from_json(row[monkey_json_col], field_name)
                if monkey_data and isinstance(monkey_data, list):
                    for i, item in enumerate(monkey_data[:max_items]):
                        if isinstance(item, dict):
                            for subfield in subfields:
                                col_name = f'{base_name}{i+1}_{subfield}_monkey'
                                value = item.get(subfield, missing_value)
                                result_df.at[index, col_name] = value
    
    return result_df

def create_comparison_dataframe(df1: pd.DataFrame, df2: pd.DataFrame,
                               extraction_list: List[List],
                               book_id_col: str = 'book_id',
                               name_col: str = 'name',
                               fuzzy_threshold: int = 80,
                               missing_value: str = 'Missing') -> pd.DataFrame:
    """
    Complete function to link dataframes and extract multiple JSON fields.
    
    Parameters:
    -----------
    df1 : pd.DataFrame
        First dataframe (e.g., AzureOCR_df)
    df2 : pd.DataFrame
        Second dataframe (e.g., MonkeyOCR_df)
    extraction_list : List[List]
        List of extraction specifications
    book_id_col : str
        Column name for book_id (default: 'book_id')
    name_col : str
        Column name for name (default: 'name')
    fuzzy_threshold : int
        Minimum fuzzy matching score (default: 80)
    missing_value : str
        Value for missing data (default: 'Missing')
    
    Returns:
    --------
    pd.DataFrame
        Final comparison dataframe with all extracted fields
    """
    
    print("="*80)
    print("CREATING COMPARISON DATAFRAME")
    print("="*80)
    
    # Step 1: Link dataframes
    print("\nStep 1: Linking dataframes...")
    linked_df = fuzzy_link_dataframes(df1, df2, book_id_col, name_col, 
                                     '_azure', '_monkey', fuzzy_threshold)
    
    # Step 2: Extract multiple JSON fields
    print("\nStep 2: Extracting JSON fields...")
    final_df = extract_multiple_json_fields(linked_df, extraction_list, 
                                           'biography_json_azure', 'biography_json_monkey',
                                           missing_value)
    
    # Step 3: Create final output with desired columns
    print("\nStep 3: Creating final output...")
    
    # Start with core columns
    output_columns = [book_id_col, f'{name_col}_azure', f'{name_col}_monkey', 'fuzzy_score']
    
    # Add all extracted field columns
    for col in final_df.columns:
        if col not in output_columns and col not in ['biography_json_azure', 'biography_json_monkey']:
            if any(suffix in col for suffix in ['_azure', '_monkey']):
                output_columns.append(col)
    
    result_df = final_df[output_columns].copy()
    
    print(f"\nFinal dataframe shape: {result_df.shape}")
    print(f"Final columns: {len(result_df.columns)}")
    
    return result_df

def compute_string_similarity(df: pd.DataFrame, 
                             azure_col: str, 
                             monkey_col: str,
                             similarity_methods: List[str] = ['ratio', 'token_sort_ratio', 'token_set_ratio', 'partial_ratio'],
                             include_length_stats: bool = True) -> Dict[str, Any]:
    """
    Compute string similarity between Azure and Monkey columns using multiple methods.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing both columns to compare
    azure_col : str
        Column name for Azure data
    monkey_col : str
        Column name for Monkey data
    similarity_methods : List[str]
        List of similarity methods to use (default: ['ratio', 'token_sort_ratio', 'token_set_ratio', 'partial_ratio'])
    include_length_stats : bool
        Whether to include length statistics (default: True)
    
    Returns:
    --------
    Dict[str, Any]
        Dictionary containing similarity metrics and statistics
    """
    
    print(f"Computing string similarity between '{azure_col}' and '{monkey_col}'...")
    
    # Filter out missing values
    valid_rows = df[(df[azure_col].notna()) & (df[monkey_col].notna()) & 
                   (df[azure_col] != 'Missing') & (df[monkey_col] != 'Missing')].copy()
    
    if len(valid_rows) == 0:
        print("No valid rows found for comparison!")
        return {"error": "No valid data for comparison"}
    
    print(f"Comparing {len(valid_rows)} valid rows out of {len(df)} total rows")
    
    # Initialize results
    results = {
        'total_rows': len(df),
        'valid_rows': len(valid_rows),
        'missing_azure': (df[azure_col].isna() | (df[azure_col] == 'Missing')).sum(),
        'missing_monkey': (df[monkey_col].isna() | (df[monkey_col] == 'Missing')).sum(),
        'similarity_scores': {},
        'statistics': {}
    }
    
    # Compute similarity scores for each method
    for method in similarity_methods:
        print(f"Computing {method} similarity...")
        scores = []
        
        for _, row in valid_rows.iterrows():
            azure_text = str(row[azure_col])
            monkey_text = str(row[monkey_col])
            
            if method == 'ratio':
                score = fuzz.ratio(azure_text, monkey_text)
            elif method == 'token_sort_ratio':
                score = fuzz.token_sort_ratio(azure_text, monkey_text)
            elif method == 'token_set_ratio':
                score = fuzz.token_set_ratio(azure_text, monkey_text)
            elif method == 'partial_ratio':
                score = fuzz.partial_ratio(azure_text, monkey_text)
            else:
                print(f"Unknown method: {method}")
                continue
            
            scores.append(score)
        
        # Store scores and compute statistics
        results['similarity_scores'][method] = scores
        results['statistics'][method] = {
            'mean': np.mean(scores),
            'median': np.median(scores),
            'std': np.std(scores),
            'min': np.min(scores),
            'max': np.max(scores),
            'q25': np.percentile(scores, 25),
            'q75': np.percentile(scores, 75)
        }
    
    # Compute length statistics if requested
    if include_length_stats:
        azure_lengths = [len(str(text)) for text in valid_rows[azure_col]]
        monkey_lengths = [len(str(text)) for text in valid_rows[monkey_col]]
        length_diffs = [abs(a - m) for a, m in zip(azure_lengths, monkey_lengths)]
        
        results['length_statistics'] = {
            'azure_lengths': {
                'mean': np.mean(azure_lengths),
                'median': np.median(azure_lengths),
                'std': np.std(azure_lengths),
                'min': np.min(azure_lengths),
                'max': np.max(azure_lengths)
            },
            'monkey_lengths': {
                'mean': np.mean(monkey_lengths),
                'median': np.median(monkey_lengths),
                'std': np.std(monkey_lengths),
                'min': np.min(monkey_lengths),
                'max': np.max(monkey_lengths)
            },
            'length_differences': {
                'mean': np.mean(length_diffs),
                'median': np.median(length_diffs),
                'std': np.std(length_diffs),
                'min': np.min(length_diffs),
                'max': np.max(length_diffs)
            }
        }
    
    # Find exact matches
    exact_matches = sum(1 for _, row in valid_rows.iterrows() 
                       if str(row[azure_col]).strip() == str(row[monkey_col]).strip())
    results['exact_matches'] = exact_matches
    results['exact_match_percentage'] = (exact_matches / len(valid_rows)) * 100
    
    # Find high similarity matches (>90%)
    if 'ratio' in results['similarity_scores']:
        high_similarity = sum(1 for score in results['similarity_scores']['ratio'] if score > 90)
        results['high_similarity_matches'] = high_similarity
        results['high_similarity_percentage'] = (high_similarity / len(valid_rows)) * 100
    
    return results

def analyze_all_similarities(df: pd.DataFrame, 
                            exclude_cols: List[str] = ['book_id', 'fuzzy_score'],
                            min_valid_rows: int = 10) -> Dict[str, Dict]:
    """
    Analyze string similarity for all matching Azure/Monkey column pairs.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with Azure and Monkey columns
    exclude_cols : List[str]
        Columns to exclude from analysis (default: ['book_id', 'fuzzy_score'])
    min_valid_rows : int
        Minimum number of valid rows required for analysis (default: 10)
    
    Returns:
    --------
    Dict[str, Dict]
        Dictionary of similarity analyses for each column pair
    """
    
    print("="*80)
    print("ANALYZING ALL COLUMN SIMILARITIES")
    print("="*80)
    
    # Find all Azure/Monkey column pairs
    azure_cols = [col for col in df.columns if col.endswith('_azure') and col not in exclude_cols]
    
    all_results = {}
    
    for azure_col in azure_cols:
        base_name = azure_col.replace('_azure', '')
        monkey_col = f"{base_name}_monkey"
        
        if monkey_col in df.columns:
            print(f"\nAnalyzing: {base_name}")
            print("-" * 50)
            
            # Check if we have enough valid data
            valid_count = len(df[(df[azure_col].notna()) & (df[monkey_col].notna()) & 
                               (df[azure_col] != 'Missing') & (df[monkey_col] != 'Missing')])
            
            if valid_count < min_valid_rows:
                print(f"Skipping {base_name}: only {valid_count} valid rows (minimum: {min_valid_rows})")
                continue
            
            results = compute_string_similarity(df, azure_col, monkey_col)
            all_results[base_name] = results
            
            # Print summary
            if 'error' not in results:
                print(f"Valid rows: {results['valid_rows']}")
                print(f"Exact matches: {results['exact_matches']} ({results['exact_match_percentage']:.1f}%)")
                if 'ratio' in results['statistics']:
                    ratio_stats = results['statistics']['ratio']
                    print(f"Fuzzy ratio - Mean: {ratio_stats['mean']:.1f}, Median: {ratio_stats['median']:.1f}")
    
    return all_results

def print_similarity_report(all_results: Dict[str, Dict], 
                           top_n: int = 10) -> None:
    """
    Print a comprehensive similarity report.
    
    Parameters:
    -----------
    all_results : Dict[str, Dict]
        Results from analyze_all_similarities()
    top_n : int
        Number of top/bottom performers to show (default: 10)
    """
    
    print("\n" + "="*80)
    print("COMPREHENSIVE SIMILARITY REPORT")
    print("="*80)
    
    # Collect summary data
    summary_data = []
    for field_name, results in all_results.items():
        if 'error' not in results and 'ratio' in results['statistics']:
            summary_data.append({
                'field': field_name,
                'valid_rows': results['valid_rows'],
                'exact_matches': results['exact_matches'],
                'exact_match_pct': results['exact_match_percentage'],
                'mean_similarity': results['statistics']['ratio']['mean'],
                'median_similarity': results['statistics']['ratio']['median'],
                'high_similarity_pct': results.get('high_similarity_percentage', 0)
            })
    
    if not summary_data:
        print("No valid similarity data found!")
        return
    
    # Overall statistics
    print("\nOVERALL STATISTICS:")
    print("-" * 40)
    total_comparisons = sum(item['valid_rows'] for item in summary_data)
    total_exact = sum(item['exact_matches'] for item in summary_data)
    avg_similarity = np.mean([item['mean_similarity'] for item in summary_data])
    
    print(f"Total fields analyzed: {len(summary_data)}")
    print(f"Total comparisons: {total_comparisons}")
    print(f"Overall exact matches: {total_exact} ({(total_exact/total_comparisons)*100:.1f}%)")
    print(f"Average similarity score: {avg_similarity:.1f}")
    
    # Best performing fields (highest similarity)
    print(f"\nTOP {top_n} MOST SIMILAR FIELDS:")
    print("-" * 50)
    best_fields = sorted(summary_data, key=lambda x: x['mean_similarity'], reverse=True)[:top_n]
    for i, field in enumerate(best_fields, 1):
        print(f"{i:2d}. {field['field']:<20} - Similarity: {field['mean_similarity']:5.1f}, "
              f"Exact: {field['exact_match_pct']:5.1f}%, Rows: {field['valid_rows']}")
    
    # Worst performing fields (lowest similarity)
    print(f"\nTOP {top_n} LEAST SIMILAR FIELDS:")
    print("-" * 50)
    worst_fields = sorted(summary_data, key=lambda x: x['mean_similarity'])[:top_n]
    for i, field in enumerate(worst_fields, 1):
        print(f"{i:2d}. {field['field']:<20} - Similarity: {field['mean_similarity']:5.1f}, "
              f"Exact: {field['exact_match_pct']:5.1f}%, Rows: {field['valid_rows']}")
    
    # Fields with most exact matches
    print(f"\nFIELDS WITH MOST EXACT MATCHES:")
    print("-" * 40)
    exact_fields = sorted(summary_data, key=lambda x: x['exact_match_pct'], reverse=True)[:top_n]
    for i, field in enumerate(exact_fields, 1):
        print(f"{i:2d}. {field['field']:<20} - Exact: {field['exact_match_pct']:5.1f}% "
              f"({field['exact_matches']}/{field['valid_rows']})")
    
    # Detailed statistics for a few key fields
    print(f"\nDETAILED STATISTICS (TOP 5 FIELDS):")
    print("-" * 60)
    for field in best_fields[:5]:
        field_name = field['field']
        if field_name in all_results:
            results = all_results[field_name]
            if 'ratio' in results['statistics']:
                stats = results['statistics']['ratio']
                print(f"\n{field_name.upper()}:")
                print(f"  Mean: {stats['mean']:.1f}, Median: {stats['median']:.1f}, Std: {stats['std']:.1f}")
                print(f"  Range: {stats['min']:.1f} - {stats['max']:.1f}")
                print(f"  Q25: {stats['q25']:.1f}, Q75: {stats['q75']:.1f}")
                
                # Length statistics if available
                if 'length_statistics' in results:
                    length_stats = results['length_statistics']
                    print(f"  Avg Length - Azure: {length_stats['azure_lengths']['mean']:.1f}, "
                          f"Monkey: {length_stats['monkey_lengths']['mean']:.1f}")
                    print(f"  Avg Length Difference: {length_stats['length_differences']['mean']:.1f}")

def main():
    """Main function to demonstrate the complete workflow"""
    
    # Load data
    print("Loading data...")
    AzureOCR_df = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_portraits_biographies_final.csv')
    MonkeyOCR_df = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_csv\extracted_all_names_portraits_biographies_final.csv')
    
    # Define extraction specification
    extraction_list = [
        ["title"],  # Simple field
        ["educations", "title", "year", 5],  # Education title and year, max 5
        ["children", "name", "birth_date", 5],  # Children name and birth_date, max 5
        ["jobs", "title", "location", "years", 5],  # Job title, location and year, max 5
        ["spouses", "name", "birth_date", 2],  # Spouse name and birth_date, max 2
        ["birth_date"],  # Simple field
        ["birth_place"],  # Simple field
        ["death_date"],  # Simple field
        ["father_name"],  # Simple field
        ["father_job"],  # Simple field
        ["mother_name"]   # Simple field
    ]
    
    # Create comparison dataframe
    comparison_df = create_comparison_dataframe(
        AzureOCR_df, MonkeyOCR_df, 
        extraction_list,
        book_id_col='book_id',
        name_col='name',
        fuzzy_threshold=80,
        missing_value='Missing'
    )
    
    # Display results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    print(f"\nFinal comparison dataframe shape: {comparison_df.shape}")
    print(f"Columns: {comparison_df.columns.tolist()}")
    
    # Show sample data
    print("\nSample data (first 3 rows):")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(comparison_df.head(3))
    
    # Save results
    output_filename = 'comprehensive_comparison_dataframe.csv'
    comparison_df.to_csv(output_filename, index=False)
    print(f"\nSaved comparison dataframe to: {output_filename}")
    
    # Statistics
    print("\n" + "="*80)
    print("STATISTICS")
    print("="*80)
    
    print(f"Total linked records: {len(comparison_df)}")
    print(f"Average fuzzy score: {comparison_df['fuzzy_score'].mean():.2f}")
    print(f"Min fuzzy score: {comparison_df['fuzzy_score'].min()}")
    print(f"Max fuzzy score: {comparison_df['fuzzy_score'].max()}")
    
    # Show columns by category
    title_cols = [col for col in comparison_df.columns if 'title' in col.lower()]
    education_cols = [col for col in comparison_df.columns if 'education' in col.lower()]
    children_cols = [col for col in comparison_df.columns if 'child' in col.lower()]
    job_cols = [col for col in comparison_df.columns if 'job' in col.lower()]
    
    print(f"\nTitle columns: {title_cols}")
    print(f"Education columns: {education_cols}")
    print(f"Children columns: {children_cols}")
    print(f"Job columns: {job_cols}")
    
    # Perform similarity analysis
    print("\n" + "="*80)
    print("STRING SIMILARITY ANALYSIS")
    print("="*80)
    
    # Analyze all column similarities
    similarity_results = analyze_all_similarities(comparison_df, 
                                                exclude_cols=['book_id', 'fuzzy_score', 'markdown_chunk_azure', 'markdown_chunk_monkey', 'image_filename_azure', 'image_filename_monkey'],
                                                min_valid_rows=10)
    
    # Print comprehensive report
    print_similarity_report(similarity_results, top_n=10)
    
    # Save similarity results
    similarity_summary = []
    for field_name, results in similarity_results.items():
        if 'error' not in results and 'ratio' in results['statistics']:
            similarity_summary.append({
                'field': field_name,
                'valid_rows': results['valid_rows'],
                'exact_matches': results['exact_matches'],
                'exact_match_percentage': results['statistics']['ratio']['mean'],
                'mean_similarity': results['statistics']['ratio']['mean'],
                'median_similarity': results['statistics']['ratio']['median'],
                'std_similarity': results['statistics']['ratio']['std'],
                'min_similarity': results['statistics']['ratio']['min'],
                'max_similarity': results['statistics']['ratio']['max'],
                'high_similarity_percentage': results.get('high_similarity_percentage', 0)
            })
    
    if similarity_summary:
        similarity_df = pd.DataFrame(similarity_summary)
        similarity_df.to_csv('similarity_analysis_report.csv', index=False)
        print(f"\nSaved detailed similarity analysis to: similarity_analysis_report.csv")
    
    # Perform job title overlap analysis
    print("\n" + "="*80)
    print("JOB TITLE OVERLAP ANALYSIS")
    print("="*80)
    
    # Compute job title overlap using fuzzy matching
    job_overlap_results = compute_job_title_overlap(
        comparison_df,
        fuzzy_threshold=80,
        missing_value='Missing'
    )
    
    # Analyze individual job overlap and flag problematic records
    print("\n" + "="*80)
    print("INDIVIDUAL JOB OVERLAP ANALYSIS")
    print("="*80)
    
    individual_overlap_results = analyze_individual_job_overlap(
        comparison_df,
        fuzzy_threshold=80,
        min_overlap_threshold=0.5,  # Flag if overlap coefficient < 50%
        missing_value='Missing'
    )
    
    # Save flagged records for manual inspection
    save_flagged_records(individual_overlap_results, 'flagged_job_overlap_records.csv')
    
    # Save job title overlap results
    if 'error' not in job_overlap_results:
        # Save matched pairs
        if job_overlap_results['matched_pairs_details']:
            matched_pairs_df = pd.DataFrame(job_overlap_results['matched_pairs_details'])
            matched_pairs_df.to_csv('job_title_matched_pairs.csv', index=False)
            print(f"\nSaved matched job title pairs to: job_title_matched_pairs.csv")
        
        # Save unmatched titles with name and book_id information
        if job_overlap_results['unmatched_azure_titles'] or job_overlap_results['unmatched_monkey_titles']:
            unmatched_data = []
            
            # Add unmatched Azure titles with record details
            for title in job_overlap_results['unmatched_azure_titles']:
                # Find all records with this Azure job title
                azure_job_cols = [col for col in comparison_df.columns if 'job' in col.lower() and 'title' in col.lower() and col.endswith('_azure')]
                for col in azure_job_cols:
                    if col in comparison_df.columns:
                        matching_rows = comparison_df[comparison_df[col] == title]
                        for _, row in matching_rows.iterrows():
                            unmatched_data.append({
                                'title': title,
                                'source': 'Azure',
                                'matched': False,
                                'book_id': row['book_id'],
                                'name_azure': row['name_azure'],
                                'name_monkey': row['name_monkey'],
                                'job_column': col
                            })
            
            # Add unmatched Monkey titles with record details
            for title in job_overlap_results['unmatched_monkey_titles']:
                # Find all records with this Monkey job title
                monkey_job_cols = [col for col in comparison_df.columns if 'job' in col.lower() and 'title' in col.lower() and col.endswith('_monkey')]
                for col in monkey_job_cols:
                    if col in comparison_df.columns:
                        matching_rows = comparison_df[comparison_df[col] == title]
                        for _, row in matching_rows.iterrows():
                            unmatched_data.append({
                                'title': title,
                                'source': 'Monkey',
                                'matched': False,
                                'book_id': row['book_id'],
                                'name_azure': row['name_azure'],
                                'name_monkey': row['name_monkey'],
                                'job_column': col
                            })
            
            if unmatched_data:
                unmatched_df = pd.DataFrame(unmatched_data)
                unmatched_df.to_csv('job_title_unmatched.csv', index=False)
                print(f"Saved unmatched job titles to: job_title_unmatched.csv")
        
        # Save summary statistics
        overlap_summary = {
            'total_azure_titles': job_overlap_results['total_azure_titles'],
            'total_monkey_titles': job_overlap_results['total_monkey_titles'],
            'matched_pairs': job_overlap_results['matched_pairs'],
            'unmatched_azure': job_overlap_results['unmatched_azure'],
            'unmatched_monkey': job_overlap_results['unmatched_monkey'],
            'azure_coverage_percent': job_overlap_results['azure_coverage_percent'],
            'monkey_coverage_percent': job_overlap_results['monkey_coverage_percent'],
            'jaccard_similarity': job_overlap_results['jaccard_similarity'],
            'overlap_coefficient': job_overlap_results['overlap_coefficient'],
            'dice_coefficient': job_overlap_results['dice_coefficient'],
            'fuzzy_threshold': job_overlap_results['fuzzy_threshold']
        }
        
        # Add similarity statistics if available
        if job_overlap_results['similarity_statistics']:
            stats = job_overlap_results['similarity_statistics']
            overlap_summary.update({
                'mean_similarity': stats['mean'],
                'median_similarity': stats['median'],
                'std_similarity': stats['std'],
                'min_similarity': stats['min'],
                'max_similarity': stats['max']
            })
        
        overlap_summary_df = pd.DataFrame([overlap_summary])
        overlap_summary_df.to_csv('job_title_overlap_summary.csv', index=False)
        print(f"Saved job title overlap summary to: job_title_overlap_summary.csv")
    
    # Analyze individual job overlap
    print("\n" + "="*80)
    print("INDIVIDUAL JOB OVERLAP ANALYSIS")
    print("="*80)
    
    individual_overlap_results = analyze_individual_job_overlap(
        comparison_df,
        fuzzy_threshold=80,
        min_overlap_threshold=0.5,
        missing_value='Missing'
    )
    
    # Save flagged records for manual inspection
    save_flagged_records(individual_overlap_results, 'flagged_job_overlap_records.csv')
    
    return comparison_df

def compute_job_title_overlap(df: pd.DataFrame, 
                              azure_job_cols: Optional[List[str]] = None,
                              monkey_job_cols: Optional[List[str]] = None,
                              fuzzy_threshold: int = 80,
                              missing_value: str = 'Missing') -> Dict[str, Any]:
    """
    Compute the overlap of job titles between Azure and MonkeyOCR using fuzzy matching.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing job title columns
    azure_job_cols : List[str], optional
        List of Azure job title columns. If None, auto-detect from column names
    monkey_job_cols : List[str], optional
        List of Monkey job title columns. If None, auto-detect from column names
    fuzzy_threshold : int
        Minimum fuzzy matching score for considering titles as matching (default: 80)
    missing_value : str
        Value representing missing data (default: 'Missing')
    
    Returns:
    --------
    Dict[str, Any]
        Dictionary containing overlap metrics and detailed results
    """
    
    print("="*80)
    print("COMPUTING JOB TITLE OVERLAP WITH FUZZY MATCHING")
    print("="*80)
    
    # Auto-detect job columns if not provided
    if azure_job_cols is None:
        azure_job_cols = [col for col in df.columns if 'job' in col.lower() and 'title' in col.lower() and col.endswith('_azure')]
    
    if monkey_job_cols is None:
        monkey_job_cols = [col for col in df.columns if 'job' in col.lower() and 'title' in col.lower() and col.endswith('_monkey')]
    
    print(f"Azure job title columns: {azure_job_cols}")
    print(f"Monkey job title columns: {monkey_job_cols}")
    
    # Extract all unique job titles from Azure columns
    azure_titles = set()
    for col in azure_job_cols:
        if col in df.columns:
            titles = df[col].dropna()
            titles = titles[titles != missing_value]
            azure_titles.update([str(title).strip() for title in titles if str(title).strip()])
    
    # Extract all unique job titles from Monkey columns
    monkey_titles = set()
    for col in monkey_job_cols:
        if col in df.columns:
            titles = df[col].dropna()
            titles = titles[titles != missing_value]
            monkey_titles.update([str(title).strip() for title in titles if str(title).strip()])
    
    print(f"\nUnique Azure job titles: {len(azure_titles)}")
    print(f"Unique Monkey job titles: {len(monkey_titles)}")
    
    if not azure_titles or not monkey_titles:
        return {
            'error': 'No valid job titles found in one or both datasets',
            'azure_titles_count': len(azure_titles),
            'monkey_titles_count': len(monkey_titles)
        }
    
    # Find fuzzy matches
    matched_pairs = []
    unmatched_azure = []
    unmatched_monkey = list(monkey_titles)
    
    print(f"\nFinding fuzzy matches with threshold {fuzzy_threshold}...")
    
    for azure_title in azure_titles:
        # Find best match in monkey titles
        best_match = process.extractOne(azure_title, monkey_titles, scorer=fuzz.ratio)
        
        if best_match and best_match[1] >= fuzzy_threshold:
            matched_pairs.append({
                'azure_title': azure_title,
                'monkey_title': best_match[0],
                'similarity_score': best_match[1]
            })
            # Remove from unmatched monkey titles
            if best_match[0] in unmatched_monkey:
                unmatched_monkey.remove(best_match[0])
        else:
            unmatched_azure.append(azure_title)
    
    # Compute overlap metrics
    total_azure = len(azure_titles)
    total_monkey = len(monkey_titles)
    matched_count = len(matched_pairs)
    
    azure_coverage = (matched_count / total_azure) * 100 if total_azure > 0 else 0
    monkey_coverage = (matched_count / total_monkey) * 100 if total_monkey > 0 else 0
    
    # Jaccard similarity (intersection over union)
    jaccard_similarity = matched_count / (total_azure + total_monkey - matched_count) if (total_azure + total_monkey - matched_count) > 0 else 0
    
    # Overlap coefficient (intersection over minimum)
    overlap_coefficient = matched_count / min(total_azure, total_monkey) if min(total_azure, total_monkey) > 0 else 0
    
    # Dice coefficient (2 * intersection / sum of sets)
    dice_coefficient = (2 * matched_count) / (total_azure + total_monkey) if (total_azure + total_monkey) > 0 else 0
    
    # Compute similarity statistics
    similarity_scores = [pair['similarity_score'] for pair in matched_pairs]
    similarity_stats = {}
    if similarity_scores:
        similarity_stats = {
            'mean': np.mean(similarity_scores),
            'median': np.median(similarity_scores),
            'std': np.std(similarity_scores),
            'min': np.min(similarity_scores),
            'max': np.max(similarity_scores),
            'q25': np.percentile(similarity_scores, 25),
            'q75': np.percentile(similarity_scores, 75)
        }
    
    results = {
        'total_azure_titles': total_azure,
        'total_monkey_titles': total_monkey,
        'matched_pairs': matched_count,
        'unmatched_azure': len(unmatched_azure),
        'unmatched_monkey': len(unmatched_monkey),
        'azure_coverage_percent': azure_coverage,
        'monkey_coverage_percent': monkey_coverage,
        'jaccard_similarity': jaccard_similarity,
        'overlap_coefficient': overlap_coefficient,
        'dice_coefficient': dice_coefficient,
        'similarity_statistics': similarity_stats,
        'matched_pairs_details': matched_pairs,
        'unmatched_azure_titles': unmatched_azure,
        'unmatched_monkey_titles': unmatched_monkey,
        'fuzzy_threshold': fuzzy_threshold
    }
    
    # Print summary
    print(f"\nJOB TITLE OVERLAP RESULTS:")
    print("-" * 40)
    print(f"Total Azure job titles: {total_azure}")
    print(f"Total Monkey job titles: {total_monkey}")
    print(f"Matched pairs (fuzzy ≥{fuzzy_threshold}): {matched_count}")
    print(f"Unmatched Azure titles: {len(unmatched_azure)}")
    print(f"Unmatched Monkey titles: {len(unmatched_monkey)}")
    print(f"\nCoverage:")
    print(f"Azure coverage: {azure_coverage:.1f}%")
    print(f"Monkey coverage: {monkey_coverage:.1f}%")
    print(f"\nSimilarity Metrics:")
    print(f"Jaccard similarity: {jaccard_similarity:.3f}")
    print(f"Overlap coefficient: {overlap_coefficient:.3f}")
    print(f"Dice coefficient: {dice_coefficient:.3f}")
    
    if similarity_stats:
        print(f"\nFuzzy Match Statistics:")
        print(f"Mean similarity: {similarity_stats['mean']:.1f}")
        print(f"Median similarity: {similarity_stats['median']:.1f}")
        print(f"Std deviation: {similarity_stats['std']:.1f}")
        print(f"Range: {similarity_stats['min']:.1f} - {similarity_stats['max']:.1f}")
    
    # Show some examples
    if matched_pairs:
        print(f"\nTOP 10 MATCHED PAIRS:")
        print("-" * 60)
        top_matches = sorted(matched_pairs, key=lambda x: x['similarity_score'], reverse=True)[:10]
        for i, pair in enumerate(top_matches, 1):
            print(f"{i:2d}. {pair['azure_title']:<25} ↔ {pair['monkey_title']:<25} ({pair['similarity_score']:.0f})")
    
    if unmatched_azure:
        print(f"\nTOP 10 UNMATCHED AZURE TITLES:")
        print("-" * 40)
        for i, title in enumerate(unmatched_azure[:10], 1):
            print(f"{i:2d}. {title}")
    
    if unmatched_monkey:
        print(f"\nTOP 10 UNMATCHED MONKEY TITLES:")
        print("-" * 40)
        for i, title in enumerate(unmatched_monkey[:10], 1):
            print(f"{i:2d}. {title}")
    
    return results

def analyze_individual_job_overlap(df: pd.DataFrame, 
                                   azure_job_cols: Optional[List[str]] = None,
                                   monkey_job_cols: Optional[List[str]] = None,
                                   fuzzy_threshold: int = 80,
                                   min_overlap_threshold: float = 0.5,
                                   missing_value: str = 'Missing') -> pd.DataFrame:
    """
    Analyze job title overlap for individual records and flag those with insufficient overlap.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing job title columns
    azure_job_cols : List[str], optional
        List of Azure job title columns. If None, auto-detect from column names
    monkey_job_cols : List[str], optional
        List of Monkey job title columns. If None, auto-detect from column names
    fuzzy_threshold : int
        Minimum fuzzy matching score for considering titles as matching (default: 80)
    min_overlap_threshold : float
        Minimum overlap ratio to not flag as problematic (default: 0.5)
    missing_value : str
        Value representing missing data (default: 'Missing')
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with individual job overlap analysis results
    """
    
    print("="*80)
    print("ANALYZING INDIVIDUAL JOB TITLE OVERLAP")
    print("="*80)
    
    # Auto-detect job columns if not provided
    if azure_job_cols is None:
        azure_job_cols = [col for col in df.columns if 'job' in col.lower() and 'title' in col.lower() and col.endswith('_azure')]
    
    if monkey_job_cols is None:
        monkey_job_cols = [col for col in df.columns if 'job' in col.lower() and 'title' in col.lower() and col.endswith('_monkey')]
    
    print(f"Azure job title columns: {azure_job_cols}")
    print(f"Monkey job title columns: {monkey_job_cols}")
    print(f"Fuzzy threshold: {fuzzy_threshold}")
    print(f"Minimum overlap threshold: {min_overlap_threshold}")
    
    individual_results = []
    
    # Analyze each record individually
    for idx, row in df.iterrows():
        # Extract Azure job titles for this individual
        azure_jobs = []
        for col in azure_job_cols:
            if col in df.columns and pd.notna(row[col]) and row[col] != missing_value:
                azure_jobs.append(str(row[col]).strip())
        
        # Extract Monkey job titles for this individual
        monkey_jobs = []
        for col in monkey_job_cols:
            if col in df.columns and pd.notna(row[col]) and row[col] != missing_value:
                monkey_jobs.append(str(row[col]).strip())
        
        # Remove duplicates while preserving order
        azure_jobs = list(dict.fromkeys(azure_jobs))
        monkey_jobs = list(dict.fromkeys(monkey_jobs))
        
        # Skip if no jobs found
        if not azure_jobs and not monkey_jobs:
            continue
        
        # Find matches between Azure and Monkey jobs for this individual
        matched_pairs = []
        unmatched_azure = []
        unmatched_monkey = list(monkey_jobs)
        
        for azure_job in azure_jobs:
            best_match = None
            best_score = 0
            
            for monkey_job in monkey_jobs:
                score = fuzz.ratio(azure_job, monkey_job)
                if score >= fuzzy_threshold and score > best_score:
                    best_score = score
                    best_match = monkey_job
            
            if best_match:
                matched_pairs.append({
                    'azure_job': azure_job,
                    'monkey_job': best_match,
                    'similarity_score': best_score
                })
                if best_match in unmatched_monkey:
                    unmatched_monkey.remove(best_match)
            else:
                unmatched_azure.append(azure_job)
        
        # Calculate overlap metrics for this individual
        total_azure_jobs = len(azure_jobs)
        total_monkey_jobs = len(monkey_jobs)
        matched_count = len(matched_pairs)
        
        # Calculate various overlap metrics
        azure_coverage = (matched_count / total_azure_jobs) if total_azure_jobs > 0 else 0
        monkey_coverage = (matched_count / total_monkey_jobs) if total_monkey_jobs > 0 else 0
        
        # Jaccard similarity (intersection over union)
        jaccard_similarity = matched_count / (total_azure_jobs + total_monkey_jobs - matched_count) if (total_azure_jobs + total_monkey_jobs - matched_count) > 0 else 0
        
        # Overlap coefficient (intersection over minimum)
        overlap_coefficient = matched_count / min(total_azure_jobs, total_monkey_jobs) if min(total_azure_jobs, total_monkey_jobs) > 0 else 0
        
        # Dice coefficient (2 * intersection / sum of sets)
        dice_coefficient = (2 * matched_count) / (total_azure_jobs + total_monkey_jobs) if (total_azure_jobs + total_monkey_jobs) > 0 else 0
        
        # Determine if this individual should be flagged
        # Flag if overlap coefficient is below threshold OR if there are jobs in both but no matches
        needs_inspection = (
            overlap_coefficient < min_overlap_threshold or 
            (total_azure_jobs > 0 and total_monkey_jobs > 0 and matched_count == 0)
        )
        
        # Calculate average similarity for matched pairs
        avg_similarity = np.mean([pair['similarity_score'] for pair in matched_pairs]) if matched_pairs else 0
        
        # Prepare detailed job information
        matched_pairs_str = "; ".join([f"{pair['azure_job']} ↔ {pair['monkey_job']} ({pair['similarity_score']:.0f}%)" for pair in matched_pairs])
        unmatched_azure_str = "; ".join(unmatched_azure)
        unmatched_monkey_str = "; ".join(unmatched_monkey)
        
        individual_results.append({
            'book_id': row.get('book_id', 'Unknown'),
            'name_azure': row.get('name_azure', 'Unknown'),
            'name_monkey': row.get('name_monkey', 'Unknown'),
            'fuzzy_score': row.get('fuzzy_score', 0),
            'total_azure_jobs': total_azure_jobs,
            'total_monkey_jobs': total_monkey_jobs,
            'matched_pairs': matched_count,
            'unmatched_azure': len(unmatched_azure),
            'unmatched_monkey': len(unmatched_monkey),
            'azure_coverage': azure_coverage,
            'monkey_coverage': monkey_coverage,
            'jaccard_similarity': jaccard_similarity,
            'overlap_coefficient': overlap_coefficient,
            'dice_coefficient': dice_coefficient,
            'avg_similarity': avg_similarity,
            'needs_inspection': needs_inspection,
            'azure_jobs': "; ".join(azure_jobs),
            'monkey_jobs': "; ".join(monkey_jobs),
            'matched_pairs_details': matched_pairs_str,
            'unmatched_azure_jobs': unmatched_azure_str,
            'unmatched_monkey_jobs': unmatched_monkey_str,
            'inspection_reason': get_inspection_reason(total_azure_jobs, total_monkey_jobs, matched_count, overlap_coefficient, min_overlap_threshold)
        })
    
    results_df = pd.DataFrame(individual_results)
    
    # Print summary statistics
    total_records = len(results_df)
    flagged_records = len(results_df[results_df['needs_inspection'] == True])
    
    print(f"\nINDIVIDUAL JOB OVERLAP ANALYSIS RESULTS:")
    print("-" * 50)
    print(f"Total records analyzed: {total_records}")
    print(f"Records flagged for inspection: {flagged_records} ({(flagged_records/total_records)*100:.1f}%)")
    print(f"Records with good overlap: {total_records - flagged_records} ({((total_records - flagged_records)/total_records)*100:.1f}%)")
    
    if flagged_records > 0:
        print(f"\nFLAGGED RECORDS BREAKDOWN:")
        print("-" * 30)
        flagged_df = results_df[results_df['needs_inspection'] == True]
        
        # Group by inspection reason
        reason_counts = flagged_df['inspection_reason'].value_counts()
        for reason, count in reason_counts.items():
            print(f"  {reason}: {count} records")
        
        # Show average metrics for flagged records
        print(f"\nFLAGGED RECORDS STATISTICS:")
        print(f"  Average overlap coefficient: {flagged_df['overlap_coefficient'].mean():.3f}")
        print(f"  Average Jaccard similarity: {flagged_df['jaccard_similarity'].mean():.3f}")
        print(f"  Average Azure jobs per record: {flagged_df['total_azure_jobs'].mean():.1f}")
        print(f"  Average Monkey jobs per record: {flagged_df['total_monkey_jobs'].mean():.1f}")
    
    # Show some examples
    if flagged_records > 0:
        print(f"\nTOP 10 FLAGGED RECORDS (ordered by overlap coefficient):")
        print("-" * 80)
        flagged_sorted = results_df[results_df['needs_inspection'] == True].sort_values('overlap_coefficient')
        
        for i, (_, row) in enumerate(flagged_sorted.head(10).iterrows(), 1):
            print(f"\n{i:2d}. {row['name_azure']} (Book: {row['book_id']})")
            print(f"    Overlap coefficient: {row['overlap_coefficient']:.3f}")
            print(f"    Azure jobs ({row['total_azure_jobs']}): {row['azure_jobs']}")
            print(f"    Monkey jobs ({row['total_monkey_jobs']}): {row['monkey_jobs']}")
            print(f"    Reason: {row['inspection_reason']}")
            if row['matched_pairs_details']:
                print(f"    Matches: {row['matched_pairs_details']}")
    
    return results_df

def get_inspection_reason(total_azure_jobs: int, total_monkey_jobs: int, matched_count: int, 
                         overlap_coefficient: float, min_overlap_threshold: float) -> str:
    """
    Determine the reason why a record needs inspection.
    
    Parameters:
    -----------
    total_azure_jobs : int
        Number of Azure jobs
    total_monkey_jobs : int
        Number of Monkey jobs
    matched_count : int
        Number of matched job pairs
    overlap_coefficient : float
        Overlap coefficient value
    min_overlap_threshold : float
        Minimum overlap threshold
    
    Returns:
    --------
    str
        Human-readable reason for inspection
    """
    
    if total_azure_jobs == 0 and total_monkey_jobs > 0:
        return "Only Monkey jobs found"
    elif total_azure_jobs > 0 and total_monkey_jobs == 0:
        return "Only Azure jobs found"
    elif total_azure_jobs > 0 and total_monkey_jobs > 0 and matched_count == 0:
        return "Jobs in both but no matches"
    elif overlap_coefficient < min_overlap_threshold:
        return f"Low overlap ({overlap_coefficient:.3f} < {min_overlap_threshold})"
    else:
        return "Good overlap"

def save_flagged_records(individual_results_df: pd.DataFrame, 
                        output_filename: str = 'flagged_job_overlap_records.csv') -> None:
    """
    Save flagged records to a CSV file for manual inspection.
    
    Parameters:
    -----------
    individual_results_df : pd.DataFrame
        DataFrame with individual job overlap analysis results
    output_filename : str
        Output filename for the CSV file (default: 'flagged_job_overlap_records.csv')
    """
    
    flagged_records = individual_results_df[individual_results_df['needs_inspection'] == True]
    
    if len(flagged_records) > 0:
        # Create a simplified version for manual inspection
        inspection_df = flagged_records[[
            'book_id', 'name_azure', 'name_monkey', 'fuzzy_score',
            'total_azure_jobs', 'total_monkey_jobs', 'matched_pairs',
            'overlap_coefficient', 'jaccard_similarity', 'avg_similarity',
            'inspection_reason', 'azure_jobs', 'monkey_jobs',
            'matched_pairs_details', 'unmatched_azure_jobs', 'unmatched_monkey_jobs'
        ]].copy()
        
        # Sort by overlap coefficient (worst first)
        inspection_df = inspection_df.sort_values('overlap_coefficient')
        
        # Save to CSV
        inspection_df.to_csv(output_filename, index=False)
        print(f"\nSaved {len(flagged_records)} flagged records to: {output_filename}")
        
        # Also save all individual results
        all_results_filename = output_filename.replace('.csv', '_all_results.csv')
        individual_results_df.to_csv(all_results_filename, index=False)
        print(f"Saved all {len(individual_results_df)} individual results to: {all_results_filename}")
    else:
        print("No records flagged for inspection!")

if __name__ == "__main__":
    comparison_df = main()
