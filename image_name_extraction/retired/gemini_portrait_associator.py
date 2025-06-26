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
        self.api_key = api_key or os.getenv("SDUGeminiAPI")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required. Set it as environment variable or pass as parameter.")
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash-lite-preview-06-17"
        
    # ...existing code... (get_page_number, get_book_id, find_page_directories, load_page_content, load_book_content, extract_json_from_response, fix_json_string methods remain unchanged)
    
    def analyze_book_portraits(self, book_id: str, pages: List[Dict]) -> List[Dict]:
        """Use Google Gemini to analyze figure placeholders and names across all pages with cross-page awareness"""
        
        # Prepare the content for LLM analysis with explicit cross-page context
        prompt_content = f"""You are analyzing a Norwegian biographical reference work that spans multiple pages. 
The book ID is: {book_id}

IMPORTANT: Biographical entries sometime span across consecutive pages. Common patterns:
1. A person's name (SURNAME, Given names) appears at the END of page N
2. Their portrait placeholder and detailed biographical information appears at the BEGINNING of page N+1
3. Some entries are split where basic info is on one page and detailed career/family info continues on the next

Each page contains biographical entries with the format:
SURNAME, Given names, profession, biographical details...

Figure placeholders appear as <figure></figure> tags in the markdown - these represent portrait locations.

PAGES TO ANALYZE (in sequential order):
"""
        
        for i, page in enumerate(pages):
            prompt_content += f"""
--- PAGE {page['page_number']} (Directory: {page['page_name']}) ---

Markdown content:
{page['content']}

"""
            
            # Add context about the next page for cross-page analysis
            if i < len(pages) - 1:
                next_page = pages[i + 1]
                # Show first 500 characters of next page to help with cross-page associations
                next_preview = next_page['content'][:500] + "..." if len(next_page['content']) > 500 else next_page['content']
                prompt_content += f"""
[PREVIEW OF NEXT PAGE {next_page['page_number']} - First 500 characters:]
{next_preview}

"""        
        prompt_content += """
TASK:
Analyze ALL pages together to associate each portrait/image with the person it most likely depicts.

IMPORTANT (strict pairing rules, in priority order):
1.  **Exact syntax** – Every portrait appears with an image tag `<figure></figure>`. Search **only** for this pattern.
2.  **Labelling the portraits** – All portraits are identified by `<figure></figure>`. Please enumerate them by their appearance, such that the figure appearing first is labelled Figure 1, the figure appearing second is labelled Figure 2, etc.
3.  **Immediate-name rule (highest certainty)** – If the image tag is followed (same line or next non-empty line) by a name whose LASTNAME is in ALL-CAPS, **always pair this image with that name**. Treat this as a 100% match unless another image intervenes. IMPORTANT: If the name is not in ALL-CAPS, do NOT use it for pairing.
4.  **Paragraph-embedded rule** – If the image tag sits inside a prose paragraph that is clearly describing a person, pair the image with that individual rather than the next standalone name heading.
5.  **Page-start rule** – If a markdown page *begins* with an image tag, set the `associated_person` to \"unknown\". This rule is overridden by the **Immediate-name rule**; if a name in ALL-CAPS immediately follows the image, use that name instead.
6.  **Conflict handling** – If two images appear back-to-back with no intervening name, or if one name plausibly maps to multiple images, list all possibilities but set `associated_person` to null and flag for manual review.

CRITICAL: Ensure your response is valid JSON format. Escape all quotes and newlines properly in string values.

For each image found (both referenced in markdown and available in directories), determine:
- Which person it most likely depicts
- Whether this is a cross-page association (name on page N, portrait on page N+1)
- Your confidence level based on proximity and context

Respond with ONLY a valid JSON array (no other text) and only for those persons that can be associated with a portrait. The JSON should have the following structure:
[
  {
    \"Portrait associated\": \"Figure 1\",
    \"referenced_in_markdown\": true or false,
    \"associated_person\": \"SURNAME, Given Names\",
    \"portrait_page\": page_number,
    \"person_page\": page_number,
    \"person_directory\": \"page_directory_name\",
    \"confidence\": 0.92,
    \"is_cross_page\": true or false,
    \"cross_page_type\": \"same_page\",
    \"reasoning\": \"Brief explanation without quotes or newlines\",
    \"context_evidence\": \"Relevant text snippet without quotes or newlines\"
  }
]

IMPORTANT (output hygiene):
- Use only double quotes for JSON strings
- Do not include newlines or unescaped quotes in string values
- Replace any quotes in text with single quotes or apostrophes
- Keep reasoning and context_evidence brief and on single lines
- If no association can be made, set `associated_person` to null
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
            print("Response received!",response_text)
            logger.debug(f"Raw Gemini Response for {book_id}: {response_text[:500]}...")
            
            # Save raw response for debugging
            debug_file = Path("debug_response.txt")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"Book: {book_id}\n")
                f.write(f"Response:\n{response_text}\n")
            
            # Parse JSON response directly
            associations = json.loads(response_text)
            
            if associations and isinstance(associations, list):
                # Add book ID to each association
                for assoc in associations:
                    assoc["book_id"] = book_id
                
                logger.info(f"Successfully extracted {len(associations)} associations")
                return associations
            else:
                logger.warning(f"No valid associations in response for {book_id}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for book {book_id}: {e}")
        except Exception as e:
            logger.error(f"Error in Gemini analysis for book {book_id}: {e}")
        
        return []
    
    def process_book(self, book_id: str, page_dirs: List[Path]) -> Dict:
        """Process a single book with cross-page awareness - analyze figure placeholders"""
        logger.info(f"Processing book: {book_id}")
        
        # Load all pages
        pages = self.load_book_content(page_dirs)
        
        if not pages:
            return {
                "book_id": book_id,
                "error": "No pages could be loaded",
                "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # Always analyze with Gemini - let Gemini find figure placeholders
        logger.info(f"Analyzing {len(pages)} pages to associate figure placeholders with names")
        
        # Analyze portraits across all pages
        associations = self.analyze_book_portraits(book_id, pages)
        
        # Compile results with cross-page statistics
        cross_page_stats = {
            "total_cross_page": len([a for a in associations if a.get("is_cross_page", False)]),
            "name_previous_page": len([a for a in associations if a.get("cross_page_type") == "name_previous_page"]),
            "continuation_entries": len([a for a in associations if a.get("cross_page_type") == "continuation"]),
            "same_page_entries": len([a for a in associations if a.get("cross_page_type") == "same_page"])
        }
        
        result = {
            "book_id": book_id,
            "pages_processed": len(pages),
            "page_range": f"{min(p['page_number'] for p in pages)}-{max(p['page_number'] for p in pages)}" if pages else "0-0",
            "page_directories": [p['page_name'] for p in pages],
            "total_figure_placeholders": len(associations),
            "associations": associations,
            "summary": {
                "total_associations": len(associations),
                "confident_associations": len([a for a in associations if a.get("confidence", 0) > 0.6]),
                "cross_page_associations": cross_page_stats["total_cross_page"],
                "cross_page_breakdown": cross_page_stats,
                "unassociated_figures": len([a for a in associations if not a.get("associated_person")]),
                "success_rate": f"{(len([a for a in associations if a.get('associated_person')])/len(associations)*100):.1f}%" if associations else "0%"
            },
            "processing_info": {
                "model_used": self.model,
                "provider": "Google Gemini",
                "cross_page_analysis": True,
                "figure_placeholder_analysis": True,
                "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        logger.info(f"Book {book_id}: {len(associations)} figure associations found ({cross_page_stats['total_cross_page']} cross-page)")
        return result
    
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
        """Find all page directories and group by book ID"""
        books = defaultdict(list)
        
        logger.info(f"Scanning directory: {input_path}")
        
        # Look for page directories directly under input path
        for item in input_path.iterdir():
            if item.is_dir():
                # Check different markdown file patterns
                possible_md_files = [
                    item / f"{item.name}.md",           # Original pattern
                    item / f"{item.name}_azure.md",    # Azure OCR pattern
                ]
                
                md_file_found = any(md_file.exists() for md_file in possible_md_files)
                
                if md_file_found:
                    book_id = self.get_book_id(item.name)
                    books[book_id].append(item)
                    logger.debug(f"Found page directory: {item.name} -> book: {book_id}")
        
        # Sort pages by page number within each book
        for book_id in books:
            books[book_id].sort(key=lambda x: self.get_page_number(x.name))
        
        logger.info(f"Found {len(books)} books with total {sum(len(pages) for pages in books.values())} pages")
        for book_id, pages in books.items():
            logger.info(f"  Book {book_id}: {len(pages)} pages")
        
        return books

    def load_page_content(self, page_dir: Path) -> Optional[Dict]:
        """Load content from a single page directory - markdown only"""
        page_name = page_dir.name
        
        # Try different markdown file naming patterns
        possible_md_files = [
            page_dir / f"{page_name}.md",           # Original pattern
            page_dir / f"{page_name}_azure.md",    # Azure OCR pattern
        ]
        
        md_file = None
        for possible_file in possible_md_files:
            if possible_file.exists():
                md_file = possible_file
                break
        
        if not md_file:
            logger.warning(f"Markdown file not found. Tried: {[str(f) for f in possible_md_files]}")
            return None
        
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
                book_output_file = output_path / f"{book_id}_portrait_associations.json"
                with open(book_output_file, 'w', encoding='utf-8') as f:
                    json.dump(book_result, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Saved results for {book_id} to {book_output_file}")
                
                # Brief pause between books
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing book {book_id}: {e}")
                results["books"][book_id] = {
                    "error": str(e),
                    "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
        
        # Save combined results
        combined_output = output_path / "all_books_portrait_associations.json"
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