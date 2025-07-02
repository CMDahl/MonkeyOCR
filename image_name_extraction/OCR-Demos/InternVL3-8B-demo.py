import math
import numpy as np
import torch
import torchvision.transforms as T
from decord import VideoReader, cpu
from PIL import Image
from torchvision.transforms.functional import InterpolationMode
from transformers import AutoModel, AutoTokenizer, AutoConfig

model_cache_dir = r'D:\models\LLMs\hub'

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

def build_transform(input_size):
    MEAN, STD = IMAGENET_MEAN, IMAGENET_STD
    transform = T.Compose([
        T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=MEAN, std=STD)
    ])
    return transform

def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_ratio_diff = float('inf')
    best_ratio = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio

def dynamic_preprocess(image, min_num=1, max_num=12, image_size=448, use_thumbnail=False):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # calculate the existing image aspect ratio
    target_ratios = set(
        (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
        i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    # find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, target_ratios, orig_width, orig_height, image_size)

    # calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        )
        # split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images

def load_image(image_file, input_size=448, max_num=12):
    image = Image.open(image_file).convert('RGB')
    transform = build_transform(input_size=input_size)
    images = dynamic_preprocess(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
    pixel_values = [transform(image) for image in images]
    pixel_values = torch.stack(pixel_values)
    return pixel_values

def split_model(model_name):
    device_map = {}
    world_size = torch.cuda.device_count()
    config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
    num_layers = config.llm_config.num_hidden_layers
    # Since the first GPU will be used for ViT, treat it as half a GPU.
    num_layers_per_gpu = math.ceil(num_layers / (world_size - 0.5))
    num_layers_per_gpu = [num_layers_per_gpu] * world_size
    num_layers_per_gpu[0] = math.ceil(num_layers_per_gpu[0] * 0.5)
    layer_cnt = 0
    for i, num_layer in enumerate(num_layers_per_gpu):
        for j in range(num_layer):
            device_map[f'language_model.model.layers.{layer_cnt}'] = i
            layer_cnt += 1
    device_map['vision_model'] = 0
    device_map['mlp1'] = 0
    device_map['language_model.model.tok_embeddings'] = 0
    device_map['language_model.model.embed_tokens'] = 0
    device_map['language_model.output'] = 0
    device_map['language_model.model.norm'] = 0
    device_map['language_model.model.rotary_emb'] = 0
    device_map['language_model.lm_head'] = 0
    device_map[f'language_model.model.layers.{num_layers - 1}'] = 0

    return device_map

# If you set `load_in_8bit=True`, you will need two 80GB GPUs.
# If you set `load_in_8bit=False`, you will need at least three 80GB GPUs.
path = 'OpenGVLab/InternVL3-8B'
device_map = split_model(path)
model = AutoModel.from_pretrained(
    path,
    torch_dtype=torch.bfloat16,
    load_in_8bit=False,
    low_cpu_mem_usage=True,
    use_flash_attn=True,
    trust_remote_code=True,
    #device_map=device_map,
    device_map='cuda:0',
    cache_dir=model_cache_dir).eval()
tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True, use_fast=False)

# set the max number of tiles in `max_num`
pixel_values = load_image(r'd:\data\HCNC\norway\biographies\raw\corpus\digibok_2007031501007\digibok_2007031501007_0103.jpg', max_num=70,input_size=448).to(torch.bfloat16).cuda()
generation_config = dict(max_new_tokens=3000, do_sample=False)


# single-image single-round conversation 
question = '<image>/Please transcribe text in the image (norwegian biography). Return as markdown. Please note that there are two columns. Tag the embedded images (which are portraits) exactly where they appear in the text. Simply use <img> as tag.</image>'
response = model.chat(tokenizer, pixel_values, question, generation_config)
print(f'User: {question}\nAssistant: {response}')

## OUTPUT: NOT Impressive. Does not tag the images correctly
"""User: <image>/Please transcribe text in the image (norwegian biography). Return as markdown. Please note that there are two columns. Tag the embedded images (which are portraits) exactly where they appear in the text. Simply use <img> as tag.</image>
Assistant: ```markdown
på ny 1199 med Rigmor Eriksen, f. 1/3-
25 Oslo, d. av faktor H. E. E. – Tok Brynn som slektsnavn 1948. Barn: Yng-
var 7/7-48, Grace Elisabeth 17/7-55.
Pr. Lekt/E – Oslo Handelsgymn.
1926, forber. prøver 1933, Fondsme-
eks. 1940, dipl.eks. Den høyere Bankskole
1954. Stipendieopphold England 1938. –
Ansatt Bergen Privatbank, Oslo 1926-,
nå avdd.sjef. – Int: Tennis.
På rette hylle?  Neppa.
Høyt vurdert egenskap? En sunn por-
sjon optimism, viljestyrke og uthol-
denhet.

Hd/L – Var ansatt ved rikstelefonen
i Halden ved sin død.

BRAEKKAN, Reidar, lærer, Stavern,
f. 20/4-03 Følda, s. av lærer, kirkesanger
Henrik Kristian B. (1865-1946) og Ed-
vårda Eline Pettersen (1870-1949). Gift
1932 med Ragna Elvhaaug, f. 6/6-03
Buksnæs, d. av gårdbruker Roland E. –
Barn: Liv 28/5-34, Bjørg 11/2-38.
Pr. Fi/R – Lærerskoleleeks. 1924, sløyd-
lærerks. 1938, kurs. – Lærer Dverberg
1924-26, Tysfjjord 1926-29, Dverberg
1929-37, Hol Lofoten 1937-39, Glo-
fjjord 1939-47, Stavern 1947-. – Medl.
kommunestyre, form. ungdomslag, for-
sorgstyre og trygdekassestyre. – Int:
Malerkunst.

På rette hylle? I 1924 hadde jeg alle-
rede valgt en hylle. Om det var den den
rette, får blå andres sak å dømme om.
Høyt vurdert egenskap? Det erke og
likefremme.

BRAEKKE, Asborg Jørgine, f.
26/6-12 Enningdal, Idd, død 8/9-34, d.
av formann Hans Jørgen Jensen B. (1877-
1953) og Helga Axel sen (1888-1916).

<image>

BROGGER, Niels Christian Ursin,
forfatter, Oslo, f. 4/6-14 sst., s. av pro-
fessor Anton Wilhelm B. (1884-1951) og
Inger Ursin (1882-1941). Gift 1943 med
Vesla (Regine) Stenersen, f. 26/1-14
Oslo, d. av artillerikaptein Fredrik S. –
Ekteskap opplyst 1949. Gift på ny 1952
med Else Lødrup, f. 21/6-27, d. av gros-
serer Trygve L. – Barn: Fredrik 23/4-
45, Nina 15/4-53.
Fb/L – Studerte litteraturhistorie i
Oslo og London 1932-34. Studerelse
med stipendium til London 1938. Kor-
tere studieopphold i Italia 1935 og Spap-
nia 1936 før borgerkrigen brøt ut. –
Gikk over til forfatterskapet og journa-
listikken 1937. Litteraturanmelder «Ti-
dens Tegn» 1934-40, dramatisk konsulent
Det Nye Teater 1938-40, teaterkritiker
«NNationen» 1945-55, litteraturanmelder
sst. 1945-. Fast teaterkronikør «Norsk
Dameblad» 1954-, og løssløppen kronikør
i «Dagbladet», «Morgenbladet», «Aften-
posten», «Verdens Gang» og «Morgen-
posten» siden 1945. Free lancer med
leilighetsjobber som litterær konsulent
for flere forlag. – «Har skrevet i alt 11
bøker om litterære, historiske, psykO-
<image>

47
```"""