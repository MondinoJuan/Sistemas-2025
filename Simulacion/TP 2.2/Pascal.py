import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import nbinom, poisson

# Definicion de parametros
r = 10     # cantidad de exitos esperados
p = 0.7    # probabilidad de exito
n = 10000  # numero de muestras


# Definicion de la funcion de Pascal
def generar_pascal_numpy(r, p, n):
    return np.random.negative_binomial(r, p, n)


# Definicion de la funcion de rechazo de Pascal
def generar_pascal_rechazo(r, p, n, c=2):
    media = r * (1 - p) / p
    muestras = []
    while len(muestras) < n:
        x = np.random.poisson(media)
        u = np.random.uniform()
        px = nbinom.pmf(x, r, p)
        qx = poisson.pmf(x, media)
        if u <= px / (c * qx):
            muestras.append(x)
    return np.array(muestras)


# Grafico
def graficar_distribuciones(muestras1, muestras2, r, p):
    plt.hist(muestras1, bins=30, density=True, alpha=0.5, color='g', label='Datos Obtenidos')
    plt.hist(muestras2, bins=30, density=True, alpha=0.5, color='b', label='Datos Método Rechazo')
    
    x = np.arange(0, max(np.max(muestras1), np.max(muestras2)) + 1)
    y = nbinom.pmf(x, r, p)
    plt.plot(x, y, 'k-', lw=2, label='Función teórica')
    
    plt.xlabel("Valor")
    plt.ylabel("Densidad de probabilidad")
    plt.title("Distribución Pascal (Binomial Negativa)")
    plt.legend()
    plt.grid(True)
    plt.show()

# Ejecucion
datos_obtenidos = generar_pascal_numpy(r, p, n)
datos_rechazo = generar_pascal_rechazo(r, p, n, c=2)
graficar_distribuciones(datos_obtenidos, datos_rechazo, r, p)