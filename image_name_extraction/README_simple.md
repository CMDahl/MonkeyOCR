
New pipeline:
1.
python AzureOCR_extracting_text_and_figures.py --input "D:/data/HCNC/norway/biographies/raw/corpus/digibok_2007031501007" --start "0057" --end "0494" --output  "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json"

2.
python gemini_portrait_name_associator.py "d:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json"  "d:\data\HCNC\norway\biographies\storage\AzureOCR\output_portrait_name_associations"

python gemini_portrait_name_associator.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007"  "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_portrait_name_associations"  --start "0057" --end "0494"

python gemini_portrait_name_associator.py "D:\data\HCNC\norway\biographies\storage\Dolphin\markdown"  "D:\data\HCNC\norway\biographies\storage\Dolphin\output_portrait_name_associations"
 --start "0057" --end "0494"

3
python concatenate_all_md_files.py "d:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json" "d:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json\concatenated_all.md" --file-separator --spacing 2

python concatenate_all_md_files.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007"  "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007\concatenated_all.md" --file-separator --spacing 2

python concatenate_all_md_files.py "D:\data\HCNC\norway\biographies\storage\Dolphin\markdown"  "D:\data\HCNC\norway\biographies\storage\Dolphin\markdown\concatenated_all.md" --file-separator --spacing 2

4.
python gemini_all_names.py "d:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_portrait_name_associations"

python gemini_all_names.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007"  "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_portrait_name_associations"

python gemini_all_names.py "D:\data\HCNC\norway\biographies\storage\Dolphin\markdown" "D:\data\HCNC\norway\biographies\storage\Dolphin\output_portrait_name_associations"

5. 
python extract_all_names.py "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_portrait_name_associations\all_books_names.json" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json\concatenated_all.md" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json\" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\" --portrait-pattern "**[FIGURE:"

python extract_all_names.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_portrait_name_associations\all_books_names.json" "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007\concatenated_all.md" "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007\" "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_csv\" --portrait-pattern "![](images/"

python extract_all_names.py "D:\data\HCNC\norway\biographies\storage\Dolphin\output_portrait_name_associations\all_books_names.json" "D:\data\HCNC\norway\biographies\storage\Dolphin\markdown\concatenated_all.md" "D:\data\HCNC\norway\biographies\storage\Dolphin\markdown\" "D:\data\HCNC\norway\biographies\storage\Dolphin\output_csv\" --portrait-pattern "![Figure]("

6.
python biography_extractor.py "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_all_names_with_chunks.csv" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\biographical_data.json" --log-file "D:\data\HCNC\norway\biographies\storage\AzureOCR\log\biography_extraction.log" --log-level "INFO"

python biography_extractor.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_csv\extracted_all_names_with_chunks.csv" "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_csv\biographical_data.json" --log-file "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\log\biography_extraction.log" --log-level "INFO"

python biography_extractor.py "D:\data\HCNC\norway\biographies\storage\Dolphin\output_csv\extracted_all_names_with_chunks.csv" "D:\data\HCNC\norway\biographies\storage\Dolphin\output_csv\biographical_data.json" --log-file "D:\data\HCNC\norway\biographies\storage\Dolphin\log\biography_extraction.log" --log-level "INFO"

7. 
python extract_portrait_names.py "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_portrait_name_associations""D:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json\concatenated_all.md" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_csv\extracted_portrait_names_with_chunks.csv"

python extract_portrait_names.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_portrait_name_associations" "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007\concatenated_all.md" "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\output_csv\extracted_portrait_names_with_chunks.csv"

python extract_portrait_names.py "D:\data\HCNC\norway\biographies\storage\Dolphin\output_portrait_name_associations" "D:\data\HCNC\norway\biographies\storage\Dolphin\markdown\concatenated_all.md" "D:\data\HCNC\norway\biographies\storage\Dolphin\output_csv\extracted_portrait_names_with_chunks.csv"

8. (ready)
python collecting_all_csv_files.py 