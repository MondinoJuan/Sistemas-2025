#!/usr/bin/env python3
"""
Alternativas gratuitas para obtener datos de tráfico usando fuentes públicas
y APIs gratuitas para la simulación de la rotonda Charles de Gaulle
"""

import requests
import json
import datetime
import pandas as pd
import os
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FreeTrafficDataCollector:
    def __init__(self):
        # Coordenadas de la Place Charles de Gaulle-Étoile
        self.location = {
            'lat': 48.8738,
            'lng': 2.2950
        }
        
        # Área de búsqueda expandida para capturar tráfico relevante
        self.bbox = {
            'north': 48.8788,  # +0.005
            'south': 48.8688,  # -0.005
            'east': 2.3000,    # +0.005  
            'west': 2.2900     # -0.005
        }
        
    def get_overpass_road_data(self) -> Optional[Dict]:
        """
        Obtiene datos de carreteras desde OpenStreetMap via Overpass API
        Útil para conocer la estructura vial, aunque no incluye tráfico real
        """
        try:
            # Query para obtener carreteras principales en el área
            overpass_query = f"""
            [out:json][timeout:25];
            (
              way["highway"~"^(motorway|trunk|primary|secondary)$"]
                  ({self.bbox['south']},{self.bbox['west']},{self.bbox['north']},{self.bbox['east']});
              way["highway"="motorway_link"]
                  ({self.bbox['south']},{self.bbox['west']},{self.bbox['north']},{self.bbox['east']});
            );
            out geom;
            """
            
            url = "http://overpass-api.de/api/interpreter"
            response = requests.post(url, data={'data': overpass_query}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                roads_info = []
                for element in data.get('elements', []):
                    if element['type'] == 'way':
                        tags = element.get('tags', {})
                        geometry = element.get('geometry', [])
                        
                        # Estimar capacidad basada en tipo de carretera
                        highway_type = tags.get('highway', 'unknown')
                        lanes = tags.get('lanes', '2')
                        
                        capacity_factor = {
                            'motorway': 1.5,
                            'trunk': 1.3,
                            'primary': 1.1,
                            'secondary': 1.0,
                            'motorway_link': 1.2
                        }.get(highway_type, 1.0)
                        
                        roads_info.append({
                            'id': element['id'],
                            'highway_type': highway_type,
                            'lanes': lanes,
                            'capacity_factor': capacity_factor,
                            'geometry': geometry
                        })
                
                return {
                    'source': 'overpass_osm',
                    'roads_count': len(roads_info),
                    'roads_data': roads_info,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo datos de Overpass: {e}")
            
        return None
    
    def get_paris_open_data(self) -> Optional[Dict]:
        """
        Intenta obtener datos de tráfico de fuentes abiertas de París
        """
        try:
            # API de datos abiertos de París - Tráfico
            # Nota: Esta URL puede cambiar, verificar en data.gouv.fr
            urls_to_try = [
                "https://opendata.paris.fr/api/records/1.0/search/?dataset=comptages-routiers-permanents",
                "https://parisdata.opendatasoft.com/api/records/1.0/search/?dataset=comptages-routiers-permanents"
            ]
            
            for url in urls_to_try:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        relevant_stations = []
                        for record in data.get('records', []):
                            fields = record.get('fields', {})
                            geometry = record.get('geometry', {})
                            
                            if geometry and 'coordinates' in geometry:
                                lon, lat = geometry['coordinates']
                                
                                # Verificar si está cerca de Charles de Gaulle
                                if (abs(lat - self.location['lat']) < 0.01 and 
                                    abs(lon - self.location['lng']) < 0.01):
                                    
                                    relevant_stations.append({
                                        'station_id': fields.get('id_arc_tra'),
                                        'name': fields.get('libelle'),
                                        'coordinates': [lon, lat],
                                        'traffic_data': fields
                                    })
                        
                        if relevant_stations:
                            return {
                                'source': 'paris_open_data',
                                'stations_found': len(relevant_stations),
                                'stations': relevant_stations,
                                'timestamp': datetime.datetime.now().isoformat()
                            }
                
                except requests.RequestException:
                    continue
                    
        except Exception as e:
            logger.error(f"Error obteniendo datos abiertos de París: {e}")
            
        return None
    
    def get_tomtom_free_data(self) -> Optional[Dict]:
        """
        Usa la capa gratuita de TomTom API
        Requiere registro pero ofrece 2500 consultas/día gratis
        """
        api_key = os.getenv('TOMTOM_API_KEY')
        if not api_key:
            logger.warning("TomTom API key no configurada")
            return None
            
        try:
            # Traffic Flow API
            url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
            params = {
                'point': f"{self.location['lat']},{self.location['lng']}",
                'unit': 'KMPH',
                'key': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                flow_data = data.get('flowSegmentData', {})
                
                current_speed = flow_data.get('currentSpeed', 0)
                free_flow_speed = flow_data.get('freeFlowSpeed', 50)  # Asumir 50 km/h si no hay datos
                current_travel_time = flow_data.get('currentTravelTime', 0)
                free_flow_travel_time = flow_data.get('freeFlowTravelTime', 0)
                
                congestion_factor = free_flow_speed / current_speed if current_speed > 0 else 1.0
                
                return {
                    'source': 'tomtom',
                    'current_speed': current_speed,
                    'free_flow_speed': free_flow_speed,
                    'congestion_factor': congestion_factor,
                    'current_travel_time': current_travel_time,
                    'free_flow_travel_time': free_flow_travel_time,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo datos de TomTom: {e}")
            
        return None
    
    def get_mapbox_free_data(self) -> Optional[Dict]:
        """
        Usa Mapbox Traffic API (100k consultas/mes gratis)
        """
        api_key = os.getenv('MAPBOX_API_KEY')
        if not api_key:
            logger.warning("Mapbox API key no configurada")
            return None
            
        try:
            # Mapbox Directions API con tráfico
            coordinates = f"{self.location['lng']},{self.location['lat']};{self.location['lng']+0.001},{self.location['lat']}"
            url = f"https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{coordinates}"
            
            params = {
                'access_token': api_key,
                'geometries': 'geojson',
                'annotations': 'duration,distance,speed'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                routes = data.get('routes', [])
                
                if routes:
                    route = routes[0]
                    duration = route.get('duration', 0)  # segundos
                    distance = route.get('distance', 0)  # metros
                    
                    # Calcular velocidad promedio
                    avg_speed = (distance / 1000) / (duration / 3600) if duration > 0 else 0  # km/h
                    
                    # Estimar factor de congestión (asumiendo velocidad libre de 50 km/h)
                    free_flow_speed = 50
                    congestion_factor = free_flow_speed / avg_speed if avg_speed > 0 else 1.0
                    
                    return {
                        'source': 'mapbox',
                        'duration': duration,
                        'distance': distance,
                        'avg_speed': avg_speed,
                        'congestion_factor': congestion_factor,
                        'timestamp': datetime.datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Error obteniendo datos de Mapbox: {e}")
            
        return None
    
    def generate_synthetic_data(self) -> Dict:
        """
        Genera datos sintéticos basados en patrones típicos de tráfico urbano
        Útil cuando no hay APIs disponibles
        """
        now = datetime.datetime.now()
        hour = now.hour
        day_of_week = now.weekday()  # 0=Lunes, 6=Domingo
        
        # Patrones típicos para rotonda urbana principal
        base_congestion = 1.0
        
        # Factor por hora del día
        hourly_factors = {
            0: 0.3, 1: 0.2, 2: 0.2, 3: 0.2, 4: 0.3, 5: 0.5,
            6: 0.8, 7: 1.3, 8: 1.6, 9: 1.4, 10: 1.2, 11: 1.1,
            12: 1.3, 13: 1.2, 14: 1.1, 15: 1.2, 16: 1.4, 17: 1.7,
            18: 1.8, 19: 1.5, 20: 1.2, 21: 0.9, 22: 0.7, 23: 0.5
        }
        
        # Factor por día de la semana
        weekly_factors = {
            0: 1.1,  # Lunes
            1: 1.2,  # Martes
            2: 1.2,  # Miércoles
            3: 1.2,  # Jueves
            4: 1.3,  # Viernes
            5: 0.8,  # Sábado
            6: 0.6   # Domingo
        }
        
        # Calcular factor de congestión
        hour_factor = hourly_factors.get(hour, 1.0)
        week_factor = weekly_factors.get(day_of_week, 1.0)
        
        # Agregar variabilidad aleatoria
        import random
        random_variation = random.uniform(0.85, 1.15)
        
        final_congestion = base_congestion + (hour_factor * week_factor * random_variation - 1.0)
        final_congestion = max(0.5, min(3.0, final_congestion))  # Limitar entre 0.5 y 3.0
        
        return {
            'source': 'synthetic',
            'congestion_factor': final_congestion,
            'hour_factor': hour_factor,
            'week_factor': week_factor,
            'random_variation': random_variation,
            'estimated_speed': 50 / final_congestion,  # km/h
            'timestamp': now.isoformat()
        }
    
    def collect_all_free_sources(self) -> Dict:
        """
        Recopila datos de todas las fuentes gratuitas disponibles
        """
        logger.info("Recopilando datos de fuentes gratuitas...")
        
        results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'location': self.location,
            'sources': {}
        }
        
        # 1. Datos de OpenStreetMap (estructura vial)
        logger.info("Obteniendo datos de OpenStreetMap...")
        osm_data = self.get_overpass_road_data()
        if osm_data:
            results['sources']['openstreetmap'] = osm_data
            logger.info("✓ Datos de OpenStreetMap obtenidos")
        else:
            logger.warning("✗ No se pudieron obtener datos de OpenStreetMap")
        
        # 2. Datos abiertos de París
        logger.info("Intentando obtener datos abiertos de París...")
        paris_data = self.get_paris_open_data()
        if paris_data:
            results['sources']['paris_open_data'] = paris_data
            logger.info("✓ Datos abiertos de París obtenidos")
        else:
            logger.warning("✗ No se pudieron obtener datos abiertos de París")
        
        # 3. TomTom (si está configurado)
        logger.info("Intentando TomTom API...")
        tomtom_data = self.get_tomtom_free_data()
        if tomtom_data:
            results['sources']['tomtom'] = tomtom_data
            logger.info("✓ Datos de TomTom obtenidos")
        else:
            logger.warning("✗ TomTom API no disponible o no configurada")
        
        # 4. Mapbox (si está configurado)
        logger.info("Intentando Mapbox API...")
        mapbox_data = self.get_mapbox_free_data()
        if mapbox_data:
            results['sources']['mapbox'] = mapbox_data
            logger.info("✓ Datos de Mapbox obtenidos")
        else:
            logger.warning("✗ Mapbox API no disponible o no configurada")
        
        # 5. Datos sintéticos (siempre disponible)
        logger.info("Generando datos sintéticos...")
        synthetic_data = self.generate_synthetic_data()
        results['sources']['synthetic'] = synthetic_data
        logger.info("✓ Datos sintéticos generados")
        
        # Calcular factor de congestión promedio
        congestion_factors = []
        speed_values = []
        
        for source_name, source_data in results['sources'].items():
            if 'congestion_factor' in source_data:
                congestion_factors.append(source_data['congestion_factor'])
            
            # Extraer velocidades donde estén disponibles
            if 'estimated_speed' in source_data:
                speed_values.append(source_data['estimated_speed'])
            elif 'current_speed' in source_data:
                speed_values.append(source_data['current_speed'])
            elif 'avg_speed' in source_data:
                speed_values.append(source_data['avg_speed'])
        
        if congestion_factors:
            results['summary'] = {
                'avg_congestion_factor': sum(congestion_factors) / len(congestion_factors),
                'min_congestion_factor': min(congestion_factors),
                'max_congestion_factor': max(congestion_factors),
                'sources_with_congestion': len(congestion_factors)
            }
        
        if speed_values:
            results['summary']['avg_speed'] = sum(speed_values) / len(speed_values)
            results['summary']['sources_with_speed'] = len(speed_values)
        
        return results
    
    def save_free_data(self, data: Dict, filename: str = 'free_traffic_data.json'):
        """
        Guarda los datos recopilados en formato JSON
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Datos guardados en {filename}")
    
    def create_simulation_dataset(self, hours: int = 168):  # 1 semana por defecto
        """
        Crea un dataset completo para simulación usando datos sintéticos
        """
        logger.info(f"Creando dataset de simulación para {hours} horas...")
        
        start_time = datetime.datetime.now()
        dataset = []
        
        for h in range(hours):
            current_time = start_time + datetime.timedelta(hours=h)
            
            # Temporalmente cambiar la hora para generar datos sintéticos
            original_now = datetime.datetime.now
            datetime.datetime.now = lambda: current_time
            
            synthetic_data = self.generate_synthetic_data()
            
            # Restaurar datetime.now
            datetime.datetime.now = original_now
            
            dataset.append({
                'timestamp': current_time.isoformat(),
                'hour': current_time.hour,
                'day_of_week': current_time.weekday(),
                'congestion_factor': synthetic_data['congestion_factor'],
                'estimated_speed': synthetic_data['estimated_speed'],
                'hour_factor': synthetic_data['hour_factor'],
                'week_factor': synthetic_data['week_factor']
            })
        
        # Convertir a DataFrame y guardar
        df = pd.DataFrame(dataset)
        csv_filename = 'synthetic_traffic_simulation_data.csv'
        df.to_csv(csv_filename, index=False)
        
        logger.info(f"Dataset de simulación guardado en {csv_filename}")
        
        # Crear resumen estadístico
        summary = {
            'total_hours': hours,
            'start_time': start_time.isoformat(),
            'statistics': {
                'mean_congestion': df['congestion_factor'].mean(),
                'std_congestion': df['congestion_factor'].std(),
                'min_congestion': df['congestion_factor'].min(),
                'max_congestion': df['congestion_factor'].max(),
                'mean_speed': df['estimated_speed'].mean(),
                'std_speed': df['estimated_speed'].std()
            },
            'hourly_patterns': df.groupby('hour')['congestion_factor'].mean().to_dict(),
            'daily_patterns': df.groupby('day_of_week')['congestion_factor'].mean().to_dict()
        }
        
        # Guardar resumen
        with open('simulation_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info("Resumen estadístico guardado en simulation_summary.json")
        
        return df, summary

def setup_free_apis():
    """
    Guía para configurar APIs gratuitas
    """
    print("=== CONFIGURACIÓN DE APIs GRATUITAS ===\n")
    
    print("APIs gratuitas recomendadas para datos de tráfico:\n")
    
    print("1. TOMTOM API (2,500 consultas/día gratis)")
    print("   - Registro: https://developer.tomtom.com/")
    print("   - Crear app y obtener API key")
    print("   - Variable: TOMTOM_API_KEY")
    
    tomtom_key = input("   Ingresa tu TomTom API Key (Enter para omitir): ").strip()
    if tomtom_key:
        os.environ['TOMTOM_API_KEY'] = tomtom_key
        print("   ✓ TomTom API configurada")
    print()
    
    print("2. MAPBOX API (100,000 consultas/mes gratis)")
    print("   - Registro: https://account.mapbox.com/")
    print("   - Obtener access token")
    print("   - Variable: MAPBOX_API_KEY")
    
    mapbox_key = input("   Ingresa tu Mapbox Access Token (Enter para omitir): ").strip()
    if mapbox_key:
        os.environ['MAPBOX_API_KEY'] = mapbox_key
        print("   ✓ Mapbox API configurada")
    print()
    
    print("3. DATOS SINTÉTICOS")
    print("   - No requiere API")
    print("   - Basado en patrones típicos de tráfico")
    print("   - Siempre disponible como respaldo")
    print()
    
    print("NOTA: Las configuraciones son temporales para esta sesión.")
    print("Para uso permanente, agregar a variables de entorno del sistema.")

def main():
    """
    Función principal
    """
    print("=== RECOPILADOR DE DATOS DE TRÁFICO GRATUITO ===")
    print("Place Charles de Gaulle-Étoile, París\n")
    
    collector = FreeTrafficDataCollector()
    
    print("Opciones disponibles:")
    print("1. Configurar APIs gratuitas")
    print("2. Recopilar datos de una muestra")
    print("3. Crear dataset completo de simulación")
    print("4. Mostrar fuentes de datos disponibles")
    
    choice = input("\nSelecciona una opción (1-4): ").strip()
    
    if choice == "1":
        setup_free_apis()
        
    elif choice == "2":
        print("\nRecopilando datos de fuentes gratuitas...")
        data = collector.collect_all_free_sources()
        
        print(f"\n=== RESULTADOS ===")
        print(f"Fuentes consultadas: {len(data['sources'])}")
        
        if 'summary' in data:
            summary = data['summary']
            if 'avg_congestion_factor' in summary:
                print(f"Factor de congestión promedio: {summary['avg_congestion_factor']:.3f}")
            if 'avg_speed' in summary:
                print(f"Velocidad promedio: {summary['avg_speed']:.1f} km/h")
        
        # Mostrar detalles por fuente
        for source_name, source_data in data['sources'].items():
            print(f"\n{source_name.upper()}:")
            if 'congestion_factor' in source_data:
                print(f"  - Factor de congestión: {source_data['congestion_factor']:.3f}")
            if 'estimated_speed' in source_data:
                print(f"  - Velocidad estimada: {source_data['estimated_speed']:.1f} km/h")
            elif 'current_speed' in source_data:
                print(f"  - Velocidad actual: {source_data['current_speed']:.1f} km/h")
        
        # Guardar datos
        collector.save_free_data(data)
        
    elif choice == "3":
        hours = input("Número de horas para el dataset (default: 168 = 1 semana): ").strip()
        hours = int(hours) if hours.isdigit() else 168
        
        df, summary = collector.create_simulation_dataset(hours)
        
        print(f"\n=== DATASET CREADO ===")
        print(f"Total de registros: {len(df)}")
        print(f"Rango temporal: {hours} horas")
        print(f"Factor de congestión promedio: {summary['statistics']['mean_congestion']:.3f}")
        print(f"Velocidad promedio: {summary['statistics']['mean_speed']:.1f} km/h")
        
        # Mostrar horas pico
        hourly_patterns = summary['hourly_patterns']
        peak_hour = max(hourly_patterns, key=hourly_patterns.get)
        low_hour = min(hourly_patterns, key=hourly_patterns.get)
        
        print(f"\nHora pico: {peak_hour:02d}:00 (factor: {hourly_patterns[peak_hour]:.3f})")
        print(f"Hora de menor tráfico: {low_hour:02d}:00 (factor: {hourly_patterns[low_hour]:.3f})")
        
    elif choice == "4":
        print("\n=== FUENTES DE DATOS DISPONIBLES ===\n")
        
        print("GRATUITAS:")
        print("✓ Datos sintéticos - Siempre disponible")
        print("✓ OpenStreetMap via Overpass API - Estructura vial")
        print("✓ TomTom API - 2,500 consultas/día")
        print("✓ Mapbox API - 100,000 consultas/mes")
        print("? Datos abiertos de París - Disponibilidad variable")
        
        print("\nDE PAGO (con capas gratuitas):")
        print("• Google Maps API - 200 consultas/día")
        print("• HERE Maps API - 250,000 transacciones/mes")
        print("• OpenRouteService - 2,000 consultas/día")
        
        print("\nRECOMENDACIÓN:")
        print("Para simulación académica, usar datos sintéticos es suficiente.")
        print("Para validación, combinar con una API gratuita como TomTom.")
        
    else:
        print("Opción inválida")

if __name__ == "__main__":
    main()