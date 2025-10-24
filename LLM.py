# Install the required library (if not already installed)
# !pip install transformers torch

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# 1. Load a pretrained small LLM (DistilGPT-2)
model_name = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# 2. Prepare a prompt
prompt = "In the future, artificial intelligence will"

# 3. Tokenize the input text
inputs = tokenizer(prompt, return_tensors="pt")

# 4. Generate text continuation
outputs = model.generate(
    **inputs,
    max_length=60,         # total output length
    temperature=0.7,       # randomness (lower = more deterministic)
    top_p=0.9,             # nucleus sampling (controls diversity)
    do_sample=True,        # enable sampling instead of greedy decoding
    repetition_penalty=1.2 # discourages repeating phrases
)

# 5. Decode and print the result
generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("\n🧠 Prompt:\n", prompt)
print("\n💬 Generated Text:\n", generated_text)

# 6. (Optional) Inspect tokenization
tokens = tokenizer.tokenize(prompt)
print("\n🔤 Tokens:\n", tokens)
