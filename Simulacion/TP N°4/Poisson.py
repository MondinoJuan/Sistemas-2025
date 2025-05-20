import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import poisson

# Definicion de parametros
lam = 4       # lambda
n = 10000     # numero de muestras

# Definicion de la funcion de poisson
def generar_poisson_numpy(lam, n):
    return np.random.poisson(lam, n)

# Definicion de la funcion de rechazo de poisson
def generar_poisson_rechazo(lam, n, c=1.5):
    muestras = []
    x_max = int(lam + 10 * np.sqrt(lam)) 

    while len(muestras) < n:
        x = np.random.randint(0, x_max)
        u = np.random.uniform()

        px = poisson.pmf(x, lam)
        qx = 1 / x_max 
        if u <= px / (c * qx):
            muestras.append(x)

    return np.array(muestras)


# Grafico
def comparar_poisson(muestras_numpy, muestras_rechazo, lam):
    plt.hist(muestras_numpy, bins=np.arange(0, max(muestras_numpy.max(), muestras_rechazo.max()) + 1) - 0.5,
             density=True, alpha=0.5, color='green', label='Datos obtenidos')

    plt.hist(muestras_rechazo, bins=np.arange(0, max(muestras_numpy.max(), muestras_rechazo.max()) + 1) - 0.5,
             density=True, alpha=0.5, color='blue', label='Datos Método Rechazo')

    x = np.arange(0, max(muestras_numpy.max(), muestras_rechazo.max()) + 1)
    y = poisson.pmf(x, lam)
    plt.plot(x, y, 'k-', lw=2, label='Función teórica')

    plt.title("Comparación de generación Poisson")
    plt.xlabel("Valor")
    plt.ylabel("Probabilidad")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# Ejecucion
datos_obtenidos = generar_poisson_numpy(lam, n)
datos_rechazo = generar_poisson_rechazo(lam, n)
comparar_poisson(datos_obtenidos, datos_rechazo, lam)