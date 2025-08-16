#!/usr/bin/env python3
"""
Script para configurar las APIs necesarias para recopilar datos de tráfico
"""

import os
import requests

def setup_environment_variables():
    """
    Guía para configurar las variables de entorno
    """
    print("=== CONFIGURACIÓN DE APIs ===\n")
    
    print("Para usar este sistema necesitas configurar las siguientes APIs:")
    print("Puedes usar una o todas según tu presupuesto y necesidades.\n")
    
    # Google Maps API
    print("1. GOOGLE MAPS API")
    print("   - Costo: Primeras 200 consultas/día gratis")
    print("   - URL: https://console.cloud.google.com/")
    print("   - Habilita: Distance Matrix API, Roads API")
    print("   - Variable de entorno: GOOGLE_MAPS_API_KEY")
    
    google_key = input("   Ingresa tu Google API Key (o Enter para omitir): ").strip()
    if google_key:
        os.environ['GOOGLE_MAPS_API_KEY'] = google_key
        print("   ✓ Google API Key configurada temporalmente")
    print()
    
    # HERE API
    print("2. HERE MAPS API")
    print("   - Costo: 250,000 transacciones/mes gratis")
    print("   - URL: https://developer.here.com/")
    print("   - API: Traffic Flow API")
    print("   - Variable de entorno: HERE_API_KEY")
    
    here_key = input("   Ingresa tu HERE API Key (o Enter para omitir): ").strip()
    if here_key:
        os.environ['HERE_API_KEY'] = here_key
        print("   ✓ HERE API Key configurada temporalmente")
    print()
    
    # OpenRouteService
    print("3. OPENROUTESERVICE API")
    print("   - Costo: 2000 consultas/día gratis")
    print("   - URL: https://openrouteservice.org/")
    print("   - Variable de entorno: OPENROUTESERVICE_API_KEY")
    
    ors_key = input("   Ingresa tu OpenRouteService API Key (o Enter para omitir): ").strip()
    if ors_key:
        os.environ['OPENROUTESERVICE_API_KEY'] = ors_key
        print("   ✓ OpenRouteService API Key configurada temporalmente")
    print()
    
    print("NOTA IMPORTANTE:")
    print("Las claves configuradas aquí son temporales (solo para esta sesión).")
    print("Para uso permanente, agrega estas líneas a tu archivo ~/.bashrc o ~/.zshrc:")
    print()
    
    if google_key:
        print(f"export GOOGLE_MAPS_API_KEY='{google_key}'")
    if here_key:
        print(f"export HERE_API_KEY='{here_key}'")
    if ors_key:
        print(f"export OPENROUTESERVICE_API_KEY='{ors_key}'")
    print()

def test_api_keys():
    """
    Prueba las APIs configuradas
    """
    print("=== PRUEBA DE APIs ===\n")
    
    # Coordenadas de prueba (Charles de Gaulle)
    test_lat, test_lng = 48.8738, 2.2950
    
    # Test Google Maps
    google_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if google_key:
        print("Probando Google Maps API...")
        try:
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                'origins': f'{test_lat},{test_lng}',
                'destinations': f'{test_lat + 0.001},{test_lng}',
                'key': google_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'OK':
                    print("  ✓ Google Maps API funcionando correctamente")
                else:
                    print(f"  ✗ Google Maps API error: {data.get('status')}")
            else:
                print(f"  ✗ Google Maps API HTTP error: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Google Maps API error: {e}")
    else:
        print("  - Google Maps API no configurada")
    
    # Test HERE API
    here_key = os.getenv('HERE_API_KEY')
    if here_key:
        print("Probando HERE Maps API...")
        try:
            url = "https://traffic.ls.hereapi.com/traffic/6.3/flow.json"
            params = {
                'prox': f'{test_lat},{test_lng},100',
                'apikey': here_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                print("  ✓ HERE Maps API funcionando correctamente")
            else:
                print(f"  ✗ HERE Maps API HTTP error: {response.status_code}")
        except Exception as e:
            print(f"  ✗ HERE Maps API error: {e}")
    else:
        print("  - HERE Maps API no configurada")
    
    # Test OpenRouteService
    ors_key = os.getenv('OPENROUTESERVICE_API_KEY')
    if ors_key:
        print("Probando OpenRouteService API...")
        try:
            url = "https://api.openrouteservice.org/v2/directions/driving-car"
            headers = {
                'Authorization': ors_key,
                'Content-Type': 'application/json'
            }
            body = {
                "coordinates": [[test_lng, test_lat], [test_lng + 0.001, test_lat]],
                "instructions": False
            }
            response = requests.post(url, json=body, headers=headers, timeout=10)
            if response.status_code == 200:
                print("  ✓ OpenRouteService API funcionando correctamente")
            else:
                print(f"  ✗ OpenRouteService API HTTP error: {response.status_code}")
        except Exception as e:
            print(f"  ✗ OpenRouteService API error: {e}")
    else:
        print("  - OpenRouteService API no configurada")
    
    print()

def get_free_alternatives():
    """
    Muestra alternativas gratuitas y datos públicos disponibles
    """
    print("=== ALTERNATIVAS GRATUITAS ===\n")
    
    print("Si no quieres usar APIs de pago, considera estas opciones:")
    print()
    
    print("1. DATOS PÚBLICOS DE FRANCIA:")
    print("   - data.gouv.fr: Datos abiertos del gobierno francés")
    print("   - Île-de-France Mobilités: Datos de transporte público")
    print("   - URL: https://prim.iledefrance-mobilites.fr/")
    print()
    
    print("2. OVERPASS API (OpenStreetMap):")
    print("   - Gratis, datos de OpenStreetMap")
    print("   - Útil para obtener geometría de carreteras")
    print("   - No incluye datos de tráfico en tiempo real")
    print()
    
    print("3. TOMTOM API:")
    print("   - 2500 consultas/día gratis")
    print("   - Traffic Flow API disponible")
    print("   - URL: https://developer.tomtom.com/")
    print()
    
    print("4. MAPBOX API:")
    print("   - 100,000 consultas/mes gratis")
    print("   - Traffic API disponible")
    print("   - URL: https://www.mapbox.com/")
    print()

def create_requirements_file():
    """
    Crea archivo requirements.txt
    """
    requirements = [
        "requests>=2.25.0",
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "matplotlib>=3.4.0",
        "seaborn>=0.11.0"
    ]
    
    with open('requirements.txt', 'w') as f:
        f.write('\n'.join(requirements))
    
    print("Archivo requirements.txt creado.")
    print("Para instalar dependencias ejecuta: pip install -r requirements.txt")
    print()

def main():
    choice = 9

    while choice != 0:
        """
        Función principal
        """
        print("CONFIGURADOR DE APIs PARA DATOS DE TRÁFICO\n")
        
        print("Opciones:")
        print("1. Configurar APIs")
        print("2. Probar APIs configuradas")
        print("3. Ver alternativas gratuitas")
        print("4. Crear archivo requirements.txt")
        print("0. Salir")
        
        choice = input("Selecciona una opción (1-4): ").strip()
        
        if choice == "1":
            setup_environment_variables()
        elif choice == "2":
            test_api_keys()
        elif choice == "3":
            get_free_alternatives()
        elif choice == "4":
            create_requirements_file()
        elif choice == "0":
            print("Saliendo del configurador...")
            break
        else:
            print("Opción inválida")

if __name__ == "__main__":
    main()