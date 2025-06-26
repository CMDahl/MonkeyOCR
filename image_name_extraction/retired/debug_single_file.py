#!/usr/bin/env python3
"""
Debug script to test Gemini analysis on a single markdown file
"""

import os
import json
import sys
from pathlib import Path
from google import genai
from google.genai import types

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from agents.key_vault import KeyVault

def analyze_single_file(md_file_path: str):
    """Debug function to analyze a single markdown file"""
    
    # Get API key
    vault = KeyVault()    
    api_key = vault.get_key("SDUGeminiAPI")
    
    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    model = "gemini-2.5-flash-lite-preview-06-17"
    
    # Load the markdown file
    md_path = Path(md_file_path)
    if not md_path.exists():
        print(f"File not found: {md_path}")
        return
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Loaded file: {md_path}")
    print(f"Content length: {len(content)} characters")
    print(f"First 200 characters: {content[:200]}...")
    
    # Simple prompt for single file analysis
    prompt_content = f"""Analyze this Norwegian biographical text and identify any portrait associations.

Markdown content:
{content}

Look for:
1. Image references like figure></figure> tags
2. Person names in ALL-CAPS format (SURNAME, Given names)
3. Associations between images and names

Respond with a JSON array of associations:
[
  {{
    "figure_label": "Figure 1",
    "associated_person": "SURNAME, Given Names",
    "confidence": 0.85,
    "reasoning": "Brief explanation"
  }}
]

If no clear associations found, return empty array [].
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
        
        print("Sending request to Gemini...")
        
        # Generate response using streaming
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text
        
        print("Response received!")
        print(f"Raw response: {response_text}")
        
        # Parse JSON response
        try:
            associations = json.loads(response_text)
            print(f"\nParsed {len(associations)} associations:")
            for i, assoc in enumerate(associations, 1):
                print(f"{i}. {assoc}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_single_file.py <path_to_markdown_file>")
        print("Example: python debug_single_file.py D:\\data\\HCNC\\norway\\biographies\\storage\\AzureOCR\\digibok_2007031501007__0060\\digibok_2007031501007_0060_azure.md")
    else:
        analyze_single_file(sys.argv[1])