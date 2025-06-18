import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# Parámetros
lambd = 5.0     
mu = 8.0        
sim_time = 1000 
n_consulta = 3  # para calcular P(n=n_consulta)
capacidad_maxima = None  # poné un número si querés denegación de servicio, ej. 10

# Variables
tiempo_actual = 0
tiempo_llegada_siguiente = np.random.exponential(1 / lambd)
tiempo_salida_siguiente = float('inf')
cola = []
cliente_en_servicio = None

# Métricas
tiempos_espera = []
tiempos_en_sistema = []
estado_cola_hist = defaultdict(float)
rechazos = 0
eventos = []

# Simulación
while tiempo_actual < sim_time:
    proximo_evento = min(tiempo_llegada_siguiente, tiempo_salida_siguiente)
    estado_cola_hist[len(cola)] += proximo_evento - tiempo_actual
    tiempo_actual = proximo_evento

    if tiempo_actual == tiempo_llegada_siguiente:
        if capacidad_maxima is not None and len(cola) >= capacidad_maxima:
            rechazos += 1
        else:
            cola.append(tiempo_actual)
            if cliente_en_servicio is None:
                cliente_en_servicio = cola.pop(0)
                tiempo_salida_siguiente = tiempo_actual + np.random.exponential(1 / mu)

        tiempo_llegada_siguiente = tiempo_actual + np.random.exponential(1 / lambd)

    else: 
        salida = tiempo_actual
        llegada = cliente_en_servicio
        tiempos_en_sistema.append(salida - llegada)
        tiempos_espera.append((salida - llegada) - (1 / mu))

        if cola:
            cliente_en_servicio = cola.pop(0)
            tiempo_salida_siguiente = tiempo_actual + np.random.exponential(1 / mu)
        else:
            cliente_en_servicio = None
            tiempo_salida_siguiente = float('inf')

# Cálculos finales
clientes_atendidos = len(tiempos_en_sistema)
rho = lambd / mu
L = np.mean(tiempos_en_sistema) * lambd
Lq = np.mean(tiempos_espera) * lambd
T = np.mean(tiempos_en_sistema)
W = np.mean(tiempos_espera)
Pn = estado_cola_hist[n_consulta] / tiempo_actual if tiempo_actual > 0 else 0
P_deneg = rechazos / (rechazos + clientes_atendidos) if rechazos + clientes_atendidos > 0 else 0

# Resultados
print(f"--- Resultados M/M/1 ---")
print(f"Tasa de llegada (λ): {lambd}")
print(f"Tasa de servicio (μ): {mu}")
print(f"Utilización del servidor (ρ): {rho:.3f}")
print(f"Clientes atendidos: {clientes_atendidos}")
print(f"Promedio de clientes en el sistema (L): {L:.3f}")
print(f"Promedio de clientes en cola (Lq): {Lq:.3f}")
print(f"Tiempo promedio en sistema (T): {T:.3f}")
print(f"Tiempo promedio en cola (W): {W:.3f}")
print(f"Probabilidad de haber {n_consulta} clientes en cola: {Pn:.3f}")
print(f"Probabilidad de denegación de servicio: {P_deneg:.3f}")

plt.bar(estado_cola_hist.keys(), [v / tiempo_actual for v in estado_cola_hist.values()])
plt.xlabel("Número de clientes en cola")
plt.ylabel("Probabilidad")
plt.title("Distribución del número de clientes en cola")
plt.grid(True)
plt.show()