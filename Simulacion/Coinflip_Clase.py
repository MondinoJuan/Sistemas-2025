import random
import sys
if len(sys.argv) != 3 or sys.argv[1] != "-n":
    print("Uso: python simulación_moneda_v0.06.py -n <num_valores>")
    sys.exit(1)
num_valores = int(sys.argv[2])
valores = [random.randint(0, 1) for _ in range(num_valores)]
frecuencia_absoluta = {0: valores.count(0), 1: valores.count(1)}
frecuencia_relativa = {0: frecuencia_absoluta[0]/num_valores, 1: frecuencia_absoluta [1] / num_valores}
print("Valores generados:", valores)
print("Frecuencia absoluta de 0:", frecuencia_absoluta[0])
print("Frecuencia absoluta de 1:", frecuencia_absoluta[1])
print("Frecuencia relativa de 0:", frecuencia_relativa[0])
print("Frecuencia relativa de 1:", frecuencia_relativa[1])
print()