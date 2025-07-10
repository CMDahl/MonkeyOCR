"""
Simple usage example for figure extraction.

This script shows how to use the figure extraction functions with your data.
"""

import pandas as pd
from figure_extraction import add_figure_columns_to_dataframe, quick_figure_check

# Example: How to use with your actual data
from typing import Optional

def process_your_csv_file(input_file_path: str, output_file_path: Optional[str] = None):
    """
    Process your CSV file to add Figure1 and Figure2 columns.
    
    Parameters:
    -----------
    input_file_path : str
        Path to your CSV file
    output_file_path : str, optional
        Path to save the output file (if None, adds '_with_figures' to input filename)
    """
    
    print(f"Loading data from: {input_file_path}")
    
    # Load your data
    try:
        df = pd.read_csv(input_file_path)
        print(f"Successfully loaded {len(df)} rows")
    except Exception as e:
        print(f"Error loading file: {e}")
        return
    
    # Check if the markdown_chunk_azure column exists
    if 'markdown_chunk_azure' not in df.columns:
        print("Available columns:", df.columns.tolist())
        print("Error: 'markdown_chunk_azure' column not found!")
        return
    
    # Quick check to see what's in your data
    print("\nRunning quick figure check...")
    stats = quick_figure_check(df, text_column='markdown_chunk_azure')
    
    if stats['total_figure_references'] == 0:
        print("No figure references found in your data.")
        return
    
    # Add figure columns
    print("\nExtracting figure references...")
    df_with_figures = add_figure_columns_to_dataframe(df)
    
    # Determine output filename
    if output_file_path is None:
        if input_file_path.endswith('.csv'):
            output_file_path = input_file_path.replace('.csv', '_with_figures.csv')
        else:
            output_file_path = input_file_path + '_with_figures.csv'
    
    # Save the result
    try:
        df_with_figures.to_csv(output_file_path, index=False)
        print(f"Results saved to: {output_file_path}")
        
        # Show a sample of the results
        print("\nSample results:")
        sample_cols = ['markdown_chunk_azure', 'Figure1', 'Figure2']
        # Only show columns that exist
        available_cols = [col for col in sample_cols if col in df_with_figures.columns]
        
        # Show first few rows with figure references
        rows_with_figures = df_with_figures[df_with_figures['Figure1'] != 'Missing value']
        if len(rows_with_figures) > 0:
            print(rows_with_figures[available_cols].head())
        else:
            print("No rows with figure references found.")
            
    except Exception as e:
        print(f"Error saving file: {e}")

# Example with sample data
def demo_with_sample_data():
    """
    Demonstrate the functions with sample data.
    """
    
    print("=" * 60)
    print("DEMO WITH SAMPLE DATA")
    print("=" * 60)
    
    # Create sample data
    sample_data = {
        'markdown_chunk_azure': [
            'This text contains **[Figure: 1.1]** and later **[Figure: 1.2]**.',
            'Another chunk with **[Figure: 2.1]** only.',
            'No figures in this text.',
            'Multiple: **[Figure: 3.1]**, **[Figure: 3.2]**, **[Figure: 3.3]**.'
        ],
        'other_column': ['A', 'B', 'C', 'D']
    }
    
    df = pd.DataFrame(sample_data)
    
    print("Original data:")
    print(df)
    print()
    
    # Quick check
    stats = quick_figure_check(df)
    print()
    
    # Add figure columns
    result = add_figure_columns_to_dataframe(df)
    
    print("Result with figure columns:")
    print(result[['markdown_chunk_azure', 'Figure1', 'Figure2']])

if __name__ == "__main__":
    print("=" * 60)
    print("FIGURE EXTRACTION USAGE EXAMPLE")
    print("=" * 60)
    
    # Run demo
    demo_with_sample_data()
    
    print("\n" + "=" * 60)
    print("TO USE WITH YOUR DATA:")
    print("=" * 60)
    print("""
# Option 1: Use the convenience function
process_your_csv_file('path/to/your/data.csv')

# Option 2: Manual approach
import pandas as pd
from figure_extraction import add_figure_columns_to_dataframe

df = pd.read_csv('your_data.csv')
result_df = add_figure_columns_to_dataframe(df)
result_df.to_csv('output_with_figures.csv', index=False)

# Option 3: If your text column has a different name
from figure_extraction import extract_figure_references

df = pd.read_csv('your_data.csv')
result_df = extract_figure_references(df, text_column='your_column_name')
result_df.to_csv('output_with_figures.csv', index=False)
""")
    
    print("\nUncomment the line below to process your actual data:")
    print("# process_your_csv_file('path/to/your/data.csv')")
    
    # Uncomment the next line and modify the path to process your actual data
    # process_your_csv_file('path/to/your/data.csv')
