#!/usr/bin/env python3
"""
Script para recopilar datos de tráfico de la rotonda Charles de Gaulle
Utiliza múltiples fuentes de datos: Google Maps, HERE Maps, y OpenRouteService
"""

import requests
import json
import time
import datetime
import pandas as pd
import os
from typing import Dict, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrafficDataCollector:
    def __init__(self):
        # Coordenadas de la Place Charles de Gaulle-Étoile
        self.location = {
            'lat': 48.8738,
            'lng': 2.2950
        }
        
        # Radio para buscar datos de tráfico (en metros)
        self.radius = 500
        
        # APIs keys (debes configurar estas variables de entorno)
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.here_api_key = os.getenv('HERE_API_KEY')
        self.ors_api_key = os.getenv('OPENROUTESERVICE_API_KEY')
        
        # Archivo para guardar datos
        self.data_file = 'traffic_data_charles_de_gaulle.csv'
        
    def get_google_traffic_data(self) -> Optional[Dict]:
        """
        Obtiene datos de tráfico usando Google Maps Roads API y Distance Matrix API
        """
        if not self.google_api_key:
            logger.warning("Google API key no configurada")
            return None
            
        try:
            # Usar Distance Matrix API para obtener duraciones con tráfico
            origin = f"{self.location['lat']},{self.location['lng']}"
            destinations = [
                "48.8758,2.2950",  # Norte
                "48.8718,2.2950",  # Sur
                "48.8738,2.2970",  # Este
                "48.8738,2.2930"   # Oeste
            ]
            
            traffic_data = []
            
            for dest in destinations:
                url = "https://maps.googleapis.com/maps/api/distancematrix/json"
                params = {
                    'origins': origin,
                    'destinations': dest,
                    'departure_time': 'now',
                    'traffic_model': 'best_guess',
                    'key': self.google_api_key
                }
                
                response = requests.get(url, params=params)
                data = response.json()
                
                if data['status'] == 'OK':
                    element = data['rows'][0]['elements'][0]
                    if element['status'] == 'OK':
                        duration_normal = element['duration']['value']
                        duration_traffic = element.get('duration_in_traffic', {}).get('value', duration_normal)
                        
                        # Calcular factor de congestión
                        congestion_factor = duration_traffic / duration_normal if duration_normal > 0 else 1.0
                        
                        traffic_data.append({
                            'destination': dest,
                            'duration_normal': duration_normal,
                            'duration_traffic': duration_traffic,
                            'congestion_factor': congestion_factor
                        })
                
                # Pausa para evitar rate limiting
                time.sleep(0.1)
            
            # Calcular promedio de congestión
            if traffic_data:
                avg_congestion = sum(td['congestion_factor'] for td in traffic_data) / len(traffic_data)
                return {
                    'source': 'google',
                    'avg_congestion_factor': avg_congestion,
                    'details': traffic_data
                }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de Google: {e}")
            
        return None
    
    def get_here_traffic_data(self) -> Optional[Dict]:
        """
        Obtiene datos de tráfico usando HERE Traffic API
        """
        if not self.here_api_key:
            logger.warning("HERE API key no configurada")
            return None
            
        try:
            # HERE Traffic Flow API
            url = "https://traffic.ls.hereapi.com/traffic/6.3/flow.json"
            params = {
                'prox': f"{self.location['lat']},{self.location['lng']},{self.radius}",
                'responseattributes': 'sh,fc',
                'apikey': self.here_api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'RWS' in data and len(data['RWS']) > 0:
                traffic_items = []
                
                for rws in data['RWS']:
                    if 'RW' in rws:
                        for rw in rws['RW']:
                            if 'FIS' in rw:
                                for fis in rw['FIS']:
                                    if 'FI' in fis:
                                        for fi in fis['FI']:
                                            cf = fi.get('CF', [{}])[0]
                                            speed = cf.get('SP', 0)  # Velocidad actual
                                            free_flow = cf.get('FF', 0)  # Velocidad libre
                                            jam_factor = cf.get('JF', 0)  # Factor de embotellamiento
                                            
                                            traffic_items.append({
                                                'speed': speed,
                                                'free_flow_speed': free_flow,
                                                'jam_factor': jam_factor,
                                                'congestion_factor': free_flow / speed if speed > 0 else 1.0
                                            })
                
                if traffic_items:
                    avg_congestion = sum(ti['congestion_factor'] for ti in traffic_items) / len(traffic_items)
                    avg_jam_factor = sum(ti['jam_factor'] for ti in traffic_items) / len(traffic_items)
                    
                    return {
                        'source': 'here',
                        'avg_congestion_factor': avg_congestion,
                        'avg_jam_factor': avg_jam_factor,
                        'details': traffic_items
                    }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de HERE: {e}")
            
        return None
    
    def get_openrouteservice_data(self) -> Optional[Dict]:
        """
        Obtiene datos usando OpenRouteService (alternativa gratuita)
        """
        if not self.ors_api_key:
            logger.warning("OpenRouteService API key no configurada")
            return None
            
        try:
            # Calcular rutas desde el centro hacia diferentes puntos
            url = "https://api.openrouteservice.org/v2/directions/driving-car"
            headers = {
                'Authorization': self.ors_api_key,
                'Content-Type': 'application/json'
            }
            
            coordinates = [
                [[self.location['lng'], self.location['lat']], [2.2970, 48.8758]],  # Norte
                [[self.location['lng'], self.location['lat']], [2.2970, 48.8718]],  # Sur
                [[self.location['lng'], self.location['lat']], [2.2990, 48.8738]],  # Este
                [[self.location['lng'], self.location['lat']], [2.2910, 48.8738]]   # Oeste
            ]
            
            route_data = []
            
            for coords in coordinates:
                body = {
                    "coordinates": coords,
                    "radiuses": [500, 500],
                    "instructions": False
                }
                
                response = requests.post(url, json=body, headers=headers)
                data = response.json()
                
                if 'routes' in data and len(data['routes']) > 0:
                    route = data['routes'][0]
                    duration = route['summary']['duration']  # en segundos
                    distance = route['summary']['distance']  # en metros
                    
                    # Calcular velocidad promedio
                    avg_speed = (distance / 1000) / (duration / 3600) if duration > 0 else 0  # km/h
                    
                    route_data.append({
                        'duration': duration,
                        'distance': distance,
                        'avg_speed': avg_speed
                    })
                
                time.sleep(0.1)
            
            if route_data:
                overall_avg_speed = sum(rd['avg_speed'] for rd in route_data) / len(route_data)
                # Asumir velocidad libre de 50 km/h en zona urbana
                free_flow_speed = 50
                congestion_factor = free_flow_speed / overall_avg_speed if overall_avg_speed > 0 else 1.0
                
                return {
                    'source': 'openrouteservice',
                    'avg_speed': overall_avg_speed,
                    'congestion_factor': congestion_factor,
                    'details': route_data
                }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de OpenRouteService: {e}")
            
        return None
    
    def collect_traffic_sample(self) -> Dict:
        """
        Recopila una muestra completa de datos de tráfico
        """
        timestamp = datetime.datetime.now()
        
        logger.info(f"Recopilando datos de tráfico para {timestamp}")
        
        # Obtener datos de todas las fuentes
        google_data = self.get_google_traffic_data()
        here_data = self.get_here_traffic_data()
        ors_data = self.get_openrouteservice_data()
        
        # Compilar resultado
        sample = {
            'timestamp': timestamp.isoformat(),
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),  # 0=Lunes, 6=Domingo
            'google_data': google_data,
            'here_data': here_data,
            'ors_data': ors_data
        }
        
        # Calcular factor de congestión promedio
        congestion_factors = []
        if google_data and 'avg_congestion_factor' in google_data:
            congestion_factors.append(google_data['avg_congestion_factor'])
        if here_data and 'avg_congestion_factor' in here_data:
            congestion_factors.append(here_data['avg_congestion_factor'])
        if ors_data and 'congestion_factor' in ors_data:
            congestion_factors.append(ors_data['congestion_factor'])
        
        if congestion_factors:
            sample['avg_congestion_factor'] = sum(congestion_factors) / len(congestion_factors)
        else:
            sample['avg_congestion_factor'] = None
        
        return sample
    
    def save_data(self, sample: Dict):
        """
        Guarda los datos en CSV
        """
        # Preparar fila para CSV
        row = {
            'timestamp': sample['timestamp'],
            'hour': sample['hour'],
            'day_of_week': sample['day_of_week'],
            'avg_congestion_factor': sample['avg_congestion_factor']
        }
        
        # Agregar datos específicos de cada fuente
        if sample['google_data']:
            row['google_congestion'] = sample['google_data']['avg_congestion_factor']
        if sample['here_data']:
            row['here_congestion'] = sample['here_data']['avg_congestion_factor']
            if 'avg_jam_factor' in sample['here_data']:
                row['here_jam_factor'] = sample['here_data']['avg_jam_factor']
        if sample['ors_data']:
            row['ors_congestion'] = sample['ors_data']['congestion_factor']
            row['ors_avg_speed'] = sample['ors_data']['avg_speed']
        
        # Crear DataFrame
        df = pd.DataFrame([row])
        
        # Guardar en CSV (agregar si existe, crear si no existe)
        if os.path.exists(self.data_file):
            df.to_csv(self.data_file, mode='a', header=False, index=False)
        else:
            df.to_csv(self.data_file, index=False)
        
        logger.info(f"Datos guardados en {self.data_file}")
    
    def run_continuous_collection(self, interval_minutes: int = 15, duration_hours: int = 24):
        """
        Ejecuta recopilación continua de datos
        """
        logger.info(f"Iniciando recopilación continua por {duration_hours} horas, cada {interval_minutes} minutos")
        
        end_time = datetime.datetime.now() + datetime.timedelta(hours=duration_hours)
        
        while datetime.datetime.now() < end_time:
            try:
                # Recopilar muestra
                sample = self.collect_traffic_sample()
                
                # Guardar datos
                self.save_data(sample)
                
                # Esperar hasta la próxima recopilación
                logger.info(f"Próxima recopilación en {interval_minutes} minutos...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("Recopilación interrumpida por el usuario")
                break
            except Exception as e:
                logger.error(f"Error durante la recopilación: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    def analyze_data(self):
        """
        Analiza los datos recopilados y genera estadísticas por hora
        """
        if not os.path.exists(self.data_file):
            logger.error(f"Archivo de datos {self.data_file} no encontrado")
            return
        
        df = pd.read_csv(self.data_file)
        
        if df.empty:
            logger.error("No hay datos para analizar")
            return
        
        # Análisis por hora
        hourly_stats = df.groupby('hour').agg({
            'avg_congestion_factor': ['mean', 'std', 'count'],
            'google_congestion': 'mean',
            'here_congestion': 'mean',
            'ors_congestion': 'mean'
        }).round(3)
        
        print("\n=== ANÁLISIS DE TRÁFICO POR HORA ===")
        print("Horas pico (mayor factor de congestión):")
        print(hourly_stats.sort_values(('avg_congestion_factor', 'mean'), ascending=False))
        
        # Guardar análisis
        analysis_file = 'traffic_analysis_charles_de_gaulle.csv'
        hourly_stats.to_csv(analysis_file)
        logger.info(f"Análisis guardado en {analysis_file}")

def main():
    """
    Función principal
    """
    collector = TrafficDataCollector()
    
    print("=== RECOPILADOR DE DATOS DE TRÁFICO - CHARLES DE GAULLE ===")
    print("Opciones:")
    print("1. Recopilar una muestra única")
    print("2. Recopilación continua")
    print("3. Analizar datos existentes")
    
    choice = input("Selecciona una opción (1-3): ").strip()
    
    if choice == "1":
        # Muestra única
        sample = collector.collect_traffic_sample()
        print(f"\nDatos recopilados:")
        print(json.dumps(sample, indent=2, default=str))
        collector.save_data(sample)
        
    elif choice == "2":
        # Recopilación continua
        try:
            interval = int(input("Intervalo en minutos (por defecto 15): ") or "15")
            duration = int(input("Duración en horas (por defecto 24): ") or "24")
            collector.run_continuous_collection(interval, duration)
        except ValueError:
            print("Valores inválidos, usando valores por defecto")
            collector.run_continuous_collection()
            
    elif choice == "3":
        # Análisis
        collector.analyze_data()
        
    else:
        print("Opción inválida")

if __name__ == "__main__":
    main()