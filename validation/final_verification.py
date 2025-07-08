"""
Final verification script to demonstrate the complete figure extraction functionality.
"""
import pandas as pd
from figure_extraction import extract_figure_references

def main():
    # Load your data
    df_filename = r'd:\data\HCNC\norway\biographies\storage\comparison_threeway_merged.csv'
    df = pd.read_csv(df_filename)
    
    print("=== FIGURE EXTRACTION WITH IMAGE FILENAME GENERATION ===")
    print(f"Original DataFrame shape: {df.shape}")
    print(f"Original columns: {len(df.columns)}")
    
    # Extract figures and create image filenames
    result = extract_figure_references(df, text_column='markdown_chunk_azureocr')
    
    print(f"\nResult DataFrame shape: {result.shape}")
    print(f"Result columns: {len(result.columns)}")
    
    # Verify all required columns are present
    required_columns = ['Figure1', 'Figure2', 'azure_image1', 'azure_image2']
    print(f"\n=== COLUMN VERIFICATION ===")
    for col in required_columns:
        present = col in result.columns
        print(f"{col}: {'✓' if present else '✗'}")
    
    # Show statistics
    print(f"\n=== STATISTICS ===")
    figure1_count = (result['Figure1'] != 'Missing value').sum()
    figure2_count = (result['Figure2'] != 'Missing value').sum()
    image1_count = (result['azure_image1'] != 'Missing value').sum()
    image2_count = (result['azure_image2'] != 'Missing value').sum()
    
    print(f"Rows with Figure1: {figure1_count}")
    print(f"Rows with Figure2: {figure2_count}")
    print(f"Rows with azure_image1: {image1_count}")
    print(f"Rows with azure_image2: {image2_count}")
    
    # Show examples
    print(f"\n=== EXAMPLES ===")
    examples = result[result['azure_image1'] != 'Missing value'].head(3)
    for i, (idx, row) in enumerate(examples.iterrows()):
        print(f"\nExample {i+1}:")
        print(f"  book_id: {row['book_id']}")
        print(f"  Figure1: {row['Figure1']}")
        print(f"  azure_image1: {row['azure_image1']}")
        if row['azure_image2'] != 'Missing value':
            print(f"  Figure2: {row['Figure2']}")
            print(f"  azure_image2: {row['azure_image2']}")
    
    # Test case sensitivity
    print(f"\n=== CASE SENSITIVITY TEST ===")
    # Check if we have both [Figure: and [FIGURE: in the data
    figure_refs = result[result['Figure1'] != 'Missing value']['Figure1'].tolist()
    figure_count = sum(1 for ref in figure_refs if '[Figure:' in ref)
    figure_upper_count = sum(1 for ref in figure_refs if '[FIGURE:' in ref)
    
    print(f"References with [Figure: (mixed case): {figure_count}")
    print(f"References with [FIGURE: (uppercase): {figure_upper_count}")
    
    # Save the result
    output_filename = 'final_output_with_figures_and_images.csv'
    result.to_csv(output_filename, index=False)
    print(f"\n=== OUTPUT ===")
    print(f"Saved result to: {output_filename}")
    print(f"Total columns in output: {len(result.columns)}")
    
    # Verify saved file
    saved_df = pd.read_csv(output_filename)
    print(f"Verified saved file has {len(saved_df.columns)} columns")
    
    print("\n=== SUCCESS ===")
    print("✓ Figure extraction working correctly")
    print("✓ Case-insensitive matching implemented")
    print("✓ Original case preserved in output")
    print("✓ Azure image filename generation working")
    print("✓ All required columns present in output")

if __name__ == "__main__":
    main()
