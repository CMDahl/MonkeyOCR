"""
Function to extract figure references from text and report first two occurrences.
"""

import pandas as pd
import re
from typing import List, Tuple, Optional, Dict, Any

def extract_figure_references(df: pd.DataFrame, 
                            text_column: str = 'markdown_chunk_azureocr',
                            figure1_column: str = 'Figure1',
                            figure2_column: str = 'Figure2',
                            missing_value: str = 'Missing value',
                            book_id_column: str = 'book_id',
                            create_image_columns: bool = True) -> pd.DataFrame:
    """
    Extract figure references from text strings and report first two occurrences.
    
    This function searches for patterns like **[Figure: 1.1]**, **[Figure: 2.3]**, etc.
    in the specified text column and reports the first two occurrences in separate columns.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the text data
    text_column : str
        Name of the column containing text to search (default: 'markdown_chunk_azureocr')
    figure1_column : str
        Name of column to store first figure reference (default: 'Figure1')
    figure2_column : str
        Name of column to store second figure reference (default: 'Figure2')
    missing_value : str
        Value to use when no figure reference is found (default: 'Missing value')
    book_id_column : str
        Name of column containing book_id for image filename generation (default: 'book_id')
    create_image_columns : bool
        Whether to create azure_image1 and azure_image2 columns (default: True)
    
    Returns:
    --------
    pd.DataFrame
        Original DataFrame with added Figure1, Figure2, and optionally azure_image1, azure_image2 columns
    """
    
    # Create a copy to avoid modifying the original DataFrame
    result_df = df.copy()
    
    # Initialize the new columns with missing values
    result_df[figure1_column] = missing_value
    result_df[figure2_column] = missing_value
    
    # Initialize image columns if requested
    if create_image_columns:
        result_df['azure_image1'] = missing_value
        result_df['azure_image2'] = missing_value
    
    # Regular expression pattern to match **[Figure: X.Y]** where X.Y are numbers
    # This pattern matches:
    # - ** at the beginning
    # - [Figure: or [FIGURE: (case insensitive)
    # - one or more digits
    # - a dot
    # - one or more digits
    # - ]
    # - ** at the end
    figure_pattern = r'\*\*\[(?:Figure|FIGURE):\s*(\d+\.\d+)\]\*\*'
    
    def extract_figure_number(figure_text):
        """Extract figure number from figure reference text"""
        if pd.isna(figure_text) or figure_text == missing_value:
            return None
        match = re.search(r'(\d+\.\d+)', figure_text)
        return match.group(1) if match else None
    
    def create_image_filename(book_id, figure_number):
        """Create image filename from book_id and figure number"""
        if pd.isna(book_id) or pd.isna(figure_number) or figure_number is None:
            return missing_value
        return f"{book_id}_{figure_number}.png"
    
    print(f"Searching for figure references in column '{text_column}'...")
    print(f"Pattern: {figure_pattern}")
    
    # Counter for tracking results
    rows_with_figures = 0
    total_figures_found = 0
    
    # Process each row
    for index, row in result_df.iterrows():
        text = row[text_column]
        
        # Skip if text is NaN or empty
        if pd.isna(text) or text == '':
            continue
        
        # Find all figure references in the text
        # Use finditer to get full matches while preserving original case
        matches = re.finditer(figure_pattern, str(text))
        match_list = []
        
        for match in matches:
            # Get the full match to preserve original case
            full_match = match.group(0)
            match_list.append(full_match)
        
        if match_list:
            rows_with_figures += 1
            total_figures_found += len(match_list)
            
            # Get book_id for image filename generation
            book_id = row[book_id_column] if book_id_column in result_df.columns else None
            
            # Store first figure reference
            if len(match_list) >= 1:
                result_df.at[index, figure1_column] = match_list[0]
                
                # Create image filename if requested
                if create_image_columns:
                    fig_number = extract_figure_number(match_list[0])
                    result_df.at[index, 'azure_image1'] = create_image_filename(book_id, fig_number)
            
            # Store second figure reference if it exists
            if len(match_list) >= 2:
                result_df.at[index, figure2_column] = match_list[1]
                
                # Create image filename if requested
                if create_image_columns:
                    fig_number = extract_figure_number(match_list[1])
                    result_df.at[index, 'azure_image2'] = create_image_filename(book_id, fig_number)
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total rows processed: {len(result_df)}")
    print(f"Rows with figure references: {rows_with_figures}")
    print(f"Total figure references found: {total_figures_found}")
    
    # Count how many rows have each figure column filled
    figure1_count = (result_df[figure1_column] != missing_value).sum()
    figure2_count = (result_df[figure2_column] != missing_value).sum()
    
    print(f"Rows with Figure1: {figure1_count}")
    print(f"Rows with Figure2: {figure2_count}")
    
    # Print image column statistics if created
    if create_image_columns:
        image1_count = (result_df['azure_image1'] != missing_value).sum()
        image2_count = (result_df['azure_image2'] != missing_value).sum()
        print(f"Rows with azure_image1: {image1_count}")
        print(f"Rows with azure_image2: {image2_count}")
    
    return result_df

