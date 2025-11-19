import os
import pandas as pd
import argparse
import shutil

def main():
    parser = argparse.ArgumentParser(description="Finalize and collect data for the illustration pipeline")
    parser.add_argument("output_dir", help="Directory containing the pipeline outputs")
    
    args = parser.parse_args()
    
    output_dir = args.output_dir
    
    # Expected final file from biography_extractor
    # It appends '_with_biographies.csv' to the input filename
    # We will feed 'extracted_all_names_with_chunks_and_portraits.csv' to it
    expected_file = os.path.join(output_dir, "extracted_all_names_with_chunks_and_portraits_with_biographies.csv")
    final_file = os.path.join(output_dir, "final_dataset.csv")
    
    if os.path.exists(expected_file):
        print(f"Found final output file: {expected_file}")
        shutil.copy(expected_file, final_file)
        print(f"Created final dataset: {final_file}")
        
        # Load and show stats
        df = pd.read_csv(final_file)
        print("\nFinal Dataset Statistics:")
        print(f"Total entries: {len(df)}")
        if 'portrait_filename' in df.columns:
            portraits = df['portrait_filename'].notna().sum()
            print(f"Entries with portraits: {portraits}")
        if 'biography_json' in df.columns:
            bios = df['biography_json'].notna() & (df['biography_json'] != '')
            print(f"Entries with extracted biography: {bios.sum()}")
            
    else:
        print(f"Warning: Expected final file not found: {expected_file}")
        # Try to find the one without biographies if that failed
        alt_file = os.path.join(output_dir, "extracted_all_names_with_chunks_and_portraits.csv")
        if os.path.exists(alt_file):
            print(f"Found intermediate file: {alt_file}")
            shutil.copy(alt_file, final_file)
            print(f"Created final dataset (without biographies): {final_file}")
        else:
            print("Error: No suitable output files found.")

if __name__ == "__main__":
    main()
