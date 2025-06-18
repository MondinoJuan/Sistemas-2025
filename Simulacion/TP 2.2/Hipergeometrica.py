import numpy as np
import math
import matplotlib.pyplot as plt

def combinacion(n, k):
    return math.comb(n, k)

def prob_hipergeometrica(N, K, n, x):
    if x < 0 or x > min(K, n) or n - x > N - K:
        return 0
    return combinacion(K, x) * combinacion(N - K, n - x) / combinacion(N, n)

# Método de rechazo
def metodo_rechazo_hipergeometrica(N, K, n, cantidad):
    resultado = []
    x_min = max(0, n - (N - K))
    x_max = min(K, n)

    # Calcular la probabilidad máxima (para normalizar)
    probs = [prob_hipergeometrica(N, K, n, x) for x in range(x_min, x_max + 1)]
    p_max = max(probs)

    while len(resultado) < cantidad:
        # Candidato x porque no hay forma directa como en otras distribuciones
        x = np.random.randint(x_min, x_max + 1)
        
        u = np.random.uniform(0, 1)
        if u <= prob_hipergeometrica(N, K, n, x) / p_max:
            resultado.append(x)

    return resultado


# Testeo
N, K, n = 80, 22, 12
muestras = metodo_rechazo_hipergeometrica(N, K, n, 10000)

# Genero con libreria para comparar
muestras_libreria = np.random.hypergeometric(K, N - K, n, 10000)

# Rango de valores posibles
x_vals = np.arange(max(0, n - (N - K)), min(K, n) + 1)
pmf_vals = [prob_hipergeometrica(N, K, n, x) for x in x_vals]

print(f"Media NumPy: {np.mean(muestras_libreria):.2f}, Media Teórica: {np.sum(x_vals * pmf_vals):.2f}")

# Gráfico único superpuesto
plt.figure(figsize=(10, 6))

# Histograma del método de rechazo
plt.hist(muestras, bins=np.arange(x_vals[0], x_vals[-1] + 2) - 0.5, density=True, alpha=0.6, color='blue', label='Método de Rechazo')

# Histograma de NumPy
plt.hist(muestras_libreria, bins=np.arange(x_vals[0], x_vals[-1] + 2) - 0.5, density=True, alpha=0.6, color='red', label='NumPy')

# Función teórica
plt.plot(x_vals, pmf_vals, 'ko-', lw=2, label='Distribución Teórica')

plt.xlabel('x')
plt.ylabel('Densidad')
plt.title('Distribución Hipergeométrica: Rechazo vs NumPy vs Teórica')
plt.legend()
plt.tight_layout()
plt.show()