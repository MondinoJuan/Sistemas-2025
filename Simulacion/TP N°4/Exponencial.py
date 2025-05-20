import numpy as np
import matplotlib.pyplot as plt

# Generador de numeros uniformes
def dist_uniforme():
    return np.random.uniform(low=0.0, high=1.0, size=100)

# Transformada inversa
def transformada_inversa_exponencial(array, lambda_param):
    """
    Debido a la simetría que existe entre la distribución uniforme que sigue la intercambiabilidad de F (x) y 1 − F (x)
    """
    return -np.log(1 - array) / lambda_param


# Metodo de rechazo
def metodo_rechazo_exponencial(array, lambda_param):
    K = len(array)
    U = np.random.uniform(low=0.0, high=1.0, size=K)
    X = -np.log(1 - U) / lambda_param
    return X

# Testeo
def comparar_exponencial(lambda_param, n=10000):
    u = dist_uniforme()
    muestras_inversa = transformada_inversa_exponencial(u, lambda_param)
    muestras_rechazo = metodo_rechazo_exponencial(muestras_inversa, lambda_param)

    plt.hist(muestras_inversa, bins=50, density=True, alpha=0.5, label='Exponencial', color='green')
    plt.hist(muestras_rechazo, bins=50, density=True, alpha=0.5, label='Método de Rechazo', color='blue')

    x = np.linspace(0, np.max([muestras_inversa.max(), muestras_rechazo.max()]), 200)
    y = lambda_param * np.exp(-lambda_param * x)
    plt.plot(x, y, 'k-', lw=2,  label='Función Teórica')

    plt.title("Comparación: Exponencial vs Método de Rechazo")
    plt.xlabel("Valor")
    plt.ylabel("Densidad")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Ejecucion
comparar_exponencial(2.0)