def find_all_figure_references(df: pd.DataFrame, 
                             text_column: str = 'markdown_chunk_azure') -> pd.DataFrame:
    """
    Find all figure references in the text and return detailed information.
    
    This is a helper function to explore what figure references exist in your data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the text data
    text_column : str
        Name of the column containing text to search
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with detailed information about found figure references
    """
    
    figure_pattern = r'\*\*\[(?:Figure|FIGURE):\s*(\d+\.\d+)\]\*\*'
    results = []
    
    for index, row in df.iterrows():
        text = row[text_column]
        
        if pd.isna(text) or text == '':
            continue
        
        matches = re.finditer(figure_pattern, str(text))
        
        for match_num, match in enumerate(matches, 1):
            results.append({
                'row_index': index,
                'figure_number': match.group(1),
                'full_reference': match.group(0),
                'match_position': match.start(),
                'occurrence_in_row': match_num
            })
    
    return pd.DataFrame(results)

def demonstrate_figure_extraction():
    """
    Demonstrate the figure extraction function with sample data.
    """
    
    # Create sample data
    sample_data = {
        'book_id': [
            'digibok_2007031501007_0001',
            'digibok_2007031501007_0002',
            'digibok_2007031501007_0003',
            'digibok_2007031501007_0004',
            'digibok_2007031501007_0005',
            'digibok_2007031501007_0006',
            'digibok_2007031501007_0007'
        ],
        'markdown_chunk_azure': [
            'This is text with **[Figure: 1.1]** and some more text with **[Figure: 1.2]**.',
            'Another text with only **[Figure: 2.1]** reference.',
            'Text with no figure references.',
            'Multiple figures: **[Figure: 3.1]**, **[Figure: 3.2]**, and **[Figure: 3.3]**.',
            None,  # Test with None value
            '',    # Test with empty string
            'Text with **[Figure: 4.10]** showing decimal numbers work.'
        ],
        'other_column': ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    }
    
    df = pd.DataFrame(sample_data)
    
    print("Original DataFrame:")
    print(df)
    print("\n" + "="*60 + "\n")
    
    # Apply the extraction function
    result_df = extract_figure_references(df, text_column='markdown_chunk_azure')
    
    print("\nResult DataFrame:")
    print(result_df[['book_id', 'markdown_chunk_azure', 'Figure1', 'Figure2', 'azure_image1', 'azure_image2']])
    
    print("\n" + "="*60 + "\n")
    
    # Show detailed analysis
    detailed_results = find_all_figure_references(df)
    print("Detailed figure reference analysis:")
    print(detailed_results)
    
    return result_df

# Example usage function
def process_your_data(csv_path: str, 
                     text_column: str = 'markdown_chunk_azure',
                     book_id_column: str = 'book_id',
                     output_path: Optional[str] = None,
                     create_image_columns: bool = True) -> pd.DataFrame:
    """
    Process your actual CSV file to extract figure references.
    
    Parameters:
    -----------
    csv_path : str
        Path to your CSV file
    text_column : str
        Name of the column containing text to search
    book_id_column : str
        Name of column containing book_id for image filename generation (default: 'book_id')
    output_path : str, optional
        Path to save the result CSV file
    create_image_columns : bool
        Whether to create azure_image1 and azure_image2 columns (default: True)
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with figure references extracted
    """
    
    print(f"Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} rows")
    
    # Extract figure references
    result_df = extract_figure_references(df, text_column=text_column, 
                                         book_id_column=book_id_column,
                                         create_image_columns=create_image_columns)
    
    # Save if output path provided
    if output_path:
        result_df.to_csv(output_path, index=False)
        print(f"Results saved to: {output_path}")
    
    return result_df

