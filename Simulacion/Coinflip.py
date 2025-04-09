import random
import sys

def Coinflip():
    return "Cara" if random.random() <= 0.5 else "Cruz"

valores = []

print("Ingrese el numero de veces que quiere tirar la moneda: ")
n = int(input())

for i in range(n):
    valores.append(Coinflip())

contCara = 0
contCruz = 0

for x in valores:
    if x == "Cara":
        contCara += 1
    else:
        contCruz += 1

print("\nCantidad de cruces: ", contCruz)
print("\nCantidad de caras: ", contCara)