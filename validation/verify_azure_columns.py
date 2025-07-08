"""
Simple verification that the azure_image columns are being created.
"""

import pandas as pd

# Check the output file that was just created
print("Checking the output file that was just created...")
result_df = pd.read_csv('output_with_figures_and_images.csv')

print("Columns in the saved file:")
print(result_df.columns.tolist())
print()

# Check for the azure_image columns specifically
if 'azure_image1' in result_df.columns and 'azure_image2' in result_df.columns:
    print("✅ SUCCESS: azure_image1 and azure_image2 columns are present!")
    
    # Show some statistics
    image1_count = (result_df['azure_image1'] != 'Missing value').sum()
    image2_count = (result_df['azure_image2'] != 'Missing value').sum()
    
    print(f"Rows with azure_image1: {image1_count}")
    print(f"Rows with azure_image2: {image2_count}")
    
    # Show some examples
    print("\nExample azure_image1 values:")
    examples1 = result_df[result_df['azure_image1'] != 'Missing value']['azure_image1'].head(5)
    for i, val in enumerate(examples1):
        print(f"  {i+1}. {val}")
    
    if image2_count > 0:
        print("\nExample azure_image2 values:")
        examples2 = result_df[result_df['azure_image2'] != 'Missing value']['azure_image2'].head(3)
        for i, val in enumerate(examples2):
            print(f"  {i+1}. {val}")
    
    # Show one complete example
    print("\nComplete example row:")
    example_row = result_df[result_df['azure_image1'] != 'Missing value'].iloc[0]
    print(f"book_id: {example_row['book_id']}")
    print(f"Figure1: {example_row['Figure1']}")
    print(f"Figure2: {example_row['Figure2']}")
    print(f"azure_image1: {example_row['azure_image1']}")
    print(f"azure_image2: {example_row['azure_image2']}")
    
else:
    print("❌ ERROR: azure_image columns are missing!")
    print("Available columns:")
    for i, col in enumerate(result_df.columns):
        print(f"  {i+1}. {col}")

print(f"\nTotal rows in result: {len(result_df)}")
print(f"Total columns in result: {len(result_df.columns)}")
