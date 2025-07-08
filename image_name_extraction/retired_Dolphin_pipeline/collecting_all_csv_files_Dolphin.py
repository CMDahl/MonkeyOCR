import pandas as pd

second = r'd:\data\HCNC\norway\biographies\storage\Dolphin\output\failed_rows_with_biographies.csv'
first = r'd:\data\HCNC\norway\biographies\storage\Dolphin\output\extracted_all_names_Dolphin_with_chunks_with_biographies.csv'
output = r'd:\data\HCNC\norway\biographies\storage\Dolphin\output\extracted_all_names_Dolphin_with_chunks_with_biographies_second_round.csv'

output_final = r'd:\data\HCNC\norway\biographies\storage\Dolphin\output\extracted_all_names_portraits_biographies_Dolphin_final.csv'


# Load both CSV files
df_main = pd.read_csv(first)
df_failed = pd.read_csv(second)

# Create a copy of main DataFrame
df_merged = df_main.copy()

# For each row in failed DataFrame, update the corresponding row in main
for _, failed_row in df_failed.iterrows():
    # Find matching row in main DataFrame
    mask = (df_merged['name'] == failed_row['name']) & (df_merged['book_id'] == failed_row['book_id'])
    
    if mask.any():
        # Update only the columns that exist in both DataFrames
        for col in df_failed.columns:
            if col in df_merged.columns:
                df_merged.loc[mask, col] = failed_row[col]
df_merged.reset_index(drop=True, inplace=True)
print(f"Updated {len(df_failed)} rows in the main DataFrame")
#df_merged.to_csv(output, index=False)

# Load the files into separate DataFrames
df_portrait_single = pd.read_csv(r'D:\data\HCNC\norway\biographies\storage\Dolphin\output\extracted_portrait_names_Dolphin_with_chunks_single_page.csv')
df_next_page_portraits = pd.read_csv(r'd:\data\HCNC\norway\biographies\storage\Dolphin\output\extracted_all_names_Dolphin_with_chunks_and_portraits.csv')

df_portrait_single = df_portrait_single[['name', 'book_id', 'image_filename']]

df_next_page_portraits = df_next_page_portraits[['name', 'book_id', 'portrait_filename']]
df_next_page_portraits.rename(columns={'portrait_filename': 'image_filename'}, inplace=True)
len(df_next_page_portraits)
#Only keep the rows in df_next_page_portraits where imagae_filename is not null
df_next_page_portraits = df_next_page_portraits[df_next_page_portraits['image_filename'].notnull()]
len(df_next_page_portraits)

# Merge the two DataFrames on 'name' and 'book_id' and in this merge replace the entry in the column 'image_filename' in df_portrait_single with the one from df_next_page_portraits
df_merged_portraits = pd.merge(df_portrait_single, df_next_page_portraits, on=['name', 'book_id'], how='outer', suffixes=('', '_next_page')).reset_index(drop=True)

#if 'image_filename_next_page' is not null, replace 'image_filename' with 'image_filename_next_page'
df_merged_portraits['image_filename'] = df_merged_portraits['image_filename_next_page'].combine_first(df_merged_portraits['image_filename']).reset_index(drop=True)
# Drop the 'image_filename_next_page' column
df_merged_portraits.drop(columns=['image_filename_next_page'], inplace=True).reset_index(drop=True)

#sort the DataFrame by 'name' and 'book_id'
df_merged_portraits.sort_values(by=['book_id','name'], inplace=True).reset_index(drop=True)

#
df_merged= df_merged[['name', 'book_id', 'markdown_chunk','biography_json']].reset_index(drop=True)
# Merge the main DataFrame with the portraits DataFrame
df_final = pd.merge(df_merged, df_merged_portraits, on=['name', 'book_id'], how='left')

# Save the final DataFrame to a CSV file
df_final.to_csv(output_final, index=False)
print(f"Final DataFrame saved to {output}")
# Print the number of rows in the final DataFrame
print(f"Final DataFrame contains {len(df_final)} rows")
# Pring the number of rows with non-null image_filename
print(f"Number of rows with non-null image_filename: {df_final['image_filename'].notnull().sum()}")
