import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import sys

class MM1Simulator:
    def __init__(self, arrival_rate, service_rate, simulation_time):
        """
        Simulador de cola M/M/1
        
        Parámetros:
        - arrival_rate (λ): tasa de llegadas por unidad de tiempo
        - service_rate (μ): tasa de servicio por unidad de tiempo
        - simulation_time: tiempo total de simulación
        """
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.simulation_time = simulation_time
        self.utilization = arrival_rate / service_rate
        
        # Verificar estabilidad del sistema
        if self.utilization >= 1:
            print(f"¡ADVERTENCIA! El sistema es inestable (ρ = {self.utilization:.3f} ≥ 1)")
        
        # Variables de estado
        self.current_time = 0
        self.queue = deque()  # Cola de espera
        self.server_busy = False
        self.server_end_time = 0
        
        # Estadísticas
        self.total_customers = 0
        self.total_wait_time = 0
        self.total_service_time = 0
        self.total_system_time = 0
        self.queue_length_over_time = []
        self.system_length_over_time = []  # Clientes en sistema (cola + servidor)
        self.time_points = []
        self.server_busy_time = 0  # Tiempo total que el servidor estuvo ocupado
        self.last_event_time = 0   # Para calcular utilización
        self.customers_denied = 0  # Para sistemas con capacidad limitada (opcional)
        self.queue_length_distribution = {}  # Distribución de longitudes de cola
        
        # Eventos
        self.events = []
        
    def generate_interarrival_time(self):
        """Genera tiempo entre llegadas (distribución exponencial)"""
        return np.random.exponential(1/self.arrival_rate)
    
    def generate_service_time(self):
        """Genera tiempo de servicio (distribución exponencial)"""
        return np.random.exponential(1/self.service_rate)
    
    def schedule_event(self, event_time, event_type, customer_id=None):
        """Programa un evento en la lista de eventos"""
        self.events.append((event_time, event_type, customer_id))
        self.events.sort()
    
    def run_simulation(self):
        """Ejecuta la simulación completa"""
        print(f"Iniciando simulación M/M/1...")
        print(f"λ = {self.arrival_rate}, μ = {self.service_rate}, ρ = {self.utilization:.3f}")
        print(f"Tiempo de simulación: {self.simulation_time}")
        print("-" * 50)
        
        # Programar primera llegada
        first_arrival = self.generate_interarrival_time()
        self.schedule_event(first_arrival, 'arrival', 1)
        
        customer_counter = 1
        
        while self.events and self.current_time < self.simulation_time:
            # Obtener próximo evento
            event_time, event_type, customer_id = self.events.pop(0)
            self.current_time = event_time
            
            if self.current_time > self.simulation_time:
                break
                
            # Actualizar tiempo de servidor ocupado
            if self.server_busy and self.last_event_time < self.current_time:
                self.server_busy_time += (self.current_time - self.last_event_time)
            
            # Registrar longitud de cola y sistema para estadísticas
            queue_length = len(self.queue)
            system_length = queue_length + (1 if self.server_busy else 0)
            
            self.time_points.append(self.current_time)
            self.queue_length_over_time.append(queue_length)
            self.system_length_over_time.append(system_length)
            
            # Actualizar distribución de longitudes de cola
            if queue_length in self.queue_length_distribution:
                self.queue_length_distribution[queue_length] += 1
            else:
                self.queue_length_distribution[queue_length] = 1
            
            self.last_event_time = self.current_time
            
            if event_type == 'arrival':
                self.handle_arrival(customer_id)
                
                # Programar próxima llegada
                customer_counter += 1
                next_arrival = self.current_time + self.generate_interarrival_time()
                if next_arrival < self.simulation_time:
                    self.schedule_event(next_arrival, 'arrival', customer_counter)
                    
            elif event_type == 'departure':
                self.handle_departure(customer_id)
        
        self.calculate_statistics()
        
    def handle_arrival(self, customer_id):
        """Maneja la llegada de un cliente"""
        arrival_time = self.current_time
        
        if not self.server_busy:
            # Servidor libre, comenzar servicio inmediatamente
            service_time = self.generate_service_time()
            departure_time = self.current_time + service_time
            
            self.server_busy = True
            self.server_end_time = departure_time
            
            # Programar salida
            self.schedule_event(departure_time, 'departure', customer_id)
            
            # Registrar estadísticas (sin tiempo de espera)
            self.total_customers += 1
            self.total_service_time += service_time
            self.total_system_time += service_time
            
        else:
            # Servidor ocupado, agregar a la cola
            self.queue.append((customer_id, arrival_time))
    
    def handle_departure(self, customer_id):
        """Maneja la salida de un cliente"""
        self.server_busy = False
        
        # Si hay clientes en cola, comenzar servicio del siguiente
        if self.queue:
            next_customer_id, arrival_time = self.queue.popleft()
            
            # Calcular tiempo de espera
            wait_time = self.current_time - arrival_time
            service_time = self.generate_service_time()
            departure_time = self.current_time + service_time
            
            self.server_busy = True
            self.server_end_time = departure_time
            
            # Programar salida del siguiente cliente
            self.schedule_event(departure_time, 'departure', next_customer_id)
            
            # Registrar estadísticas
            self.total_customers += 1
            self.total_wait_time += wait_time
            self.total_service_time += service_time
            self.total_system_time += wait_time + service_time
    
    def calculate_statistics(self):
        """Calcula estadísticas finales"""
        # Actualizar tiempo final de servidor ocupado
        if self.server_busy and self.last_event_time < self.simulation_time:
            self.server_busy_time += (self.simulation_time - self.last_event_time)
        
        if self.total_customers > 0:
            self.avg_wait_time = self.total_wait_time / self.total_customers
            self.avg_service_time = self.total_service_time / self.total_customers
            self.avg_system_time = self.total_system_time / self.total_customers
        else:
            self.avg_wait_time = 0
            self.avg_service_time = 0
            self.avg_system_time = 0
        
        # Calcular promedios usando integración numérica (más preciso)
        if len(self.time_points) > 1:
            # Promedio de clientes en cola
            self.avg_customers_queue = self._calculate_time_weighted_average(
                self.time_points, self.queue_length_over_time
            )
            # Promedio de clientes en sistema
            self.avg_customers_system = self._calculate_time_weighted_average(
                self.time_points, self.system_length_over_time
            )
        else:
            self.avg_customers_queue = 0
            self.avg_customers_system = 0
        
        # Utilización del servidor
        self.server_utilization = self.server_busy_time / self.simulation_time if self.simulation_time > 0 else 0
        
        # Probabilidades de encontrar n clientes en cola
        total_observations = sum(self.queue_length_distribution.values())
        self.queue_probabilities = {}
        if total_observations > 0:
            for n, count in self.queue_length_distribution.items():
                self.queue_probabilities[n] = count / total_observations
        
        # Probabilidad de denegación (para M/M/1 sin límite es 0)
        self.denial_probability = 0  # En M/M/1 básico no hay denegación
    
    def _calculate_time_weighted_average(self, time_points, values):
        """Calcula el promedio ponderado por tiempo"""
        if len(time_points) < 2 or len(values) < 2:
            return 0
        
        total_area = 0
        total_time = 0
        
        for i in range(len(time_points) - 1):
            dt = time_points[i + 1] - time_points[i]
            total_area += values[i] * dt
            total_time += dt
        
        return total_area / total_time if total_time > 0 else 0
    
    def get_theoretical_results(self):
        """Calcula resultados teóricos para comparación"""
        if self.utilization >= 1:
            return None
            
        rho = self.utilization
        
        theoretical = {
            'avg_customers_system': rho / (1 - rho),
            'avg_customers_queue': (rho ** 2) / (1 - rho),
            'avg_time_system': 1 / (self.service_rate - self.arrival_rate),
            'avg_time_queue': rho / (self.service_rate - self.arrival_rate),
            'server_utilization': rho
        }
        
        return theoretical
    
    def print_results(self):
        """Imprime resultados de la simulación"""
        print("\n" + "="*60)
        print("RESULTADOS DE LA SIMULACIÓN M/M/1")
        print("="*60)
        
        print(f"Parámetros:")
        print(f"  Tasa de llegadas (λ): {self.arrival_rate}")
        print(f"  Tasa de servicio (μ): {self.service_rate}")
        print(f"  Utilización teórica (ρ): {self.utilization:.4f}")
        print(f"  Tiempo de simulación: {self.simulation_time}")
        print(f"  Clientes procesados: {self.total_customers}")
        
        print(f"\nMEDIDAS DE RENDIMIENTO SIMULADAS:")
        print(f"  Promedio de clientes en el sistema (L): {self.avg_customers_system:.4f}")
        print(f"  Promedio de clientes en cola (Lq): {self.avg_customers_queue:.4f}")
        print(f"  Tiempo promedio en sistema (W): {self.avg_system_time:.4f}")
        print(f"  Tiempo promedio en cola (Wq): {self.avg_wait_time:.4f}")
        print(f"  Utilización del servidor: {self.server_utilization:.4f}")
        print(f"  Probabilidad de denegación de servicio: {self.denial_probability:.4f}")
        
        # Mostrar probabilidades de encontrar n clientes en cola
        print(f"\nPROBABILIDADES DE ENCONTRAR n CLIENTES EN COLA:")
        max_display = min(10, max(self.queue_probabilities.keys()) if self.queue_probabilities else 0)
        for n in range(max_display + 1):
            prob = self.queue_probabilities.get(n, 0)
            print(f"  P(n={n}): {prob:.4f}")
        
        # Comparar con resultados teóricos
        theoretical = self.get_theoretical_results()
        if theoretical:
            print(f"\nMEDIDAS DE RENDIMIENTO TEÓRICAS:")
            print(f"  Promedio de clientes en el sistema (L): {theoretical['avg_customers_system']:.4f}")
            print(f"  Promedio de clientes en cola (Lq): {theoretical['avg_customers_queue']:.4f}")
            print(f"  Tiempo promedio en sistema (W): {theoretical['avg_time_system']:.4f}")
            print(f"  Tiempo promedio en cola (Wq): {theoretical['avg_time_queue']:.4f}")
            print(f"  Utilización del servidor: {theoretical['server_utilization']:.4f}")
            
            # Probabilidades teóricas
            print(f"\nPROBABILIDADES TEÓRICAS DE ENCONTRAR n CLIENTES EN COLA:")
            rho = self.utilization
            for n in range(max_display + 1):
                prob_theoretical = (1 - rho) * (rho ** n)
                print(f"  P(n={n}): {prob_theoretical:.4f}")
            
            print(f"\nCOMPARACIÓN (Error Relativo %):")
            if theoretical['avg_customers_system'] > 0:
                error_L = abs(self.avg_customers_system - theoretical['avg_customers_system']) / theoretical['avg_customers_system'] * 100
                print(f"  Clientes en sistema (L): {error_L:.2f}%")
            if theoretical['avg_customers_queue'] > 0:
                error_Lq = abs(self.avg_customers_queue - theoretical['avg_customers_queue']) / theoretical['avg_customers_queue'] * 100
                print(f"  Clientes en cola (Lq): {error_Lq:.2f}%")
            if theoretical['avg_time_system'] > 0:
                error_W = abs(self.avg_system_time - theoretical['avg_time_system']) / theoretical['avg_time_system'] * 100
                print(f"  Tiempo en sistema (W): {error_W:.2f}%")
            if theoretical['avg_time_queue'] > 0:
                error_Wq = abs(self.avg_wait_time - theoretical['avg_time_queue']) / theoretical['avg_time_queue'] * 100
                print(f"  Tiempo en cola (Wq): {error_Wq:.2f}%")
            
            error_util = abs(self.server_utilization - theoretical['server_utilization']) / theoretical['server_utilization'] * 100
            print(f"  Utilización del servidor: {error_util:.2f}%")

