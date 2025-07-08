# Direct comparison of your pipeline results
import pandas as pd
import json
from difflib import SequenceMatcher
from Levenshtein import distance as levenshtein_distance
from thefuzz import fuzz, process
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

def fuzzy_match_names_by_book(df1: pd.DataFrame, df2: pd.DataFrame, 
                             name_column: str = 'name', 
                             book_id_column: str = 'book_id',
                             similarity_threshold: float = 80.0) -> pd.DataFrame:
    """
    Perform fuzzy matching on names within each book_id between two dataframes.
    
    Parameters:
    -----------
    df1, df2 : pd.DataFrame
        DataFrames to match
    name_column : str
        Column containing names to match
    book_id_column : str
        Column containing book IDs to group by
    similarity_threshold : float
        Minimum similarity score for matching (0-100)
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with matched pairs and similarity scores
    """
    matched_pairs = []
    
    # Get common book_ids
    common_book_ids = set(df1[book_id_column].unique()) & set(df2[book_id_column].unique())
    
    print(f"Found {len(common_book_ids)} common book_ids between dataframes")
    
    for book_id in common_book_ids:
        # Get names for this book_id from both dataframes
        names_df1 = df1[df1[book_id_column] == book_id][name_column].tolist()
        names_df2 = df2[df2[book_id_column] == book_id][name_column].tolist()
        
        if not names_df1 or not names_df2:
            continue
            
        print(f"Book {book_id}: {len(names_df1)} names in df1, {len(names_df2)} names in df2")
        
        # Create indices for tracking original dataframe rows
        df1_book = df1[df1[book_id_column] == book_id].reset_index()
        df2_book = df2[df2[book_id_column] == book_id].reset_index()
        
        # Perform fuzzy matching for each name in df1
        for idx1, name1 in enumerate(names_df1):
            # Find best match in df2 for this book_id
            match_result = process.extractOne(
                name1, names_df2, 
                scorer=fuzz.ratio
            )
            
            if match_result and match_result[1] >= similarity_threshold:
                matched_name = match_result[0]
                similarity_score = match_result[1]
                
                # Find the index of the matched name in df2_book
                idx2 = names_df2.index(matched_name)
                
                # Get original indices from the full dataframes
                original_idx1 = df1_book.iloc[idx1]['index']
                original_idx2 = df2_book.iloc[idx2]['index']
                
                matched_pairs.append({
                    'book_id': book_id,
                    'name_df1': name1,
                    'name_df2': matched_name,
                    'name_similarity': similarity_score,
                    'idx_df1': original_idx1,
                    'idx_df2': original_idx2
                })
                
                print(f"  Matched: '{name1}' <-> '{matched_name}' (similarity: {similarity_score:.1f})")
    
    if not matched_pairs:
        print("No matches found above the similarity threshold")
        return pd.DataFrame()
    
    matched_df = pd.DataFrame(matched_pairs)
    print(f"\nTotal matched pairs: {len(matched_df)}")
    
    return matched_df

