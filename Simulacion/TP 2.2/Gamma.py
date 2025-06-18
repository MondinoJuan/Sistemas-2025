import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

# Generador de numeros uniformes
def dist_uniforme(cantidad = 1000):
    return np.random.uniform(low=0.0, high=1.0, size=cantidad)

# Transformada inversa
def transformada_inversa_Gamma(array, shape = 2.0, scale = 2.0):
    # Método de suma de exponentiales para k entero
    resultado = []
    for u in array:
        prod = 1.0
        for _ in range(int(shape)):
            prod *= np.random.uniform(0, 1)
        x = -scale * np.log(prod)
        resultado.append(x)
    return np.array(resultado)

# Metodo de rechazo
def metodo_rechazo_Gamma(array, shape = 2.0, scale = 2.0):
    resultado = []
    for u in array:
        x = -scale * np.log(u)
        y = np.random.uniform(0, 1)
        if y < (x ** (shape - 1)) * np.exp(-x / scale) / (scale ** shape):
            resultado.append(x)
    return np.array(resultado)

# Testeo
# Parámetros
shape = 2.0
scale = 2.0
cantidad = 10000

uniformes = dist_uniforme(cantidad)
gamma_inversa = transformada_inversa_Gamma(uniformes, shape, scale)
gamma_rechazo = metodo_rechazo_Gamma(uniformes, shape, scale)
gamma_np = np.random.gamma(shape, scale, cantidad)

# Rango para la función teórica
x = np.linspace(0, max(np.max(gamma_inversa), np.max(gamma_rechazo), np.max(gamma_np)), 1000)
y = stats.gamma.pdf(x, a=shape, scale=scale)

# Gráfico
plt.figure(figsize=(12, 8))

plt.hist(gamma_inversa, bins=50, density=True, alpha=0.5, color='b', label='Transformada Inversa')
plt.hist(gamma_rechazo, bins=50, density=True, alpha=0.5, color='g', label='Método de Rechazo')
plt.hist(gamma_np, bins=50, density=True, alpha=0.5, color='r', label='np Gamma')

plt.plot(x, y, 'k-', linewidth=2, label='Función Teórica')

plt.title('Distribución Gamma - Comparación de Métodos')
plt.xlabel('Valor')
plt.ylabel('Densidad')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

