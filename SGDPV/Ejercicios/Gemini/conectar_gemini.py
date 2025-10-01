import google.generativeai as genai

# Configurar API_KEY
genai.configure(api_key='AIzaSyDYm3CM1vnyj2V5OZij43LeHjPadrT5tN0')

'''print("-------------------------------------------------------------------")
for model in genai.list_models():
    print(f"Modelo: {model.display_name} ({model.name})")
    print(f"Descripción: {model.description}")
    
    if "generateContent" in model.supported_generation_methods:
        print("   ➤ Puede generar texto e interpretar prompts.")
    if "embedContent" in model.supported_generation_methods:
        print("   ➤ Sirve para embeddings (vectorizar texto).")
    if "countTokens" in model.supported_generation_methods:
        print("   ➤ Puede calcular cuántos tokens tiene un input.")
    if "generateImage" in model.supported_generation_methods:
        print("   ➤ Genera imágenes a partir de prompts.")
    
    print(f"Límite de entrada: {model.input_token_limit} tokens")
    print(f"Límite de salida: {model.output_token_limit} tokens")
    print("-" * 60)
print("-------------------------------------------------------------------")'''

# Crear el modelo especifico
modelo = genai.GenerativeModel('gemini-2.5-flash')

# Generar contenido usando el modelo
'''response = modelo.generate_content("¿A qué departamento de argentina corresponden las siguientes coordenadas? " \
                                    "Coordenadas: -34.6037, -58.3816" \
                                    "Además, dame los datos climáticos de los últimos 3 meses en una tabla.")'''

#response = modelo.generate_content("¿Qué otros métodos tiene la libreria google.generativeai que puedan ser interesantes?")
response = modelo.generate_content("La libreria google.generativeai, como se imprime lo recuperado en genai.list_models()?")

print(response.text)