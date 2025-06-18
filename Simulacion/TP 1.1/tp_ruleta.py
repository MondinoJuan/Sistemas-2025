import random
import sys
import numpy as np
import matplotlib.pyplot as plt
from typing import List


# Definicion de funciones aux
def vpRespectoN(array: List[int]):
    cont = 0
    suma = 0
    devuelvo = [] * len(array)

    for i in array:
        suma += i
        cont += 1
        devuelvo.append(suma/cont)
    
    return devuelvo

def desvio_estandar_acumulado(resultados):
    desvios = []
    for i in range(1, len(resultados) + 1):
        datos = resultados[:i]
        desvios.append(np.std(datos, ddof=0))
    return desvios

def varianza_acumulada(arreglo):
    varianzas = []
    for i in arreglo:
        varianzas.append(i**2)

    return varianzas

# Verificar si se proporciona el número de valores como argumento
if len(sys.argv) != 7 or sys.argv[1] != "-c" or sys.argv[3] != "-n" or sys.argv[5] != "-e":
    print("Uso: python tp_ruleta.py -c <num_corridas> -n <num_tiradas> -e <num_objetivo>")
    sys.exit(1)
if int(sys.argv[6]) < 0 or int(sys.argv[6]) > 36:
    print("El numero objetivo debe pertenecer al intervalo [0, 36]")
    sys.exit(1)

# Obtener cantidad de corridas
num_corridas = int(sys.argv[2])

# Obtener cantidad de tiradas por corridas
num_tiradas = int(sys.argv[4])

# Obtener numero objetivo
num_objetivo = int(sys.argv[6])

# Generar los valores aleatorios por cada tirada (valores entre 0 y 36)
def tiradas(num_tiradas): 
    lista_tiradas = [random.randint(0, 36) for _ in range(num_tiradas)]
    return lista_tiradas

# Crear la lista donde se guardan todas las corridas
corridas = []
for i in range(num_corridas):
    corridas.append(tiradas(num_tiradas))

# Analizar la media, la varianza y el desvio por corrida
for x in corridas:
    data = np.array(x)

    media = data.mean()
    desvio = data.std()
    varianza = data.var()

    #print(f"El listado de numeros que salió es: {data}")
    #print(f"Media: {media}, Desvío estándar: {desvio}, Varianza: {varianza}")

# Generando graficas
fig1, axs1 = plt.subplots(2, 2, figsize=(10, 10), constrained_layout=True)
fig2, axs2 = plt.subplots(2, 2, figsize=(10, 10), constrained_layout=True)

# Graficas singulares
# Grafica de Fr y Fe
fe = 1/37
conteos = np.cumsum(np.array(corridas[0]) == num_objetivo)
no_fr = conteos / np.arange(1, num_tiradas + 1)

axs1[0, 0].plot(no_fr, color='red', linestyle='-', label = f'Frecuencia relativa de {num_objetivo}') 
axs1[0, 0].axhline(fe, color='blue', linewidth=3, linestyle='--', label='Frecuencia relativa esperada')
axs1[0, 0].set_title('Gráfico 1: FR y FE de NO')
axs1[0, 0].set_xlabel('Tiradas')
axs1[0, 0].set_ylabel('Frecuencia')
axs1[0, 0].legend()

# Grafica de la media
rango = np.array(list(range(37)))
media = rango.mean()
vpU_Arreglo = vpRespectoN(np.array(corridas[0]))

axs1[0, 1].plot(vpU_Arreglo, color='red', linestyle='-', label = "Valor promedio con respecto a las tiradas")
axs1[0, 1].axhline(media, color='blue', linestyle='--', label = "Valor promedio esperado")
axs1[0, 1].set_title('Gráfico 2: Media')
axs1[0, 1].set_xlabel('Tiradas')
axs1[0, 1].set_ylabel('Valor promedio')
axs1[0,1].legend()

# Grafica del desvio
desvAcum = desvio_estandar_acumulado(np.array(corridas[0]))

axs1[1,0].plot(desvAcum, color='red', linestyle='-', label = f"Valor del desvío con respecto a las tiradas")
axs1[1,0].axhline(desvio, color='blue', linestyle='--', label = "Valor del desvio esperado")
axs1[1,0].set_title('Gráfico 3: Desvio')
axs1[1,0].set_xlabel('Tiradas')
axs1[1,0].set_ylabel('Valor del desvío')
axs1[1,0].legend()

# Grafica de la varianza
varAcum = varianza_acumulada(desvAcum)

axs1[1,1].plot(varAcum, color='red', linestyle='-', label = f"Valor de la varianza con respecto a las tiradas")
axs1[1,1].axhline(varianza, color='blue', linestyle='--', label = "Valor de la varianza esperada") 
axs1[1,1].set_title('Gráfico 4: Varianza')
axs1[1,1].set_xlabel('Tiradas')
axs1[1,1].set_ylabel('Varianza')
axs1[1,1].legend()

# Graficas de varias corridas
# Grafica de Fr y Fe
for x in corridas:
    conteos = np.cumsum(np.array(x) == num_objetivo)
    no_fr = conteos / np.arange(1, num_tiradas + 1)
    axs2[0, 0].plot(no_fr) 
axs2[0, 0].axhline(fe, color='blue', linewidth=3, linestyle='--')
axs2[0, 0].set_title('Gráfico 1: FR y FE de NO (multiples corridas)')
axs2[0, 0].set_xlabel('Tiradas')
axs2[0, 0].set_ylabel('Frecuencia')

# Grafica de la media
rango = np.array(list(range(37)))
media = rango.mean()

for x in corridas:
    vpU_Arreglo = vpRespectoN(np.array(x))
    axs2[0, 1].plot(vpU_Arreglo, linestyle='-')
axs2[0, 1].axhline(media, color='blue', linestyle='--', label = "Valor promedio esperado")
axs2[0, 1].set_title('Gráfico 2: Media (multiples corridas)')
axs2[0, 1].set_xlabel('Tiradas')
axs2[0, 1].set_ylabel('Valor promedio')

# Grafica del desvio
for x in corridas:
    desvAcum = desvio_estandar_acumulado(np.array(x))
    axs2[1,0].plot(desvAcum, linestyle='-')
axs2[1,0].axhline(desvio, color='blue', linestyle='--', label = "Valor del desvio esperado")
axs2[1,0].set_title('Gráfico 3: Desvio (multiples corridas)')
axs2[1,0].set_xlabel('Tiradas')
axs2[1,0].set_ylabel('Valor del desvío')

# Grafica de la varianza
num = 0
for x in corridas:
    num =+ 1
    desvAcum = desvio_estandar_acumulado(np.array(x))
    varAcum = varianza_acumulada(desvAcum)
    axs2[1,1].plot(varAcum, linestyle='-')
axs2[1,1].axhline(varianza, color='blue', linestyle='--', label = "Valor de la varianza esperada") 
axs2[1,1].set_title('Gráfico 4: Varianza (multiples corridas)')
axs2[1,1].set_xlabel('Tiradas')
axs2[1,1].set_ylabel('Varianza')

# Guardando las graficas
fig1.tight_layout()
fig1.savefig('GraficasSingulares.png')
fig1.show()

fig2.tight_layout()
fig2.savefig('GraficasMultiples.png')
fig2.show()