## Pipeline

1. Run `azure_portrait_associator_Dolphin.py`: This script generates `digibok_2007031501007_0XXX_portrait_associations.json` based on all the OCR'ed images stores in *.md files. In these JSON files possible name-portrait relations are reported. 

2. Run `extract_portrait_names_Dolphin.py` -> `extracted_portrait_names_Dolphin_with_chunks_single_page.csv` : This script extract names, extract the chunks based on the names and the associated portrait when they are on the same image (single_page). Based on the `digibok_2007031501007_0XXX_portrait_associations.json` files.  

3. Run `extract_all_names_Dolphin.py` ->  `extracted_all_names_Dolphin_with_chunks.csv` and `extracted_all_names_Dolphin_with_chunks_and_portraits.csv`: This script extract all names, all chunks and portraits that appears on the top of an image and associate the image with the last person with capital "SURNAME" on the previous page.

4. Run `python biography_extractor_Dolphin.py "D:\data\HCNC\norway\biographies\storage\Dolphin\output\extracted_all_names_Dolphin_with_chunks.csv" "D:\data\HCNC\norway\biographies\storage\Dolphin\output\biographical_data.json"` -> `extracted_all_names_Dolphin_with_chunks_with_biographies.csv` and `biographical_data.json` : Extracts structured biographical information from markdown text chunks using Gemini. Note that the structured output is also parsed as json.

### Note: Since not not all names was succesfully processed under 4 (mainly due to json parsing errors) there was a second round

4a. Run `failed_rows_to_biography_extractor_Dolphin.py` -> `d:\data\HCNC\norway\biographies\storage\Dolphin\logs\failed_rows.csv`

4b. Run `python biography_extractor_Dolphin.py "d:\data\HCNC\norway\biographies\storage\Dolphin\logs\failed_rows.csv" "d:\data\HCNC\norway\biographies\storage\Dolphin\logs\biographical_data_failed_rows.json"` -> `failed_rows_with_biographies.csv` and `biographical_data_failed_rows.json`

5. Run `collecting_all_csv_files_Dolphin.py` -> `extracted_all_names_portraits_biographies_Dolphin_final.csv` : Collect all the information in the CSV files above and produce the final output.