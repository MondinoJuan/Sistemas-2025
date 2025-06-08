import cv2
import numpy as np

# Diccionario ArUco
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(dictionary, parameters)

# Inicializar cámara
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Calibración de cámara (suponiendo valores aproximados)
camera_matrix = np.array([[800, 0, 640], [0, 800, 360], [0, 0, 1]], dtype=np.float32)
dist_coeffs = np.zeros((5, 1))  # Sin distorsión

marker_length = 0.05  # Tamaño del marcador en metros

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(gray)

    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        for corner in corners:
            # Puntos de la imagen (2D)
            img_points = corner[0].astype(np.float32)

            # Puntos del objeto (3D) en el mundo real (en el plano XY)
            obj_points = np.array(
                [
                    [0, 0, 0],
                    [marker_length, 0, 0],
                    [marker_length, marker_length, 0],
                    [0, marker_length, 0],
                ],
                dtype=np.float32,
            )

            # Resolver pose
            retval, rvec, tvec = cv2.solvePnP(
                obj_points, img_points, camera_matrix, dist_coeffs
            )

            if retval:
                # Dibujar ejes
                ##cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, rvec, tvec, 0.03)

                # Dibujar cubo
                cube_points = np.float32(
                    [
                        [0, 0, 0],
                        [0, marker_length, 0],
                        [marker_length, marker_length, 0],
                        [marker_length, 0, 0],
                        [0, 0, -marker_length],
                        [0, marker_length, -marker_length],
                        [marker_length, marker_length, -marker_length],
                        [marker_length, 0, -marker_length],
                    ]
                )
                imgpts, _ = cv2.projectPoints(
                    cube_points, rvec, tvec, camera_matrix, dist_coeffs
                )
                imgpts = np.int32(imgpts).reshape(-1, 2)

                # Dibujar caras del cubo
                frame = cv2.drawContours(frame, [imgpts[:4]], -1, (0, 255, 0), -1)
                for i in range(4):
                    frame = cv2.line(
                        frame, tuple(imgpts[i]), tuple(imgpts[i + 4]), (255, 0, 0), 2
                    )
                frame = cv2.drawContours(frame, [imgpts[4:]], -1, (0, 0, 255), 2)

    cv2.imshow("Realidad Aumentada - Cubo 3D", frame)
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
