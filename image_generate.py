from diffusers import StableDiffusionPipeline
import torch

# Load the model (this will download it once)
model_id = "runwayml/stable-diffusion-v1-5"

# Load pipeline
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")

# Get a prompt from user
prompt = input("Enter your prompt: ")

# Generate the image
image = pipe(prompt).images[0]

# Save and show
image.save("generated_image.png")
print("✅ Image generated and saved as 'generated_image.png'")
image.show()
