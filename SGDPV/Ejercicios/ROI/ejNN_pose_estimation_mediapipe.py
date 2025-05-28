import cv2
import mediapipe
import time
import os

mpPose = mediapipe.solutions.pose
pose = mpPose.Pose()
mpDraw = mediapipe.solutions.drawing_utils

cap = cv2.VideoCapture(0)
pTime = 0

# Coordenadas del ROI de foto
x1, y1 = 80, 80
x2, y2 = 250, 250

# Coordenadas del ROI de video
x3, y3 = 300, 80
x4, y4 = 480, 250

photo_taken = False  # Para evitar tomar muchas fotos seguidas

while True:
	success, img = cap.read()
	imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	results = pose.process(imgRGB)
	if results.pose_landmarks:
		mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)
		h, w, c = img.shape
		for wrist_id in [15, 16]:
			lm = results.pose_landmarks.landmark[wrist_id]
			cx, cy = int(lm.x * w), int(lm.y * h)
			cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
			if x1 < cx < x2 and y1 < cy < y2:
				if not photo_taken:
					filename = f"foto_{int(time.time())}.png"
					cv2.imwrite(filename, img)
					print(f"Foto tomada: {filename}")
					photo_taken = True
				break
			else:
				photo_taken = False

			# Variable para controlar el estado de grabación
			if 'grabando' not in locals():
				grabando = False
				salida = None

			if x3 < cx < x4 and y3 < cy < y4:
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
			elif grabando and salida is not None:
				salida.write(img)




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
