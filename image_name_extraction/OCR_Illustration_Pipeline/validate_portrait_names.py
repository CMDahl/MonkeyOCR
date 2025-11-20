"""
Validate that portrait-associated names are actually the main biographical subjects.
Uses Gemini to check if each name has a dedicated biographical entry.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from google import genai
from google.genai import types
from azure.identity import AzureCliCredential
from azure.keyvault.secrets import SecretClient
from config_loader import ConfigLoader

# Set up logging - suppress verbose HTTP logs
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logs from google.genai and azure libraries
logging.getLogger('google.genai').setLevel(logging.WARNING)
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

class PortraitNameValidator:
    def __init__(self, api_key: str, config_loader: ConfigLoader = None):
        """Initialize the validator with Gemini API key and configuration"""
        self.client = genai.Client(api_key=api_key)
        
        # Load configuration
        self.config = config_loader or ConfigLoader()
        self.prompt_config = self.config.get_prompt_config('portrait_validation')
        self.temperature = self.prompt_config.get('temperature', 0.01)
        self.context_window = self.prompt_config.get('context_window_chars', 1000)
        
    def validate_name_is_main_subject(self, name: str, markdown_content: str, portrait_filename: str) -> Dict:
        """
        Use Gemini to validate if the name is the main subject of a biographical entry.
        
        Args:
            name: The person's name to validate
            markdown_content: The full markdown content
            portrait_filename: The filename of the portrait to help locate context
        
        Returns:
            {
                "is_main_subject": bool,
                "confidence": float,
                "reasoning": str,
                "suggested_name": str or None  # If wrong, suggest the correct name
            }
        """
        
        # Extract context around the portrait to help validation
        portrait_context = ""
        if portrait_filename in markdown_content:
            idx = markdown_content.find(portrait_filename)
            start = max(0, idx - self.context_window)
            end = min(len(markdown_content), idx + self.context_window)
            portrait_context = markdown_content[start:end]
        
        # Get prompt from configuration
        prompt = self.config.get_prompt('portrait_validation',
                                       portrait_filename=portrait_filename,
                                       name=name,
                                       portrait_context=portrait_context)

        try:
            response = self.client.models.generate_content(
                model=self.config.get_gemini_settings().get('model', 'gemini-2.5-flash'),
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text)
            return result
            
        except Exception as e:
            logger.error(f"Validation failed for {name}: {e}")
            return {
                "is_main_subject": True,  # Default to accepting if validation fails
                "confidence": 0.5,
                "reasoning": f"Validation error: {e}",
                "suggested_name": None
            }

def load_azure_api_key(vault_url: str, key_name: str) -> str:
    """Load API key from Azure Key Vault"""
    try:
        credential = AzureCliCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        secret = client.get_secret(key_name)
        return secret.value
    except Exception as e:
        logger.error(f"Failed to load API key from Azure Key Vault: {e}")
        raise

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_portrait_names.py <output_directory>")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    staging_dir = output_dir / "input_staging"
    
    # Load Azure Key Vault configuration
    vault_url = "https://rmaocr.vault.azure.net/"
    key_name = "SDUGeminiAPI"
    
    print("Loading API key from Azure Key Vault...")
    api_key = load_azure_api_key(vault_url, key_name)
    
    # Initialize validator
    validator = PortraitNameValidator(api_key)
    
    # Find all portrait association files
    portrait_files = list(output_dir.glob("*_portrait_associations.json"))
    
    if not portrait_files:
        print("No portrait association files found")
        return
    
    print(f"Found {len(portrait_files)} portrait association file(s)")
    
    validated_count = 0
    corrected_count = 0
    removed_count = 0
    
    # Process each file
    for portrait_file in portrait_files:
        # Skip the all_books summary file
        if portrait_file.name.startswith("all_books_"):
            continue
            
        try:
            with open(portrait_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            book_id = data.get('book_id')
            if not book_id:
                continue
            
            # Load the corresponding markdown file
            md_file = staging_dir / f"{book_id}.md"
            if not md_file.exists():
                logger.warning(f"Markdown file not found: {md_file}")
                continue
            
            with open(md_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Validate each biographical entry
            if 'biographical_entries' not in data:
                continue
            
            validated_entries = []
            seen_names = set()  # Track names we've already added to avoid duplicates
            
            for entry in data['biographical_entries']:
                name = entry.get('associated_person')
                filename = entry.get('filename', '')
                
                if not name or name.lower() == 'null':
                    continue
                
                print(f"  Validating: {name} in {book_id}")
                
                # Validate with Gemini
                validation = validator.validate_name_is_main_subject(name, markdown_content, filename)
                
                if validation['is_main_subject'] and validation['confidence'] >= 0.7:
                    # Name is valid
                    if name not in seen_names:
                        validated_entries.append(entry)
                        seen_names.add(name)
                        validated_count += 1
                        print(f"    [OK] Valid (confidence: {validation['confidence']})")
                    else:
                        print(f"    [SKIP] Duplicate entry skipped")
                else:
                    # Name is not the main subject
                    if validation['suggested_name'] and validation['suggested_name'] not in seen_names:
                        print(f"    [X] Invalid: {validation['reasoning']}")
                        print(f"      Suggested correction: {validation['suggested_name']}")
                        
                        # Update the entry with the correct name
                        entry['associated_person'] = validation['suggested_name']
                        entry['confidence'] = validation['confidence']
                        entry['validation_note'] = f"Corrected from '{name}'"
                        validated_entries.append(entry)
                        seen_names.add(validation['suggested_name'])
                        corrected_count += 1
                    elif validation['suggested_name'] and validation['suggested_name'] in seen_names:
                        print(f"    [X] Invalid: {validation['reasoning']}")
                        print(f"      Removed: {validation['suggested_name']} already has a portrait")
                        removed_count += 1
                    else:
                        print(f"    [X] Removed: {validation['reasoning']}")
                        removed_count += 1
            
            # Update the file with validated entries
            data['biographical_entries'] = validated_entries
            data['validation_timestamp'] = __import__('datetime').datetime.now().isoformat()
            
            with open(portrait_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Error processing {portrait_file.name}: {e}")
            continue
    
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Total entries validated: {validated_count}")
    print(f"Entries corrected: {corrected_count}")
    print(f"Entries removed: {removed_count}")
    print("="*60)

if __name__ == "__main__":
    main()
