import cv2
import time
import mediapipe as mp

# Inicialización de MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Coordenadas del ROI de foto
x1, y1 = 80, 80
x2, y2 = 250, 250

# Coordenadas del ROI de video
x3, y3 = 300, 80
x4, y4 = 480, 250

photo_taken = False
mano_dentro_roi_video = False
grabando = False
salida = None

cap = cv2.VideoCapture(0)
pTime = 0

with mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as hands:

    while True:
        success, img = cap.read()
        if not success:
            print("No se pudo acceder a la cámara")
            break

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        h, w, _ = img.shape

        if results.multi_hand_landmarks:
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                mp_drawing.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Coordenadas de la muñeca (landmark 0)
                wrist = hand_landmarks.landmark[0]
                cx, cy = int(wrist.x * w), int(wrist.y * h)

                # Mano 0: foto
                if i == 0:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
                    if x1 < cx < x2 and y1 < cy < y2:
                        if not photo_taken:
                            filename = f"foto_{int(time.time())}.png"
                            cv2.imwrite(filename, img)
                            print(f"Foto tomada: {filename}")
                            photo_taken = True
                    else:
                        photo_taken = False

                # Mano 1: video
                elif i == 1:
                    cv2.circle(img, (cx, cy), 5, (255, 255, 255), cv2.FILLED)
                    if x3 < cx < x4 and y3 < cy < y4:
                        if not mano_dentro_roi_video:
                            mano_dentro_roi_video = True
                            if not grabando:
                                salida = cv2.VideoWriter("video.avi", cv2.VideoWriter_fourcc(*"XVID"), 20.0, (img.shape[1], img.shape[0]))
                                grabando = True
                                print("Grabación iniciada")
                            else:
                                grabando = False
                                if salida is not None:
                                    salida.release()
                                    salida = None
                                print("Grabación finalizada")
                    else:
                        mano_dentro_roi_video = False

        if grabando and salida is not None:
            salida.write(img)
            cv2.putText(img, "Grabando...", (x3, y3 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            cv2.putText(img, "No grabando", (x3, y3 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Dibujo las ROI
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.rectangle(img, (x3, y3), (x4, y4), (0, 0, 255), 2)

        # Mostrar FPS
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, str(int(fps)), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Liberar recursos
cap.release()
if salida is not None:
    salida.release()
cv2.destroyAllWindows()
