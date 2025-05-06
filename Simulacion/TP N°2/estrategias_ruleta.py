import random
import sys
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Estilo de gráficos
plt.style.use("seaborn-v0_8")

# Constantes
CAPITAL_INICIAL = 100000
APUESTA_BASE = 1


def leer_parametros():
    """Leer, parsear y validar parámetros desde consola."""
    if (
        len(sys.argv) != 11
        or sys.argv[1] != "-c"
        or sys.argv[3] != "-n"
        or sys.argv[5] != "-e"
        or sys.argv[7] != "-s"
        or sys.argv[9] != "-a"
    ):
        print(
            "Uso: python estrategias_ruleta.py -c <num_corridas> -n <num_tiradas> -e <num_objetivo> -s <estrategia (m, f, d, o)> -a <capital (i, f)>"
        )
        sys.exit(1)

    try:
        num_corridas = int(sys.argv[2])
        num_tiradas = int(sys.argv[4])
        num_objetivo = int(sys.argv[6]) if sys.argv[6] != "-" else "-"
        estrategia = sys.argv[8]
        capital_infinito = sys.argv[10] == "i"

        if estrategia not in ["m", "d", "f", "o"] or (
            sys.argv[6] != "-" and (num_objetivo < 0 or num_objetivo > 36)
        ):
            raise ValueError

    except ValueError:
        print(
            "Error en los argumentos. Revisá el formato y los valores proporcionados."
        )
        sys.exit(1)

    return num_corridas, num_tiradas, num_objetivo, estrategia, capital_infinito


def tiradas(n):
    """Generar lista de tiradas aleatorias."""
    return [random.randint(0, 36) for _ in range(n)]


def es_ganadora(resultado, objetivo):
    """Determinar si la apuesta es ganadora."""
    if objetivo == "-":
        return resultado % 2 == 0
    return resultado == objetivo


def obtener_multiplicador(objetivo):
    """Obtener multiplicador de ganancia."""
    return 2 if objetivo == "-" else 36


# Estrategias


def martingala(corridas, ilimitado, objetivo):
    fnd_hist = []
    mult = obtener_multiplicador(objetivo)

    for corrida in corridas:
        ap = APUESTA_BASE
        fnd = [CAPITAL_INICIAL]
        for resultado in corrida:
            if fnd[-1] < ap and not ilimitado:
                break
            fondos = fnd[-1] - ap

            if es_ganadora(resultado, objetivo):
                fondos += ap * mult
                ap = APUESTA_BASE
            else:
                ap *= 2
            fnd.append(fondos)
        fnd_hist.append(fnd)
    return fnd_hist


def fibonacci(corridas, ilimitado, objetivo):
    fnd_hist = []
    mult = obtener_multiplicador(objetivo)

    for corrida in corridas:
        serie = [0, 1]
        fnd = [CAPITAL_INICIAL]
        for resultado in corrida:
            if fnd[-1] < serie[-1] and not ilimitado:
                break
            fondos = fnd[-1] - serie[-1]

            if es_ganadora(resultado, objetivo):
                fondos += serie[-1] * mult
                if len(serie) > 3:
                    serie.pop()
                    serie.pop()
                elif len(serie) == 3:
                    serie.pop()
            else:
                serie.append(serie[-1] + serie[-2])
            fnd.append(fondos)
        fnd_hist.append(fnd)
    return fnd_hist


def dalembert(corridas, ilimitado, objetivo):
    fnd_hist = []
    mult = obtener_multiplicador(objetivo)

    for corrida in corridas:
        ap = APUESTA_BASE
        fnd = [CAPITAL_INICIAL]
        for resultado in corrida:
            if fnd[-1] < ap and not ilimitado:
                break
            fondos = fnd[-1] - ap

            if es_ganadora(resultado, objetivo):
                fondos += ap * mult
                ap = max(1, ap - 1)
            else:
                ap += 1
            fnd.append(fondos)
        fnd_hist.append(fnd)
    return fnd_hist


def paroli(corridas, ilimitado, objetivo):
    fnd_hist = []
    mult = obtener_multiplicador(objetivo)

    for corrida in corridas:
        v = 0
        ap = APUESTA_BASE
        fnd = [CAPITAL_INICIAL]
        for resultado in corrida:
            if fnd[-1] < ap and not ilimitado:
                break
            fondos = fnd[-1] - ap

            if es_ganadora(resultado, objetivo):
                fondos += ap * mult
                v += 1
                ap = ap * 2 if v < 3 else APUESTA_BASE
                if v == 3:
                    v = 0
            else:
                v = 0
                ap = APUESTA_BASE
            fnd.append(fondos)
        fnd_hist.append(fnd)
    return fnd_hist


def elegir_estrategia(estrategia, corridas, ilimitado, objetivo):
    """Seleccionar estrategia de apuesta."""
    estrategias = {
        "m": martingala,
        "f": fibonacci,
        "d": dalembert,
        "o": paroli,
    }
    return estrategias[estrategia](corridas, ilimitado, objetivo)


def generar_graficas(corridas, fnd_hist, objetivo, estrategia, ilimitado):
    """Generar las tres gráficas solicitadas."""
    flujo_capital = np.array(fnd_hist[0])
    tipo_apuesta = "pares" if objetivo == "-" else f"número {objetivo}"
    tipo_capital = "infinito" if ilimitado else "finito"

    fig, axs = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(
        f"Estrategia {estrategia.capitalize()} - Apuesta a {tipo_apuesta} - Capital {tipo_capital}",
        fontsize=16,
    )

    # Gráfico de frecuencia relativa
    resultado_tiradas = [
        (x % 2 == 0) if objetivo == "-" else (x == objetivo) for x in corridas[0]
    ]
    conteo = np.cumsum(resultado_tiradas)
    frecuencia = conteo / np.arange(1, len(resultado_tiradas) + 1)

    axs[0].bar(range(len(frecuencia)), frecuencia, color="red")
    axs[0].axhline(
        y=(18 / 37 if objetivo == "-" else 1 / 37),
        color="blue",
        linestyle="--",
        linewidth=2,
    )
    axs[0].set_title("Frecuencia relativa de éxitos")
    axs[0].set_xlabel("Tiradas")
    axs[0].set_ylabel("Frecuencia")

    # Gráfico de flujo de capital (una corrida)
    axs[1].plot(flujo_capital, color="green")
    axs[1].axhline(y=CAPITAL_INICIAL, color="blue", linestyle="--")
    axs[1].set_title("Evolución del Capital (Primera Corrida)")
    axs[1].set_xlabel("Tiradas")
    axs[1].set_ylabel("Capital")

    # Gráfico de múltiples corridas
    for corrida in fnd_hist:
        axs[2].plot(corrida, alpha=0.7)
    axs[2].axhline(y=CAPITAL_INICIAL, color="blue", linestyle="--")
    axs[2].set_title("Evolución del Capital (Varias Corridas)")
    axs[2].set_xlabel("Tiradas")
    axs[2].set_ylabel("Capital")

    # Guardar archivo
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo = f"Grafica_{estrategia}_{tipo_apuesta}_{tipo_capital}_{fecha}.png"
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(archivo)
    print(f"Gráficas guardadas como: {archivo}")
    plt.show()


def main():
    num_corridas, num_tiradas, objetivo, estrategia, ilimitado = leer_parametros()

    corridas = [tiradas(num_tiradas) for _ in range(num_corridas)]
    fnd_hist = elegir_estrategia(estrategia, corridas, ilimitado, objetivo)

    generar_graficas(corridas, fnd_hist, objetivo, estrategia, ilimitado)


if __name__ == "__main__":
    main()
