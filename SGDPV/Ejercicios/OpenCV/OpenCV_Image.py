import cv2
import datetime

cap = cv2.VideoCapture(0)
cont = 0

while True:
    _, frame = cap.read()

    cv2.imshow("RGB", frame)

    if cv2.waitKey(1) & 0xFF == ord('s'):
        print("Guardando imagen...")

        # Texto
        hora_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Hora de captura: {hora_actual}")
        posicion = (50, 50)
        fuente = cv2.FONT_HERSHEY_SIMPLEX
        escala_fuente = 1
        color_texto = (255, 255, 255)
        grosor_texto = 2
        cv2.putText(frame, hora_actual, posicion, fuente, escala_fuente, color_texto, grosor_texto)

        cv2.imwrite(f"captura_{cont}.png", frame)
        cont += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()