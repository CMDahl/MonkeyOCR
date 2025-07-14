from PIL import Image
from transformers import AutoTokenizer, AutoProcessor, AutoModelForImageTextToText

model_path = "nanonets/Nanonets-OCR-s"
model_cache_dir = r'D:\models\LLMs\hub'

model = AutoModelForImageTextToText.from_pretrained(
    model_path, 
    torch_dtype="auto", 
    device_map="cuda:1", 
    low_cpu_mem_usage=True,
    cache_dir=model_cache_dir,
    trust_remote_code=True    
    
)
model.eval()

tokenizer = AutoTokenizer.from_pretrained(model_path)
processor = AutoProcessor.from_pretrained(model_path,use_fast=True)


def ocr_page_with_nanonets_s(image_path, model, processor, max_new_tokens=8192,
                           prompt="""Extract the text from the above document as if you were reading it naturally"""):
    image = Image.open(image_path)
    messages = [
        {"role": "user", "content": [
            {"type": "image", "image": f"file://{image_path}"},
            {"type": "text", "text": prompt},
        ]},
    ]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[image], padding=True, return_tensors="pt")
    inputs = inputs.to(model.device)
    
    output_ids = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, output_ids)]
    
    output_text = processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
    return output_text[0]

image_path = r'd:\GitHub\rma_ocr\data\amd\amd1921\Book_0015_CROP16.jpg'
result = ocr_page_with_nanonets_s(image_path, model, processor)
print(result)
## Output: NOT GOOD
""" på ny 1947 med Rigmor Eriksen, f. 1/3-25 Oslo, d. av faktor H. E. E. – Tok Brynn som slektnavn 1948. Barn: Yngvar 7/7-48, Grace Elisabeth 17/7-55.
Pr. Lekt/E – Oslo Handelsgymn. 1926, forber. prøver 1933, Fondsmeglereks. 1940, dipl.eks. Den høyere Bankskole 1954. Stipendieopphold England 1938. – Ansatt Bergens Privatbank, Oslo 1926-, nå avd.sjef. – Int: Tennis.

På rette hylle? Neppe.
Høyt vurdert egenskap? En sunn person optimisme, viljestyrke og utholdenhet.

Hd/L – Var ansatt ved rikstelefonen i Halden ved sin død.

BRØGGER, Niels Christian Ursin, forfatter, Oslo, f. 4/6-14 sst., s. av professor Anton Wilhelm B. (1884-1951) og Inger Ursin (1882-1941). Gift 1943 med Vesla (Regine) Stenersen, f. 26/1-14 Oslo, d. av artillerikaptein Fredrik S. – Ekteskap oppløst 1949. Gift på ny 1952 med Else Lødrup, f. 21/6-27, d. av grosserer Trygve L. – Barn: Fredrik 23/4-45, Nina 15/4-53.

Fb/L – Studerte litteraturhistorie i Oslo og London 1932-34. Studiereise med stipendium til London 1938. Kortere studieopphold i Italia 1935 og Spania 1936 før borgerkrigen brøt ut. – Gikk over til forfatterskapet og journalistikken 1937. Litteraturanmelder «Tidens Tegn» 1934-40, dramatisk konsulent Det Nye Teater 1938-40, teaterkritiker «Nationen» 1945-55, litteraturanmelder sst. 1945-. Fast teaterkronikør «Norsk Dameblad» 1954-, og løssloppen kronikør i «Dagbladet», «Morgenbladet», «Aftenposten», «Verdens Gang» og «Morgenposten» siden 1945. Free lancer med leilighetsjobber som litterær konsulent for flere forlag. – «Har skrevet i alt 11 bøker om litterære, historiske, psyko-

† BRÆKKE, Asborg Jørgine, f. 26/6-12 Enningdal, Idd, død 8/9-34, d. av formann Hans Jørgen Jensen B. (1877-1953) og Helga Axelsen (1888-1916).

På rette hylle? I 1924 hadde jeg allerede valgt en hylle. Om det var den rette, får bli andres sak å dømme om. Høyt vurdert egenskap? Det ekte og likefremme. """

