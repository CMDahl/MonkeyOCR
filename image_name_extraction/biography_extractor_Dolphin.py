#!/usr/bin/env python3
"""
Norwegian Biography Information Extractor - Google Gemini Version
Extracts structured biographical information from markdown text chunks using Gemini.
"""

import os
import sys
import json
import pandas as pd
import logging
import time
from pathlib import Path
from google import genai
from google.genai import types

import re

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from agents.key_vault import KeyVault

# Set up logging at the top of your script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'd:\data\HCNC\norway\biographies\storage\Dolphin\logs\biography_extractor_Dolphin_failed_rows.log'),  # Log to file
        logging.StreamHandler()  # Also log to console
    ]
)
logger = logging.getLogger(__name__)

# TBA model structure
tba_model = {
    "name": str,
    "birth_date": str,
    "birth_place": str,
    "death_date": str,
    "father_job": str,
    "father_name": str,
    "mother_name": str,
    "jobs": [
        {
            "title": str,
            "location": str,
            "years": str
        }
    ],
    "educations": [
        {
            "title": str,
            "institution": str,
            "year": str
        }
    ],
    "stays_abroad": [
        {
            "country": str,
            "years": str,
            "reason": str
        }
    ],
    "spouses": [
        {
            "name": str,
            "birth_date": str,
            "birth_place": str
        }
    ],
    "children": [
        {
            "name": str,
            "birth_date": str,
            "birth_place": str
        }
    ]
}

# TBA input instructions
tba_input = """
The structure of the text is generally: 
 - name of main person 
 - occupation
 - birth date 
 - birth place
 - optionally death date
 - father's job
 - father's name
 - father's birth and death date (optional)
 - mother's name
 - mother's birth date and death date (optional)
 - spouses including occupation (optional), birth date and birth place
 - The father of the spouse including name and occupation
 - The children of main person including name, birth date (always given), and birth place (optional)
 - Educations including education degree/name, institution, and years of enrollment or completion. This part begins with a three to four character short form of a degree which always include a "/".
 - Jobs including title, location and/or company, and years
 
The shift from educations to jobs is often difficult to identify. Put the entries under jobs if there is any doubt whether the entry is an education or job.

Sometimes there can be entries for figures, like ![Figure](figures/digibok_2007031501007_0057_figure_001.png). Just ignore this part and do not include it in the biography.
"""

