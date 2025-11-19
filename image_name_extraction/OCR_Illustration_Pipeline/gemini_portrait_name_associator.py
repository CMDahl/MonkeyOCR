#!/usr/bin/env python3
"""
Norwegian Biography Portrait Associator - Google Gemini Version
Associates portrait images with person names using a single markdown file only.
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from google import genai
from google.genai import types
import argparse
import logging
import time
from collections import defaultdict
import sys

# Adjust path to find agents module
# Assuming structure: MonkeyOCR/image_name_extraction/OCR_Illustration_Pipeline/this_script.py
# And agents is in MonkeyOCR/agents
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from agents.key_vault import KeyVault

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BookPortraitAssociator:
    def __init__(self, api_key: str = None):
        # Google Gemini configuration
        self.api_key = api_key or os.getenv("AMDGeminiFlashKey")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required. Set it as environment variable or pass as parameter.")
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash"
    
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
    
    def find_page_directories(self, input_path: Path, single_file: str = None, file_range: Tuple[int, int] = None, file_list: List[str] = None, start_page: str = None, end_page: str = None) -> Dict[str, List[Path]]:
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
                start_page_num, end_page_num = file_range
                if not (start_page_num <= page_number <= end_page_num):
                    should_include = False
            elif start_page or end_page:
                # If start/end specified, filter by filename suffix
                page_suffix = f"{page_number:04d}"  # Convert to 4-digit format (e.g., 0057)
                
                if start_page and page_suffix < start_page:
                    should_include = False
                if end_page and page_suffix > end_page:
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
        # Save the original for debugging
        original = json_str
        
        try:
            # Replace newlines within strings with \\n
            json_str = re.sub(r'(?<=: ")(.*?)(?=")', lambda m: m.group(1).replace('\n', '\\n').replace('\r', '\\r'), json_str)
            
            return json_str
            
        except Exception as e:
            logger.debug(f"JSON fixing failed: {e}")
            return original
        
    def analyze_book_portraits(self, book_id: str, pages: List[Dict]) -> List[Dict]:
        """Use Google Gemini to identify all biographical names in sequential order"""
        
        # Combine all page content
        all_content = ""
        for page in pages:
            all_content += f"\n--- PAGE {page['page_number']} ---\n"
            all_content += page['content']
        
        # Use triple quotes and avoid f-string formatting for the JSON template
        prompt_content = f"""You are analyzing a Norwegian biography. Your task is to associate portrait images with the person they depict based on the provided markdown page.
The book ID is: {book_id}

IMPORTANT: Common patterns:

1. Each page contains biographical entries with the format:
SURNAME, Given names, profession, biographical details.
2. Biographical entries may span multiple pages. Text in the beginning of the page belongs to a person whose name appeared last on the previous page. Please ignore this text. 
3. Portraits/images are tagged in HTML format as: <img src="imgs/filename.jpg" alt="Image" width="18%" /> inside a div tag.

TASK:
Analyze the markdown pages and associate each portrait/image with the person it most likely depicts.

IMPORTANT (strict pairing rules, in priority order):
1. **Exact syntax** – Every portrait appears as HTML: <div style="text-align: center;"><img src="imgs/FILENAME.jpg" alt="Image" width="18%" /></div>. Search for this HTML pattern. The filename is the unique identifier (e.g., img_in_image_box_173_357_600_930.jpg).
2. **Immediate-name rule (highest certainty)** – If the image tag is immediately followed by a name whose LASTNAME is in ALL-CAPS, **always pair this image with that name**. Treat this as a 100% match unless another image intervenes. IMPORTANT: If the name is not in ALL-CAPS, do NOT use it for pairing.
3. **Paragraph-embedded rule** – If the image tag sits inside a prose paragraph that is clearly describing a person, pair the image with that individual rather than the next standalone name heading.  
4. **Page-start rule (cross-page)** – When a markdown page *begins* with an image tag, assume the portrait belongs to the person whose name appeared last on the *previous* page. Do not attempt to make an association. The exception is if the **Immediate-name rule (highest certainty)** applies, in which case use that name instead. 

CRITICAL: Ensure your response is valid JSON format. Escape all quotes and newlines properly in string values.

For each image found (both referenced in markdown and available), determine:
- Which person it most likely depicts
- Your confidence level based on proximity and context

Respond with ONLY a valid JSON array (no other text):""" + """
[
  {
    "filename": "actual_image_filename.jpg",
    "portrait": "figure.id",
    "associated_person": "SURNAME, Given Names",
    "confidence": 0.92,
    "reasoning": "Brief explanation without quotes or newlines",
    "context_evidence": "Relevant text snippet without quotes or newlines"
  }
]

IMPORTANT (output hygiene):
- Use only double quotes for JSON strings
- Do not include newlines or unescaped quotes in string values
- Replace any quotes in text with single quotes or apostrophes
- Keep reasoning and context_evidence brief and on single lines
- If no association can be made, set associated_person to null

The markdown content to analyze:

