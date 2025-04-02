# Ejercicio
# Realiza un porgrama que lea un numero por teclado y lo almacene en una variable llamada numero.
# Si ese numero introducido por teclado no es multiplo de 5 debe repetirse de nuevo la lectura hasta que lo

numero = int(input())

while((numero % 5) != 0):
    print("El numero", str(numero), "no es multiplo de 5.")
    numero = int(input())

print("El numero", str(numero), "es multiplo de 5.")