def plot_consolidated_results(simulators, ciclos):
    """Genera gráficos consolidados de todas las simulaciones"""
    # Preparar colores para cada corrida
    colors = plt.cm.tab10(np.linspace(0, 1, ciclos))
    
    #fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig, ax1 = plt.subplots(1, 1, figsize=(16, 12))
    
    # Variables para calcular promedios
    all_avg_customers_system = []
    all_avg_customers_queue = []
    all_avg_system_time = []
    all_avg_wait_time = []
    all_server_utilization = []
    all_queue_distributions = {}
    
    # Gráfico 1: Evolución del sistema en el tiempo para todas las corridas
    for i, simulator in enumerate(simulators):
        alpha = 0.7 if ciclos <= 5 else 0.4  # Más transparente si hay muchas corridas
        ax1.plot(simulator.time_points, simulator.queue_length_over_time, 
                color=colors[i], linewidth=0.8, alpha=alpha, label=f'Cola Run {i+1}' if ciclos <= 5 else '')
        ax1.plot(simulator.time_points, simulator.system_length_over_time, 
                color=colors[i], linewidth=0.8, alpha=alpha, linestyle=':', 
                label=f'Sistema Run {i+1}' if ciclos <= 5 else '')
        
        # Recolectar datos para promedios
        all_avg_customers_system.append(simulator.avg_customers_system)
        all_avg_customers_queue.append(simulator.avg_customers_queue)
        all_avg_system_time.append(simulator.avg_system_time)
        all_avg_wait_time.append(simulator.avg_wait_time)
        all_server_utilization.append(simulator.server_utilization)
        
        # Combinar distribuciones de cola
        for n, count in simulator.queue_length_distribution.items():
            if n in all_queue_distributions:
                all_queue_distributions[n] += count
            else:
                all_queue_distributions[n] = count
    
    # Calcular promedios
    prom_L = np.mean(all_avg_customers_system)
    prom_Lq = np.mean(all_avg_customers_queue)
    prom_W = np.mean(all_avg_system_time)
    prom_Wq = np.mean(all_avg_wait_time)
    prom_Util = np.mean(all_server_utilization)
    
    # Líneas punteadas con promedios
    ax1.axhline(y=prom_Lq, color='blue', linestyle='--', linewidth=2,
               label=f'Promedio Cola: {prom_Lq:.2f}')
    ax1.axhline(y=prom_L, color='red', linestyle='--', linewidth=2,
               label=f'Promedio Sistema: {prom_L:.2f}')
    ax1.axhline(y=prom_W, color='green', linestyle='--', linewidth=2,
               label=f'Promedio W: {prom_W:.2f}')
    ax1.axhline(y=prom_Wq, color='yellow', linestyle='--', linewidth=2,
               label=f'Promedio Wq: {prom_Wq:.2f}')
    ax1.axhline(y=prom_Util, color='black', linestyle='--', linewidth=2,
               label=f'Promedio Util: {prom_Util:.2f}')
    
    ax1.set_xlabel('Tiempo')
    ax1.set_ylabel('Número de Clientes')
    ax1.set_title(f'Evolución del Sistema - {ciclos} Corridas')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    '''# Gráfico 2: Distribución consolidada de longitudes de cola
    if all_queue_distributions:
        max_queue = max(all_queue_distributions.keys())
        total_observations = sum(all_queue_distributions.values())
        
        n_values = list(range(max_queue + 1))
        probabilities = [all_queue_distributions.get(n, 0) / total_observations for n in n_values]
        
        ax2.bar(n_values, probabilities, alpha=0.7, edgecolor='black', 
               label='Simulado (Consolidado)')
        
        # Distribución teórica
        if simulators[0].utilization < 1:
            rho = simulators[0].utilization
            theo_probs = [(1 - rho) * (rho ** n) for n in n_values]
            ax2.plot(n_values, theo_probs, 'ro-', label='Teórica', markersize=4)
        
        ax2.set_xlabel('Longitud de Cola')
        ax2.set_ylabel('Probabilidad')
        ax2.set_title(f'Distribución de Longitudes de Cola - {ciclos} Corridas')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
    
    # Gráfico 3: Comparación de medidas simuladas vs teóricas
    theoretical = simulators[0].get_theoretical_results()
    if theoretical and simulators[0].utilization < 1:
        categories = ['L\n(Sistema)', 'Lq\n(Cola)', 'W\n(Sistema)', 'Wq\n(Cola)', 'Utilización']
        simulated_avg = [prom_L, prom_Lq, prom_W, prom_Wq, prom_Util]
        theoretical_vals = [theoretical['avg_customers_system'], theoretical['avg_customers_queue'],
                          theoretical['avg_time_system'], theoretical['avg_time_queue'], 
                          theoretical['server_utilization']]
        
        x = np.arange(len(categories))
        width = 0.35
        
        ax3.bar(x - width/2, simulated_avg, width, label='Simulado (Promedio)', alpha=0.8)
        ax3.bar(x + width/2, theoretical_vals, width, label='Teórico', alpha=0.8)
        
        # Agregar líneas de error mostrando la variabilidad
        std_L = np.std(all_avg_customers_system)
        std_Lq = np.std(all_avg_customers_queue)
        std_W = np.std(all_avg_system_time)
        std_Wq = np.std(all_avg_wait_time)
        std_Util = np.std(all_server_utilization)
        
        errors = [std_L, std_Lq, std_W, std_Wq, std_Util]
        ax3.errorbar(x - width/2, simulated_avg, yerr=errors, fmt='none', 
                    color='black', capsize=3, label='Desv. Estándar')
        
        ax3.set_xlabel('Medidas de Rendimiento')
        ax3.set_ylabel('Valores')
        ax3.set_title(f'Comparación: Simulado vs Teórico - {ciclos} Corridas')
        ax3.set_xticks(x)
        ax3.set_xticklabels(categories)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    
    # Gráfico 4: Boxplots de las métricas
    metricas_data = [all_avg_customers_system, all_avg_customers_queue, 
                    all_avg_system_time, all_avg_wait_time, all_server_utilization]
    metricas_names = ['L', 'Lq', 'W', 'Wq', 'Utilización']
    
    bp = ax4.boxplot(metricas_data, labels=metricas_names, patch_artist=True)
    
    # Colorear boxplots
    colors_box = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink']
    for patch, color in zip(bp['boxes'], colors_box):
        patch.set_facecolor(color)
    
    # Agregar líneas punteadas con valores teóricos
    if theoretical:
        theo_values = [theoretical['avg_customers_system'], theoretical['avg_customers_queue'],
                      theoretical['avg_time_system'], theoretical['avg_time_queue'], 
                      theoretical['server_utilization']]
        for i, val in enumerate(theo_values):
            ax4.axhline(y=val, xmin=(i)/len(theo_values), xmax=(i+1)/len(theo_values), 
                       color='red', linestyle='--', linewidth=2)
    
    ax4.set_ylabel('Valores')
    ax4.set_title(f'Distribución de Métricas - {ciclos} Corridas')
    ax4.grid(True, alpha=0.3)'''
    
    plt.tight_layout()
    plt.suptitle(f'Simulación M/M/1: λ={simulators[0].arrival_rate}, μ={simulators[0].service_rate}, '
                f'ρ={simulators[0].utilization:.3f}, {ciclos} Corridas', 
                fontsize=14, y=0.98)
    plt.subplots_adjust(top=0.93)
    plt.show()

