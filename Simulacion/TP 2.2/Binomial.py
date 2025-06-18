import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binom
from scipy.stats import chisquare

## Distribución Binomial

orig_n, orig_p = 20, 0.3  # Parámetros originales: n ensayos, p probabilidad de éxito
num_muestras = 1000
datos_dist_binom_original = np.random.binomial(orig_n, orig_p, num_muestras)

print("\n--- Estadísticas de la Distribución Binomial ---")
print(f"  Binomial B({orig_n}, {orig_p}): Media = {np.mean(datos_dist_binom_original):.3f} (Teórica: {orig_n * orig_p}), "f"Varianza = {np.var(datos_dist_binom_original):.3f} (Teórica: {orig_n * orig_p * (1 - orig_p)})")

plt.figure(figsize=(15, 6))

plt.subplot(1, 2, 1)
# Histograma y PMF (función de masa de probabilidad) para la distribución binomial original
valores, conteos = np.unique(datos_dist_binom_original, return_counts=True)
plt.bar(valores, conteos/num_muestras, alpha=0.7, color='b', edgecolor='black', label='Muestras')
x_pmf_original = np.arange(0, orig_n + 1)
plt.plot(x_pmf_original, binom.pmf(x_pmf_original, orig_n, orig_p), 'ro-', linewidth=2, label='PMF Teórica')
plt.title(f'Distribución Binomial B({orig_n}, {orig_p})')
plt.xlabel('Número de éxitos')
plt.ylabel('Probabilidad')
plt.xlim(-1, orig_n + 1)
plt.legend()

## Método de Rechazo

# Para el método de rechazo necesitamos una distribución propuesta y una constante M
rech_n, rech_p = 10, 0.6  # Parámetros para el método de rechazo
max_pmf = max(binom.pmf(np.arange(0, rech_n + 1), rech_n, rech_p))
M = 1.2 * max_pmf  # Factor de escala para asegurar que M sea mayor que el máximo de la PMF

muestras_rechazo = []
intentos = 0
max_intentos = num_muestras * 100  # Limitamos el número máximo de intentos

while len(muestras_rechazo) < num_muestras and intentos < max_intentos:
    intentos += 1
    x_candidato = np.random.randint(0, rech_n + 1)
    y_candidato = np.random.uniform(0, M)
    if y_candidato <= binom.pmf(x_candidato, rech_n, rech_p):
        muestras_rechazo.append(x_candidato)

muestras_rechazo = np.array(muestras_rechazo)

print("\n--- Estadísticas del Método de Rechazo ---")
print(f"  Binomial B({rech_n}, {rech_p}): Media = {np.mean(muestras_rechazo):.3f} (Teórica: {rech_n * rech_p}), "f"Varianza = {np.var(muestras_rechazo):.3f} (Teórica: {rech_n * rech_p * (1 - rech_p)})")
print(f"  Eficiencia del método de rechazo: {num_muestras/intentos:.4f} ({num_muestras} aceptados de {intentos} intentos)")

plt.subplot(1, 2, 2)
valores_rech, conteos_rech = np.unique(muestras_rechazo, return_counts=True)
plt.bar(valores_rech, conteos_rech/num_muestras, alpha=0.7, color='skyblue', edgecolor='black', label='Muestras')
x_pmf_rechazo = np.arange(0, rech_n + 1)
plt.plot(x_pmf_rechazo, binom.pmf(x_pmf_rechazo, rech_n, rech_p), 'ro-', label='PMF Teórica')
plt.title(f'Distribución Binomial B({rech_n}, {rech_p}) \n(Método de Rechazo)')
plt.xlabel('Número de éxitos')
plt.ylabel('Probabilidad')
plt.xlim(-1, rech_n + 1)
plt.legend()

plt.tight_layout()
plt.savefig('distribuciones_binomiales.png')
plt.show()

## Testeo

print("\n--- Testeo de la Distribución Binomial ---")

def test_chi_cuadrado_binomial(datos, n, p):
    valores, frecuencias_observadas = np.unique(datos, return_counts=True)
    frecuencias_esperadas = len(datos) * binom.pmf(valores, n, p)
    # Aseguramos que las frecuencias esperadas sumen exactamente el tamaño de la muestra para evitar errores de tolerancia numérica
    frecuencias_esperadas = frecuencias_esperadas * (len(datos) / np.sum(frecuencias_esperadas))
    stat, p_valor = chisquare(frecuencias_observadas, frecuencias_esperadas)
    return stat, p_valor

# Test de Chi-Cuadrado para la distribución binomial original
chi2_stat_orig, p_val_orig = test_chi_cuadrado_binomial(datos_dist_binom_original, orig_n, orig_p)
print(f"  Chi-Cuadrado Test B({orig_n}, {orig_p}): Estadístico = {chi2_stat_orig:.4f}, p-valor = {p_val_orig:.4f}")

if p_val_orig > 0.05:
    print("  La muestra original proviene de una distribución binomial (Chi-cuadrado no rechaza la Hipótesis Nula (H0)).")
else:
    print("  La muestra original NO parece provenir de una distribución binomial (Chi-cuadrado rechaza la Hipótesis Nula (H0)).")

# Test de Chi-Cuadrado para el método de rechazo
print("\n--- Testeo de la Distribución Binomial ---")

chi2_stat_rej, p_val_rej = test_chi_cuadrado_binomial(muestras_rechazo, rech_n, rech_p)
print(f"  Chi-Cuadrado Test B({rech_n}, {rech_p}): Estadístico = {chi2_stat_rej:.4f}, p-valor = {p_val_rej:.4f}")

if p_val_rej > 0.05:
    print("  La muestra generada por el método de rechazo proviene de una distribución binomial (Chi-cuadrado no rechaza la Hipótesis Nula (H0)).")
else:
    print("  La muestra generada por el método de rechazo NO parece binomial (Chi-cuadrado rechaza la Hipótesis Nula (H0)).")