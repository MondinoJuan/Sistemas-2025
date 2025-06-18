import numpy as np
import matplotlib.pyplot as plt
from collections import deque, defaultdict
import sys
import random
import math


def generar_interarribo(lambd):
    u = random.random()
    return -1.0 / lambd * np.log(1 - u)

def generar_servicio(mu):
    u = random.random()
    return -1.0 / mu * np.log(1 - u)

def simular_mm1(lambd, mu, tiempo_simulacion, tamaño_cola):
    eventos = []
    tiempo_actual = 0
    servidor_ocupado = False
    cola = deque()
    id_cliente = 1
    clientes_rechazados = 0

    # Estadísticas
    tiempo_eventos = []
    largo_cola = []
    largo_sistema = []
    tiempos_cola = []
    tiempos_sistema = []
    tiempo_espera_total = 0
    tiempo_servicio_total = 0
    tiempo_sistema_total = 0
    clientes_atendidos = 0
    tiempo_ocupado_servidor = 0
    distribucion_cola = defaultdict(int)
    tiempo_ultimo_evento = 0

    # Programar primera llegada
    llegada = generar_interarribo(lambd)
    eventos.append((llegada, 'llegada', id_cliente))

    while eventos and tiempo_actual < tiempo_simulacion:
        eventos.sort()
        evento_tiempo, tipo_evento, id_evento = eventos.pop(0)
        tiempo_actual = evento_tiempo

        dt = tiempo_actual - tiempo_ultimo_evento
        if servidor_ocupado:
            tiempo_ocupado_servidor += dt
        tiempo_ultimo_evento = tiempo_actual

        distribucion_cola[len(cola)] += 1
        tiempo_eventos.append(tiempo_actual)
        largo_cola.append(len(cola))
        largo_sistema.append(len(cola) + int(servidor_ocupado))

        if tipo_evento == 'llegada':
            if not servidor_ocupado:
                tiempo_servicio = generar_servicio(mu)
                salida = tiempo_actual + tiempo_servicio
                eventos.append((salida, 'salida', id_evento))
                servidor_ocupado = True

                tiempo_servicio_total += tiempo_servicio
                tiempo_sistema_total += tiempo_servicio
                tiempos_cola.append(0)
                tiempos_sistema.append(tiempo_servicio)
                clientes_atendidos += 1
            else:
                if len(cola) < tamaño_cola:
                    cola.append((id_evento, tiempo_actual))
                else:
                    clientes_rechazados += 1

            id_cliente += 1
            proxima_llegada = tiempo_actual + generar_interarribo(lambd)
            if proxima_llegada < tiempo_simulacion:
                eventos.append((proxima_llegada, 'llegada', id_cliente))

        elif tipo_evento == 'salida':
            servidor_ocupado = False
            if cola:
                siguiente_id, tiempo_llegada = cola.popleft()
                espera = tiempo_actual - tiempo_llegada
                tiempo_servicio = generar_servicio(mu)
                salida = tiempo_actual + tiempo_servicio
                eventos.append((salida, 'salida', siguiente_id))
                servidor_ocupado = True

                tiempo_espera_total += espera
                tiempo_servicio_total += tiempo_servicio
                tiempo_sistema_total += espera + tiempo_servicio
                tiempos_cola.append(espera)
                tiempos_sistema.append(espera + tiempo_servicio)
                clientes_atendidos += 1

    # Cálculos finales
    L = np.mean(largo_sistema)
    Lq = np.mean(largo_cola)
    W = tiempo_sistema_total / clientes_atendidos if clientes_atendidos else 0
    Wq = tiempo_espera_total / clientes_atendidos if clientes_atendidos else 0
    utilizacion = tiempo_ocupado_servidor / tiempo_simulacion
    probabilidades = {n: c / sum(distribucion_cola.values()) for n, c in distribucion_cola.items()}

    return L, Lq, W, Wq, utilizacion, probabilidades, tiempo_eventos, largo_cola, largo_sistema, tiempos_cola, tiempos_sistema, clientes_atendidos, clientes_rechazados

def imprimir_resultados(promedios, teoricos, probabilidades, prob_denegacion, tamaño_cola):
    print("\n--- Resultados Promedio Simulación M/M/1 ---")
    print(f"Promedio de clientes en sistema (L): {promedios['L']:.4f} | Teórico: {teoricos['L']:.4f}")
    print(f"Promedio de clientes en cola (Lq): {promedios['Lq']:.4f} | Teórico: {teoricos['Lq']:.4f}")
    print(f"Tiempo promedio en sistema (W): {promedios['W']:.4f} | Teórico: {teoricos['W']:.4f}")
    print(f"Tiempo promedio en cola (Wq): {promedios['Wq']:.4f} | Teórico: {teoricos['Wq']:.4f}")
    print(f"Utilización del servidor: {promedios['rho']:.4f}")
    print("\n--- Probabilidad de encontrar n clientes en cola ---")
    for n in sorted(probabilidades.keys()):
        print(f"P(n={n} en cola) ≈ {probabilidades[n]:.4f}")
    print(f"\n--- Probabilidad de denegación de servicio (cola finita tamaño {tamaño_cola}) ---")
    print(f"P(rechazo) ≈ {prob_denegacion:.4f}")

