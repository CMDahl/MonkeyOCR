from transformers import pipeline
from PIL import Image

model_cache_dir = r'D:\models\LLMs\hub'

# pipe = pipeline("image-text-to-text", model="ChatDOC/OCRFlux-3B",
#                 use_fast=True,
#                 cache_dir=model_cache_dir) #Load the image
pipe = pipeline("image-text-to-text", model="reducto/RolmOCR",
                use_fast=True,
                cache_dir=model_cache_dir) #Load the image
image = Image.open(r'd:\data\HCNC\norway\biographies\raw\corpus\digibok_2007031501007\digibok_2007031501007_0103.jpg')

def build_page_to_markdown_prompt() -> str:
    return (
        f"Below is the image of one page of a document. "
        f"Just return the markdown representation of this document as if you were reading it naturally.\n"
        f"If there are images or figures embedded in the document, present them as ![](images) in your output\n"
        f"Do not hallucinate.\n"
    )

# Combine the custom prompt with the image
messages = [
    {
        "role": "user",  
        "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": build_page_to_markdown_prompt()}  # Use the custom prompt
        ]
    },
]

result = pipe(text=messages, max_new_tokens=5000, temperature=0.01)
print(result[0]['generated_text'][-1]['content'])

## Output: NOT GOOD and no identification of images
"""på ny 1947 med Rigmor Eriksen, f. 1/3-25 Oslo, d. av faktor H. E. E. — Tok Brynn som slektsnavn 1948. Barn: Yngvar 7/7-48, Grace Elisabeth 17/7-55.

Pr. Lekt/E — Oslo Handelsgymn. 1926, forber. prøver 1933, Fondsmeglereks. 1940, dipl.eks. Den høyere Bankskole 1954. Stipendieopphold England 1938. — Ansatt Bergens Privatbank, Oslo 1926-, nå avd.sjef. — Int: Tennis.

På rette bhylle? Neppe.

Høyt vurdert egenskap? En sunn porsjon optimisme, viljestyrke og utholdenhet.

Hd/L — Var ansatt ved rikstelefonen i Halden ved sin død.

BRÆKKAN, Reidar, lærer, Stavern, f. 20/4-03 Folda, s. av lærer, kirkesanger Henrik Kristian B. (1865-1946) og Edvarda Eline Pettersen (1870-1949). Gift 1932 med Ragna Elvhaug, f. 6/6-03 Buksnes, d. av gårdbruker Roland E. — Barn: Liv 28/5-34, Bjørg 11/2-38.

Pr. Fi/R — Lærerskoleeks. 1924, sløyd-lærereks. 1938, kurser. — Lærer Dverberg 1924-26, Tysfjord 1926-29, Dverberg 1929-37, Hol i Lofoten 1937-39, Glomfjord 1939-47, Stavern 1947-. — Medl. kommunestyre, form. ungdomslag, forsorgstyre og trygdekassestyre. — Int: Malerkunst.

På rette bhylle? I 1924 hadde jeg allerede valgt en bhylle. Om det var den rette, får bli andres sak å dømme om.

Høyt vurdert egenskap? Det ekte og likefremme.

† BRÆKKE, Asborg Jørgine, f. 26/6-12 Enningdal, Idd, død 8/9-34, d. av formann Hans Jørgen Jensen B. (1877-1953) og Helga Axelsen (1888-1916).

BRØGGER, Niels Christian Ursin, forfatter, Oslo, f. 4/6-14 sst., s. av professor Anton Wilhelm B. (1884-1951) og Inger Ursin (1882-1941). Gift 1943 med Vesla (Regine) Stenersen, f. 26/1-14 Oslo, d. av artillerikaptein Fredrik S. — Ekteskap oppløst 1949. Gift på ny 1952 med Else Lødrup, f. 21/6-27, d. av grosserer Trygve L. — Barn: Fredrik 23/4-45, Nina 15/4-53.

Fb/L — Studerte litteraturhistorie i Oslo og London 1932-34. Studiereise med stipendium til London 1938. Kortere studieopphold i Italia 1935 og Spania 1936 før borgerkrigen brøt ut. — Gikk over til forfatterskapet og journalistikken 1937. Litteraturanmelder «Tidens Tegn» 1934-40, dramatisk konsulent Det Nye Teater 1938-40, teaterkritiker «Nationen» 1945-55, litteraturanmelder sst. 1945-. Fast teaterkronikør «Norsk Dameblad» 1954-, og løssloppen kronikør i «Dagbladet», «Morgenbladet», «Aftenposten», «Verdens Gang» og «Morgenposten» siden 1945. Free lancer med leilighetsjobber som litterær konsulent for flere forlag. — «Har skrevet i alt 11 bøker om litterære, historiske, psyko-"""