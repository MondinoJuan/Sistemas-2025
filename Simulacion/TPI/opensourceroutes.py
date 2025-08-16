import requests
import json
from datetime import datetime

# Tu API key de OpenRouteService
API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjM3YjRkMjE2MDE2MDQ0YWFiZGVmZjkxMTJkODNmNzBjIiwiaCI6Im11cm11cjY0In0="

# Coordenadas del Arco del Triunfo (lon, lat)
# Usamos un punto de entrada y uno de salida dentro de la rotonda para obtener tráfico aproximado
coordenadas = [
    [2.2946, 48.8738],  # Punto A
    [2.2955, 48.8738]   # Punto B
]

def obtener_trafico():
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "coordinates": coordenadas,
        "instructions": False  # No queremos pasos detallados
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(body))
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error al consultar OpenRouteService: {e}")
        return None

def main():
    print(f"Consultando tráfico en la rotonda del Arco del Triunfo ({datetime.now()})...")
    trafico = obtener_trafico()
    if trafico:
        # Imprime el JSON formateado
        print(json.dumps(trafico, indent=2))
        # Ejemplo: obtener duración estimada en segundos
        duracion_segundos = trafico['features'][0]['properties']['summary']['duration']
        print(f"\nDuración estimada del recorrido: {duracion_segundos:.0f} segundos")
    else:
        print("No se pudo recuperar la información de tráfico.")

if __name__ == "__main__":
    main()