def graficar_resultados(colas_raw, sistemas_raw, tiempos_cola_raw, tiempos_sistema_raw):
    plt.figure(figsize=(14, 12))

    # 1. Usuarios en cola
    plt.subplot(2, 2, 1)
    for t, v in colas_raw:
        plt.plot(t, v, alpha=0.3, color='blue')
    promedio = np.mean([np.interp(np.linspace(0, max(t), 500), t, v) for t, v in colas_raw], axis=0)
    plt.plot(np.linspace(0, max(colas_raw[0][0]), 500), promedio, color='black', linewidth=2, label='Promedio')
    plt.title('Clientes en cola')
    plt.xlabel('Tiempo')
    plt.ylabel('Cantidad')
    plt.grid(True)
    plt.legend()

    # 2. Usuarios en sistema
    plt.subplot(2, 2, 2)
    for t, v in sistemas_raw:
        plt.plot(t, v, alpha=0.3, color='red')
    promedio = np.mean([np.interp(np.linspace(0, max(t), 500), t, v) for t, v in sistemas_raw], axis=0)
    plt.plot(np.linspace(0, max(sistemas_raw[0][0]), 500), promedio, color='black', linewidth=2, label='Promedio')
    plt.title('Clientes en sistema')
    plt.xlabel('Tiempo')
    plt.ylabel('Cantidad')
    plt.grid(True)
    plt.legend()

    # 3. Tiempos en cola
    plt.subplot(2, 2, 3)
    for t in tiempos_cola_raw:
        plt.hist(t, bins=30, alpha=0.3, color='skyblue')
    
    #plt.hist(np.concatenate(tiempos_cola_raw), bins=30, color='black', alpha=0.7, label='Promedio')
    promedio_t_cola = [np.mean(t) for t in tiempos_cola_raw]
    plt.axvline(np.mean(promedio_t_cola), color='black', linestyle='--', linewidth=2, label='Promedio')

    plt.title('Tiempo en cola')
    plt.xlabel('Tiempo')
    plt.ylabel('Frecuencia')
    plt.grid(True)
    plt.legend()

    # 4. Tiempos en sistema
    plt.subplot(2, 2, 4)
    for t in tiempos_sistema_raw:
        plt.hist(t, bins=30, alpha=0.3, color='salmon')
    
    #plt.hist(np.concatenate(tiempos_sistema_raw), bins=30, color='black', alpha=0.7, label='Promedio')
    promedio_t_sistema = [np.mean(t) for t in tiempos_sistema_raw]
    plt.axvline(np.mean(promedio_t_sistema), color='black', linestyle='--', linewidth=2, label='Promedio')

    plt.title('Tiempo en sistema')
    plt.xlabel('Tiempo')
    plt.ylabel('Frecuencia')
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) != 7 or sys.argv[1] != '-m' or sys.argv[3] != '-p' or sys.argv[5] != '-c':
        print("Uso: python simulacion_mm1.py -m <mu> -p <proporcion entre llegadas y salidas> -c <ciclos>")
        sys.exit(1)

    proporcion = float(sys.argv[4])
    mu = float(sys.argv[2])
    ciclos = int(sys.argv[6])
    #max_tamaño_cola = int(sys.argv[8])
    tamaños_cola = [0, 2, 5, 10, 50]

    lambd = proporcion * mu

    for tamaño_cola in tamaños_cola:
        print(f"\n================== Tamaño de Cola: {tamaño_cola} ==================\n")
        rechazos_totales = 0
        llegadas_totales = 0
        resultados = []
        colas_raw = []
        sistemas_raw = []
        tiempos_cola_raw = []
        tiempos_sistema_raw = []

        for _ in range(ciclos):
            tiempo_simulacion = 100
            sim = simular_mm1(lambd, mu, tiempo_simulacion, tamaño_cola)
            L, Lq, W, Wq, utilizacion, probs, tiempos, colas, sistemas, t_cola, t_sistema, atendidos, rechazados = sim

            resultados.append((L, Lq, W, Wq, utilizacion))
            colas_raw.append((tiempos, colas))
            sistemas_raw.append((tiempos, sistemas))
            tiempos_cola_raw.append(t_cola)
            tiempos_sistema_raw.append(t_sistema)
            llegadas_totales += atendidos + rechazados
            rechazos_totales += rechazados

        p_denegacion = rechazos_totales / llegadas_totales if llegadas_totales > 0 else 0

        promedios = {
            'L': np.mean([r[0] for r in resultados]),
            'Lq': np.mean([r[1] for r in resultados]),
            'W': np.mean([r[2] for r in resultados]),
            'Wq': np.mean([r[3] for r in resultados]),
            'rho': np.mean([r[4] for r in resultados])
        }

        rho = lambd / mu
        teoricos = {
            'L': rho / (1 - rho),
            'Lq': rho ** 2 / (1 - rho),
            'W': 1 / (mu - lambd),
            'Wq': rho / (mu * (1 - rho))
        }

        imprimir_resultados(promedios, teoricos, probs, p_denegacion, tamaño_cola)
        graficar_resultados(colas_raw, sistemas_raw, tiempos_cola_raw, tiempos_sistema_raw)