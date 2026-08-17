from google import genai

client = genai.Client(api_key="")
for model in client.models.list():
    if "embed" in model.name:
        print(model.name)
