import cv2
import mediapipe
import time

mpPose = mediapipe.solutions.pose
pose = mpPose.Pose()
mpDraw = mediapipe.solutions.drawing_utils

cap = cv2.VideoCapture(0)
#cap = cv2.VideoCapture(2)
pTime = 0

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

while True:
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = pose.process(imgRGB)
    if results.pose_landmarks:
        mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)
        h, w, c = img.shape

        # Identifico muñecas
        munieca_derecha = 16
        munieca_izquierda = 15
            
        #Para foto
        lm_derecha = results.pose_landmarks.landmark[munieca_derecha]
        cx_derecha, cy_derecha = int(lm_derecha.x * w), int(lm_derecha.y * h)
        cv2.circle(img, (cx_derecha, cy_derecha), 5, (255, 0, 0), cv2.FILLED)
        
        # Verifico si la muñeca está dentro del ROI de foto
        if x1 < cx_derecha < x2 and y1 < cy_derecha < y2:
            if not photo_taken:
                filename = f"foto_{int(time.time())}.png"
                cv2.imwrite(filename, img)
                print(f"Foto tomada: {filename}")
                photo_taken = True
        else:
            photo_taken = False
            
        # Para video
        lm_izquierda = results.pose_landmarks.landmark[munieca_izquierda]
        cx_izquierda, cy_izquierda = int(lm_izquierda.x * w), int(lm_izquierda.y * h)
        cv2.circle(img, (cx_izquierda, cy_izquierda), 5, (255, 255, 255), cv2.FILLED)

        # Verifico si la muñeca está dentro del ROI de video
        if x3 < cx_izquierda < x4 and y3 < cy_izquierda < y4:
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

        if grabando:
            cv2.putText(img, "Grabando...", (x3, y3 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            if salida is not None:
                salida.write(img)
        else:
            cv2.putText(img, "No grabando", (x3, y3 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    # Dibujo la Region Of Interest (ROI) Foto
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Dibujo la Region Of Interest (ROI) Video
    cv2.rectangle(img, (x3, y3), (x4, y4), (0, 0, 255), 2)

    cv2.putText(img, str(int(fps)), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)
    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
