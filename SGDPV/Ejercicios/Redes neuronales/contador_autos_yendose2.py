import cv2
import numpy as np

VEHICLE_CLASS_IDS = {6, 7, 14}  # bus, car, motorbike

def iou(b1, b2):
    xA = max(b1[0], b2[0]); yA = max(b1[1], b2[1])
    xB = min(b1[2], b2[2]); yB = min(b1[3], b2[3])
    interW = max(0, xB - xA); interH = max(0, yB - yA)
    inter = interW * interH
    if inter <= 0:
        return 0.0
    area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    return inter / float(area1 + area2 - inter + 1e-6)

def centroid(b):
    return ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)

def nms_boxes(boxes, scores, iou_thresh=0.4):
    if not boxes:
        return [], []
    b = np.array(boxes, dtype=np.float32)
    s = np.array(scores, dtype=np.float32)

    x1, y1, x2, y2 = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = s.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = int(order[0])
        keep.append(i)

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)

        inds = np.where(ovr <= iou_thresh)[0]
        order = order[inds + 1]

    return [boxes[k] for k in keep], [scores[k] for k in keep]

def clamp_bbox(b, w, h):
    x1, y1, x2, y2 = b
    x1 = max(0, min(w - 1, x1))
    x2 = max(0, min(w - 1, x2))
    y1 = max(0, min(h - 1, y1))
    y2 = max(0, min(h - 1, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1, y1, x2, y2)

class Track:
    def __init__(self, track_id, bbox):
        self.id = track_id
        self.bbox = bbox
        self.prev_bbox = bbox   # <-- NUEVO
        self.prev_c = centroid(bbox)
        self.curr_c = self.prev_c
        self.vx = 0
        self.vy = 0
        self.missed = 0
        self.hits = 1
        self.age = 1
        self.counted = False

    def predict_bbox(self):
        # desplaza bbox según velocidad estimada
        x1, y1, x2, y2 = self.bbox
        return (x1 + self.vx, y1 + self.vy, x2 + self.vx, y2 + self.vy)

    def update(self, bbox):
        self.prev_bbox = self.bbox  # <-- NUEVO (guardar el anterior)
        self.age += 1
        self.missed = 0
        self.hits += 1
        self.prev_c = self.curr_c
        self.curr_c = centroid(bbox)
        self.vx = int(self.curr_c[0] - self.prev_c[0])
        self.vy = int(self.curr_c[1] - self.prev_c[1])
        self.bbox = bbox

class RobustTracker:
    """
    Matching robusto:
    - Gating por distancia (centro)
    - Score combinado (IoU + cercanía al centro predicho)
    - Tracks confirmados (min_hits) para contar / reducir ruido
    """
    def __init__(
        self,
        iou_match_thresh=0.08,
        max_missed=45,
        max_center_dist=120,
        alpha_iou=0.65,
        min_hits=3,
    ):
        self.iou_match_thresh = iou_match_thresh
        self.max_missed = max_missed
        self.max_center_dist = max_center_dist
        self.alpha_iou = alpha_iou
        self.min_hits = min_hits

        self.tracks = {}
        self.next_id = 1

    def update(self, detections, frame_w, frame_h):
        # 1) incrementar missed a todos; luego lo resetean los matcheados
        for tr in self.tracks.values():
            tr.missed += 1
            tr.age += 1

        track_ids = list(self.tracks.keys())
        if len(track_ids) == 0:
            for d in detections:
                self.tracks[self.next_id] = Track(self.next_id, d)
                self.next_id += 1
            return list(self.tracks.values())

        # 2) armar matriz de scores
        scores = np.full((len(track_ids), len(detections)), -1.0, dtype=np.float32)

        for r, tid in enumerate(track_ids):
            tr = self.tracks[tid]
            pb = tr.predict_bbox()
            pcx, pcy = centroid(pb)
            for c, det in enumerate(detections):
                dcx, dcy = centroid(det)
                dist = abs(dcx - pcx) + abs(dcy - pcy)  # L1 (rápida y estable)

                if dist > self.max_center_dist:
                    continue

                iv = iou(tr.bbox, det)
                if iv < self.iou_match_thresh:
                    continue

                # normalizar distancia a [0..1] y combinar
                dist_score = 1.0 - min(1.0, dist / float(self.max_center_dist))
                scores[r, c] = self.alpha_iou * iv + (1.0 - self.alpha_iou) * dist_score

        matched_tracks = set()
        matched_dets = set()

        # 3) asignación greedy por mejor score
        while True:
            if scores.size == 0:
                break
            r, c = np.unravel_index(int(np.argmax(scores)), scores.shape)
            best = float(scores[r, c])
            if best < 0:
                break

            tid = track_ids[r]
            self.tracks[tid].update(detections[c])
            matched_tracks.add(tid)
            matched_dets.add(c)

            scores[r, :] = -1
            scores[:, c] = -1

        # 4) borrar tracks viejos
        to_delete = [tid for tid, tr in self.tracks.items() if tr.missed > self.max_missed]
        for tid in to_delete:
            del self.tracks[tid]

        # 5) crear tracks nuevos para detecciones no matcheadas
        for di, det in enumerate(detections):
            if di not in matched_dets:
                self.tracks[self.next_id] = Track(self.next_id, det)
                self.next_id += 1

        return list(self.tracks.values())

    def is_confirmed(self, tr: Track) -> bool:
        return tr.hits >= self.min_hits

def main():
    cap = cv2.VideoCapture("autopista_video1.mp4")

    net = cv2.dnn.readNetFromCaffe(
        "MobileNetSSD_deploy.prototxt.txt",
        "MobileNetSSD_deploy.caffemodel"
    )

    # Parámetros robustos para “alejándose”
    tracker = RobustTracker(
        iou_match_thresh=0.08,
        max_missed=45,
        max_center_dist=120,
        alpha_iou=0.65,
        min_hits=3
    )

    total_count = 0
    fuente = cv2.FONT_HERSHEY_SIMPLEX
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1

        altura, ancho = frame.shape[:2]
        x0 = ancho // 2

        # ROI base: mitad izquierda
        x0 = ancho // 2

        # Línea de conteo dentro del ROI
        posicionY_linea = int(altura / 2) + 35
        cv2.line(frame, (0, posicionY_linea), (x0 - 1, posicionY_linea), (255, 0, 0), 4)

        # -------- NUEVO: banda vertical alrededor de la línea --------
        BANDA = 160  # probá 120..220 según el video
        y_off = max(0, posicionY_linea - BANDA)
        y_fin = min(altura, posicionY_linea + BANDA)

        roi = frame[y_off:y_fin, 0:x0]   # izquierda + banda
        roi_h, roi_w = roi.shape[:2]

        # (opcional) dibujar la banda para verla
        cv2.rectangle(frame, (0, y_off), (x0 - 1, y_fin - 1), (0, 0, 255), 2)

        # DNN sobre ROI banda
        roi_resized = cv2.resize(roi, (300, 300))
        blob = cv2.dnn.blobFromImage(
            roi_resized, 0.007843, (300, 300),
            (127.5, 127.5, 127.5), swapRB=False
        )
        net.setInput(blob)
        detections = net.forward()

        heightFactor = roi_h / 300.0
        widthFactor  = roi_w / 300.0

        raw_boxes = []
        raw_scores = []

        # Filtro por área (evita cajitas que disparan IDs)
        # Podés ajustar: 700–1400 según tu video
        MIN_AREA = 600

        for i in range(detections.shape[2]):
            confidence = float(detections[0, 0, i, 2])
            if confidence < 0.25:
                continue

            class_id = int(detections[0, 0, i, 1])
            if class_id not in VEHICLE_CLASS_IDS:
                continue

            x1 = int(detections[0, 0, i, 3] * 300)
            y1 = int(detections[0, 0, i, 4] * 300)
            x2 = int(detections[0, 0, i, 5] * 300)
            y2 = int(detections[0, 0, i, 6] * 300)

            x1 = int(widthFactor * x1)
            y1 = int(heightFactor * y1)
            x2 = int(widthFactor * x2)
            y2 = int(heightFactor * y2)

            b = clamp_bbox((x1, y1, x2, y2), roi_w, roi_h)
            if b is None:
                continue

            box_area = (b[2] - b[0]) * (b[3] - b[1])

            # abajo (más cerca): exigimos cajas más grandes
            # arriba (más lejos): permitimos cajas más chicas
            min_area = 1100 if b[3] > posicionY_linea else 450  # usa y2 del bbox (= b[3])

            if box_area < min_area:
                continue

            # b está en coords de la ROI banda (0..roi_h)
            # pasarlo a coords del frame completo sumando offsets
            b_full = (b[0], b[1] + y_off, b[2], b[3] + y_off)
            raw_boxes.append(b_full)
            raw_scores.append(confidence)

        boxes, scores = nms_boxes(raw_boxes, raw_scores, iou_thresh=0.40)

        cv2.putText(frame, f"Dets: {len(boxes)}", (30, 115), fuente, 0.7, (255,255,255), 2)

        # update tracker (coordenadas ya están en ROI, y dibujamos en el frame en las mismas coords
        tracks = tracker.update(boxes, frame_w=x0, frame_h=altura)

        for tr in tracks:
            x1, y1, x2, y2 = tr.bbox
            cx, cy = tr.curr_c
            px, py = tr.prev_c

            # dibujar
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 255), -1)
            cv2.putText(frame, f"ID {tr.id}", (x1, max(20, y1 - 8)), fuente, 0.6, (255, 255, 255), 2)

            # Conteo cuando la línea intersecta el rectángulo (antes NO, ahora SÍ)
            py1, py2 = tr.prev_bbox[1], tr.prev_bbox[3]
            y1, y2   = tr.bbox[1], tr.bbox[3]

            prev_toca = (py1 <= posicionY_linea <= py2)
            curr_toca = (y1  <= posicionY_linea <= y2)

            if (not tr.counted) and tracker.is_confirmed(tr) and (not prev_toca) and curr_toca:
                total_count += 1
                tr.counted = True

        cv2.putText(frame, f"Autos: {total_count}", (30, 50), fuente, 1.0, (255, 255, 0), 2)
        cv2.putText(frame, f"Tracks activos: {len(tracks)}  NextID: {tracker.next_id}", (30, 85), fuente, 0.7, (255, 255, 255), 2)

        cv2.imshow("Contador de autos (ROI izquierda, robusto)", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Total contado:", total_count)

if __name__ == "__main__":
    main()