""" + all_content

        # Temperature options for retry attempts
        temperature_options = [0.01, 0.01, 0.1, 0.2]
        
        # Rest of the method remains the same...
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
    
    def process_input(self, input_path: str, output_dir: str, single_file: str = None, file_range: Tuple[int, int] = None, file_list: List[str] = None, start_page: str = None, end_page: str = None) -> Dict:
        """Process input directory containing markdown files"""
        input_path = Path(input_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if not input_path.exists():
            return {"error": f"Input path not found: {input_path}"}
        
        # Find markdown files grouped by book
        books = self.find_page_directories(input_path, single_file, file_range, file_list, start_page, end_page)
        
        if not books:
            filter_msg = ""
            if single_file:
                filter_msg = f" matching file '{single_file}'"
            elif file_list:
                filter_msg = f" matching files in list: {file_list}"
            elif file_range:
                filter_msg = f" in page range {file_range[0]}-{file_range[1]}"
            elif start_page or end_page:
                filter_msg = f" in filename range {start_page or 'start'}-{end_page or 'end'}"
            return {"error": f"No digibok*.md files found in {input_path}{filter_msg}"}
        
        results = {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "books_found": len(books),
            "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "filter_applied": {
                "single_file": single_file,
                "file_range": file_range,
                "file_list": file_list,
                "start_page": start_page,
                "end_page": end_page
            },
            "books": {}
        }
        
        for book_id, file_infos in books.items():
            try:
                book_result = self.process_book(book_id, file_infos)
                results["books"][book_id] = book_result
                
                # Save individual book result with timestamp if file exists
                book_output_file = output_path / f"{book_id}_portrait_associations.json"
                
                with open(book_output_file, 'w', encoding='utf-8') as f:
                    json.dump(book_result, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Found {len(book_result.get('biographical_entries', []))} names in {book_id}")
                
            except Exception as e:
                logger.error(f"Error processing book {book_id}: {e}")
                results["books"][book_id] = {"error": str(e)}
        
        # Save combined results with timestamp if file exists
        combined_output = output_path / "all_books_portrait_associations.json"
        if combined_output.exists():
            # Add short timestamp to avoid overwriting
            time_id = time.strftime("%H%M%S")  # HHMMSS format (e.g., 143052 for 14:30:52)
            combined_output = output_path / f"all_books_portrait_associations_{time_id}.json"
            logger.info(f"File exists, saving as: {combined_output.name}")
        
        with open(combined_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
def main():
    vault = KeyVault()    
    api_key = vault.get_key("SDUGeminiAPI")

    parser = argparse.ArgumentParser(description="Associate portraits with names in Norwegian biography pages using Google Gemini")
    parser.add_argument("input_path", help="Directory containing page directories")
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
    
    # Add the new start/end options
    parser.add_argument("--start", help="Start from filename suffix (e.g., '0057' for digibok_2007031501007_0057.md)")
    parser.add_argument("--end", help="End at filename suffix (e.g., '0494' for digibok_2007031501007_0494.md)")
    
    args = parser.parse_args()
    
    # Validate start/end arguments
    if (args.start or args.end) and (args.single_file or args.range or args.list):
        print("Error: --start/--end cannot be used with --single-file, --range, or --list")
        return
    
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
        start_page = args.start
        end_page = args.end
        
        if args.list:
            # Parse the comma-separated list and clean up whitespace
            file_list = [f.strip() for f in args.list.split(',') if f.strip()]
            logger.info(f"Filter: Processing file list: {file_list}")
        elif single_file:
            logger.info(f"Filter: Processing single file '{single_file}'")
        elif file_range:
            logger.info(f"Filter: Processing page range {file_range[0]}-{file_range[1]}")
        elif start_page or end_page:
            logger.info(f"Filter: Processing filename range {start_page or 'start'}-{end_page or 'end'}")
        
        # Process the input
        results = associator.process_input(args.input_path, args.output_dir, single_file, file_range, file_list, start_page, end_page)
        
        # Print summary
        if "books" in results:
            print(f"\n{'='*60}")
            print("MULTI-BOOK PORTRAIT ASSOCIATION SUMMARY")
            print(f"{'='*60}")
            print(f"Input path: {results['input_path']}")
            
            # Show filter information
            if results['filter_applied']['single_file']:
                print(f"Filter: Single file '{results['filter_applied']['single_file']}'")
            elif results['filter_applied']['file_list']:
                print(f"Filter: File list: {results['filter_applied']['file_list']}")
            elif results['filter_applied']['file_range']:
                print(f"Filter: Page range {results['filter_applied']['file_range'][0]}-{results['filter_applied']['file_range'][1]}")
            elif results['filter_applied']['start_page'] or results['filter_applied']['end_page']:
                start = results['filter_applied']['start_page'] or 'start'
                end = results['filter_applied']['end_page'] or 'end'
                print(f"Filter: Filename range {start}-{end}")
            
            print(f"Books found: {results['books_found']}")
            
            for book_id, book_result in results["books"].items():
                if "biographical_entries" in book_result:
                    entries_count = len(book_result.get('biographical_entries', []))
                    print(f"  {book_id}: {entries_count} entries")
            
            print(f"Results saved to: {args.output_dir}")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Failed to process: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