def compare_biography_elements_for_matches(df1: pd.DataFrame, df2: pd.DataFrame, 
                                         matched_pairs: pd.DataFrame,
                                         json_column: str, 
                                         elements_to_compare: List[str],
                                         distance_metric: str = 'levenshtein') -> pd.DataFrame:
    """
    Compare biographical elements for fuzzy-matched name pairs.
    
    Parameters:
    -----------
    df1, df2 : pd.DataFrame
        Original dataframes with biographical data
    matched_pairs : pd.DataFrame
        Result from fuzzy_match_names_by_book()
    json_column : str
        Column containing JSON biographical data
    elements_to_compare : List[str]
        List of JSON elements to compare
    distance_metric : str
        Distance metric to use
    
    Returns:
    --------
    pd.DataFrame
        Detailed comparison results for each matched pair
    """
    def safe_json_parse(json_str):
        """Safely parse JSON string"""
        if pd.isna(json_str) or json_str == '':
            return {}
        try:
            if isinstance(json_str, str):
                return json.loads(json_str)
            elif isinstance(json_str, dict):
                return json_str
            else:
                return {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def extract_element(json_obj, key):
        """Extract element from JSON object"""
        if not isinstance(json_obj, dict):
            return None
        return json_obj.get(key, None)
    
    def normalize_for_comparison(value):
        """Normalize values for comparison"""
        if value is None:
            return ""
        elif isinstance(value, str):
            return value.strip().lower()
        elif isinstance(value, list):
            return str(sorted([str(item).strip().lower() for item in value]))
        elif isinstance(value, dict):
            return str(sorted([(k, str(v).strip().lower()) for k, v in value.items()]))
        else:
            return str(value).strip().lower()
    
    def calculate_distance(val1, val2, metric):
        """Calculate distance between two values"""
        if val1 == val2:
            return 0.0
        
        if val1 == "" and val2 == "":
            return 0.0
        
        if val1 == "" or val2 == "":
            return 1.0
        
        if metric == 'levenshtein':
            max_len = max(len(val1), len(val2))
            if max_len == 0:
                return 0.0
            return levenshtein_distance(val1, val2) / max_len
        
        elif metric == 'sequence_matcher':
            return 1 - SequenceMatcher(None, val1, val2).ratio()
        
        elif metric == 'jaccard':
            set1 = set(val1.split())
            set2 = set(val2.split())
            union = set1.union(set2)
            intersection = set1.intersection(set2)
            if len(union) == 0:
                return 0.0
            return 1 - (len(intersection) / len(union))
        
        else:
            raise ValueError(f"Unknown distance metric: {metric}")
    
    comparison_results = []
    
    print(f"Comparing {len(elements_to_compare)} elements for {len(matched_pairs)} matched pairs...")
    
    for _, match_row in matched_pairs.iterrows():
        idx1 = match_row['idx_df1']
        idx2 = match_row['idx_df2']
        
        # Get the JSON data for both matched records
        json_data1 = safe_json_parse(df1.loc[idx1, json_column])
        json_data2 = safe_json_parse(df2.loc[idx2, json_column])
        
        # Compare each element
        for element in elements_to_compare:
            val1 = extract_element(json_data1, element)
            val2 = extract_element(json_data2, element)
            
            norm_val1 = normalize_for_comparison(val1)
            norm_val2 = normalize_for_comparison(val2)
            
            distance = calculate_distance(norm_val1, norm_val2, distance_metric)
            similarity = 1 - distance
            exact_match = norm_val1 == norm_val2
            
            comparison_results.append({
                'book_id': match_row['book_id'],
                'name_df1': match_row['name_df1'],
                'name_df2': match_row['name_df2'],
                'name_similarity': match_row['name_similarity'],
                'element': element,
                f'{element}_df1': val1,
                f'{element}_df2': val2,
                'edit_distance': distance,
                'similarity_score': similarity,
                'exact_match': exact_match,
                'distance_metric': distance_metric
            })
    
    result_df = pd.DataFrame(comparison_results)
    return result_df

def comprehensive_biography_comparison(df1: pd.DataFrame, df2: pd.DataFrame,
                                     df1_name: str = "DataFrame1",
                                     df2_name: str = "DataFrame2",
                                     name_column: str = 'name',
                                     book_id_column: str = 'book_id',
                                     json_column: str = 'biography_json',
                                     elements_to_compare: List[str] = None,
                                     name_similarity_threshold: float = 80.0,
                                     distance_metric: str = 'levenshtein') -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Comprehensive comparison of biographical data between two dataframes.
    
    This function:
    1. Performs fuzzy matching on names within each book_id
    2. Compares biographical elements for matched pairs
    3. Generates summary statistics
    
    Parameters:
    -----------
    df1, df2 : pd.DataFrame
        DataFrames to compare (e.g., Dolphin vs AzureOCR results)
    df1_name, df2_name : str
        Names for the dataframes (for reporting)
    elements_to_compare : List[str]
        Biographical elements to compare
    name_similarity_threshold : float
        Minimum similarity for name matching (0-100)
    
    Returns:
    --------
    Tuple[pd.DataFrame, pd.DataFrame, Dict]
        - matched_pairs: DataFrame with fuzzy-matched name pairs
        - comparison_results: Detailed element comparison results  
        - summary: Summary statistics
    """
    
    if elements_to_compare is None:
        elements_to_compare = [
            'father_name', 'mother_name', 'birth_date', 'birth_place',
            'death_date', 'educations', 'jobs', 'spouses', 'children'
        ]
    
    print(f"=== Comprehensive Biography Comparison: {df1_name} vs {df2_name} ===")
    print(f"DataFrame 1 ({df1_name}): {len(df1)} records")
    print(f"DataFrame 2 ({df2_name}): {len(df2)} records")
    print(f"Elements to compare: {elements_to_compare}")
    print(f"Name similarity threshold: {name_similarity_threshold}%")
    
    # Step 1: Fuzzy match names by book_id
    print("\n--- Step 1: Fuzzy matching names within each book_id ---")
    matched_pairs = fuzzy_match_names_by_book(
        df1, df2, 
        name_column=name_column,
        book_id_column=book_id_column,
        similarity_threshold=name_similarity_threshold
    )
    
    if matched_pairs.empty:
        return matched_pairs, pd.DataFrame(), {"error": "No name matches found"}
    
    # Step 2: Compare biographical elements for matched pairs
    print("\n--- Step 2: Comparing biographical elements for matched pairs ---")
    comparison_results = compare_biography_elements_for_matches(
        df1, df2, matched_pairs,
        json_column=json_column,
        elements_to_compare=elements_to_compare,
        distance_metric=distance_metric
    )
    
    # Step 3: Generate summary statistics
    print("\n--- Step 3: Generating summary statistics ---")
    summary = generate_comparison_summary_v2(comparison_results, df1_name, df2_name)
    
    return matched_pairs, comparison_results, summary

def generate_comparison_summary_v2(comparison_df: pd.DataFrame, 
                                  df1_name: str, df2_name: str) -> Dict[str, Any]:
    """
    Generate enhanced summary statistics for the comparison results.
    """
    if comparison_df.empty:
        return {"error": "No comparison data available"}
    
    summary = {
        'comparison_info': {
            'df1_name': df1_name,
            'df2_name': df2_name,
            'total_comparisons': len(comparison_df),
            'unique_matched_pairs': comparison_df.groupby(['name_df1', 'name_df2']).ngroups,
            'elements_compared': comparison_df['element'].nunique(),
            'books_compared': comparison_df['book_id'].nunique()
        }
    }
    
    # Overall statistics
    summary['overall_stats'] = {
        'exact_matches': comparison_df['exact_match'].sum(),
        'exact_match_rate': comparison_df['exact_match'].mean(),
        'mean_similarity': comparison_df['similarity_score'].mean(),
        'median_similarity': comparison_df['similarity_score'].median(),
        'mean_edit_distance': comparison_df['edit_distance'].mean()
    }
    
    # Per-element statistics
    element_stats = comparison_df.groupby('element').agg({
        'exact_match': ['count', 'sum', 'mean'],
        'similarity_score': ['mean', 'median', 'std'],
        'edit_distance': ['mean', 'median', 'std']
    }).round(4)
    
    element_stats.columns = ['_'.join(col).strip() for col in element_stats.columns]
    summary['per_element_stats'] = element_stats.to_dict('index')
    
    # Per-book statistics
    book_stats = comparison_df.groupby('book_id').agg({
        'exact_match': ['count', 'sum', 'mean'],
        'similarity_score': ['mean', 'median'],
        'edit_distance': ['mean', 'median']
    }).round(4)
    
    book_stats.columns = ['_'.join(col).strip() for col in book_stats.columns]
    summary['per_book_stats'] = book_stats.to_dict('index')
    
    # Name matching quality
    if 'name_similarity' in comparison_df.columns:
        summary['name_matching_stats'] = {
            'mean_name_similarity': comparison_df['name_similarity'].mean(),
            'median_name_similarity': comparison_df['name_similarity'].median(),
            'min_name_similarity': comparison_df['name_similarity'].min(),
            'max_name_similarity': comparison_df['name_similarity'].max()
        }
    
    return summary

# Convenience function for your specific pipeline comparison
def compare_ocr_pipeline_results(dolphin_csv_path: str, azureocr_csv_path: str,
                               output_path: str = None) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Compare results from Dolphin and AzureOCR pipelines.
    
    Example usage for your README pipeline:
    """
    print("Loading pipeline results...")
    
    # Load the final CSV files from both pipelines
    df_dolphin = pd.read_csv(dolphin_csv_path)
    df_azureocr = pd.read_csv(azureocr_csv_path)
    
    print(f"Loaded Dolphin results: {len(df_dolphin)} records")
    print(f"Loaded AzureOCR results: {len(df_azureocr)} records")
    
    # Perform comprehensive comparison
    matched_pairs, comparison_results, summary = comprehensive_biography_comparison(
        df_dolphin, df_azureocr,
        df1_name="Dolphin",
        df2_name="AzureOCR",
        name_column='name',
        book_id_column='book_id',
        json_column='biography_json'
    )
    
    # Save results if output path provided
    if output_path:
        import os
        os.makedirs(output_path, exist_ok=True)
        
        matched_pairs.to_csv(f"{output_path}/fuzzy_matched_pairs.csv", index=False)
        comparison_results.to_csv(f"{output_path}/detailed_comparison_results.csv", index=False)
        
        with open(f"{output_path}/comparison_summary.json", 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"Results saved to: {output_path}")
    
    return matched_pairs, comparison_results, summary


def compare_list_elements_detailed(list1, list2, similarity_threshold=90):
    """
    Compare list elements (like educations, jobs, children) with detailed sub-element analysis.
    
    Parameters:
    -----------
    list1, list2 : list
        Lists of dictionaries to compare
    similarity_threshold : float
        Minimum similarity score for considering a match (0-100)
    
    Returns:
    --------
    dict
        Detailed comparison metrics for each sub-element type
    """
    from thefuzz import fuzz
    
    if not isinstance(list1, list) or not isinstance(list2, list):
        return {
            'total_items_df1': 0,
            'total_items_df2': 0,
            'matched_items': 0,
            'match_rate': 0.0,
            'sub_element_stats': {}
        }
    
    # Convert to lists if they're strings (sometimes JSON parsing returns strings)
    if isinstance(list1, str):
        try:
            list1 = json.loads(list1) if list1.strip() else []
        except:
            list1 = []
    
    if isinstance(list2, str):
        try:
            list2 = json.loads(list2) if list2.strip() else []
        except:
            list2 = []
    
    # Get all possible sub-element keys from both lists
    all_keys = set()
    for item in list1 + list2:
        if isinstance(item, dict):
            all_keys.update(item.keys())
    
    # Initialize statistics
    stats = {
        'total_items_df1': len(list1),
        'total_items_df2': len(list2),
        'matched_items': 0,
        'match_rate': 0.0,
        'sub_element_stats': {}
    }
    
    # Initialize sub-element statistics
    for key in all_keys:
        stats['sub_element_stats'][key] = {
            'total_df1': 0,
            'total_df2': 0,
            'exact_matches': 0,
            'high_similarity_matches': 0,  # >= similarity_threshold
            'exact_match_rate': 0.0,
            'high_similarity_rate': 0.0
        }
    
    # Count non-empty values for each sub-element in each list
    for item in list1:
        if isinstance(item, dict):
            for key in all_keys:
                value = item.get(key, '')
                if value and str(value).strip():
                    stats['sub_element_stats'][key]['total_df1'] += 1
    
    for item in list2:
        if isinstance(item, dict):
            for key in all_keys:
                value = item.get(key, '')
                if value and str(value).strip():
                    stats['sub_element_stats'][key]['total_df2'] += 1
    
    # Compare items between lists using fuzzy matching
    matched_pairs = []
    
    for i, item1 in enumerate(list1):
        if not isinstance(item1, dict):
            continue
            
        best_match_idx = -1
        best_similarity = 0
        
        # Compare with each item in list2
        for j, item2 in enumerate(list2):
            if not isinstance(item2, dict):
                continue
                
            # Skip if already matched
            if j in [pair[1] for pair in matched_pairs]:
                continue
            
            # Calculate overall similarity for this item pair
            similarities = []
            for key in all_keys:
                val1 = str(item1.get(key, '')).strip().lower()
                val2 = str(item2.get(key, '')).strip().lower()
                
                if val1 or val2:  # Only compare if at least one has a value
                    if val1 == val2:
                        similarities.append(100)
                    elif val1 and val2:
                        similarities.append(fuzz.ratio(val1, val2))
                    else:
                        similarities.append(0)  # One empty, one not
            
            if similarities:
                avg_similarity = sum(similarities) / len(similarities)
                if avg_similarity > best_similarity:
                    best_similarity = avg_similarity
                    best_match_idx = j
        
        # If we found a good match, record the pair and analyze sub-elements
        if best_match_idx >= 0 and best_similarity >= similarity_threshold:
            matched_pairs.append((i, best_match_idx))
            item2 = list2[best_match_idx]
            
            # Analyze sub-elements for this matched pair
            for key in all_keys:
                val1 = str(item1.get(key, '')).strip()
                val2 = str(item2.get(key, '')).strip()
                
                if val1 and val2:  # Both have values
                    if val1.lower() == val2.lower():
                        stats['sub_element_stats'][key]['exact_matches'] += 1
                        stats['sub_element_stats'][key]['high_similarity_matches'] += 1
                    else:
                        similarity = fuzz.ratio(val1.lower(), val2.lower())
                        if similarity >= similarity_threshold:
                            stats['sub_element_stats'][key]['high_similarity_matches'] += 1
    
    # Calculate final rates
    stats['matched_items'] = len(matched_pairs)
    if max(len(list1), len(list2)) > 0:
        stats['match_rate'] = len(matched_pairs) / max(len(list1), len(list2))
    
    for key in all_keys:
        key_stats = stats['sub_element_stats'][key]
        total_possible = max(key_stats['total_df1'], key_stats['total_df2'])
        
        if total_possible > 0:
            key_stats['exact_match_rate'] = key_stats['exact_matches'] / total_possible
            key_stats['high_similarity_rate'] = key_stats['high_similarity_matches'] / total_possible
    
    return stats

def compare_biography_elements_for_matches_detailed(df1: pd.DataFrame, df2: pd.DataFrame, 
                                                  matched_pairs: pd.DataFrame,
                                                  json_column: str, 
                                                  elements_to_compare: List[str],
                                                  distance_metric: str = 'levenshtein',
                                                  similarity_threshold: float = 90.0) -> pd.DataFrame:
    """
    Enhanced version that provides detailed analysis for complex elements like educations, jobs, children.
    """
    def safe_json_parse(json_str):
        """Safely parse JSON string"""
        if pd.isna(json_str) or json_str == '':
            return {}
        try:
            if isinstance(json_str, str):
                return json.loads(json_str)
            elif isinstance(json_str, dict):
                return json_str
            else:
                return {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def extract_element(json_obj, key):
        """Extract element from JSON object"""
        if not isinstance(json_obj, dict):
            return None
        return json_obj.get(key, None)
    
    def normalize_for_comparison(value):
        """Normalize values for comparison"""
        if value is None:
            return ""
        elif isinstance(value, str):
            return value.strip().lower()
        elif isinstance(value, list):
            return str(sorted([str(item).strip().lower() for item in value]))
        elif isinstance(value, dict):
            return str(sorted([(k, str(v).strip().lower()) for k, v in value.items()]))
        else:
            return str(value).strip().lower()
    
    def calculate_distance(val1, val2, metric):
        """Calculate distance between two values"""
        if val1 == val2:
            return 0.0
        
        if val1 == "" and val2 == "":
            return 0.0
        
        if val1 == "" or val2 == "":
            return 1.0
        
        if metric == 'levenshtein':
            max_len = max(len(val1), len(val2))
            if max_len == 0:
                return 0.0
            return levenshtein_distance(val1, val2) / max_len
        
        elif metric == 'sequence_matcher':
            return 1 - SequenceMatcher(None, val1, val2).ratio()
        
        elif metric == 'jaccard':
            set1 = set(val1.split())
            set2 = set(val2.split())
            union = set1.union(set2)
            intersection = set1.intersection(set2)
            if len(union) == 0:
                return 0.0
            return 1 - (len(intersection) / len(union))
        
        else:
            raise ValueError(f"Unknown distance metric: {metric}")
    
    comparison_results = []
    
    # Define which elements are complex (lists) and need detailed analysis
    complex_elements = ['educations', 'jobs', 'children', 'spouses', 'stays_abroad']
    
    print(f"Comparing {len(elements_to_compare)} elements for {len(matched_pairs)} matched pairs...")
    print(f"Using similarity threshold of {similarity_threshold}% for detailed analysis")
    
    for _, match_row in matched_pairs.iterrows():
        idx1 = match_row['idx_df1']
        idx2 = match_row['idx_df2']
        
        # Get the JSON data for both matched records
        json_data1 = safe_json_parse(df1.loc[idx1, json_column])
        json_data2 = safe_json_parse(df2.loc[idx2, json_column])
        
        # Compare each element
        for element in elements_to_compare:
            val1 = extract_element(json_data1, element)
            val2 = extract_element(json_data2, element)
            
            norm_val1 = normalize_for_comparison(val1)
            norm_val2 = normalize_for_comparison(val2)
            
            distance = calculate_distance(norm_val1, norm_val2, distance_metric)
            similarity = 1 - distance
            exact_match = norm_val1 == norm_val2
            
            # Base comparison result
            result = {
                'book_id': match_row['book_id'],
                'name_df1': match_row['name_df1'],
                'name_df2': match_row['name_df2'],
                'name_similarity': match_row['name_similarity'],
                'element': element,
                f'{element}_df1': val1,
                f'{element}_df2': val2,
                'edit_distance': distance,
                'similarity_score': similarity,
                'exact_match': exact_match,
                'distance_metric': distance_metric
            }
            
            # Add detailed analysis for complex elements
            if element in complex_elements and (val1 is not None or val2 is not None):
                detailed_stats = compare_list_elements_detailed(
                    val1 if val1 is not None else [],
                    val2 if val2 is not None else [],
                    similarity_threshold
                )
                
                # Add detailed statistics to the result
                result.update({
                    f'{element}_total_items_df1': detailed_stats['total_items_df1'],
                    f'{element}_total_items_df2': detailed_stats['total_items_df2'],
                    f'{element}_matched_items': detailed_stats['matched_items'],
                    f'{element}_match_rate': detailed_stats['match_rate']
                })
                
                # Add sub-element statistics
                for sub_key, sub_stats in detailed_stats['sub_element_stats'].items():
                    result.update({
                        f'{element}_{sub_key}_total_df1': sub_stats['total_df1'],
                        f'{element}_{sub_key}_total_df2': sub_stats['total_df2'],
                        f'{element}_{sub_key}_exact_matches': sub_stats['exact_matches'],
                        f'{element}_{sub_key}_high_sim_matches': sub_stats['high_similarity_matches'],
                        f'{element}_{sub_key}_exact_rate': sub_stats['exact_match_rate'],
                        f'{element}_{sub_key}_high_sim_rate': sub_stats['high_similarity_rate']
                    })
            
            comparison_results.append(result)
    
    result_df = pd.DataFrame(comparison_results)
    return result_df

def generate_detailed_summary(comparison_df: pd.DataFrame, 
                            df1_name: str, df2_name: str,
                            similarity_threshold: float = 90.0) -> Dict[str, Any]:
    """
    Generate enhanced summary with detailed statistics for complex elements.
    """
    if comparison_df.empty:
        return {"error": "No comparison data available"}
    
    summary = {
        'comparison_info': {
            'df1_name': df1_name,
            'df2_name': df2_name,
            'similarity_threshold': similarity_threshold,
            'total_comparisons': len(comparison_df),
            'unique_matched_pairs': comparison_df.groupby(['name_df1', 'name_df2']).ngroups,
            'elements_compared': comparison_df['element'].nunique(),
            'books_compared': comparison_df['book_id'].nunique()
        }
    }
    
    # Overall statistics
    summary['overall_stats'] = {
        'exact_matches': comparison_df['exact_match'].sum(),
        'exact_match_rate': comparison_df['exact_match'].mean(),
        'mean_similarity': comparison_df['similarity_score'].mean(),
        'median_similarity': comparison_df['similarity_score'].median(),
        'mean_edit_distance': comparison_df['edit_distance'].mean()
    }
    
    # Standard per-element statistics
    element_stats = comparison_df.groupby('element').agg({
        'exact_match': ['count', 'sum', 'mean'],
        'similarity_score': ['mean', 'median', 'std'],
        'edit_distance': ['mean', 'median', 'std']
    }).round(4)
    
    element_stats.columns = ['_'.join(col).strip() for col in element_stats.columns]
    summary['per_element_stats'] = element_stats.to_dict('index')
    
    # Detailed statistics for complex elements
    complex_elements = ['educations', 'jobs', 'children', 'spouses', 'stays_abroad']
    summary['detailed_complex_element_stats'] = {}
    
    for element in complex_elements:
        if element in comparison_df['element'].values:
            element_data = comparison_df[comparison_df['element'] == element]
            
            # Find all sub-element types for this element
            sub_elements = set()
            for col in element_data.columns:
                if col.startswith(f'{element}_') and col.endswith('_exact_rate'):
                    sub_element = col.replace(f'{element}_', '').replace('_exact_rate', '')
                    sub_elements.add(sub_element)
            
            element_summary = {
                'total_comparisons': len(element_data),
                'avg_matched_items_rate': element_data[f'{element}_match_rate'].mean() if f'{element}_match_rate' in element_data.columns else 0,
                'sub_elements': {}
            }
            
            # Aggregate statistics for each sub-element
            for sub_element in sub_elements:
                exact_rate_col = f'{element}_{sub_element}_exact_rate'
                high_sim_rate_col = f'{element}_{sub_element}_high_sim_rate'
                total_df1_col = f'{element}_{sub_element}_total_df1'
                total_df2_col = f'{element}_{sub_element}_total_df2'
                
                if exact_rate_col in element_data.columns:
                    element_summary['sub_elements'][sub_element] = {
                        'avg_exact_match_rate': element_data[exact_rate_col].mean(),
                        'avg_high_similarity_rate': element_data[high_sim_rate_col].mean() if high_sim_rate_col in element_data.columns else 0,
                        'total_instances_df1': element_data[total_df1_col].sum() if total_df1_col in element_data.columns else 0,
                        'total_instances_df2': element_data[total_df2_col].sum() if total_df2_col in element_data.columns else 0
                    }
            
            summary['detailed_complex_element_stats'][element] = element_summary
    
    # Name matching quality
    if 'name_similarity' in comparison_df.columns:
        summary['name_matching_stats'] = {
            'mean_name_similarity': comparison_df['name_similarity'].mean(),
            'median_name_similarity': comparison_df['name_similarity'].median(),
            'min_name_similarity': comparison_df['name_similarity'].min(),
            'max_name_similarity': comparison_df['name_similarity'].max()
        }
    
    return summary

# Update the main comparison function to use the detailed version
def comprehensive_biography_comparison_detailed(df1: pd.DataFrame, df2: pd.DataFrame,
                                               df1_name: str = "DataFrame1",
                                               df2_name: str = "DataFrame2",
                                               name_column: str = 'name',
                                               book_id_column: str = 'book_id',
                                               json_column: str = 'biography_json',
                                               elements_to_compare: List[str] = None,
                                               name_similarity_threshold: float = 80.0,
                                               element_similarity_threshold: float = 90.0,
                                               distance_metric: str = 'levenshtein') -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Enhanced comprehensive comparison with detailed analysis for complex elements.
    """
    
    if elements_to_compare is None:
        elements_to_compare = [
            'father_name', 'mother_name', 'birth_date', 'birth_place',
            'death_date', 'educations', 'jobs', 'spouses', 'children'
        ]
    
    print(f"=== Detailed Biography Comparison: {df1_name} vs {df2_name} ===")
    print(f"DataFrame 1 ({df1_name}): {len(df1)} records")
    print(f"DataFrame 2 ({df2_name}): {len(df2)} records")
    print(f"Elements to compare: {elements_to_compare}")
    print(f"Name similarity threshold: {name_similarity_threshold}%")
    print(f"Element similarity threshold: {element_similarity_threshold}%")
    
    # Step 1: Fuzzy match names by book_id
    print("\n--- Step 1: Fuzzy matching names within each book_id ---")
    matched_pairs = fuzzy_match_names_by_book(
        df1, df2, 
        name_column=name_column,
        book_id_column=book_id_column,
        similarity_threshold=name_similarity_threshold
    )
    
    if matched_pairs.empty:
        return matched_pairs, pd.DataFrame(), {"error": "No name matches found"}
    
    # Step 2: Compare biographical elements with detailed analysis
    print("\n--- Step 2: Detailed comparison of biographical elements ---")
    comparison_results = compare_biography_elements_for_matches_detailed(
        df1, df2, matched_pairs,
        json_column=json_column,
        elements_to_compare=elements_to_compare,
        distance_metric=distance_metric,
        similarity_threshold=element_similarity_threshold
    )
    
    # Step 3: Generate detailed summary statistics
    print("\n--- Step 3: Generating detailed summary statistics ---")
    summary = generate_detailed_summary(comparison_results, df1_name, df2_name, element_similarity_threshold)
    
    return matched_pairs, comparison_results, summary

# Update the convenience function
def compare_ocr_pipeline_results_detailed(dolphin_csv_path: str, azureocr_csv_path: str,
                                        output_path: str = None,
                                        similarity_threshold: float = 90.0) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Enhanced pipeline comparison with detailed analysis of complex elements.
    """
    print("Loading pipeline results...")
    
    # Load the final CSV files from both pipelines
    df_dolphin = pd.read_csv(dolphin_csv_path)
    df_azureocr = pd.read_csv(azureocr_csv_path)
    
    print(f"Loaded Dolphin results: {len(df_dolphin)} records")
    print(f"Loaded AzureOCR results: {len(df_azureocr)} records")
    
    # Perform detailed comprehensive comparison
    matched_pairs, comparison_results, summary = comprehensive_biography_comparison_detailed(
        df_dolphin, df_azureocr,
        df1_name="Dolphin",
        df2_name="AzureOCR",
        name_column='name',
        book_id_column='book_id',
        json_column='biography_json',
        element_similarity_threshold=similarity_threshold
    )
    
    # Save results if output path provided
    if output_path:
        import os
        os.makedirs(output_path, exist_ok=True)
        
        matched_pairs.to_csv(f"{output_path}/fuzzy_matched_pairs.csv", index=False)
        comparison_results.to_csv(f"{output_path}/detailed_comparison_results.csv", index=False)
        
        with open(f"{output_path}/detailed_comparison_summary.json", 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"Results saved to: {output_path}")
    
    return matched_pairs, comparison_results, summary

// ...existing code...

def find_exact_matches_by_name_and_book(df1: pd.DataFrame, df2: pd.DataFrame,
                                       name_column: str = 'name',
                                       book_id_column: str = 'book_id') -> pd.DataFrame:
    """
    Find exact matches between dataframes based on name and book_id.
    
    Parameters:
    -----------
    df1, df2 : pd.DataFrame
        DataFrames to match
    name_column : str
        Column containing names to match
    book_id_column : str
        Column containing book IDs to match
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with exactly matched pairs
    """
    print("Finding exact matches based on name and book_id...")
    
    # Create composite keys for matching
    df1_copy = df1.copy()
    df2_copy = df2.copy()
    
    df1_copy['match_key'] = df1_copy[name_column].astype(str) + "___" + df1_copy[book_id_column].astype(str)
    df2_copy['match_key'] = df2_copy[name_column].astype(str) + "___" + df2_copy[book_id_column].astype(str)
    
    # Find common match keys
    common_keys = set(df1_copy['match_key']) & set(df2_copy['match_key'])
    
    if not common_keys:
        print("No exact matches found between the dataframes")
        return pd.DataFrame()
    
    print(f"Found {len(common_keys)} exact matches")
    
    # Create matched pairs
    matched_pairs = []
    
    for match_key in common_keys:
        # Get indices for this match key
        df1_matches = df1_copy[df1_copy['match_key'] == match_key]
        df2_matches = df2_copy[df2_copy['match_key'] == match_key]
        
        # Handle multiple matches for the same key (shouldn't happen with good data, but just in case)
        for _, row1 in df1_matches.iterrows():
            for _, row2 in df2_matches.iterrows():
                matched_pairs.append({
                    'book_id': row1[book_id_column],
                    'name_df1': row1[name_column],
                    'name_df2': row2[name_column],
                    'name_similarity': 100.0,  # Exact match
                    'idx_df1': row1.name,  # Original index
                    'idx_df2': row2.name   # Original index
                })
                break  # Take only the first match to avoid duplicates
    
    matched_df = pd.DataFrame(matched_pairs)
    
    # Group by book_id for summary
    books_with_matches = matched_df['book_id'].nunique()
    print(f"Matches found across {books_with_matches} different books")
    
    # Show breakdown by book
    book_counts = matched_df['book_id'].value_counts().head(10)
    print("Top books by number of matches:")
    for book_id, count in book_counts.items():
        print(f"  {book_id}: {count} matches")
    
    return matched_df

def compare_biography_elements_exact_matches(df1: pd.DataFrame, df2: pd.DataFrame, 
                                           matched_pairs: pd.DataFrame,
                                           json_column: str, 
                                           elements_to_compare: List[str],
                                           distance_metric: str = 'levenshtein') -> pd.DataFrame:
    """
    Compare biographical elements only for exactly matched name+book_id pairs.
    
    This ensures we're comparing the same person's data from both sources.
    """
    def safe_json_parse(json_str):
        """Safely parse JSON string"""
        if pd.isna(json_str) or json_str == '':
            return {}
        try:
            if isinstance(json_str, str):
                return json.loads(json_str)
            elif isinstance(json_str, dict):
                return json_str
            else:
                return {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def extract_element(json_obj, key):
        """Extract element from JSON object"""
        if not isinstance(json_obj, dict):
            return None
        return json_obj.get(key, None)
    
    def normalize_for_comparison(value):
        """Normalize values for comparison"""
        if value is None:
            return ""
        elif isinstance(value, str):
            return value.strip().lower()
        elif isinstance(value, list):
            return str(sorted([str(item).strip().lower() for item in value]))
        elif isinstance(value, dict):
            return str(sorted([(k, str(v).strip().lower()) for k, v in value.items()]))
        else:
            return str(value).strip().lower()
    
    def calculate_distance(val1, val2, metric):
        """Calculate distance between two values"""
        if val1 == val2:
            return 0.0
        
        if val1 == "" and val2 == "":
            return 0.0
        
        if val1 == "" or val2 == "":
            return 1.0
        
        if metric == 'levenshtein':
            max_len = max(len(val1), len(val2))
            if max_len == 0:
                return 0.0
            return levenshtein_distance(val1, val2) / max_len
        
        elif metric == 'sequence_matcher':
            return 1 - SequenceMatcher(None, val1, val2).ratio()
        
        elif metric == 'jaccard':
            set1 = set(val1.split())
            set2 = set(val2.split())
            union = set1.union(set2)
            intersection = set1.intersection(set2)
            if len(union) == 0:
                return 0.0
            return 1 - (len(intersection) / len(union))
        
        else:
            raise ValueError(f"Unknown distance metric: {metric}")
    
    comparison_results = []
    
    print(f"Comparing {len(elements_to_compare)} elements for {len(matched_pairs)} exactly matched pairs...")
    print("Note: Only comparing records with identical name+book_id combinations")
    
    for _, match_row in matched_pairs.iterrows():
        idx1 = match_row['idx_df1']
        idx2 = match_row['idx_df2']
        
        # Verify we can find these indices in the original dataframes
        if idx1 not in df1.index or idx2 not in df2.index:
            print(f"Warning: Could not find indices {idx1}, {idx2} in dataframes")
            continue
        
        # Get the JSON data for both matched records
        json_data1 = safe_json_parse(df1.loc[idx1, json_column])
        json_data2 = safe_json_parse(df2.loc[idx2, json_column])
        
        # Compare each element
        for element in elements_to_compare:
            val1 = extract_element(json_data1, element)
            val2 = extract_element(json_data2, element)
            
            norm_val1 = normalize_for_comparison(val1)
            norm_val2 = normalize_for_comparison(val2)
            
            distance = calculate_distance(norm_val1, norm_val2, distance_metric)
            similarity = 1 - distance
            exact_match = norm_val1 == norm_val2
            
            comparison_results.append({
                'book_id': match_row['book_id'],
                'name': match_row['name_df1'],  # Same for both since exact match
                'element': element,
                f'{element}_df1': val1,
                f'{element}_df2': val2,
                'edit_distance': distance,
                'similarity_score': similarity,
                'exact_match': exact_match,
                'distance_metric': distance_metric
            })
    
    result_df = pd.DataFrame(comparison_results)
    
    if not result_df.empty:
        print(f"Successfully compared {len(result_df)} element pairs across {len(matched_pairs)} matched records")
    
    return result_df

def comprehensive_biography_comparison_exact_matches(df1: pd.DataFrame, df2: pd.DataFrame,
                                                   df1_name: str = "DataFrame1",
                                                   df2_name: str = "DataFrame2",
                                                   name_column: str = 'name',
                                                   book_id_column: str = 'book_id',
                                                   json_column: str = 'biography_json',
                                                   elements_to_compare: List[str] = None,
                                                   distance_metric: str = 'levenshtein') -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Comprehensive comparison of biographical data between two dataframes.
    
    RESTRICTED TO EXACT MATCHES: Only compares records that have identical 
    name+book_id combinations in both dataframes.
    
    Parameters:
    -----------
    df1, df2 : pd.DataFrame
        DataFrames to compare (e.g., Dolphin vs AzureOCR results)
    df1_name, df2_name : str
        Names for the dataframes (for reporting)
    elements_to_compare : List[str]
        Biographical elements to compare
    
    Returns:
    --------
    Tuple[pd.DataFrame, pd.DataFrame, Dict]
        - matched_pairs: DataFrame with exactly matched name+book_id pairs
        - comparison_results: Detailed element comparison results  
        - summary: Summary statistics
    """
    
    if elements_to_compare is None:
        elements_to_compare = [
            'father_name', 'mother_name', 'birth_date', 'birth_place',
            'death_date', 'educations', 'jobs', 'spouses', 'children'
        ]
    
    print(f"=== Exact Match Biography Comparison: {df1_name} vs {df2_name} ===")
    print(f"DataFrame 1 ({df1_name}): {len(df1)} records")
    print(f"DataFrame 2 ({df2_name}): {len(df2)} records")
    print(f"Elements to compare: {elements_to_compare}")
    print("RESTRICTION: Only comparing records with identical name+book_id in both dataframes")
    
    # Step 1: Find exact matches by name and book_id
    print("\n--- Step 1: Finding exact matches by name+book_id ---")
    matched_pairs = find_exact_matches_by_name_and_book(
        df1, df2, 
        name_column=name_column,
        book_id_column=book_id_column
    )
    
    if matched_pairs.empty:
        return matched_pairs, pd.DataFrame(), {"error": "No exact name+book_id matches found"}
    
    # Step 2: Compare biographical elements for exactly matched pairs
    print("\n--- Step 2: Comparing biographical elements for exactly matched pairs ---")
    comparison_results = compare_biography_elements_exact_matches(
        df1, df2, matched_pairs,
        json_column=json_column,
        elements_to_compare=elements_to_compare,
        distance_metric=distance_metric
    )
    
    # Step 3: Generate summary statistics
    print("\n--- Step 3: Generating summary statistics ---")
    summary = generate_exact_match_summary(comparison_results, df1_name, df2_name, len(df1), len(df2))
    
    return matched_pairs, comparison_results, summary

def generate_exact_match_summary(comparison_df: pd.DataFrame, 
                                df1_name: str, df2_name: str,
                                total_df1_records: int, total_df2_records: int) -> Dict[str, Any]:
    """
    Generate summary statistics for exact match comparison results.
    """
    if comparison_df.empty:
        return {"error": "No comparison data available"}
    
    unique_matched_pairs = comparison_df['name'].nunique() if 'name' in comparison_df.columns else 0
    
    summary = {
        'comparison_info': {
            'df1_name': df1_name,
            'df2_name': df2_name,
            'total_df1_records': total_df1_records,
            'total_df2_records': total_df2_records,
            'matched_records': unique_matched_pairs,
            'match_rate_df1': unique_matched_pairs / total_df1_records if total_df1_records > 0 else 0,
            'match_rate_df2': unique_matched_pairs / total_df2_records if total_df2_records > 0 else 0,
            'total_element_comparisons': len(comparison_df),
            'elements_compared': comparison_df['element'].nunique(),
            'books_compared': comparison_df['book_id'].nunique(),
            'restriction': 'exact_name_and_book_id_matches_only'
        }
    }
    
    # Overall statistics
    summary['overall_stats'] = {
        'exact_matches': comparison_df['exact_match'].sum(),
        'exact_match_rate': comparison_df['exact_match'].mean(),
        'mean_similarity': comparison_df['similarity_score'].mean(),
        'median_similarity': comparison_df['similarity_score'].median(),
        'mean_edit_distance': comparison_df['edit_distance'].mean(),
        'std_similarity': comparison_df['similarity_score'].std()
    }
    
    # Per-element statistics
    element_stats = comparison_df.groupby('element').agg({
        'exact_match': ['count', 'sum', 'mean'],
        'similarity_score': ['mean', 'median', 'std'],
        'edit_distance': ['mean', 'median', 'std']
    }).round(4)
    
    element_stats.columns = ['_'.join(col).strip() for col in element_stats.columns]
    summary['per_element_stats'] = element_stats.to_dict('index')
    
    # Per-book statistics
    if comparison_df['book_id'].nunique() > 1:
        book_stats = comparison_df.groupby('book_id').agg({
            'exact_match': ['count', 'sum', 'mean'],
            'similarity_score': ['mean', 'median'],
            'edit_distance': ['mean', 'median']
        }).round(4)
        
        book_stats.columns = ['_'.join(col).strip() for col in book_stats.columns]
        summary['per_book_stats'] = book_stats.to_dict('index')
    
    # Quality assessment
    high_similarity_threshold = 0.9
    medium_similarity_threshold = 0.7
    
    high_quality = (comparison_df['similarity_score'] >= high_similarity_threshold).sum()
    medium_quality = ((comparison_df['similarity_score'] >= medium_similarity_threshold) & 
                     (comparison_df['similarity_score'] < high_similarity_threshold)).sum()
    low_quality = (comparison_df['similarity_score'] < medium_similarity_threshold).sum()
    
    summary['quality_distribution'] = {
        'high_similarity_90_plus': {
            'count': high_quality,
            'percentage': high_quality / len(comparison_df) if len(comparison_df) > 0 else 0
        },
        'medium_similarity_70_to_90': {
            'count': medium_quality,
            'percentage': medium_quality / len(comparison_df) if len(comparison_df) > 0 else 0
        },
        'low_similarity_below_70': {
            'count': low_quality,
            'percentage': low_quality / len(comparison_df) if len(comparison_df) > 0 else 0
        }
    }
    
    return summary

# Updated convenience function for exact matches only
def compare_ocr_pipeline_results_exact_matches(dolphin_csv_path: str, azureocr_csv_path: str,
                                             output_path: str = None) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Compare results from Dolphin and AzureOCR pipelines.
    
    RESTRICTED TO EXACT MATCHES: Only compares records that appear in both datasets
    with identical name+book_id combinations.
    """
    print("Loading pipeline results for exact match comparison...")
    
    # Load the final CSV files from both pipelines
    df_dolphin = pd.read_csv(dolphin_csv_path)
    df_azureocr = pd.read_csv(azureocr_csv_path)
    
    print(f"Loaded Dolphin results: {len(df_dolphin)} records")
    print(f"Loaded AzureOCR results: {len(df_azureocr)} records")
    
    # Perform exact match comparison
    matched_pairs, comparison_results, summary = comprehensive_biography_comparison_exact_matches(
        df_dolphin, df_azureocr,
        df1_name="Dolphin",
        df2_name="AzureOCR",
        name_column='name',
        book_id_column='book_id',
        json_column='biography_json'
    )
    
    # Save results if output path provided
    if output_path:
        import os
        os.makedirs(output_path, exist_ok=True)
        
        matched_pairs.to_csv(f"{output_path}/exact_matched_pairs.csv", index=False)
        comparison_results.to_csv(f"{output_path}/exact_match_comparison_results.csv", index=False)
        
        with open(f"{output_path}/exact_match_comparison_summary.json", 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"Results saved to: {output_path}")
    
    return matched_pairs, comparison_results, summary

# Example usage for exact matches:
"""
# Compare your pipeline results - EXACT MATCHES ONLY
matched_pairs, comparison_results, summary = compare_ocr_pipeline_results_exact_matches(
    dolphin_csv_path="D:/data/HCNC/norway/biographies/storage/Dolphin/output/final.csv",
    azureocr_csv_path="D:/data/HCNC/norway/biographies/storage/AzureOCR/output_csv/final.csv",
    output_path="D:/data/HCNC/norway/biographies/storage/exact_match_comparison_results"
)

# Print summary
print("=== EXACT MATCH COMPARISON SUMMARY ===")
print(f"Total records - Dolphin: {summary['comparison_info']['total_df1_records']}")
print(f"Total records - AzureOCR: {summary['comparison_info']['total_df2_records']}")
print(f"Exact matches found: {summary['comparison_info']['matched_records']}")
print(f"Match rate (Dolphin): {summary['comparison_info']['match_rate_df1']:.1%}")
print(f"Match rate (AzureOCR): {summary['comparison_info']['match_rate_df2']:.1%}")
print(f"Overall exact match rate: {summary['overall_stats']['exact_match_rate']:.1%}")
print(f"Mean similarity score: {summary['overall_stats']['mean_similarity']:.3f}")

# Show per-element performance
print("\n=== PER-ELEMENT PERFORMANCE (EXACT MATCHES ONLY) ===")
for element, stats in summary['per_element_stats'].items():
    print(f"{element}: {stats['exact_match_mean']:.1%} exact matches, {stats['similarity_score_mean']:.3f} avg similarity")

# Show quality distribution
print("\n=== QUALITY DISTRIBUTION ===")
print(f"High similarity (≥90%): {summary['quality_distribution']['high_similarity_90_plus']['percentage']:.1%}")
print(f"Medium similarity (70-90%): {summary['quality_distribution']['medium_similarity_70_to_90']['percentage']:.1%}")
print(f"Low similarity (<70%): {summary['quality_distribution']['low_similarity_below_70']['percentage']:.1%}")
"""

# Example usage for detailed analysis:
"""
# Compare your pipeline results with detailed analysis
matched_pairs, comparison_results, summary = compare_ocr_pipeline_results_detailed(
    dolphin_csv_path=r"d:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007\output\extracted_all_names_portraits_biographies_final.csv",
    azureocr_csv_path=r"d:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_with_chunks_checkpoint_440.csv",
    output_path="D:/data/HCNC/norway/biographies/storage/comparison_results,
    similarity_threshold=90.0
)

# Print detailed summary for educations
if 'educations' in summary['detailed_complex_element_stats']:
    edu_stats = summary['detailed_complex_element_stats']['educations']
    print(f"\n=== EDUCATION ANALYSIS ===")
    print(f"Average item match rate: {edu_stats['avg_matched_items_rate']:.1%}")
    
    for sub_element, stats in edu_stats['sub_elements'].items():
        print(f"{sub_element}:")
        print(f"  Exact matches: {stats['avg_exact_match_rate']:.1%}")
        print(f"  High similarity (≥90%): {stats['avg_high_similarity_rate']:.1%}")
        print(f"  Total instances - Dolphin: {stats['total_instances_df1']}, AzureOCR: {stats['total_instances_df2']}")
"""
# Example usage:

matched_pairs, comparison_results, summary = compare_ocr_pipeline_results_exact_matches(
    dolphin_csv_path=r"d:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007\output\extracted_all_names_portraits_biographies_final.csv",
    azureocr_csv_path=r"d:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_with_chunks_checkpoint_600.csv",output_path=r"D:/data/HCNC/norway/biographies/storage/comparison_results"
)

if 'educations' in summary['detailed_complex_element_stats']:
    edu_stats = summary['detailed_complex_element_stats']['educations']
    print(f"\n=== EDUCATION ANALYSIS ===")
    print(f"Average item match rate: {edu_stats['avg_matched_items_rate']:.1%}")
    
    for sub_element, stats in edu_stats['sub_elements'].items():
        print(f"{sub_element}:")
        print(f"  Exact matches: {stats['avg_exact_match_rate']:.1%}")
        print(f"  High similarity (≥90%): {stats['avg_high_similarity_rate']:.1%}")
        print(f"  Total instances - Dolphin: {stats['total_instances_df1']}, AzureOCR: {stats['total_instances_df2']}")


# Compare your pipeline results
matched_pairs, comparison_results, summary = compare_ocr_pipeline_results(
    dolphin_csv_path=r"d:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007\output\extracted_all_names_portraits_biographies_final.csv",
    azureocr_csv_path=r"d:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_with_chunks_checkpoint_440.csv",
    output_path="D:/data/HCNC/norway/biographies/storage/comparison_results"
)

# Print summary
print("=== COMPARISON SUMMARY ===")
print(f"Total matched pairs: {summary['comparison_info']['unique_matched_pairs']}")
print(f"Overall exact match rate: {summary['overall_stats']['exact_match_rate']:.1%}")
print(f"Mean similarity score: {summary['overall_stats']['mean_similarity']:.3f}")

# Show per-element performance
print("\n=== PER-ELEMENT PERFORMANCE ===")
for element, stats in summary['per_element_stats'].items():
    print(f"{element}: {stats['exact_match_mean']:.1%} exact matches, {stats['similarity_score_mean']:.3f} avg similarity")
"""