class BiographyExtractor:
    def __init__(self, api_key: str = None):
        # Google Gemini configuration
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            # Try to get from KeyVault
            try:
                vault = KeyVault()
                #self.api_key = vault.get_key("AMDGeminiFlashKey")
                self.api_key = vault.get_key("SDUGeminiAPI")
            except Exception as e:
                raise ValueError("GEMINI_API_KEY is required. Set it as environment variable or pass as parameter.")
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        #self.model = "gemini-2.5-flash-lite-preview-06-17"
        self.model = "gemini-2.5-flash"
        
    def safe_json_parse(self, response_text, person_name):
        """Safely parse JSON with error recovery"""
        try:
            # Clean the response
            response_text = response_text.strip()
            
            # Find JSON boundaries
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response_text[start:end]
                
                # Remove trailing commas (common issue)
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found")
                
        except Exception as e:
            print(f"⚠️  JSON error for {person_name}: {e}")
            logger.error(f"JSON parsing failed for {person_name}: {e}")
            return None

    def extract_biography(self, name: str, markdown_chunk: str) -> dict:
        """Extract structured biographical information from markdown chunk"""
    
        prompt_content = f"""You are extracting structured biographical information from Norwegian biographical text.

        PERSON NAME: {name}

        INSTRUCTIONS:
        {tba_input}

        BIOGRAPHICAL TEXT:
        {markdown_chunk}

        CRITICAL JSON FORMATTING RULES:
        - Return ONLY valid JSON, no additional text before or after
        - Use double quotes for ALL strings
        - Do NOT include newlines, line breaks, or unescaped quotes within string values
        - Replace any quotes in text with single quotes or remove them
        - If a field is missing, use empty string "" or empty array []
        - Ensure all objects and arrays are properly closed with matching brackets
        - Do not add comments or explanations

        TASK:
        Extract biographical information for "{name}" and return it in this EXACT JSON structure:

        {{
            "name": "{name}",
            "birth_date": "YYYY-MM-DD or partial date or empty string",
            "birth_place": "place name or empty string",
            "death_date": "YYYY-MM-DD or partial date or empty string",
            "father_job": "occupation or empty string",
            "father_name": "full name or empty string",
            "mother_name": "full name or empty string",
            "jobs": [
                {{
                    "title": "job title",
                    "location": "workplace/company/location",
                    "years": "year range or single year"
                }}
            ],
            "educations": [
                {{
                    "title": "degree/education name",
                    "institution": "school/university name",
                    "year": "year or year range"
                }}
            ],
            "stays_abroad": [
                {{
                    "country": "country name",
                    "years": "year or year range",
                    "reason": "purpose of stay"
                }}
            ],
            "spouses": [
                {{
                    "name": "spouse full name",
                    "birth_date": "birth date if available",
                    "birth_place": "birth place if available"
                }}
            ],
            "children": [
                {{
                    "name": "child full name",
                    "birth_date": "birth date",
                    "birth_place": "birth place if available"
                }}
            ]
        }}

        Return ONLY the JSON object above with filled values. No other text.
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
            
            logger.debug(f"Raw Gemini Response for {name}: {response_text[:200]}...")
            
            # Use safe JSON parsing instead of direct json.loads
            biography_data = self.safe_json_parse(response_text, name)
            
            if biography_data is None:
                print(f"⚠️  Failed to parse JSON for {name}, using empty biography")
                logger.warning(f"Using empty biography for {name} due to JSON parsing failure")
                return self._get_empty_biography(name)
            
            print(f"✅ Successfully extracted biography for {name}")
            logger.info(f"Successfully extracted biography for {name}")
            return biography_data
            
        except Exception as e:
            error_msg = f"Error extracting biography for {name}: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            return self._get_empty_biography(name)

      
    def _get_empty_biography(self, name: str) -> dict:
        """Return empty biography structure"""
        return {
            "name": name,
            "birth_date": "",
            "birth_place": "",
            "death_date": "",
            "father_job": "",
            "father_name": "",
            "mother_name": "",
            "jobs": [],
            "educations": [],
            "stays_abroad": [],
            "spouses": [],
            "children": []
        }
    
    def process_csv(self, csv_file_path: str, output_file_path: str) -> None:
        """Process the entire CSV file and extract biographies"""
        
        # Load the CSV file
        df = pd.read_csv(csv_file_path)

        # TEMPORARY: Limit to first 5 rows for testing
        #df = df.head(5)
        #print("🧪 TESTING MODE: Processing only first 5 rows")
        #logger.info("TESTING MODE: Processing only first 5 rows")
        
        print(f"📊 Processing {len(df)} entries from {csv_file_path}")
        logger.info(f"Processing {len(df)} entries from {csv_file_path}")
        
        # Check required columns
        if 'name' not in df.columns or 'markdown_chunk' not in df.columns:
            error_msg = "CSV must contain 'name' and 'markdown_chunk' columns"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Add new column for biographical JSON
        df['biography_json'] = ''
        
        # Process each row
        biographies = []
        failed_extractions = 0
        
        for index, row in df.iterrows():
            name = row['name']
            markdown_chunk = str(row['markdown_chunk'])
            
            # Skip if markdown chunk is empty or too short
            if not markdown_chunk or len(markdown_chunk.strip()) < 50:
                warning_msg = f"Skipping {name}: markdown chunk too short or empty"
                print(f"⚠️  {warning_msg}")
                logger.warning(warning_msg)
                biography = self._get_empty_biography(name)
                biographies.append(biography)
                failed_extractions += 1
                df.at[index, 'biography_json'] = json.dumps(biography, ensure_ascii=False)
                continue
            
            print(f"🔄 Processing {index + 1}/{len(df)}: {name}")
            logger.info(f"Processing {index + 1}/{len(df)}: {name}")
            
            try:
                biography = self.extract_biography(name, markdown_chunk)
                biographies.append(biography)
                
                # Add JSON to DataFrame
                df.at[index, 'biography_json'] = json.dumps(biography, ensure_ascii=False)
                
                # Add a small delay to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"Failed to process {name}: {e}"
                print(f"❌ {error_msg}")
                logger.error(error_msg)
                biography = self._get_empty_biography(name)
                biographies.append(biography)
                failed_extractions += 1
                df.at[index, 'biography_json'] = json.dumps(biography, ensure_ascii=False)
        
        # Save enhanced CSV file
        enhanced_csv_path = csv_file_path.replace('.csv', '_with_biographies.csv')
        df.to_csv(enhanced_csv_path, index=False, encoding='utf-8')
        print(f"💾 Enhanced CSV saved to: {enhanced_csv_path}")
        logger.info(f"Enhanced CSV saved to: {enhanced_csv_path}")
        
        # Save results JSON (keep original functionality)
        output_data = {
            "extraction_info": {
                "total_entries": len(df),
                "successful_extractions": len(biographies) - failed_extractions,
                "failed_extractions": failed_extractions,
                "model_used": self.model,
                "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "enhanced_csv_path": enhanced_csv_path
            },
            "biographies": biographies
        }
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Extraction complete!")
        print(f"📈 Total entries: {len(df)}")
        print(f"✅ Successful extractions: {len(biographies) - failed_extractions}")
        print(f"❌ Failed extractions: {failed_extractions}")
        print(f"📊 Success rate: {((len(biographies) - failed_extractions)/len(df)*100):.1f}%")
        print(f"💾 JSON results saved to: {output_file_path}")
        
        logger.info(f"Extraction complete!")
        logger.info(f"Total entries: {len(df)}")
        logger.info(f"Successful extractions: {len(biographies) - failed_extractions}")
        logger.info(f"Failed extractions: {failed_extractions}")
        logger.info(f"Success rate: {((len(biographies) - failed_extractions)/len(df)*100):.1f}%")
        logger.info(f"JSON results saved to: {output_file_path}")
        logger.info(f"Enhanced CSV saved to: {enhanced_csv_path}")
        
        return output_data

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract biographical information from CSV using Gemini")
    parser.add_argument("csv_file", help="Path to CSV file with names and markdown chunks")
    parser.add_argument("output_file", help="Path to output JSON file")
    parser.add_argument("--api-key", help="Google Gemini API key", 
                       default=os.getenv("GEMINI_API_KEY"))
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Initialize extractor
    try:
        extractor = BiographyExtractor(api_key=args.api_key)
        
        logger.info(f"Processing CSV: {args.csv_file}")
        logger.info(f"Using Gemini model: {extractor.model}")
        
        # Process the CSV
        results = extractor.process_csv(args.csv_file, args.output_file)
        
        print(f"\n{'='*60}")
        print("BIOGRAPHY EXTRACTION SUMMARY")
        print(f"{'='*60}")
        print(f"Input file: {args.csv_file}")
        print(f"Output file: {args.output_file}")
        print(f"Total entries: {results['extraction_info']['total_entries']}")
        print(f"Successful extractions: {results['extraction_info']['successful_extractions']}")
        print(f"Failed extractions: {results['extraction_info']['failed_extractions']}")
        print(f"Success rate: {(results['extraction_info']['successful_extractions']/results['extraction_info']['total_entries']*100):.1f}%")
        
    except Exception as e:
        logger.error(f"Failed to process: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    # Example usage if run directly
    if len(sys.argv) == 1:
        # Default paths for testing
        csv_file = r"D:\data\HCNC\norway\biographies\storage\Dolphin\output\extracted_names_Dolphin_with_chunks.csv"
        output_file = r"D:\data\HCNC\norway\biographies\storage\Dolphin\output\biographical_data.json"
        
        extractor = BiographyExtractor()
        extractor.process_csv(csv_file, output_file)
    else:
        main()


# Basic usage
#python biography_extractor_Dolphin.py "D:\data\HCNC\norway\biographies\storage\Dolphin\output\extracted_all_names_Dolphin_with_chunks.csv" "D:\data\HCNC\norway\biographies\storage\Dolphin\output\biographical_data.json"

# With API key
#python biography_extractor_Dolphin.py input.csv output.json --api-key your_api_key

# With debug logging
#python biography_extractor_Dolphin.py input.csv output.json --log-level DEBUG        

# To read the JSON back later:
#import json
#df = pd.read_csv('extracted_names_Dolphin_with_chunks_with_biographies.csv')
#first_biography = json.loads(df.iloc[0]['biography_json'])
#print(first_biography['birth_date'])

#Second round of processing
#python biography_extractor_Dolphin.py "d:\data\HCNC\norway\biographies\storage\Dolphin\logs\failed_rows.csv" "d:\data\HCNC\norway\biographies\storage\Dolphin\logs\biographical_data_failed_rows.json"