"""
Standalone Job Title Overlap Analysis Tool

This script provides functions to analyze the overlap of job titles between 
Azure and MonkeyOCR using fuzzy matching. It can be used independently of 
the main comprehensive_json_extraction.py script.
"""

import pandas as pd
import json
from thefuzz import fuzz, process
import numpy as np
from typing import List, Dict, Any, Optional

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

def analyze_job_title_overlap_from_csv(csv_file: str,
                                       azure_job_cols: Optional[List[str]] = None,
                                       monkey_job_cols: Optional[List[str]] = None,
                                       fuzzy_threshold: int = 80,
                                       missing_value: str = 'Missing',
                                       save_results: bool = True) -> Dict[str, Any]:
    """
    Analyze job title overlap from a CSV file.
    
    Parameters:
    -----------
    csv_file : str
        Path to the CSV file containing the comparison dataframe
    azure_job_cols : List[str], optional
        List of Azure job title columns. If None, auto-detect from column names
    monkey_job_cols : List[str], optional
        List of Monkey job title columns. If None, auto-detect from column names
    fuzzy_threshold : int
        Minimum fuzzy matching score for considering titles as matching (default: 80)
    missing_value : str
        Value representing missing data (default: 'Missing')
    save_results : bool
        Whether to save results to CSV files (default: True)
    
    Returns:
    --------
    Dict[str, Any]
        Dictionary containing overlap metrics and detailed results
    """
    
    print(f"Loading data from: {csv_file}")
    df = pd.read_csv(csv_file)
    
    print(f"DataFrame shape: {df.shape}")
    print(f"DataFrame columns: {df.columns.tolist()}")
    
    # Perform job title overlap analysis
    results = compute_job_title_overlap(
        df, azure_job_cols, monkey_job_cols, fuzzy_threshold, missing_value
    )
    
    if save_results and 'error' not in results:
        # Save matched pairs
        if results['matched_pairs_details']:
            matched_pairs_df = pd.DataFrame(results['matched_pairs_details'])
            matched_pairs_df.to_csv('job_title_matched_pairs.csv', index=False)
            print(f"\nSaved matched job title pairs to: job_title_matched_pairs.csv")
        
        # Save unmatched titles with name and book_id information
        if results['unmatched_azure_titles'] or results['unmatched_monkey_titles']:
            unmatched_data = []
            
            # Add unmatched Azure titles with record details
            for title in results['unmatched_azure_titles']:
                # Find all records with this Azure job title
                azure_job_cols = [col for col in df.columns if 'job' in col.lower() and 'title' in col.lower() and col.endswith('_azure')]
                for col in azure_job_cols:
                    if col in df.columns:
                        matching_rows = df[df[col] == title]
                        for _, row in matching_rows.iterrows():
                            unmatched_data.append({
                                'title': title,
                                'source': 'Azure',
                                'matched': False,
                                'book_id': row.get('book_id', 'N/A'),
                                'name_azure': row.get('name_azure', 'N/A'),
                                'name_monkey': row.get('name_monkey', 'N/A'),
                                'job_column': col
                            })
            
            # Add unmatched Monkey titles with record details
            for title in results['unmatched_monkey_titles']:
                # Find all records with this Monkey job title
                monkey_job_cols = [col for col in df.columns if 'job' in col.lower() and 'title' in col.lower() and col.endswith('_monkey')]
                for col in monkey_job_cols:
                    if col in df.columns:
                        matching_rows = df[df[col] == title]
                        for _, row in matching_rows.iterrows():
                            unmatched_data.append({
                                'title': title,
                                'source': 'Monkey',
                                'matched': False,
                                'book_id': row.get('book_id', 'N/A'),
                                'name_azure': row.get('name_azure', 'N/A'),
                                'name_monkey': row.get('name_monkey', 'N/A'),
                                'job_column': col
                            })
            
            if unmatched_data:
                unmatched_df = pd.DataFrame(unmatched_data)
                unmatched_df.to_csv('job_title_unmatched.csv', index=False)
                print(f"Saved unmatched job titles to: job_title_unmatched.csv")
        
        # Save summary statistics
        overlap_summary = {
            'total_azure_titles': results['total_azure_titles'],
            'total_monkey_titles': results['total_monkey_titles'],
            'matched_pairs': results['matched_pairs'],
            'unmatched_azure': results['unmatched_azure'],
            'unmatched_monkey': results['unmatched_monkey'],
            'azure_coverage_percent': results['azure_coverage_percent'],
            'monkey_coverage_percent': results['monkey_coverage_percent'],
            'jaccard_similarity': results['jaccard_similarity'],
            'overlap_coefficient': results['overlap_coefficient'],
            'dice_coefficient': results['dice_coefficient'],
            'fuzzy_threshold': results['fuzzy_threshold']
        }
        
        # Add similarity statistics if available
        if results['similarity_statistics']:
            stats = results['similarity_statistics']
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
    
    return results

def main():
    """
    Main function to demonstrate job title overlap analysis.
    
    This function can be modified to analyze your specific CSV file.
    """
    
    # Example usage with the comprehensive comparison dataframe
    csv_file = 'comprehensive_comparison_dataframe.csv'
    
    print("JOB TITLE OVERLAP ANALYSIS TOOL")
    print("="*50)
    
    try:
        # Analyze job title overlap
        results = analyze_job_title_overlap_from_csv(
            csv_file,
            fuzzy_threshold=80,
            missing_value='Missing',
            save_results=True
        )
        
        if 'error' not in results:
            print("\nAnalysis completed successfully!")
            print(f"Check the following output files:")
            print("- job_title_matched_pairs.csv")
            print("- job_title_unmatched.csv")
            print("- job_title_overlap_summary.csv")
        else:
            print(f"\nError in analysis: {results['error']}")
            
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found.")
        print("Please ensure the CSV file exists in the current directory.")
        print("You can generate it by running comprehensive_json_extraction.py first.")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
