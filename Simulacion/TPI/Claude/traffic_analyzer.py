#!/usr/bin/env python3
"""
Analizador avanzado de datos de tráfico para la rotonda Charles de Gaulle
Genera gráficos y estadísticas detalladas
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import json

class TrafficAnalyzer:
    def __init__(self, data_file: str = 'traffic_data_charles_de_gaulle.csv'):
        self.data_file = data_file
        self.df = None
        
        # Configurar estilo de gráficos
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def load_data(self) -> bool:
        """
        Carga los datos desde el archivo CSV
        """
        if not os.path.exists(self.data_file):
            print(f"Error: Archivo {self.data_file} no encontrado")
            return False
        
        try:
            self.df = pd.read_csv(self.data_file)
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            self.df['date'] = self.df['timestamp'].dt.date
            print(f"Datos cargados: {len(self.df)} registros desde {self.df['timestamp'].min()} hasta {self.df['timestamp'].max()}")
            return True
        except Exception as e:
            print(f"Error cargando datos: {e}")
            return False
    
    def basic_statistics(self):
        """
        Muestra estadísticas básicas
        """
        if self.df is None:
            print("Error: No hay datos cargados")
            return
        
        print("\n=== ESTADÍSTICAS BÁSICAS ===")
        print(f"Período de datos: {self.df['timestamp'].min()} a {self.df['timestamp'].max()}")
        print(f"Total de registros: {len(self.df)}")
        print(f"Días únicos: {self.df['date'].nunique()}")
        
        if 'avg_congestion_factor' in self.df.columns:
            congestion_stats = self.df['avg_congestion_factor'].describe()
            print(f"\nFactor de congestión promedio:")
            print(congestion_stats)
    
    def hourly_analysis(self):
        """
        Análisis detallado por hora
        """
        if self.df is None:
            return
        
        print("\n=== ANÁLISIS POR HORA ===")
        
        # Agrupar por hora
        hourly_stats = self.df.groupby('hour').agg({
            'avg_congestion_factor': ['count', 'mean', 'std', 'min', 'max']
        }).round(3)
        
        hourly_stats.columns = ['Muestras', 'Promedio', 'Desv_Est', 'Mínimo', 'Máximo']
        
        # Identificar horas pico
        peak_hours = hourly_stats.nlargest(5, 'Promedio')
        low_hours = hourly_stats.nsmallest(5, 'Promedio')
        
        print("\nTOP 5 HORAS PICO (mayor congestión):")
        print(peak_hours)
        
        print("\nTOP 5 HORAS DE MENOR TRÁFICO:")
        print(low_hours)
        
        return hourly_stats
    
    def weekly_analysis(self):
        """
        Análisis por día de la semana
        """
        if self.df is None:
            return
        
        print("\n=== ANÁLISIS POR DÍA DE LA SEMANA ===")
        
        # Mapear días de la semana
        day_names = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 
                    4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
        
        self.df['day_name'] = self.df['day_of_week'].map(day_names)
        
        weekly_stats = self.df.groupby('day_name').agg({
            'avg_congestion_factor': ['count', 'mean', 'std']
        }).round(3)
        
        weekly_stats.columns = ['Muestras', 'Promedio', 'Desv_Est']
        
        # Ordenar por días de la semana
        day_order = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        weekly_stats = weekly_stats.reindex(day_order)
        
        print(weekly_stats)
        return weekly_stats
    
    def create_visualizations(self):
        """
        Crea visualizaciones de los datos de tráfico
        """
        if self.df is None:
            return
        
        # Configurar figura con múltiples subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Análisis de Tráfico - Place Charles de Gaulle-Étoile', fontsize=16)
        
        # 1. Tráfico por hora del día
        if 'avg_congestion_factor' in self.df.columns:
            hourly_data = self.df.groupby('hour')['avg_congestion_factor'].mean()
            axes[0, 0].plot(hourly_data.index, hourly_data.values, marker='o', linewidth=2, markersize=6)
            axes[0, 0].set_title('Factor de Congestión Promedio por Hora')
            axes[0, 0].set_xlabel('Hora del día')
            axes[0, 0].set_ylabel('Factor de congestión')
            axes[0, 0].grid(True, alpha=0.3)
            axes[0, 0].set_xticks(range(0, 24, 2))
        
        # 2. Heatmap por hora y día de la semana
        if 'day_name' in self.df.columns:
            pivot_data = self.df.pivot_table(
                values='avg_congestion_factor', 
                index='day_name', 
                columns='hour', 
                aggfunc='mean'
            )
            
            day_order = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            pivot_data = pivot_data.reindex(day_order)
            
            sns.heatmap(pivot_data, ax=axes[0, 1], cmap='YlOrRd', cbar_kws={'label': 'Factor de congestión'})
            axes[0, 1].set_title('Heatmap: Congestión por Día y Hora')
            axes[0, 1].set_xlabel('Hora del día')
            axes[0, 1].set_ylabel('Día de la semana')
        
        # 3. Distribución de factores de congestión
        if 'avg_congestion_factor' in self.df.columns:
            self.df['avg_congestion_factor'].hist(bins=30, ax=axes[1, 0], alpha=0.7, edgecolor='black')
            axes[1, 0].set_title('Distribución de Factores de Congestión')
            axes[1, 0].set_xlabel('Factor de congestión')
            axes[1, 0].set_ylabel('Frecuencia')
            axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Boxplot por día de la semana
        if 'day_name' in self.df.columns and 'avg_congestion_factor' in self.df.columns:
            day_order = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            sns.boxplot(data=self.df, x='day_name', y='avg_congestion_factor', 
                       order=day_order, ax=axes[1, 1])
            axes[1, 1].set_title('Distribución de Congestión por Día')
            axes[1, 1].set_xlabel('Día de la semana')
            axes[1, 1].set_ylabel('Factor de congestión')
            axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Guardar gráfico
        output_file = 'traffic_analysis_charts.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\nGráficos guardados en: {output_file}")
        
        plt.show()
    
    def time_series_analysis(self):
        """
        Análisis de series de tiempo
        """
        if self.df is None:
            return
        
        print("\n=== ANÁLISIS DE SERIES DE TIEMPO ===")
        
        # Crear serie temporal
        ts_data = self.df.set_index('timestamp')['avg_congestion_factor'].dropna()
        
        if len(ts_data) < 2:
            print("Datos insuficientes para análisis temporal")
            return
        
        # Estadísticas básicas de la serie
        print(f"Período: {ts_data.index.min()} a {ts_data.index.max()}")
        print(f"Valor promedio: {ts_data.mean():.3f}")
        print(f"Valor máximo: {ts_data.max():.3f} en {ts_data.idxmax()}")
        print(f"Valor mínimo: {ts_data.min():.3f} en {ts_data.idxmin()}")
        
        # Gráfico de serie temporal
        plt.figure(figsize=(12, 6))
        plt.plot(ts_data.index, ts_data.values, alpha=0.7, linewidth=1)
        plt.title('Serie Temporal - Factor de Congestión')
        plt.xlabel('Tiempo')
        plt.ylabel('Factor de congestión')
        plt.grid(True, alpha=0.3)
        
        # Agregar línea de tendencia si hay suficientes datos
        if len(ts_data) > 10:
            z = np.polyfit(range(len(ts_data)), ts_data.values, 1)
            p = np.poly1d(z)
            plt.plot(ts_data.index, p(range(len(ts_data))), "r--", alpha=0.8, 
                    label=f'Tendencia (pendiente: {z[0]:.6f})')
            plt.legend()
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        output_file = 'traffic_time_series.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Gráfico de serie temporal guardado en: {output_file}")
        plt.show()
    
    def identify_patterns(self):
        """
        Identifica patrones específicos en los datos
        """
        if self.df is None:
            return
        
        print("\n=== IDENTIFICACIÓN DE PATRONES ===")
        
        # Patrones por hora
        hourly_avg = self.df.groupby('hour')['avg_congestion_factor'].mean()
        
        # Identificar horas pico matutinas (6-10 AM)
        morning_peak = hourly_avg.loc[6:10].idxmax()
        morning_value = hourly_avg.loc[morning_peak]
        
        # Identificar horas pico vespertinas (16-20 PM)
        evening_peak = hourly_avg.loc[16:20].idxmax()
        evening_value = hourly_avg.loc[evening_peak]
        
        # Hora de menor tráfico
        low_traffic = hourly_avg.idxmin()
        low_value = hourly_avg.loc[low_traffic]
        
        print(f"Pico matutino: {morning_peak:02d}:00 (factor: {morning_value:.3f})")
        print(f"Pico vespertino: {evening_peak:02d}:00 (factor: {evening_value:.3f})")
        print(f"Menor tráfico: {low_traffic:02d}:00 (factor: {low_value:.3f})")
        
        # Diferencia entre días laborales y fines de semana
        weekdays = self.df[self.df['day_of_week'].isin([0, 1, 2, 3, 4])]  # Lun-Vie
        weekends = self.df[self.df['day_of_week'].isin([5, 6])]  # Sab-Dom
        
        if len(weekdays) > 0 and len(weekends) > 0:
            weekday_avg = weekdays['avg_congestion_factor'].mean()
            weekend_avg = weekends['avg_congestion_factor'].mean()
            
            print(f"\nPromedio días laborales: {weekday_avg:.3f}")
            print(f"Promedio fines de semana: {weekend_avg:.3f}")
            print(f"Diferencia: {weekday_avg - weekend_avg:.3f}")
        
        # Variabilidad por fuente de datos
        print("\n--- Comparación por fuente de datos ---")
        sources = ['google_congestion', 'here_congestion', 'ors_congestion']
        for source in sources:
            if source in self.df.columns:
                avg_val = self.df[source].mean()
                std_val = self.df[source].std()
                count_val = self.df[source].count()
                print(f"{source}: promedio={avg_val:.3f}, std={std_val:.3f}, muestras={count_val}")
    
    def generate_report(self, output_file: str = 'traffic_report.txt'):
        """
        Genera un reporte completo
        """
        if self.df is None:
            return
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("REPORTE DE ANÁLISIS DE TRÁFICO - PLACE CHARLES DE GAULLE-ÉTOILE\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Estadísticas generales
            f.write("ESTADÍSTICAS GENERALES:\n")
            f.write(f"- Período analizado: {self.df['timestamp'].min()} a {self.df['timestamp'].max()}\n")
            f.write(f"- Total de registros: {len(self.df)}\n")
            f.write(f"- Días únicos: {self.df['date'].nunique()}\n")
            
            if 'avg_congestion_factor' in self.df.columns:
                stats = self.df['avg_congestion_factor'].describe()
                f.write(f"- Factor de congestión promedio: {stats['mean']:.3f}\n")
                f.write(f"- Desviación estándar: {stats['std']:.3f}\n")
                f.write(f"- Valor máximo: {stats['max']:.3f}\n")
                f.write(f"- Valor mínimo: {stats['min']:.3f}\n\n")
            
            # Análisis por hora
            f.write("ANÁLISIS POR HORA:\n")
            hourly_stats = self.df.groupby('hour')['avg_congestion_factor'].mean()
            
            # Top 5 horas pico
            top_hours = hourly_stats.nlargest(5)
            f.write("Top 5 horas con mayor congestión:\n")
            for hour, value in top_hours.items():
                f.write(f"  {hour:02d}:00 - Factor: {value:.3f}\n")
            
            f.write("\n")
            
            # Recomendaciones
            f.write("RECOMENDACIONES PARA LA SIMULACIÓN:\n")
            f.write("- Usar los factores de congestión por hora identificados\n")
            f.write("- Considerar diferencias entre días laborales y fines de semana\n")
            f.write("- Implementar variabilidad estocástica basada en desviación estándar\n")
            f.write("- Validar resultados con múltiples fuentes de datos cuando estén disponibles\n")
        
        print(f"Reporte guardado en: {output_file}")
    
    def export_simulation_data(self, output_file: str = 'simulation_traffic_data.json'):
        """
        Exporta datos optimizados para simulación
        """
        if self.df is None:
            return
        
        # Crear estructura de datos para simulación
        simulation_data = {
            'metadata': {
                'location': 'Place Charles de Gaulle-Étoile, Paris',
                'coordinates': {'lat': 48.8738, 'lng': 2.2950},
                'data_period': {
                    'start': self.df['timestamp'].min().isoformat(),
                    'end': self.df['timestamp'].max().isoformat()
                },
                'total_samples': len(self.df)
            },
            'hourly_patterns': {},
            'weekly_patterns': {},
            'statistical_parameters': {}
        }
        
        # Patrones por hora
        hourly_stats = self.df.groupby('hour')['avg_congestion_factor'].agg(['mean', 'std', 'min', 'max'])
        for hour in range(24):
            if hour in hourly_stats.index:
                simulation_data['hourly_patterns'][str(hour)] = {
                    'mean_congestion': float(hourly_stats.loc[hour, 'mean']),
                    'std_congestion': float(hourly_stats.loc[hour, 'std']),
                    'min_congestion': float(hourly_stats.loc[hour, 'min']),
                    'max_congestion': float(hourly_stats.loc[hour, 'max'])
                }
            else:
                # Valores por defecto si no hay datos
                simulation_data['hourly_patterns'][str(hour)] = {
                    'mean_congestion': 1.0,
                    'std_congestion': 0.1,
                    'min_congestion': 1.0,
                    'max_congestion': 1.2
                }
        
        # Patrones semanales
        if 'day_name' in self.df.columns:
            day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            weekly_stats = self.df.groupby('day_name')['avg_congestion_factor'].agg(['mean', 'std'])
            
            for day in day_names:
                if day in weekly_stats.index:
                    simulation_data['weekly_patterns'][day] = {
                        'mean_congestion': float(weekly_stats.loc[day, 'mean']),
                        'std_congestion': float(weekly_stats.loc[day, 'std'])
                    }
        
        # Parámetros estadísticos generales
        if 'avg_congestion_factor' in self.df.columns:
            overall_stats = self.df['avg_congestion_factor'].describe()
            simulation_data['statistical_parameters'] = {
                'global_mean': float(overall_stats['mean']),
                'global_std': float(overall_stats['std']),
                'global_min': float(overall_stats['min']),
                'global_max': float(overall_stats['max'])
            }
        
        # Guardar datos
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(simulation_data, f, indent=2, ensure_ascii=False)
        
        print(f"Datos para simulación exportados a: {output_file}")
        return simulation_data

def main():
    """
    Función principal del analizador
    """
    print("=== ANALIZADOR DE DATOS DE TRÁFICO ===\n")
    
    # Verificar si existe archivo de datos
    data_file = 'traffic_data_charles_de_gaulle.csv'
    if not os.path.exists(data_file):
        print(f"Error: No se encontró el archivo {data_file}")
        print("Primero ejecuta traffic_data_collector.py para recopilar datos.")
        return
    
    # Crear analizador y cargar datos
    analyzer = TrafficAnalyzer(data_file)
    if not analyzer.load_data():
        return
    
    print("Opciones disponibles:")
    print("1. Estadísticas básicas")
    print("2. Análisis por hora")
    print("3. Análisis semanal") 
    print("4. Crear visualizaciones")
    print("5. Análisis de series temporales")
    print("6. Identificar patrones")
    print("7. Generar reporte completo")
    print("8. Exportar datos para simulación")
    print("9. Análisis completo (todas las opciones)")
    
    choice = input("\nSelecciona una opción (1-9): ").strip()
    
    if choice == "1":
        analyzer.basic_statistics()
    elif choice == "2":
        analyzer.hourly_analysis()
    elif choice == "3":
        analyzer.weekly_analysis()
    elif choice == "4":
        analyzer.create_visualizations()
    elif choice == "5":
        analyzer.time_series_analysis()
    elif choice == "6":
        analyzer.identify_patterns()
    elif choice == "7":
        analyzer.generate_report()
    elif choice == "8":
        analyzer.export_simulation_data()
    elif choice == "9":
        print("Ejecutando análisis completo...")
        analyzer.basic_statistics()
        analyzer.hourly_analysis()
        analyzer.weekly_analysis()
        analyzer.create_visualizations()
        analyzer.time_series_analysis()
        analyzer.identify_patterns()
        analyzer.generate_report()
        analyzer.export_simulation_data()
        print("\n¡Análisis completo finalizado!")
    else:
        print("Opción inválida")

if __name__ == "__main__":
    main()