import random
import numpy as np
import matplotlib.pyplot as plt
import math

from typing import List

## RULETA

rango = list(range(37))

def armoArreglo(n: int):
    arreglo = []

    for i in range(n):
        arreglo.append(random.choice(rango))
    
    return arreglo

def vpRespectoN(array):
    suma = 0
    devuelvo = []
    for i, val in enumerate(array):
        suma += val
        devuelvo.append(suma / (i + 1))
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


## INICIO

print("Ingrese la cantidad de tiradas que se realizarán: ")
n = int(input())

print("Ingrese el número objetivo: ")
no = int(input())

while type(n) != int:
    print("Ingrese un numero entero :")
    n = int(input())


data = np.array(armoArreglo(n))

rango = np.array(rango)

media = rango.mean()
vpU_Arreglo = vpRespectoN(data)

desvio = rango.std()
desvAcum = desvio_estandar_acumulado(data)

varianza = rango.var()
varAcum = varianza_acumulada(desvAcum)

fe = 1 / len(rango)
conteos = np.cumsum(data == no)
no_fr = conteos / np.arange(1, n + 1)

print(f"El listado de numeros que salió es: {data}")
print(f"Media: {media}, Desvío estándar: {desvio}, Varianza: {varianza}")

fig, axs = plt.subplots(1, 4, figsize=(18, 6))

axs[0].plot(no_fr, color='red', linestyle='-', label = f'Frecuencia relativa de {no}') 
axs[0].axhline(fe, color='blue', linestyle='--', label = 'Frecuencia relativa esperada')
axs[0].set_title('Gráfico 1: FR y FE de NO')
axs[0].set_xlabel('Tiradas')
axs[0].set_ylabel('Frecuencia')

axs[1].plot(vpU_Arreglo, color='red', linestyle='-', label = "Valor promedio de las tiradas con respecto a n")
axs[1].axhline(media, color='blue', linestyle='--', label = "Valor promedio esperado")
axs[1].set_title('Gráfico 2: Media')
axs[1].set_xlabel('Tiradas')
axs[1].set_ylabel('Valor promedio')

axs[2].plot(desvAcum, color='red', linestyle='-', label = f"Valor del desvío de {no} en {n} tiradas")
axs[2].axhline(desvio, color='blue', linestyle='--', label = "Valor del desvio esperado")
axs[2].set_title('Gráfico 3: Desvio')
axs[2].set_xlabel('Tiradas')
axs[2].set_ylabel('Valor del desvío')

axs[3].plot(varAcum, color='red', linestyle='-', label = f"Valor de la varianza del número X con respecto a n")
axs[3].axhline(varianza, color='blue', linestyle='--', label = "Valor de la varianza esperada") 
axs[3].set_title('Gráfico 4: Varianza')
axs[3].set_xlabel('Tiradas')
axs[3].set_ylabel('Varianza')

plt.tight_layout()
plt.savefig('TP N°1/Graficas.png')
plt.show()
