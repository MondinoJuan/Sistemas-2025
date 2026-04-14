import cv2
import numpy as np

VEHICLE_CLASS_IDS = {6, 7, 14}  # bus, car, motorbike

# ---------------------------
# Utils
# ---------------------------
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

# ---------------------------
# Robust tracker (como tu yendose2)
# ---------------------------
class Track:
    def __init__(self, track_id, bbox):
        self.id = track_id
        self.bbox = bbox
        self.prev_bbox = bbox
        self.prev_c = centroid(bbox)
        self.curr_c = self.prev_c
        self.vx = 0
        self.vy = 0
        self.missed = 0
        self.hits = 1
        self.age = 1
        self.counted = False

    def predict_bbox(self):
        x1, y1, x2, y2 = self.bbox
        return (x1 + self.vx, y1 + self.vy, x2 + self.vx, y2 + self.vy)

    def update(self, bbox):
        self.prev_bbox = self.bbox
        self.age += 1
        self.missed = 0
        self.hits += 1
        self.prev_c = self.curr_c
        self.curr_c = centroid(bbox)
        self.vx = int(self.curr_c[0] - self.prev_c[0])
        self.vy = int(self.curr_c[1] - self.prev_c[1])
        self.bbox = bbox

class RobustTracker:
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

    def update(self, detections):
        # sumar missed (se resetea al matchear)
        for tr in self.tracks.values():
            tr.missed += 1
            tr.age += 1

        track_ids = list(self.tracks.keys())
        if len(track_ids) == 0:
            for d in detections:
                self.tracks[self.next_id] = Track(self.next_id, d)
                self.next_id += 1
            return list(self.tracks.values())

        scores = np.full((len(track_ids), len(detections)), -1.0, dtype=np.float32)

        for r, tid in enumerate(track_ids):
            tr = self.tracks[tid]
            pb = tr.predict_bbox()
            pcx, pcy = centroid(pb)
            for c, det in enumerate(detections):
                dcx, dcy = centroid(det)
                dist = abs(dcx - pcx) + abs(dcy - pcy)
                if dist > self.max_center_dist:
                    continue

                iv = iou(tr.bbox, det)
                if iv < self.iou_match_thresh:
                    continue

                dist_score = 1.0 - min(1.0, dist / float(self.max_center_dist))
                scores[r, c] = self.alpha_iou * iv + (1.0 - self.alpha_iou) * dist_score

        matched_tracks = set()
        matched_dets = set()

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

        # borrar viejos
        to_delete = [tid for tid, tr in self.tracks.items() if tr.missed > self.max_missed]
        for tid in to_delete:
            del self.tracks[tid]

        # nuevos
        for di, det in enumerate(detections):
            if di not in matched_dets:
                self.tracks[self.next_id] = Track(self.next_id, det)
                self.next_id += 1

        return list(self.tracks.values())

    def is_confirmed(self, tr: Track) -> bool:
        return tr.hits >= self.min_hits

