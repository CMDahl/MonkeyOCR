import os
from pathlib import Path
import sys
sys.path.append(str(Path(os.getcwd()).parent.parent))  # Go two levels up instead of one
from agents.key_vault import KeyVault
# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types

vault = KeyVault()               
api_key = vault.get_key("SDUGeminiAPI")

client = genai.Client(
    api_key=api_key,
)

# Define the paths to your 3 JPG images - UPDATE THESE PATHS
image_paths = [
    Path(r"v:\BDADShareData2\Brain\0013.jpg"),  # Replace with your first image path
    Path(r"v:\BDADShareData2\Brain\0014.jpg"),  # Replace with your second image path  
    #Path(r"v:\BDADShareData2\Brain\0015.jpg")   # Replace with your third image path
]

# Structured prompt for extracting patient information from images
structured_prompt = """
Analyser venligst de 3 vedhæftede billeder og udtræk patientinformation i et struktureret JSON-format.
Returner KUN et gyldigt JSON-objekt uden yderligere tekst eller forklaringer.
Alle tekstfelter skal være på dansk, som de fremgår i de originale dokumenter.

Udtræk information i denne nøjagtige struktur (sæt felter til null hvis information ikke er tilgængelig):

{
    "patient": [
        {
            "efternavn": "patientens efternavn",
            "fornavn": "patientens fornavn",
            "fødselsdato": "dd-mm-åååå format",
            "fødselssted": "fødested",
            "stilling": "patientens stilling/erhverv",
            "adresse": "patientens adresse",
            "journalnummer": "journal/patient nummer",
            "dødstidspunkt": "dd-mm-åååå tt:mm format hvis tilgængelig",
            "autopsitidspunkt": "autopsi dato/tid hvis tilgængelig",
            "hjerneautopsidiagnoser": [
                "array af autopsi diagnoser"
            ],
            "histologiske diagnoser": [
                "array af histologiske diagnoser",
                "bemærkninger om histologiske fund"
            ],
            "kliniske diagnoser": [
                "array af kliniske diagnoser"
            ],
            "øvrige oplysninger": [
                "array af øvrige relevante oplysninger"
            ]
        }
    ]
}

Læs alle billeder og udtræk al tilgængelig information. Hvis der er flere patienter i billederne, skal de alle inkluderes i patient arrayet.
For datoer, brug dd-mm-åååå format. For manglende information, brug null-værdier.
Alle tekstfelter skal bevare den originale danske tekst fra dokumenterne.
"""

temperature = 0.1

# Prepare content for Gemini with multiple images
parts = []

# Add all images to the parts
for i, image_path in enumerate(image_paths):
    if image_path.exists():
        parts.append(types.Part.from_bytes(
            data=image_path.read_bytes(),
            mime_type='image/jpeg'
        ))
        print(f"Added image {i+1}: {image_path.name}")
    else:
        print(f"Warning: Image {i+1} not found: {image_path}")

# Add the text prompt
parts.append(types.Part.from_text(text=structured_prompt))

contents = [
    types.Content(
        role="user",
        parts=parts
    )
]

# Configure generation with temperature
generate_content_config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(
        thinking_budget=-1,
        include_thoughts=True
    ),
    response_mime_type="application/json",
    temperature=temperature,
)

model = "gemini-2.5-pro"

# Initialize variables to collect thoughts and answer
thoughts = ""
answer = ""

print("Starting analysis of 3 images...")
print("="*50)

# Use streaming to capture thoughts and answer
for chunk in client.models.generate_content_stream(
    model=model,
    contents=contents,
    config=generate_content_config
):
    for part in chunk.candidates[0].content.parts:
        if not part.text:
            continue
        elif part.thought:
            if not thoughts:
                print("Thoughts summary:")
            print(part.text)
            thoughts += part.text
        else:
            if not answer:
                print("\nAnswer:")
            print(part.text)
            answer += part.text

print("\n" + "="*50)
print("FINAL RESULTS:")
print("="*50)
print("Generated JSON:")
print(answer)

# Save results to file
def save_results_to_file(answer_text, thoughts_text, filename_suffix=""):
    """Save the JSON results and thoughts to files"""
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"extracted_data_{timestamp}{filename_suffix}.json"
    thoughts_filename = f"thoughts_{timestamp}{filename_suffix}.txt"
    
    try:
        # Parse and pretty-print the JSON
        json_data = json.loads(answer_text)
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {output_filename}")
        
    except json.JSONDecodeError as e:
        # If not valid JSON, save as text
        with open(f"raw_output_{timestamp}.txt", 'w', encoding='utf-8') as f:
            f.write(answer_text)
        print(f"Raw output saved to: raw_output_{timestamp}.txt")
        print(f"JSON parsing error: {e}")
    
    # Save thoughts if available
    if thoughts_text:
        with open(thoughts_filename, 'w', encoding='utf-8') as f:
            f.write("GEMINI THOUGHTS/REASONING PROCESS\n")
            f.write("="*50 + "\n\n")
            f.write(thoughts_text)
        print(f"Thoughts saved to: {thoughts_filename}")
    else:
        print("No thoughts to save.")

# Save results to file
save_results_to_file(answer, thoughts, "_multiple_images")
