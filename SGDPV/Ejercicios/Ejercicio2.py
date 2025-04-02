# Ejercicio For
# En este ejerciicio se le facilitará un numero aleatorio que no conoces en la variable numero.
# Utilizando lo que conoces sobre los bucles for y la funcion range() debes realizar un sumatorio de todos los numeros desde 0 hasta 
# ese numero (incluido) exceptuando los multiplos de 5 y 7, y almacenarlo en la variable sumatorio.


numero = int(input())

listado = range(0, numero)

suma = 0

for i in listado:
    if ((i % 5) != 0) and ((i % 7) != 0):
        suma += i

print(suma)