# Ejemplo de uso
if __name__ == "__main__":
    lambda_rate = 2.0
    mu_rate = 3.0
    sim_time = 100.0

    if len(sys.argv) != 7 or sys.argv[1] != "-l" or sys.argv[3] != "-u" or sys.argv[5] != "-c":
        print("Uso: python simulacion_mm1_1.py -l <lambda> -u <mu> -c <ciclos>")
        sys.exit(1)
    if float(sys.argv[2]) < 0 or int(sys.argv[6]) <= 0 or float(sys.argv[4]) < 0:
        print("Error: python simulacion_mm1_1.py -l <lambda> -u <mu> -c <ciclos>")
        sys.exit(1)

    ciclosPrograma = int(sys.argv[6])
    lambda_rate = float(sys.argv[2])
    mu_rate = float(sys.argv[4])
    sim_time = 100.0

    # Crear simulaciones independientes (no copias del mismo objeto)
    coleccionSimulaciones = [MM1Simulator(lambda_rate, mu_rate, sim_time) for _ in range(ciclosPrograma)]

    # Ejecutar todas las simulaciones y recolectar resultados
    resultados = {
        "avg_customers_system": [],
        "avg_customers_queue": [],
        "avg_system_time": [],
        "avg_wait_time": [],
        "server_utilization": [],
    }

    for idx, simulator in enumerate(coleccionSimulaciones):
        print(f"\n{'='*30} CORRIDA {idx+1} {'='*30}")
        simulator.run_simulation()
        simulator.print_results()

        # Guardar resultados para promediar después
        resultados["avg_customers_system"].append(simulator.avg_customers_system)
        resultados["avg_customers_queue"].append(simulator.avg_customers_queue)
        resultados["avg_system_time"].append(simulator.avg_system_time)
        resultados["avg_wait_time"].append(simulator.avg_wait_time)
        resultados["server_utilization"].append(simulator.server_utilization)

    # Mostrar resumen de todas las corridas
    print("\n" + "="*60)
    print("RESUMEN DE TODAS LAS CORRIDAS")
    print("="*60)
    print(f"Cantidad de simulaciones: {ciclosPrograma}")
    print(f"{'Corrida':>8} | {'L':>8} | {'Lq':>8} | {'W':>8} | {'Wq':>8} | {'Utiliz.':>8}")
    print("-"*60)
    for i in range(ciclosPrograma):
        print(f"{i+1:>8} | {resultados['avg_customers_system'][i]:>8.4f} | {resultados['avg_customers_queue'][i]:>8.4f} | "
              f"{resultados['avg_system_time'][i]:>8.4f} | {resultados['avg_wait_time'][i]:>8.4f} | {resultados['server_utilization'][i]:>8.4f}")

    # Calcular y mostrar promedios
    prom_L = np.mean(resultados["avg_customers_system"])
    prom_Lq = np.mean(resultados["avg_customers_queue"])
    prom_W = np.mean(resultados["avg_system_time"])
    prom_Wq = np.mean(resultados["avg_wait_time"])
    prom_Util = np.mean(resultados["server_utilization"])

    print("-"*60)
    print(f"{'PROMEDIO':>8} | {prom_L:>8.4f} | {prom_Lq:>8.4f} | {prom_W:>8.4f} | {prom_Wq:>8.4f} | {prom_Util:>8.4f}")

    # MOSTRAR GRÁFICAS CONSOLIDADAS UNA SOLA VEZ
    plot_consolidated_results(coleccionSimulaciones, ciclosPrograma)
    
    print(f"\n" + "="*60)
    print("Simulación completada exitosamente!")