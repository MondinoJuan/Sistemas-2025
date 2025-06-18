import numpy as np
import matplotlib.pyplot as plt

# Generador de numeros uniformes
def dist_uniforme(cantidad=100):
    return np.random.uniform(low=0.0, high=1.0, size=cantidad)

# Transformo un arreglo de numeros uniformes a una normal con el procedimiento directo
def transformar_inversa_normal(array):
    resultado = []
    for i in range(0, len(array), 2):
        if i + 1 < len(array):
            r1 = array[i]
            r2 = array[i + 1]
            
            z1 = np.sqrt(-2 * np.log(r1)) * np.cos(2 * np.pi * r2)
            z2 = np.sqrt(-2 * np.log(r1)) * np.sin(2 * np.pi * r2)

            resultado.append(z1)
            resultado.append(z2)

    return np.array(resultado)

# Metodo de rechazo
def normal_rechazo(array_uniforme):    
    if len(array_uniforme) % 2 != 0:
        array_uniforme = array_uniforme[:-1]
    
    resultado = []
    rechazos = 0
    total_intentos = 0
    
    # Rango para mapear [0,1] a [-a,a]
    #Esto es necesario porque la distribución normal tiene soporte en todo ℝ (no solo en [0,1]).
    a = 4.0
    
    i = 0
    while i < len(array_uniforme) - 1:
        total_intentos += 1
        
        u1 = array_uniforme[i]
        x = -a + 2*a*u1  # Mapear [0,1] a [-a,a]
        
        # Segundo valor para el criterio de aceptación
        u2 = array_uniforme[i+1]
        
        # Función de densidad normalizada
        fx_normalizada = np.exp(-(x**2)/2)
        
        # Criterio de aceptación
        if u2 <= fx_normalizada:
            resultado.append(x)
        else:
            rechazos += 1
        
        i += 2
    
    tasa_aceptacion = len(resultado) / total_intentos if total_intentos > 0 else 0
    print(f"Tasa de aceptación: {tasa_aceptacion:.4f}")
    print(f"Total de rechazos: {rechazos}")
    print(f"Valores generados: {len(resultado)}")
    
    return np.array(resultado)

def normal_parametros(valores_estandar, mu=0, sigma=1):
    """
    Adapta valores de una normal estándar a N(μ, σ²)
    """
    return mu + sigma * valores_estandar

# Testeo
mu = 0
sigma = 1
cantidad_numeros = 2000

arreglo_uniforme = dist_uniforme(cantidad_numeros)

arreglo_normal_rechazo = normal_rechazo(arreglo_uniforme)
arreglo_normal_inversa = transformar_inversa_normal(arreglo_uniforme)

arregloN_inversa_parametros = normal_parametros(arreglo_normal_inversa, mu, sigma)
arregloN_rechazos_parametros = normal_parametros(arreglo_normal_rechazo, mu, sigma)

# Comparamos con numpy para verificar
arreglo_numpy = np.random.normal(mu, sigma, len(arregloN_rechazos_parametros))

# Gráficos
plt.figure(figsize=(12, 8))

# Histograma Método de Rechazo
plt.hist(arregloN_rechazos_parametros, bins=30, density=True, alpha=0.6, color='r', label='Método de Rechazo')


# Histograma Transformada Inversa
plt.hist(arregloN_inversa_parametros, bins=30, density=True, alpha=0.6, color='g', label='Transformada Inversa')

# Histograma NumPy
plt.hist(arreglo_numpy, bins=30, density=True, alpha=0.6, color='b', label='NumPy normal')

x = np.linspace(-4, 4, 1000)
y = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
plt.plot(x, y, 'k-', lw=2, label='Función teórica')
plt.xlim(-4, 4)
plt.xlabel('Valor')
plt.ylabel('Densidad')
plt.title('Distribución Normal Comparación')
plt.legend()
plt.tight_layout()
plt.show()