# ---------------------------
# Detección en ROI “banda” (zoom local alrededor de la línea)
# ---------------------------
def detect_in_band(net, frame, x1_roi, x2_roi, line_y, band, conf_th, min_area_near, min_area_far):
    """
    Retorna boxes en coordenadas del frame completo (x1,y1,x2,y2) + scores
    ROI: [x1_roi:x2_roi] y banda vertical alrededor de line_y.
    """
    h, w = frame.shape[:2]
    y_off = max(0, line_y - band)
    y_fin = min(h, line_y + band)

    roi = frame[y_off:y_fin, x1_roi:x2_roi]
    roi_h, roi_w = roi.shape[:2]
    if roi_h < 5 or roi_w < 5:
        return [], [], (x1_roi, y_off, x2_roi, y_fin)

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

    for i in range(detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence < conf_th:
            continue

        class_id = int(detections[0, 0, i, 1])
        if class_id not in VEHICLE_CLASS_IDS:
            continue

        rx1 = int(detections[0, 0, i, 3] * 300)
        ry1 = int(detections[0, 0, i, 4] * 300)
        rx2 = int(detections[0, 0, i, 5] * 300)
        ry2 = int(detections[0, 0, i, 6] * 300)

        rx1 = int(widthFactor * rx1)
        ry1 = int(heightFactor * ry1)
        rx2 = int(widthFactor * rx2)
        ry2 = int(heightFactor * ry2)

        b = clamp_bbox((rx1, ry1, rx2, ry2), roi_w, roi_h)
        if b is None:
            continue

        # área adaptativa: más exigente “cerca” (abajo), más permisiva “lejos” (arriba)
        box_area = (b[2] - b[0]) * (b[3] - b[1])
        # b[3] es y2 dentro de la banda; lo convertimos a coords del frame con y_off
        y2_full = b[3] + y_off
        min_area = min_area_near if (y2_full > line_y) else min_area_far
        if box_area < min_area:
            continue

        # pasar a coords del frame
        b_full = (b[0] + x1_roi, b[1] + y_off, b[2] + x1_roi, b[3] + y_off)
        raw_boxes.append(b_full)
        raw_scores.append(confidence)

    boxes, scores = nms_boxes(raw_boxes, raw_scores, iou_thresh=0.40)
    return boxes, scores, (x1_roi, y_off, x2_roi, y_fin)

# ---------------------------
# Conteo por “toca la línea” + dirección
# ---------------------------
def count_if_touches_line(tr, line_y, direction):
    """
    direction:
      +1 => viniendo (arriba->abajo): requiere delta_y > 0
      -1 => yendose  (abajo->arriba): requiere delta_y < 0
    """
    py1, py2 = tr.prev_bbox[1], tr.prev_bbox[3]
    y1, y2   = tr.bbox[1], tr.bbox[3]

    prev_touch = (py1 <= line_y <= py2)
    curr_touch = (y1  <= line_y <= y2)

    # movimiento vertical del centro
    dy = tr.curr_c[1] - tr.prev_c[1]

    moved_ok = (dy > 0) if direction == +1 else (dy < 0)

    return (not tr.counted) and (not prev_touch) and curr_touch and moved_ok

# ---------------------------
# Main
# ---------------------------
def main():
    cap = cv2.VideoCapture("autopista_video1.mp4")

    net = cv2.dnn.readNetFromCaffe(
        "MobileNetSSD_deploy.prototxt.txt",
        "MobileNetSSD_deploy.caffemodel"
    )

    # Dos trackers separados
    tracker_right = RobustTracker(iou_match_thresh=0.10, max_missed=30, max_center_dist=110, min_hits=3)
    tracker_left  = RobustTracker(iou_match_thresh=0.08, max_missed=45, max_center_dist=120, min_hits=3)

    fuente = cv2.FONT_HERSHEY_SIMPLEX
    count_viniendo = 0
    count_yendose = 0

    # Líneas (podés moverlas)
    # Derecha: viniendo (arriba->abajo)
    LINE_RIGHT = None  # se calcula por frame
    # Izquierda: yéndose (abajo->arriba)
    LINE_LEFT = None   # se calcula por frame

    # Bandas (zoom alrededor de la línea)
    BAND_RIGHT = 140
    BAND_LEFT  = 160

    # Umbrales detección (ajustables)
    CONF_RIGHT = 0.35
    CONF_LEFT  = 0.25

    # Área adaptativa (ajustables)
    # cerca = abajo, lejos = arriba
    MINAREA_RIGHT_NEAR, MINAREA_RIGHT_FAR = 900, 450
    MINAREA_LEFT_NEAR,  MINAREA_LEFT_FAR  = 1100, 450

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        x_mid = w // 2

        # Definir líneas (por si cambia tamaño)
        LINE_RIGHT = int(h / 2) + 100
        LINE_LEFT  = int(h / 2) + 35

        # --- Detectar en banda derecha ---
        boxes_r, scores_r, band_rect_r = detect_in_band(
            net, frame,
            x1_roi=x_mid, x2_roi=w,
            line_y=LINE_RIGHT,
            band=BAND_RIGHT,
            conf_th=CONF_RIGHT,
            min_area_near=MINAREA_RIGHT_NEAR,
            min_area_far=MINAREA_RIGHT_FAR
        )
        tracks_r = tracker_right.update(boxes_r)

        # --- Detectar en banda izquierda ---
        boxes_l, scores_l, band_rect_l = detect_in_band(
            net, frame,
            x1_roi=0, x2_roi=x_mid,
            line_y=LINE_LEFT,
            band=BAND_LEFT,
            conf_th=CONF_LEFT,
            min_area_near=MINAREA_LEFT_NEAR,
            min_area_far=MINAREA_LEFT_FAR
        )
        tracks_l = tracker_left.update(boxes_l)

        # --- Dibujos de ROIs/bandas y líneas ---
        # Mitades
        cv2.line(frame, (x_mid, 0), (x_mid, h - 1), (80, 80, 80), 2)

        # Bandas
        (rx1, ry1, rx2, ry2) = band_rect_r
        (lx1, ly1, lx2, ly2) = band_rect_l
        cv2.rectangle(frame, (rx1, ry1), (rx2 - 1, ry2 - 1), (0, 0, 255), 2)
        cv2.rectangle(frame, (lx1, ly1), (lx2 - 1, ly2 - 1), (0, 0, 255), 2)

        # Líneas SOLO en su mitad
        cv2.line(frame, (x_mid, LINE_RIGHT), (w - 1, LINE_RIGHT), (255, 0, 0), 4)
        cv2.line(frame, (0, LINE_LEFT), (x_mid - 1, LINE_LEFT), (255, 0, 0), 4)

        # --- Procesar tracks derecha (viniendo) ---
        for tr in tracks_r:
            if not tracker_right.is_confirmed(tr):
                # igual dibujamos, pero no contamos
                pass

            x1, y1, x2, y2 = tr.bbox
            cx, cy = tr.curr_c

            # seguridad: que esté en derecha
            if cx < x_mid:
                continue

            # conteo: toca línea + dirección arriba->abajo
            if tracker_right.is_confirmed(tr) and count_if_touches_line(tr, LINE_RIGHT, direction=+1):
                count_viniendo += 1
                tr.counted = True

            # draw
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 255), -1)
            cv2.putText(frame, f"R{tr.id}", (x1, max(20, y1 - 8)), fuente, 0.6, (255, 255, 255), 2)

        # --- Procesar tracks izquierda (yéndose) ---
        for tr in tracks_l:
            x1, y1, x2, y2 = tr.bbox
            cx, cy = tr.curr_c

            # seguridad: que esté en izquierda
            if cx >= x_mid:
                continue

            # conteo: toca línea + dirección abajo->arriba
            if tracker_left.is_confirmed(tr) and count_if_touches_line(tr, LINE_LEFT, direction=-1):
                count_yendose += 1
                tr.counted = True

            # draw
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 200, 0), 2)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 255), -1)
            cv2.putText(frame, f"L{tr.id}", (x1, max(20, y1 - 8)), fuente, 0.6, (255, 255, 255), 2)

        # HUD
        cv2.putText(frame, f"Viniendo (derecha): {count_viniendo}", (20, 45), fuente, 0.9, (255, 255, 0), 2)
        cv2.putText(frame, f"Yendose (izquierda): {count_yendose}", (20, 80), fuente, 0.9, (255, 0, 255), 2)
        cv2.putText(frame, f"Dets R:{len(boxes_r)}  Dets L:{len(boxes_l)}", (20, 115), fuente, 0.7, (0, 255, 255), 2)

        cv2.imshow("Contador 2 sentidos", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Total viniendo (derecha):", count_viniendo)
    print("Total yendose (izquierda):", count_yendose)

if __name__ == "__main__":
    main()
