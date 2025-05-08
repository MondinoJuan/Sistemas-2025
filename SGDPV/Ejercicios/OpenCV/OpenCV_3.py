import cv2
import numpy as np

cap = cv2.VideoCapture(0)

while True:
    _, rgb = cap.read()
    escala_grises = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
    _, binara = cv2.threshold(escala_grises, 90, 255, cv2.THRESH_BINARY_INV)

    # Marco
    altura, ancho, _ = rgb.shape
    verde = (0, 255, 0)
    rojo = (0, 0, 255)
    azul = (255, 0, 0)
    grosor = 10
    cv2.rectangle(rgb, (0, 0), (ancho, altura), verde, grosor)
    cv2.line(rgb, (200, 200), (300, 200), azul, grosor)           # el primer par es el punto de inicio y el segundo el de fin
    cv2.circle(rgb, (120, 120), (60), rojo, grosor)

    # Texto
    texto = "Video en vivo"
    posicion = (50, 50)
    fuente = cv2.FONT_HERSHEY_SIMPLEX
    escala_fuente = 1
    color_texto = (255, 255, 255)
    grosor_texto = 2
    cv2.putText(rgb, texto, posicion, fuente, escala_fuente, color_texto, grosor_texto)

    cv2.imshow("RGB", rgb)
    #cv2.imshow("Escala de grises", escala_grises)
    #cv2.imshow("Binaria", binara)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()