"""
Standalone String Similarity Analysis Tool

This script provides easy-to-use functions for computing string similarity
between columns in your comparison dataframes.
"""

from comprehensive_json_extraction import compute_string_similarity, analyze_all_similarities, print_similarity_report
import pandas as pd

def quick_similarity_check(df: pd.DataFrame, 
                          azure_col: str, 
                          monkey_col: str) -> None:
    """
    Quick similarity check between two columns with formatted output.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing both columns
    azure_col : str
        Azure column name
    monkey_col : str
        Monkey column name
    """
    
    print(f"Similarity Analysis: {azure_col} vs {monkey_col}")
    print("=" * 60)
    
    results = compute_string_similarity(df, azure_col, monkey_col)
    
    if 'error' in results:
        print(f"Error: {results['error']}")
        return
    
    print(f"Valid comparisons: {results['valid_rows']} / {results['total_rows']}")
    print(f"Exact matches: {results['exact_matches']} ({results['exact_match_percentage']:.1f}%)")
    
    if 'ratio' in results['statistics']:
        stats = results['statistics']['ratio']
        print(f"Similarity Score - Mean: {stats['mean']:.1f}, Median: {stats['median']:.1f}")
        print(f"Range: {stats['min']:.1f} - {stats['max']:.1f}")
    
    if 'high_similarity_matches' in results:
        print(f"High similarity (>90%): {results['high_similarity_matches']} ({results['high_similarity_percentage']:.1f}%)")
    
    # Show some examples of low similarity matches
    if 'ratio' in results['similarity_scores']:
        scores = results['similarity_scores']['ratio']
        valid_data = df[(df[azure_col].notna()) & (df[monkey_col].notna()) & 
                       (df[azure_col] != 'Missing') & (df[monkey_col] != 'Missing')].copy()
        
        valid_data['similarity_score'] = scores
        low_similarity = valid_data[valid_data['similarity_score'] < 80].head(3)
        
        if len(low_similarity) > 0:
            print(f"\nExamples of low similarity matches:")
            for _, row in low_similarity.iterrows():
                print(f"  Score: {row['similarity_score']:.1f}")
                print(f"    Azure:  '{row[azure_col]}'")
                print(f"    Monkey: '{row[monkey_col]}'")
                print()

def compare_field_types(df: pd.DataFrame) -> None:
    """
    Compare similarity across different types of fields.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Comparison dataframe with Azure/Monkey columns
    """
    
    print("FIELD TYPE COMPARISON")
    print("=" * 50)
    
    # Categorize fields
    field_categories = {
        'Personal Info': ['name', 'birth_date', 'birth_place', 'father_name', 'mother_name'],
        'Titles': ['title'],
        'Education': [col.replace('_azure', '').replace('_monkey', '') for col in df.columns 
                     if 'education' in col and '_azure' in col],
        'Jobs': [col.replace('_azure', '').replace('_monkey', '') for col in df.columns 
                if 'job' in col and '_azure' in col],
        'Family': [col.replace('_azure', '').replace('_monkey', '') for col in df.columns 
                  if ('child' in col or 'spouse' in col) and '_azure' in col]
    }
    
    # Analyze each category
    for category, fields in field_categories.items():
        if not fields:
            continue
            
        print(f"\n{category.upper()}:")
        print("-" * 30)
        
        category_stats = []
        
        for field in fields:
            azure_col = f"{field}_azure"
            monkey_col = f"{field}_monkey"
            
            if azure_col in df.columns and monkey_col in df.columns:
                results = compute_string_similarity(df, azure_col, monkey_col, 
                                                  similarity_methods=['ratio'], 
                                                  include_length_stats=False)
                
                if 'error' not in results and 'ratio' in results['statistics']:
                    stats = results['statistics']['ratio']
                    category_stats.append({
                        'field': field,
                        'mean_similarity': stats['mean'],
                        'exact_matches': results['exact_match_percentage'],
                        'valid_rows': results['valid_rows']
                    })
        
        if category_stats:
            # Sort by similarity
            category_stats.sort(key=lambda x: x['mean_similarity'], reverse=True)
            
            for stat in category_stats:
                print(f"  {stat['field']:<20} - Similarity: {stat['mean_similarity']:5.1f}, "
                      f"Exact: {stat['exact_matches']:5.1f}%, Rows: {stat['valid_rows']}")
            
            # Category average
            avg_similarity = sum(s['mean_similarity'] for s in category_stats) / len(category_stats)
            avg_exact = sum(s['exact_matches'] for s in category_stats) / len(category_stats)
            print(f"  {'CATEGORY AVERAGE':<20} - Similarity: {avg_similarity:5.1f}, Exact: {avg_exact:5.1f}%")

def main():
    """Demonstrate the similarity analysis tools"""
    
    print("Loading comparison data...")
    df = pd.read_csv('comprehensive_comparison_dataframe.csv')
    
    print(f"Loaded dataframe with {df.shape[0]} rows and {df.shape[1]} columns")
    
    # Example 1: Quick check of specific columns
    print("\n" + "="*80)
    print("EXAMPLE 1: QUICK SIMILARITY CHECK")
    print("="*80)
    
    quick_similarity_check(df, 'title_azure', 'title_monkey')
    
    # Example 2: Compare field types
    print("\n" + "="*80)
    print("EXAMPLE 2: FIELD TYPE COMPARISON")
    print("="*80)
    
    compare_field_types(df)
    
    # Example 3: Analyze specific problematic fields
    print("\n" + "="*80)
    print("EXAMPLE 3: DETAILED ANALYSIS OF PROBLEMATIC FIELDS")
    print("="*80)
    
    problematic_fields = [
        ('job1_title_azure', 'job1_title_monkey'),
        ('job1_location_azure', 'job1_location_monkey'),
        ('education1_title_azure', 'education1_title_monkey')
    ]
    
    for azure_col, monkey_col in problematic_fields:
        print("\n" + "-"*60)
        quick_similarity_check(df, azure_col, monkey_col)

if __name__ == "__main__":
    main()