# Simple integration function for immediate use
def add_figure_columns_to_dataframe(df: pd.DataFrame, 
                                   text_column: str = 'markdown_chunk_azure',
                                   book_id_column: str = 'book_id',
                                   create_image_columns: bool = True) -> pd.DataFrame:
    """
    Simple function to add Figure1 and Figure2 columns to your existing DataFrame.
    
    This is the most straightforward way to use the figure extraction functionality.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Your existing DataFrame
    text_column : str
        Column name containing the text to search (default: 'markdown_chunk_azure')
    book_id_column : str
        Column name containing the book_id for image filename generation (default: 'book_id')
    create_image_columns : bool
        Whether to create azure_image1 and azure_image2 columns (default: True)
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with added Figure1, Figure2, and optionally azure_image1, azure_image2 columns
    
    Example:
    --------
    # Load your data
    df = pd.read_csv('your_file.csv')
    
    # Add figure columns
    df_with_figures = add_figure_columns_to_dataframe(df)
    
    # Save the result
    df_with_figures.to_csv('output_with_figures.csv', index=False)
    """
    
    return extract_figure_references(df, text_column=text_column, 
                                   book_id_column=book_id_column, 
                                   create_image_columns=create_image_columns)

# Quick test function to check if your data has figure references
def quick_figure_check(df: pd.DataFrame, 
                      text_column: str = 'markdown_chunk_azure',
                      show_examples: bool = True) -> Dict[str, Any]:
    """
    Quick check to see if your data contains figure references.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Your DataFrame
    text_column : str
        Column to check
    show_examples : bool
        Whether to print example figure references found
    
    Returns:
    --------
    dict
        Summary statistics about figure references
    """
    
    figure_pattern = r'\*\*\[(?:Figure|FIGURE):\s*(\d+\.\d+)\]\*\*'
    
    total_rows = len(df)
    rows_with_figures = 0
    total_figures = 0
    example_figures = []
    
    for index, row in df.iterrows():
        text = row[text_column]
        
        if pd.isna(text) or text == '':
            continue
        
        matches = re.findall(figure_pattern, str(text))
        
        if matches:
            rows_with_figures += 1
            total_figures += len(matches)
            
            # Collect examples
            if len(example_figures) < 5:  # Show up to 5 examples
                for match in matches:
                    if len(example_figures) < 5:
                        example_figures.append(f"**[Figure: {match}]**")
    
    stats = {
        'total_rows': total_rows,
        'rows_with_figures': rows_with_figures,
        'percentage_with_figures': (rows_with_figures / total_rows * 100) if total_rows > 0 else 0,
        'total_figure_references': total_figures,
        'example_figures': example_figures
    }
    
    print(f"Quick Figure Check Results:")
    print(f"Total rows: {stats['total_rows']}")
    print(f"Rows with figure references: {stats['rows_with_figures']} ({stats['percentage_with_figures']:.1f}%)")
    print(f"Total figure references found: {stats['total_figure_references']}")
    
    if show_examples and example_figures:
        print(f"Example figures found: {', '.join(example_figures)}")
    
    return stats

if __name__ == "__main__":
    # Run demonstration
    print("=" * 80)
    print("FIGURE EXTRACTION WITH IMAGE FILENAME GENERATION")
    print("=" * 80)
    
    result = demonstrate_figure_extraction()
    
    print("\n" + "=" * 80)
    print("USAGE EXAMPLES")
    print("=" * 80)
    
    print("""
# Example 1: Process your CSV file with image filename generation
df = pd.read_csv('your_data.csv')
result_df = extract_figure_references(df, text_column='markdown_chunk_azureocr')

# Example 2: Use the convenience function
result_df = add_figure_columns_to_dataframe(df, text_column='markdown_chunk_azureocr')

# Example 3: Process with file I/O
result_df = process_your_data('your_data.csv', 
                             text_column='markdown_chunk_azureocr',
                             output_path='output_with_figures.csv')

# Example 4: Custom column names and settings
result_df = extract_figure_references(df, 
                                    text_column='your_text_column',
                                    figure1_column='FirstFigure',
                                    figure2_column='SecondFigure',
                                    book_id_column='your_book_id_column',
                                    missing_value='No Figure',
                                    create_image_columns=True)

# Example 5: Disable image filename generation
result_df = extract_figure_references(df, create_image_columns=False)

NEW FEATURES:
=============
- Automatically creates azure_image1 and azure_image2 columns
- Combines book_id + figure_number + '.png'
- Example: 'digibok_2007031501007_0057' + '1.2' = 'digibok_2007031501007_0057_1.2.png'
- Handles both **[Figure: X.Y]** and **[FIGURE: X.Y]** formats
- Preserves original case in figure references
- Gracefully handles missing values
""")
    
result_df = extract_figure_references(df, 
                                    text_column='',
                                    figure1_column='FirstFigure',
                                    figure2_column='SecondFigure',
                                    book_id_column='your_book_id_column',
                                    missing_value='No Figure',
                                    create_image_columns=True)    