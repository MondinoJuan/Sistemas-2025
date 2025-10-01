import google.generativeai as genai

genai.configure(api_key="AIzaSyDYm3CM1vnyj2V5OZij43LeHjPadrT5tN0")

model = "models/embedding-001"
text = "El clima en Rosario es soleado"

result = genai.embed_content(model=model, content=text)
print(result['embedding'][:10])  # muestra los primeros 10 valores del vector
