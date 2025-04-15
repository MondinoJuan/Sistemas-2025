import random


class Tupla:
    id:int
    binario:list
    decimal:int
    fit:float

    def __init__(self, id:int, poblacion:list):
        self.id = id
        self.binario = completoCromosoma()
        self.decimal = binario_A_Decimal(self.binario)
        self.fit = fitness(self.decimal, poblacion)

def aleatorio():
    return random.randint(0, 1)

def completoCromosoma(cantidad):
    cromosoma = [aleatorio() for _ in range(cantidad)] # Genera un cromosoma de ... genes aleatorios
    return cromosoma

def fitness(decimal, poblacion):
    total = 0
    for i in range(len(poblacion)):
        total += funcionObjetivo(poblacion[i])

    return decimal / total

def funcionObjetivo(x):
    return (x * x) - 1 
    

def seleccionRandom(poblacion):
    padre1 = random.choice(poblacion)

    posible_padre2 = random.choice(poblacion)
    while padre1 == posible_padre2:
        posible_padre2 = random.choice(poblacion)

    padre2 = posible_padre2

    return padre1, padre2

def binario_A_Decimal(cromosoma):
    decimal = 0
    for i in range(len(cromosoma)):
        decimal += cromosoma[i] * (2 ** (len(cromosoma) - 1 - i))





# Programa
# No usar macros ni librerias ni nada para el metodo de selección de padres.

poblacion = []
cantidad = 10
cantGenes = 30
arregloFitness = []

# Generar la poblacion inicial
for i in range(cantidad):
    cromosoma = completoCromosoma(cantGenes)
    poblacion.append(cromosoma)

# Calculo el fitness de un cromosoma
for i in range(cantidad):
    cromosoma = poblacion[i]
    print(f"Cromosoma {i}: {cromosoma} -> Fitness: {fitness(funcionObjetivo(cromosoma), poblacion)}")
    arregloFitness.append(fitness(funcionObjetivo(cromosoma), poblacion))
