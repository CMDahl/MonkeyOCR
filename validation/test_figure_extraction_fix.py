import pandas as pd
from figure_extraction import extract_figure_references

# Load your data
df_filename = r'd:\data\HCNC\norway\biographies\storage\comparison_threeway_merged.csv'
df = pd.read_csv(df_filename)

print("Extracting figure references with image filename generation...")

# Extract figures and create image filenames
result = extract_figure_references(df, text_column='markdown_chunk_azureocr')

print("\nColumns in result:")
print(result.columns.tolist())

print(f"\nConfirming azure_image columns are present:")
print(f"azure_image1 in columns: {'azure_image1' in result.columns}")
print(f"azure_image2 in columns: {'azure_image2' in result.columns}")

# Show some statistics
if 'azure_image1' in result.columns:
    image1_count = (result['azure_image1'] != 'Missing value').sum()
    image2_count = (result['azure_image2'] != 'Missing value').sum()
    print(f"\nStatistics:")
    print(f"Rows with azure_image1: {image1_count}")
    print(f"Rows with azure_image2: {image2_count}")
    
    # Show an example
    example_with_images = result[result['azure_image1'] != 'Missing value'].iloc[0]
    print(f"\nExample row:")
    print(f"book_id: {example_with_images['book_id']}")
    print(f"Figure1: {example_with_images['Figure1']}")
    print(f"azure_image1: {example_with_images['azure_image1']}")
    if example_with_images['azure_image2'] != 'Missing value':
        print(f"Figure2: {example_with_images['Figure2']}")
        print(f"azure_image2: {example_with_images['azure_image2']}")

# Save the result
result.to_csv('output_with_figures_and_images.csv', index=False)

print(f"\nSaved result with {len(result.columns)} columns to output_with_figures_and_images.csv")