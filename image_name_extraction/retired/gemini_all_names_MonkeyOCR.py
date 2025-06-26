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

class BookPortraitAssociator:
    def __init__(self, api_key: str = None):
        # Google Gemini configuration
        #self.api_key = api_key or os.getenv("SDUGeminiAPI")
        self.api_key = api_key or os.getenv("AMDGeminiFlashKey")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required. Set it as environment variable or pass as parameter.")
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash-lite-preview-06-17"
        
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
    Identify all biographical entries in the text. Look for names where the SURNAME is in ALL-CAPS followed by given names, like "ALGER, Bjørn" or "ALNÆS, Ingeborg". These indicate biographical entries.
    
    Return all names in the exact order they appear in the text.
    
    Respond with ONLY a valid JSON array:
    [
      {{
        "person_name": "SURNAME, Given Names",
      }}
    ]
    """
    
        try:
            # Prepare content for Gemini
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt_content),
                    ],
                ),
            ]
            
            # Configure generation
            generate_content_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=2996,
                ),
                response_mime_type="application/json",
            )
            
            # Generate response using streaming
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                response_text += chunk.text
            

            
            biographical_entries = json.loads(response_text)
            
            # Add book ID to each entry
            for entry in biographical_entries:
                entry["book_id"] = book_id
            
            return biographical_entries
            
        except Exception as e:
            logger.error(f"Error extracting names for {book_id}: {e}")
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
        """Find all page directories and group by book ID - only digibook files"""
        books = defaultdict(list)
        
        logger.info(f"Scanning directory: {input_path}")
        
        # Look for page directories directly under input path
        for item in input_path.iterdir():
            if item.is_dir():
                # Check for markdown files starting with "digibook"
                possible_md_files = []
                
                # Look for any .md files in the directory that start with "digibook"
                for md_file in item.glob("digibok*.md"):
                    possible_md_files.append(md_file)
                
                if possible_md_files:
                    book_id = self.get_book_id(item.name)
                    books[book_id].append(item)
                    logger.debug(f"Found page directory: {item.name} -> bok: {book_id} (found {len(possible_md_files)} digibok files)")
        
        # Sort pages by page number within each book
        for book_id in books:
            books[book_id].sort(key=lambda x: self.get_page_number(x.name))
        
        logger.info(f"Found {len(books)} books with total {sum(len(pages) for pages in books.values())} pages")
        for book_id, pages in books.items():
            logger.info(f"  Book {book_id}: {len(pages)} pages")
        
        return books

    def load_page_content(self, page_dir: Path) -> Optional[Dict]:
        """Load content from a single page directory - markdown only (digibok files)"""
        page_name = page_dir.name
        
        # Look for markdown files starting with "digibook"
        md_files = list(page_dir.glob("digibok*.md"))
        
        if not md_files:
            logger.warning(f"No digibok*.md files found in {page_dir}")
            return None
        
        # Use the first digibook file found (there should typically be only one)
        md_file = md_files[0]
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            page_info = {
                "page_directory": str(page_dir),
                "page_name": page_name,
                "page_number": self.get_page_number(page_name),
                "md_file": str(md_file),
                "content": content
            }
            
            return page_info
            
        except Exception as e:
            logger.error(f"Error loading page {page_dir}: {e}")
            return None
    
    def load_book_content(self, page_dirs: List[Path]) -> List[Dict]:
        """Load content from all pages in the book"""
        pages = []
        
        logger.info(f"Loading content from {len(page_dirs)} pages")
        
        for page_dir in page_dirs:
            page_info = self.load_page_content(page_dir)
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

    def process_input(self, input_path: str, output_dir: str) -> Dict:
        """Process input directory containing page directories"""
        input_path = Path(input_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if not input_path.exists():
            return {"error": f"Input path not found: {input_path}"}
        
        # Find page directories grouped by book
        books = self.find_page_directories(input_path)
        
        if not books:
            return {"error": f"No page directories found in {input_path}"}
        
        results = {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "books_found": len(books),
            "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "books": {}
        }
        
        for book_id, page_dirs in books.items():
            try:
                book_result = self.process_book(book_id, page_dirs)
                results["books"][book_id] = book_result
                
                # Save individual book result
                book_output_file = output_path / f"{book_id}_names.json"
                with open(book_output_file, 'w', encoding='utf-8') as f:
                    json.dump(book_result, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Found {len(book_result.get('biographical_entries', []))} names in {book_id}")
                
            except Exception as e:
                logger.error(f"Error processing book {book_id}: {e}")
                results["books"][book_id] = {"error": str(e)}
        
        # Save combined results
        combined_output = output_path / "all_books_names.json"
        with open(combined_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
def main():
    vault = KeyVault()    
    #api_key = vault.get_key("SDUGeminiAPI")
    api_key = vault.get_key("AMDGeminiFlashKey")

    parser = argparse.ArgumentParser(description="Associate portraits with names in Norwegian biography pages using Google Gemini")
    parser.add_argument("input_path", help="Directory containing page directories")
    parser.add_argument("output_dir", help="Directory to save results")
    parser.add_argument("--api-key", help="Google Gemini API key", 
                       default=api_key)
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
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
        
        # Process the input
        results = associator.process_input(args.input_path, args.output_dir)
        
        # Print summary
        if "books" in results:
            print(f"\n{'='*60}")
            print("MULTI-BOOK PORTRAIT ASSOCIATION SUMMARY")
            print(f"{'='*60}")
            print(f"Input path: {results['input_path']}")
            print(f"Books found: {results['books_found']}")
            
            total_images = 0
            total_associations = 0
            total_cross_page = 0
            
            for book_id, book_result in results["books"].items():
                if "summary" in book_result:
                    total_images += book_result.get("total_images", 0)
                    total_associations += book_result["summary"]["total_associations"]
                    total_cross_page += book_result["summary"]["cross_page_associations"]
                    print(f"  {book_id}: {book_result['summary']['total_associations']} associations ({book_result['summary']['cross_page_associations']} cross-page)")
            
            print(f"\nOverall totals:")
            print(f"  Total images: {total_images}")
            print(f"  Total associations: {total_associations}")
            print(f"  Cross-page associations: {total_cross_page}")
            print(f"  Success rate: {(total_associations/total_images*100):.1f}%" if total_images > 0 else "0%")
            print(f"Results saved to: {args.output_dir}")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Failed to process: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

#python gemini_all_names_Dolphin.py "D:\data\HCNC\norway\biographies\storage\Dolphin\markdown" "D:\data\HCNC\norway\biographies\storage\Dolphin\output" 