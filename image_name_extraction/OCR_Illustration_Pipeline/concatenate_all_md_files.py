import os
import glob
import argparse

def concatenate_md_files(input_dir, output_dir):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "all_text.md")
    
    # Find all .md files in the input directory
    md_files = glob.glob(os.path.join(input_dir, "*.md"))
    
    print(f"Found {len(md_files)} markdown files in {input_dir}")
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for filename in md_files:
            # Skip the output file itself if it's in the same directory
            if os.path.abspath(filename) == os.path.abspath(output_file):
                continue
                
            with open(filename, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
                outfile.write("\n\n")  # Add separation between files
                
    print(f"Concatenated content written to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Concatenate all MD files in a directory")
    parser.add_argument("input_dir", help="Directory containing MD files")
    parser.add_argument("output_dir", help="Directory to save the concatenated file")
    
    args = parser.parse_args()
    
    concatenate_md_files(args.input_dir, args.output_dir)
