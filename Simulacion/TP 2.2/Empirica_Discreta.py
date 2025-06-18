import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import rv_discrete

# Valores y probabilidades de la distribución empírica
valores = np.array([1, 2, 3, 4, 5])
probabilidades = np.array([0.1, 0.2, 0.3, 0.2, 0.2])
cantidad = 10000

# Método de rechazo
def metodo_rechazo_empirica(valores, probabilidades, cantidad):
    resultado = []
    p_max = max(probabilidades)
    while len(resultado) < cantidad:
        idx = np.random.randint(0, len(valores))
        candidato = valores[idx]
        u = np.random.uniform()
        if u < probabilidades[idx] / p_max:
            resultado.append(candidato)
    return np.array(resultado)

distribucion_empirica = rv_discrete(name='distribucion_empirica', values=(valores, probabilidades))  # se crea un objeto distribución
muestras_scipy = distribucion_empirica.rvs(size=cantidad)                                            # se generan muestras, devuelve un array donde los valores es 
                                                                                                     # cada uno de los numeros dentro de valores, pero elegidos segun su probabilidad

muestras_rechazo = metodo_rechazo_empirica(valores, probabilidades, cantidad)

# Gráficos
fig, axs = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

# Gráfico método de rechazo
axs[0].hist(muestras_rechazo, bins=np.arange(0.5, 6.6, 1), density=True, alpha=0.7, color='tomato', edgecolor='black')
axs[0].vlines(valores, 0, probabilidades, color='black', linewidth=2, label='Distribución teórica')
axs[0].set_title('Método de Rechazo (a mano)')
axs[0].set_xlabel('Valor')
axs[0].set_ylabel('Densidad')
axs[0].legend()

# Gráfico método con scipy
axs[1].hist(muestras_scipy, bins=np.arange(0.5, 6.6, 1), density=True, alpha=0.7, color='skyblue', edgecolor='black')
axs[1].vlines(valores, 0, probabilidades, color='black', linewidth=2, label='Distribución teórica')
axs[1].set_title('Método con librería (scipy)')
axs[1].set_xlabel('Valor')
axs[1].legend()

plt.tight_layout()
plt.show()
