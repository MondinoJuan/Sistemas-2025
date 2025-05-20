import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import uniform
from scipy.stats import kstest

## Distribución Uniforme

orig_a, orig_b = 0, 1
num_muestras = 1000
datos_dist_unif_original = np.random.uniform(orig_a, orig_b, num_muestras)

print("\n--- Estadísticas de la Distribución Uniforme ---")
print(f"  Uniforme U({orig_a}, {orig_b}): Media = {np.mean(datos_dist_unif_original):.3f} (Teórica: {(orig_a + orig_b)/2}), "f"Varianza = {np.var(datos_dist_unif_original):.3f} (Teórica: {(orig_b - orig_a)**2 / 12})")

plt.figure(figsize=(15, 6))

plt.subplot(1, 3, 1)
plt.hist(datos_dist_unif_original, bins=30, density=True, alpha=0.7, color='b', edgecolor='black', label='Muestras')
x_pdf_original = np.linspace(orig_a - 0.2, orig_b + 0.2, 100)
plt.plot(x_pdf_original, uniform.pdf(x_pdf_original, loc=orig_a, scale=orig_b - orig_a), 'r-', linewidth=2, label='PDF Teórica')
plt.title(f'Distribución Uniforme U({orig_a}, {orig_b})')
plt.xlabel('Valor')
plt.ylabel('Densidad')
plt.xlim(orig_a - 0.2, orig_b + 0.2)
plt.legend()

## Transformada Inversa de la Distribución Uniforme

def transformada_inversa_uniforme(array, limiteInf, limiteSup):
    return limiteInf + (limiteSup - limiteInf) * array

inv_a, inv_b = 0, 10
numeros_aleatorios = np.random.rand(num_muestras)
datos_inversa = transformada_inversa_uniforme(numeros_aleatorios, inv_a, inv_b)

print("\n--- Estadísticas de la Transformada Inversa de la Distribución Uniforme ---")
print(f"  Uniforme U({inv_a}, {inv_b}): Media = {np.mean(datos_inversa):.3f} (Teórica: {(inv_a + inv_b)/2}), "f"Varianza = {np.var(datos_inversa):.3f} (Teórica: {(inv_b - inv_a)**2 / 12})")

plt.subplot(1, 3, 2)
plt.hist(datos_inversa, bins=30, density=True, alpha=0.7, color='skyblue', edgecolor='black', label='Muestras')
x_pdf_inversa = np.linspace(inv_a - 1, inv_b + 1, 1000)
plt.plot(x_pdf_inversa, uniform.pdf(x_pdf_inversa, loc=inv_a, scale=inv_b - inv_a), 'r-', label='PDF Teórica')
plt.title(f'Distribución Uniforme U({inv_a}, {inv_b}) \n(Método Transformación Inversa)')
plt.xlabel('Valor')
plt.ylabel('Densidad')
plt.xlim(inv_a - 1, inv_b + 1)
plt.legend()

## Metodo de rechazo

# Suponemos que deseamos generar muestras de U(2, 5) usando el método de rechazo
rech_a, rech_b = 2, 5  # Intervalo objetivo de la distribución uniforme
cota_superior = 1.0  # Cota superior para la función de densidad (PDF constante en uniforme)

muestras_rechazo = []
while len(muestras_rechazo) < num_muestras:
    x_candidato = np.random.uniform(rech_a, rech_b)
    y_candidato = np.random.uniform(0, cota_superior)

    if y_candidato <= 1 / (rech_b - rech_a):
        muestras_rechazo.append(x_candidato)

muestras_rechazo = np.array(muestras_rechazo)

print("\n--- Estadísticas del Método de Rechazo ---")
print(f"  Uniforme U({rech_a}, {rech_b}): Media = {np.mean(muestras_rechazo):.3f} (Teórica: {(rech_a + rech_b)/2}), "f"Varianza = {np.var(muestras_rechazo):.3f} (Teórica: {(rech_b - rech_a)**2 / 12})")

plt.subplot(1, 3, 3)
plt.hist(muestras_rechazo, bins=30, density=True, alpha=0.7, color='skyblue', edgecolor='black', label='Muestras')
x_pdf_rechazo = np.linspace(rech_a - 1, rech_b + 1, 1000)
plt.plot(x_pdf_rechazo, uniform.pdf(x_pdf_rechazo, loc=rech_a, scale=rech_b - rech_a), 'r-', label='PDF Teórica')
plt.title(f'Distribución Uniforme U({rech_a}, {rech_b}) \n(Método de Rechazo)')
plt.xlabel('Valor')
plt.ylabel('Densidad')
plt.xlim(rech_a - 1, rech_b + 1)
plt.legend()

plt.tight_layout()
plt.savefig('distribuciones_uniformes.png')
plt.show()

## Testeo

# Test de Kolmogorov-Smirnov para la distribución uniforme original
print("\n--- Testeo de la Distribución Uniforme ---")

ks_stat_orig, p_val_orig = kstest(datos_dist_unif_original, 'uniform', args=(orig_a, orig_b - orig_a))
print(f"  KS Test U({orig_a}, {orig_b}): Estadístico = {ks_stat_orig:.4f}, p-valor = {p_val_orig:.4f}")

if p_val_orig > 0.05:
    print("  La muestra original proviene de una distribución uniforme (Kolmogorov-Smirnov no rechaza la Hipótesis Nula (H0)).")
else:
    print("  La muestra original NO parece provenir de una distribución uniforme (Kolmogorov-Smirnov rechaza la Hipótesis Nula (H0)).")

# Test de Kolmogorov-Smirnov para la transformada inversa
print("\n--- Testeo de la Transformada Inversa de la Distribución Uniforme ---")

ks_stat_inv, p_val_inv = kstest(datos_inversa, 'uniform', args=(inv_a, inv_b - inv_a))
print(f"  KS Test U({inv_a}, {inv_b}): Estadístico = {ks_stat_inv:.4f}, p-valor = {p_val_inv:.4f}")

if p_val_inv > 0.05:
    print("  La muestra generada por transformación inversa proviene de una distribución uniforme (Kolmogorov-Smirnov no rechaza la Hipótesis Nula (H0)).")
else:
    print("  La muestra generada por transformación inversa NO parece provenir de una distribución uniforme (Kolmogorov-Smirnov rechaza la Hipótesis Nula (H0)).")

# Test de Kolmogorov-Smirnov para el método de rechazo
print("\n--- Testeo del Método de Rechazo ---")

ks_stat_rej, p_val_rej = kstest(muestras_rechazo, 'uniform', args=(rech_a, rech_b - rech_a))
print(f"  KS Test U({rech_a}, {rech_b}): Estadístico = {ks_stat_rej:.4f}, p-valor = {p_val_rej:.4f}")

if p_val_rej > 0.05:
    print("  La muestra generada por el método de rechazo proviene de una distribución uniforme (Kolmogorov-Smirnov no rechaza la Hipótesis Nula (H0)).")
else:
    print("  La muestra generada por el método de rechazo NO parece uniforme (Kolmogorov-Smirnov rechaza la Hipótesis Nula (H0)).")