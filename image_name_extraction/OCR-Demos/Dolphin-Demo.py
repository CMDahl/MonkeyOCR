from transformers import AutoTokenizer, AutoModelForVision2Seq
model_path = "ByteDance/Dolphin"
model_cache_dir = r'D:\models\LLMs\hub'


model = AutoModelForVision2Seq.from_pretrained(
    model_path, 
    torch_dtype="auto", 
    device_map="cuda:1", 
    low_cpu_mem_usage=True,
    cache_dir=model_cache_dir,
    trust_remote_code=True    
    
)
model.eval()

tokenizer = AutoTokenizer.from_pretrained(model_path)