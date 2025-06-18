# Generador de numeros pseudoaleatorios

# GCL
def gcl(multiplicador, constante, modulo, semilla, n):
    numeros = []
    for i in range(n):
        semilla = (multiplicador * semilla + constante) % modulo
        numeros.append(semilla)
    return numeros

# MWC
def mwc(multiplicador, semilla, carry, modulo, n):
    numeros = []
    for i in range(n):
        t = multiplicador * semilla + carry
        semilla = t % modulo
        carry = t // modulo
        numeros.append(semilla)
    return numeros

# Generador propio de Python, el Mersenne Twister. El que está en la librería random de Python.
def mersenne_twister(n):
    import random
    numeros = [random.randint(0, 2**32 - 1) for _ in range(n)]
    return numeros


# TESTS
import numpy as np
from scipy.stats import chisquare
from scipy.stats import norm
from scipy.stats import kstest
from scipy.stats import chi2
import matplotlib.pyplot as plt


# Evalúo la ausencia de patrones
# Test Scatter Plot
# Es un grafico visual
def test_scatter_plot(numeros, n=1000):
    # Usar solo los primeros n valores (y asegurarse de tener al menos n+1 valores para pares)
    numeros = np.array(numeros[:n+1])

    # Normalizar a [0, 1]
    numeros_norm = (numeros - 1) / (2**32 - 2)

    # Formar pares consecutivos
    x = numeros_norm[:-1]
    y = numeros_norm[1:]

    # Crear scatter plot de pares consecutivos
    plt.figure(figsize=(6, 6))
    plt.scatter(x, y, s=1)
    plt.title("Scatter Plot de Pares Consecutivos (xₙ vs xₙ₊₁)")
    plt.xlabel("xₙ")
    plt.ylabel("xₙ₊₁")
    plt.grid()
    plt.show()

# Test Serial
# Cuantifica la dependencia entre pares consecutivos de números generados.
def serial_test(numeros, bins=5, alpha=0.05):
    # Normalizar a [0,1]
    numeros_norm = (np.array(numeros) - 1) / (2**32 - 2)

    # Formar pares consecutivos
    x = numeros_norm[:-1]
    y = numeros_norm[1:]

    # Construye histograma
    hist, _, _, = np.histogram2d(x, y, bins=bins, range=[[0, 1], [0, 1]])

    # Número total de pares
    n = len(x)

    # Frecuencia esperada por celda (bajo H₀ de uniformidad)
    esperado = n / (bins * bins)

    # Calcular estadístico chi-cuadrado
    chi2_stat = np.sum((hist - esperado)**2 / esperado)

    # Grados de libertad = (k² - 1)
    gl = bins * bins - 1

    p_value = 1 - chi2.cdf(chi2_stat, df=gl)

    # Imprimir resultados
    print(f"Chi cuadrado: {chi2_stat}")
    print(f"Grados de libertad: {gl}")
    print(f"P-valor: {p_value}")

    if p_value < alpha:
        print(f"Rechazamos H₀: Hay evidencia de dependencia/patrones (p-valor < {alpha})")
    else:
        print(f"No se rechaza H₀: No hay evidencia de patrones (p-valor >= {alpha})")

    # Opcional: visualizar el histograma 2D
    plt.imshow(hist, cmap='Blues', origin='lower')
    plt.colorbar(label='Frecuencia')
    plt.title(f"Histograma 2D de Pares Consecutivos ({bins}x{bins})")
    plt.xlabel("xₙ (bins)")
    plt.ylabel("xₙ₊₁ (bins)")
    plt.show()

    return chi2_stat, p_value

