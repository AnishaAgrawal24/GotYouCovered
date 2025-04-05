from transformers import pipeline
from transformers import AutoTokenizer
from peft import PeftModel, PeftConfig
from transformers import AutoModelForCausalLM , BitsAndBytesConfig
import torch

#config = PeftConfig.from_pretrained("ayoubkirouane/Llama2_13B_startup_hf")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=getattr(torch, "float16"),
    bnb_4bit_use_double_quant=False)
model = AutoModelForCausalLM.from_pretrained(
        "meta-llama/Llama-2-7b-hf",
        quantization_config=bnb_config,
        device_map={"": 0})
model.config.use_cache = False
model.config.pretraining_tp = 1
model = PeftModel.from_pretrained(model, "TuningAI/Llama2_7B_Cover_letter_generator")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf" , trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"
Instruction = "Given a user's information about the target job, you will generate a Cover letter for this job based on this information."   
while 1:
  input_text = input(">>>")
  logging.set_verbosity(logging.CRITICAL)
  prompt = f"### Instruction\n{Instruction}.\n ###Input \n\n{input_text}. ### Output:"
  pipe = pipeline(task="text-generation", model=model, tokenizer=tokenizer,max_length=400)
  result = pipe(prompt)
  print(result[0]['generated_text'].replace(prompt, ''))
