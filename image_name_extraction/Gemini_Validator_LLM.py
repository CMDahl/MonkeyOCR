from google import genai
from google.genai import types
import base64
import sys
from pathlib import Path
import os
sys.path.append(str(Path(os.getcwd()).parent))
from agents.key_vault import KeyVault

vault = KeyVault()        
api_key = vault.get_key("SDUGeminiAPI")
client = genai.Client(api_key=api_key)

dolphin_md_dir = r"D:\data\HCNC\norway\biographies\storage\Dolphin\markdown"
monkeyocr_md_dir = r"D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007"

def generate(client):
    # Read content from two text files
    def read_text_file(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return f"[ERROR READING FILE: {os.path.basename(file_path)}]"
    
    def load_image_safely(image_path):
        """Load image with error handling using bytes method"""
        try:
            if os.path.exists(image_path):
                # Read image as bytes
                with open(image_path, 'rb') as file:
                    image_data = file.read()
                
                # Determine MIME type based on file extension
                ext = os.path.splitext(image_path)[1].lower()
                mime_type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg', 
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                mime_type = mime_type_map.get(ext, 'image/jpeg')
                
                return types.Part.from_bytes(
                    data=image_data,
                    mime_type=mime_type
                )
            else:
                print(f"Warning: Image not found at {image_path}")
                return types.Part.from_text(text=f"[IMAGE NOT FOUND: {os.path.basename(image_path)}]")
        except Exception as e:
            print(f"Error loading image: {e}")
            return types.Part.from_text(text=f"[IMAGE LOAD ERROR: {os.path.basename(image_path)}]")
    
    # Load documents
    document1 = types.Part.from_text(
        text=read_text_file(r'D:\data\HCNC\norway\biographies\storage\Dolphin\markdown\digibok_2007031501007_0103.md')
    )
    document2 = types.Part.from_text(
        text=read_text_file(r'D:\data\HCNC\norway\biographies\storage\MonkeyOCR\digibok_2007031501007\digibok_2007031501007_0103.md')
    )
    
    # Load original image
    original_image = load_image_safely(r'd:\data\HCNC\norway\biographies\raw\corpus\digibok_2007031501007\digibok_2007031501007_0103.jpg')
    
    # Add labels for clarity
    label1 = types.Part.from_text(text="=== ORIGINAL DOCUMENT IMAGE ===")
    label2 = types.Part.from_text(text="=== DOLPHIN OCR RESULT ===")  
    label3 = types.Part.from_text(text="=== MONKEYOCR RESULT ===")
    
    # Comprehensive analysis prompt
    text1 = types.Part.from_text(
        text="""Given the original document image and two OCR results (Dolphin vs MonkeyOCR), provide a comprehensive comparison:

            **ACCURACY COMPARISON:**
            - Robust recognition of all SURNAMES (names where the surname is in all caps) 
            
            **LAYOUT COMPARISON:**
            - Read the entire first column, then the entire second column
            - Paragraph and section breaks
            - Image/figure placement and tagging (look for ![](images) or ![Figures]() tags)
            
            **RECOMMENDATIONS:**
            - Which OCR performed better overall?
            - Is it trustworthy

            From a preliminary string comparison there might be indications of a missing SURNAME in the dolphin OCR. Please pay attention to that.
            
            Please note that misspellings are not of vital importance, but the overall structure and content accuracy are crucial. Please check carefully for any missing SURNAMES in the OCR results, as they are critical for the analysis. It is often the case that SURNAMES are missed so look extremely careful. They should be easy to spot. I recommend that you make you own identification of the SURNAMES first and then see if you can find them in the OCR results.
            
            Provide your analysis in the following structured JSON format:
            {
                "analysis": {
                    "surnames": {
                        "Gemini": ["SURNAMES from original image"],
                        "dolphin": ["SURNAMES from Dolphin OCR"],
                        "monkeyocr": ["SURNAMES from MonkeyOCR"]
                    },
                    "image_tags": {
                        "dolphin": "Ok or Not Ok",
                        "monkeyocr": "Ok or Not Ok"
                    },
                    "recommendations": "dolphin or monkeyocr or both or none"
                }
            }""",
    )

    model = "gemini-2.5-pro"
    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                label1,
                original_image,
                label2,
                document1,
                label3,
                document2, 
                text1
            ]
        )
    ]
    
    # Add the missing generate_content_config
    generate_content_config = types.GenerateContentConfig(
        temperature=0.1,
        top_p=1,
        seed=0,
        max_output_tokens=20048,
        thinking_config=types.ThinkingConfig(thinking_budget=-1),        
        response_mime_type="application/json"        
    )

    try:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            print(chunk.text, end="")
    except Exception as e:
        print(f"Error generating content: {e}")

generate(client)