# Evalúo independencia
# Test de autocorrelación
def test_autocorrelacion(numeros, lag=1, alpha=0.05):
    n = len(numeros)
    media = np.mean(numeros)
    
    # Se normalizan los numeros a [0, 1]
    numeros_norm = (numeros - 1) / (2**32 - 2)  # Si los números están entre 1 y 2**32-1

    # Calculo autocorrelacion
    numerador = np.sum((numeros_norm[:-lag] - media) * (numeros_norm[lag:] - media))
    denominador = np.sum((numeros_norm - media) ** 2)
    autocorr = numerador / denominador

    # Error estándar
    # Da una medida de la variabilidad esperada en la estimación de la autocorrelación.
    # Cuanto más grande sea el número de observaciones, menor será el error estándar.
    error_estandar = np.sqrt((1 + 2 * np.sum(autocorr ** 2)) / n)

    # Estadístico Z
    # Indica qué tan lejos está la autocorrelacion observada de lo que esperaríamos si no hay autocorrelación. 
    # Mas cerca del 0, menos autocorrelación, mas independencia.
    z = autocorr / error_estandar

    # Valor crítico
    # Es un umbral calculado de acuerdo con el nivel de significancia (alpha), 
    # y nos dice cuál es el límite a partir del cual podemos rechazar la hipótesis nula.
    valor_critico = norm.ppf(1 - alpha / 2)

    print(f"Autocorrelación: {autocorr}")
    print(f"Z: {z}")
    print(f"Valor crítico: ±{valor_critico}")

    if abs(z) <= valor_critico:
        print("No se rechaza H₀: No hay autocorrelación significativa.")
    else:
        print("Se rechaza H₀: Hay autocorrelación significativa.")

    return autocorr, z, valor_critico

# Evaluo uniformidad
# Chi cuadrado para uniformidad
def test_chi_square(numeros, intervalos=10, alpha=0.05):
    # Dividir los números en intervalos
    hist, _ = np.histogram(numeros, bins=intervalos)

    # Calcular la expectativa uniforme para cada intervalo
    esperado = len(numeros) / intervalos
    esperados = [esperado] * len(hist)

    # Calcular la estadística chi-cuadrado
    chi2, p_value = chisquare(hist, f_exp=esperados)

    print(f"Chi cuadrado: {chi2}, p-valor: {p_value}")

    # Decisión
    if p_value < alpha:
        print(f"Rechazamos la hipótesis nula (p-valor < {alpha})")
    else:
        print(f"No podemos rechazar la hipótesis nula (p-valor >= {alpha})")

    return chi2, p_value

# Test de Kolmogorov-Smirnov para uniformidad
def test_kolmogorov_smirnov(numeros, alpha=0.05):

    numeros_norm = (np.array(numeros) - 1) / (2**32 - 2)

    # Aplicar el test K-S contra la distribución uniforme [0,1]
    stat, p_value = kstest(numeros_norm, 'uniform')

    print(f"Estadística D: {stat}")
    print(f"P-valor: {p_value}")

    if p_value > alpha:
        print("No se rechaza H₀: Los datos son consistentes con una distribución uniforme.")
    else:
        print("Se rechaza H₀: Los datos no son consistentes con una distribución uniforme.")

    return stat, p_value

# Test de la media
def test_media(numeros, alpha=0.05):

    # Normalizar a [0, 1]
    numeros_norm = (np.array(numeros) - 1) / (2**32 - 2)

    n = len(numeros_norm)
    media_muestral = np.mean(numeros_norm)
    media_esperada = 0.5
    varianza = 1 / 12

    # Calcular la estadística Z
    error_estandar = (varianza / n) ** 0.5
    z = (media_muestral - media_esperada) / error_estandar

    # Valor crítico para el intervalo de confianza (bilateral)
    valor_critico = norm.ppf(1 - alpha / 2)

    print(f"Media muestral: {media_muestral}")
    print(f"Z: {z}")
    print(f"Valor crítico: ±{valor_critico}")

    if abs(z) <= valor_critico:
        print("No se rechaza H₀: La media es consistente con una distribución uniforme.")
    else:
        print("Se rechaza H₀: La media no es consistente con una distribución uniforme.")

    return z, valor_critico