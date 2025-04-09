import random
import matplotlib.pyplot as plt

x1 = list(range(1000))
y1 = [random.random() for _ in x1]
x2 = list(range(1000))
y2 = [random.random() for _ in x2]
y_avg = [(y1[i] + y2[i]/2) for i in range(1000)]
fig, axs = plt.subplots(1, 3, figsize=(18, 6))

axs[0].plot(x1, y1, color='blue')
axs[0].set_title('Gráfico 1: Valores Aleatorios')
axs[0].set_xlabel('Indice')
axs[0].set_ylabel('Valor Aleatorio')

axs[1].plot(x2, y2, color='red')
axs[1].set_title('Gráfico 2: Valores Aleatorios')
axs[1].set_xlabel('Índice')
axs[1].set_ylabel('Valor Aleatorio')

axs[2].plot(x1, y_avg, color='green', linewidth=3, linestyle='--') 
axs[2].set_title('Gráfico 3: Promedio de los dos primeros')
axs[2].set_xlabel('Índice')
axs[2].set_ylabel('Valor Promedio')

plt.tight_layout()
plt.savefig('tres_graficas_valores_aleatorios.png')
plt.show()