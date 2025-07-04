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


filepath = Path(r'z:\datasets\braincollection\Æske 8\Æske 8\447 ny.pdf')

# Original prompt for simple field extraction
prompt_content = """
                    "Please read the attached clinical note (PDF) and return a **single JSON object**. "
                    "Each key must correspond **exactly** to the field names listed below. "
                    "If a field is not mentioned, set its value to `null`. "
                    "Return **only** the JSON object – no explanatory text.\n\n"
                    "Fields to extract (in Danish):\n"
                    "- Diagnoser\n"
                    "- Symptomer inkl. ændringer i symptomatologi og QoL (quality of life) over tid\n"
                    "- Objektive fund samt ændringer over tid\n"
                    "- Generelt lidelsespres eller andre lignende parametre\n"
                    "- Undersøgelser og fund (skanninger, blod/vævsprøver, psykologiske tests mv)\n"
                    "- Behandlinger inkl. diverse typer (medicin, samtale, ECT mv) inkl. psykoterapeutisk tilgang og intensitet\n"
                    "- Tidligere øvrige behandlingsforløb og effekt heraf\n"
                    "- Bivirkninger ved behandling\n"
                    "- Compliance og behandlingsalliance\n"
                    "- Indlæggelsesvarigheder og antal\n"
                    "- Særlige forhold for netop denne patient sammenlignet med andre (hvis muligt?)\n"
                    "- Alder/fødselsdato\n"
                    "- Debutalder for lidelsen\n"
                    "- Varighed af symptomer og sygdom\n"
                    "- Baggrundsinformation inkl. komorbiditeter (fysiske lidelser, psykiske/fysiske traumer, familiær baggrund)\n"
                    "- Sociale netværk og støttepersoner\n"
                    "- Tidspunkter for relevante hændelser (fx traumer, indlæggelser)\n"
                    "- Familiære dispositioner (andre i familien med psykiske lidelser mv.)\n"
                    "- Risikovurderinger: Suicidalitet og voldsrisiko\n"
                    "- Rehabiliteringsvurdering\n"
                    "- Retspsykiatriske data\n"
                    "- Kognitiv funktion (hukommelse, opmærksomhed, eksekutive funktioner)\n"
                    "- Funktionsniveau (fx GAF, WHODAS, ADL)\n"
                    "- Sprog- og kommunikationsvanskeligheder (fx afasi, autisme, dysartri)\n"
                    "- Misbrugsproblematik og substansbrug\n"
                    "- Uddannelses- og beskæftigelseshistorik\n"
                    "- Boligforhold og økonomisk situation\n"
                    "- Fritid og interesser\n"
                    "- Livsstil (søvn, kost, fysisk aktivitet, rygning mv.)\n"
                    "- Patientens egne mål, ønsker og oplevelse af sygdom (hvis omtalt)\n"
                    "- Notater fra pårørende og andre fagpersoner\n"
                    "- Juridiske forhold (værgemål, samtykkekompetence mv.)\n"
                    "- Udviklingshistorie\n"
                    "- Etiske og kulturelle hensyn (sprog, religion, holdninger til behandling)"
                    """



# Alternative structured prompt for detailed patient record format
structured_prompt = """
Analyser venligst det vedhæftede kliniske PDF-dokument og udtræk patientinformation i et struktureret JSON-format.
Returner KUN et gyldigt JSON-objekt uden yderligere tekst eller forklaringer.
Alle tekstfelter skal være på dansk, som de fremgår i det originale dokument.

Udtræk information i denne nøjagtige struktur (sæt felter til null hvis information ikke er tilgængelig):

{
  "patient": {
    "journal_number": "udtræk journal/patient nummer",
    "full_name": "udtræk fulde patientnavn",
    "alternate_name_part": "eventuelle alternative navnekomponenter",
    "date_of_birth": "ÅÅÅÅ-MM-DD format",
    "place_of_birth": "fødested",
    "age_at_admission": "numerisk alder",
    "marital_status": "civilstand på dansk",
    "occupation": "patientens erhverv",
    "residence": {
      "address": "hjemmeadresse",
      "current_location": "nuværende opholdssted hvis anderledes"
    },
    "admission": {
      "date": "ÅÅÅÅ-MM-DD format",
      "hospital": "hospitalsnavn",
      "referring_source": "hvem henviste patienten",
      "diagnoses_at_admission": ["array af indledende diagnoser"],
      "additional_initial_diagnoses": ["array af yderligere/observations diagnoser"],
      "journal_taker": "navn på person der tager journalen"
    },
    "medical_history": {
      "conditions": [
        {
          "name": "tilstandsnavn",
          "year": "årstal hvis nævnt",
          "since_year": "igangværende siden år",
          "date": "specifik dato hvis nævnt",
          "notes": "yderligere detaljer",
          "details": "specifikke medicinske detaljer"
        }
      ],
      "psychological_profile": ["array af psykologiske observationer og træk"]
    },
    "death": {
      "date": "ÅÅÅÅ-MM-DD hvis patient døde",
      "diagnoses_at_death": ["array af dødediagnoser"]
    },
    "family_history": {
      "disposition_to_mental_illness": "familiens psykiske sundhedsdisposition",
      "father": {
        "name": "faders navn",
        "place_of_birth": "faders fødested",
        "date_of_death": "dødsår",
        "cause_of_death": "dødsårsag"
      },
      "mother": {
        "name": "moders navn", 
        "place_of_residence": "moders bopæl",
        "date_of_death": "dødsår",
        "cause_of_death": "dødsårsag"
      },
      "closest_relative": {
        "relationship": "slægtskabstype",
        "name": "pårørendes navn",
        "address": "pårørendes adresse"
      },
      "appointed_guardian": {
        "name": "værges navn",
        "details": "værgedetaljer"
      },
      "siblings": [
        {
          "name": "søskendes navn",
          "occupation": "søskendes erhverv", 
          "residence": "søskendes bopæl"
        }
      ]
    },
    "special_investigations": [
      {
        "type": "undersøgelsestype (f.eks. Spinalvæskeanalyse, Encephalografi, Røntgen)",
        "date": "ÅÅÅÅ-MM-DD format",
        "results": "undersøgelsesresultater (kan være objekt eller streng)"
      }
    ],
    "autopsy_findings": {
      "date": "ÅÅÅÅ-MM-DD format",
      "brain_pathology": {
        "diagnosis": "patologisk diagnose",
        "macroscopic_description": "makroskopiske fund",
        "histological_description": "histologiske fund"
      }
    }
  }
}

Udtræk al tilgængelig information fra dokumentet. For datoer, brug ÅÅÅÅ-MM-DD format hvor muligt. For manglende information, brug null-værdier.
Alle tekstfelter skal bevare den originale danske tekst fra dokumentet.
"""

temperature=0.1

# Choose which prompt to use
USE_STRUCTURED_FORMAT = False  # Set to False to use original simple format
selected_prompt = structured_prompt if USE_STRUCTURED_FORMAT else prompt_content

# Prepare content for Gemini
contents = [
    types.Content(
        role="user",
        parts=[
                types.Part.from_bytes(data=filepath.read_bytes(),mime_type='application/pdf'),
                types.Part.from_text(text=selected_prompt),
        ],
    ),
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
                print("Answer:")
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
save_results_to_file(answer, thoughts, "_structured" if USE_STRUCTURED_FORMAT else "_simple")
