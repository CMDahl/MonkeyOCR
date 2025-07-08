#!/usr/bin/env python3
"""
Norwegian Biography Portrait Associator - Google Gemini Version
Associates portrait images with person names across multiple markdown files,
with special handling for cross-page biographical entries and robust JSON parsing.
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import base64
from google import genai
from google.genai import types
import argparse
import logging
import time
from collections import defaultdict
# In Python interactive shell for testing
import sys
from pathlib import Path
import os
sys.path.append(str(Path(os.getcwd()).parent))
from agents.key_vault import KeyVault

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from pydantic import BaseModel
class Name(BaseModel):
    person_name: str

class BookPortraitAssociator:
    def __init__(self, api_key: str = None):
        # Google Gemini configuration
        #self.api_key = api_key or os.getenv("SDUGeminiAPI")
        self.api_key = api_key or os.getenv("AMDGeminiFlashKey")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required. Set it as environment variable or pass as parameter.")
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        #self.model = "gemini-2.5-flash-lite-preview-06-17"
        self.model = "gemini-2.5-flash"
        
    # ...existing code... (get_page_number, get_book_id, find_page_directories, load_page_content, load_book_content, extract_json_from_response, fix_json_string methods remain unchanged)
    
    def analyze_book_portraits(self, book_id: str, pages: List[Dict]) -> List[Dict]:
        """Use Google Gemini to identify all biographical names in sequential order"""
        
        # Combine all page content
        all_content = ""
        for page in pages:
            all_content += f"\n--- PAGE {page['page_number']} ---\n"
            all_content += page['content']
        
        prompt_content = f"""You are analyzing Norwegian biographical text to identify all people with biographical entries.
    
    BIOGRAPHICAL TEXT:
    {all_content}
    
    TASK:
    Identify all biographical entries in the text. Look for names where the SURNAME is in ALL-CAPS followed by given names, like "ALGER, Bjørn" or "ALNÆS, Ingeborg". These indicate biographical entries. If it is just the name , ike "ALGER, Bjørn", with no additional biographical entries ignore the name. One exception can be the last name listed. This might contain very limited biographic information due to a page break. So always include the last name in the text where the SURNAME is in ALL-CAPS followed by given names.
    
    Return all names in the exact order they appear in the text. Please also return all the names as they appear written in the text (do not change the case of the names). If you find a name that is not in the format "SURNAME, Given Names", ignore it.
    
    Respond with ONLY a valid JSON array:
    [
      {{
        "person_name": "SURNAME, Given Names",
      }}
    ]
    """
    
        # Temperature options for retry attempts
        temperature_options = [0.05, 0.1, 0.2, 0.5]
        
        # Retry up to 3 times with increasing temperature
        for attempt in range(4):
            temperature = temperature_options[attempt]
            
            try:
                logger.info(f"Attempt {attempt + 1} for {book_id} with temperature {temperature}")
                
                # Prepare content for Gemini
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt_content),
                        ],
                    ),
                ]
                
                # Configure generation with increasing temperature
                generate_content_config = types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=500,
                    ),
                    response_mime_type="application/json",
                    temperature=temperature
                )
                
                # Generate response
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=generate_content_config,
                )
            
                # Extract text from response
                response_text = response.text
                
                # Parse JSON response
                try:
                    biographical_entries = json.loads(response_text)
                    
                    # Success - add book ID to each entry
                    for entry in biographical_entries:
                        entry["book_id"] = book_id
                    
                    logger.info(f"Successfully extracted {len(biographical_entries)} names from {book_id} on attempt {attempt + 1}")
                    return biographical_entries
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Attempt {attempt + 1}: JSON decode error for {book_id}: {e}")
                    
                    # Try fallback JSON extraction
                    try:
                        biographical_entries = self.extract_json_from_response(response_text)
                        if biographical_entries:
                            for entry in biographical_entries:
                                entry["book_id"] = book_id
                            logger.info(f"Recovered {len(biographical_entries)} names from {book_id} using fallback method")
                            return biographical_entries
                    except Exception as fallback_error:
                        logger.warning(f"Fallback JSON extraction also failed: {fallback_error}")
                    
                    # If this is the last attempt, log the response for debugging
                    if attempt == 2:
                        logger.error(f"Raw response causing JSON error: {response_text[:500]}...")
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}: General error for {book_id}: {e}")
                
                # If this is the last attempt, log the full error
                if attempt == 2:
                    logger.error(f"All attempts failed for {book_id}: {e}")
        
        # All attempts failed
        logger.error(f"Failed to extract names for {book_id} after 3 attempts")
        return []
    
    def process_book(self, book_id: str, page_dirs: List[Path]) -> Dict:
        """Process a single book to identify all biographical names"""
        
        pages = self.load_book_content(page_dirs)
        if not pages:
            return {"book_id": book_id, "error": "No pages loaded"}
        
        biographical_entries = self.analyze_book_portraits(book_id, pages)
        
        return {
            "book_id": book_id,
            "total_entries": len(biographical_entries),
            "biographical_entries": biographical_entries,
            "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    def get_page_number(self, page_dir_name: str) -> int:
        """Extract page number from page directory name"""
        match = re.search(r'_(\d+)$', page_dir_name)
        return int(match.group(1)) if match else 0
    
    def get_book_id(self, page_dir_name: str) -> str:
        """Extract book ID from page directory name"""
        parts = page_dir_name.split('_')
        if len(parts) >= 4:  # e.g., digibok_2007031501007_0057
            return '_'.join(parts[:-1])  # Everything except the last part (page number)
        return page_dir_name
    
    def find_page_directories(self, input_path: Path) -> Dict[str, List[Path]]:
        """Find all digibok markdown files and group by book ID"""
        books = defaultdict(list)
        
        logger.info(f"Scanning directory: {input_path}")
        
        # Look for digibok markdown files directly in the input path
        for md_file in input_path.glob("digibok*.md"):
            # Extract book info from filename
            file_stem = md_file.stem  # filename without extension
            book_id = self.get_book_id(file_stem)
            
            # Create a mock directory structure for compatibility
            file_info = {
                "file_path": md_file,
                "book_id": book_id,
                "page_number": self.get_page_number(file_stem)
            }
            
            books[book_id].append(file_info)
            logger.debug(f"Found markdown file: {md_file.name} -> book: {book_id}")
        
        # Sort files by page number within each book
        for book_id in books:
            books[book_id].sort(key=lambda x: x["page_number"])
        
        logger.info(f"Found {len(books)} books with total {sum(len(files) for files in books.values())} files")
        for book_id, files in books.items():
            logger.info(f"  Book {book_id}: {len(files)} files")
        
        return books
    
    def load_page_content(self, file_info: Dict) -> Optional[Dict]:
        """Load content from a markdown file"""
        md_file = file_info["file_path"]
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            page_info = {
                "page_directory": str(md_file.parent),
                "page_name": md_file.stem,
                "page_number": file_info["page_number"],
                "md_file": str(md_file),
                "content": content
            }
            
            return page_info
            
        except Exception as e:
            logger.error(f"Error loading file {md_file}: {e}")
            return None
    
    def load_book_content(self, file_infos: List[Dict]) -> List[Dict]:
        """Load content from all files in the book"""
        pages = []
        
        logger.info(f"Loading content from {len(file_infos)} files")
        
        for file_info in file_infos:
            page_info = self.load_page_content(file_info)
            if page_info:
                pages.append(page_info)
        
        return pages
    
    def process_book(self, book_id: str, file_infos: List[Dict]) -> Dict:
        """Process a single book to identify all biographical names"""
        
        pages = self.load_book_content(file_infos)
        if not pages:
            return {"book_id": book_id, "error": "No pages loaded"}
        
        biographical_entries = self.analyze_book_portraits(book_id, pages)
        
        return {
            "book_id": book_id,
            "total_entries": len(biographical_entries),
            "biographical_entries": biographical_entries,
            "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def extract_json_from_response(self, response_text: str) -> List[Dict]:
        """Robust JSON extraction from LLM response"""
        # Try to find JSON array in the response
        json_patterns = [
            r'\[(?:[^[\]]*|\[[^\]]*\])*\]',  # Match nested JSON arrays
            r'```json\s*(\[.*?\])\s*```',    # JSON in code blocks
            r'```\s*(\[.*?\])\s*```',        # JSON in generic code blocks
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    # Clean up the JSON string
                    json_str = match.strip()
                    
                    # Try to parse it
                    data = json.loads(json_str)
                    if isinstance(data, list):
                        return data
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON parse error with pattern {pattern}: {e}")
                    continue
        
        # If no JSON found, try to extract and fix common issues
        # Look for array-like structures
        array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if array_match:
            json_str = array_match.group()
            
            # Try to fix common JSON issues
            try:
                # Replace problematic characters in strings
                fixed_json = self.fix_json_string(json_str)
                data = json.loads(fixed_json)
                if isinstance(data, list):
                    return data
            except Exception as e:
                logger.debug(f"Failed to fix JSON: {e}")
        
        logger.warning("No valid JSON array found in response")
        return []
    
    def fix_json_string(self, json_str: str) -> str:
        """Attempt to fix common JSON formatting issues"""
        # This is a basic approach - for production, consider using a more robust JSON parser
        
        # Save the original for debugging
        original = json_str
        
        try:
            # First, try to identify string values and escape quotes within them
            # This is a simplified approach
            
            # Replace newlines within strings with \\n
            json_str = re.sub(r'(?<=: ")(.*?)(?=")', lambda m: m.group(1).replace('\n', '\\n').replace('\r', '\\r'), json_str)
            
            # Replace unescaped quotes within string values (basic approach)
            # This is very basic and may not work for all cases
            
            return json_str
            
        except Exception as e:
            logger.debug(f"JSON fixing failed: {e}")
            return original

    def find_page_directories(self, input_path: Path, single_file: str = None, file_range: Tuple[int, int] = None, file_list: List[str] = None) -> Dict[str, List[Path]]:
        """Find all digibok markdown files and group by book ID"""
        books = defaultdict(list)
        
        logger.info(f"Scanning directory: {input_path}")
        
        # Look for digibok markdown files directly in the input path
        for md_file in input_path.glob("digibok*.md"):
            # Extract book info from filename
            file_stem = md_file.stem  # filename without extension
            book_id = self.get_book_id(file_stem)
            page_number = self.get_page_number(file_stem)
            
            # Apply filtering based on arguments
            should_include = True
            
            if single_file:
                # If single file specified, only include that specific file
                if md_file.name != single_file and file_stem != single_file:
                    should_include = False
            elif file_list:
                # If file list specified, only include files in the list
                if md_file.name not in file_list and file_stem not in file_list:
                    should_include = False
            elif file_range:
                # If range specified, only include files within that range
                start_page, end_page = file_range
                if not (start_page <= page_number <= end_page):
                    should_include = False
            
            if should_include:
                # Create a mock directory structure for compatibility
                file_info = {
                    "file_path": md_file,
                    "book_id": book_id,
                    "page_number": page_number
                }
                
                books[book_id].append(file_info)
                logger.debug(f"Found markdown file: {md_file.name} -> book: {book_id}")
        
        # Sort files by page number within each book
        for book_id in books:
            books[book_id].sort(key=lambda x: x["page_number"])
        
        logger.info(f"Found {len(books)} books with total {sum(len(files) for files in books.values())} files")
        for book_id, files in books.items():
            logger.info(f"  Book {book_id}: {len(files)} files")
        
        return books
    
    def process_input(self, input_path: str, output_dir: str, single_file: str = None, file_range: Tuple[int, int] = None, file_list: List[str] = None) -> Dict:
        """Process input directory containing markdown files"""
        input_path = Path(input_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if not input_path.exists():
            return {"error": f"Input path not found: {input_path}"}
        
        # Find markdown files grouped by book
        books = self.find_page_directories(input_path, single_file, file_range, file_list)
        
        if not books:
            filter_msg = ""
            if single_file:
                filter_msg = f" matching file '{single_file}'"
            elif file_list:
                filter_msg = f" matching files in list: {file_list}"
            elif file_range:
                filter_msg = f" in page range {file_range[0]}-{file_range[1]}"
            return {"error": f"No digibok*.md files found in {input_path}{filter_msg}"}
        
        # Load existing combined results if they exist
        combined_output = output_path / "all_books_names.json"
        existing_results = {}
        
        if combined_output.exists():
            try:
                with open(combined_output, 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
                logger.info(f"Loaded existing results with {len(existing_results.get('books', {}))} books")
            except Exception as e:
                logger.warning(f"Could not load existing results: {e}")
                existing_results = {}
        
        # Create new results structure
        results = {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "books_found": len(books),
            "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "filter_applied": {
                "single_file": single_file,
                "file_range": file_range,
                "file_list": file_list
            },
            "books": existing_results.get("books", {}).copy()  # Start with existing books
        }
        
        # Process new/updated books
        for book_id, file_infos in books.items():
            try:
                book_result = self.process_book(book_id, file_infos)
                results["books"][book_id] = book_result  # This will overwrite if book already exists
                
                # Save individual book result
                book_output_file = output_path / f"{book_id}_names.json"
                
                with open(book_output_file, 'w', encoding='utf-8') as f:
                    json.dump(book_result, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Found {len(book_result.get('biographical_entries', []))} names in {book_id}")
                
            except Exception as e:
                logger.error(f"Error processing book {book_id}: {e}")
                results["books"][book_id] = {"error": str(e)}
        
        # Update metadata
        results["books_found"] = len(results["books"])
        
        # Save combined results
        if combined_output.exists():
            # Create timestamped backup of old version
            time_id = time.strftime("%H%M%S")
            backup_output = output_path / f"all_books_names_{time_id}.json"
            
            # Copy old file to backup with timestamp
            import shutil
            shutil.copy2(combined_output, backup_output)
            logger.info(f"Created backup: {backup_output.name}")
        
        # Save updated combined results (overwriting the original)
        with open(combined_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated combined results saved to: {combined_output.name}")
        logger.info(f"Total books in combined file: {len(results['books'])}")
        
        return results
    
def main():
    vault = KeyVault()    
    api_key = vault.get_key("SDUGeminiAPI")
    #api_key = vault.get_key("AMDGeminiFlashKey")

    parser = argparse.ArgumentParser(description="Extract all biographical names from Norwegian biography pages using Google Gemini")
    parser.add_argument("input_path", help="Directory containing markdown files")
    parser.add_argument("output_dir", help="Directory to save results")
    parser.add_argument("--api-key", help="Google Gemini API key", 
                        default=api_key)
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    # New filtering options
    filter_group = parser.add_mutually_exclusive_group()
    filter_group.add_argument("--single-file", help="Process only a specific file (e.g., 'digibok_2007031501007_0103.md')")
    filter_group.add_argument("--range", nargs=2, type=int, metavar=('START', 'END'), 
                                help="Process files in page number range (e.g., --range 100 110)")
    filter_group.add_argument("--list", help="Process specific files from comma-separated list (e.g., 'file1.md,file2.md')")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Check for API key
    if not args.api_key:
        print("Error: Google Gemini API key is required!")
        print("Set it via:")
        print("1. Environment variable: set GEMINI_API_KEY=your-key-here")
        print("2. Command line: --api-key 'your-key-here'")
        return
    
    # Initialize associator
    try:
        associator = BookPortraitAssociator(api_key=args.api_key)
        
        logger.info(f"Processing input: {args.input_path}")
        logger.info(f"Using Google Gemini model: {associator.model}")
        
        # Prepare filter arguments
        single_file = args.single_file
        file_range = tuple(args.range) if args.range else None
        file_list = None
        
        if args.list:
            # Parse the comma-separated list and clean up whitespace
            file_list = [f.strip() for f in args.list.split(',') if f.strip()]
            logger.info(f"Filter: Processing file list: {file_list}")
        elif single_file:
            logger.info(f"Filter: Processing single file '{single_file}'")
        elif file_range:
            logger.info(f"Filter: Processing page range {file_range[0]}-{file_range[1]}")
        
        # Process the input
        results = associator.process_input(args.input_path, args.output_dir, single_file, file_range, file_list)
        
        # Print summary
        if "books" in results:
            print(f"\n{'='*60}")
            print("MULTI-BOOK NAME EXTRACTION SUMMARY")
            print(f"{'='*60}")
            print(f"Input path: {results['input_path']}")
            
            # Show filter information
            if results['filter_applied']['single_file']:
                print(f"Filter: Single file '{results['filter_applied']['single_file']}'")
            elif results['filter_applied']['file_list']:
                print(f"Filter: File list: {results['filter_applied']['file_list']}")
            elif results['filter_applied']['file_range']:
                print(f"Filter: Page range {results['filter_applied']['file_range'][0]}-{results['filter_applied']['file_range'][1]}")
            
            print(f"Books found: {results['books_found']}")
            
            total_entries = 0
            for book_id, book_result in results["books"].items():
                if "biographical_entries" in book_result:
                    entries_count = len(book_result.get('biographical_entries', []))
                    total_entries += entries_count
                    print(f"  {book_id}: {entries_count} biographical entries")
            
            print(f"\nTotal biographical entries found: {total_entries}")
            print(f"Results saved to: {args.output_dir}")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Failed to process: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()


# python gemini_all_names.py "d:\data\HCNC\norway\biographies\storage\AzureOCR\output_md_and_json" "D:\data\HCNC\norway\biographies\storage\AzureOCR\output_portrait_name_associations" --list "digibok_2007031501007_0067.md,digibok_2007031501007_0097.md,digibok_2007031501007_0148.md,digibok_2007031501007_0169.md,digibok_2007031501007_0190.md,digibok_2007031501007_0199.md,digibok_2007031501007_0216.md,digibok_2007031501007_0253.md,digibok_2007031501007_0315.md,digibok_2007031501007_0430.md,digibok_2007031501007_0465.md"

#python gemini_all_names.py "D:\data\HCNC\norway\biographies\storage\Dolphin\markdown" "D:\data\HCNC\norway\biographies\storage\Dolphin\output" 

#python gemini_all_names.py "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007" "D:\data\HCNC\norway\biographies\storage\MonkeyOCR\output"

# # First run - processes files 0067, 0097
# python gemini_all_names.py "path" "output" --list "file1.md,file2.md"
# # Creates: all_books_names.json (2 books)

# # Second run - processes files 0148, 0169  
# python gemini_all_names.py "path" "output" --list "file3.md,file4.md"
# # Creates: all_books_names_143052.json (backup of old 2 books)
# # Updates: all_books_names.json (now has 4 books total)

# #Process everything in the directory
# python gemini_all_names.py "D:\data\HCNC\norway\biographies\storage\Dolphin\markdown" "D:\data\HCNC\norway\biographies\storage\Dolphin\output"

# # Process a specific file
# python gemini_all_names.py "path" "output" --single-file "digibok_2007031501007_0103.md"

# # Process a range of files
# python gemini_all_names.py "path" "output" --range 100 110

# # Process a list of specific files
# python gemini_all_names.py "path" "output" --list "file1.md,file2.md"