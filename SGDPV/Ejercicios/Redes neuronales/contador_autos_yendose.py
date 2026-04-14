import cv2
import numpy as np

# ---------------------------
# Config / clases del modelo
# ---------------------------
classNames = {
    0: 'background',
    1: 'aeroplane', 2: 'bicycle', 3: 'bird', 4: 'boat',
    5: 'bottle', 6: 'bus', 7: 'car', 8: 'cat', 9: 'chair',
    10: 'cow', 11: 'diningtable', 12: 'dog', 13: 'horse',
    14: 'motorbike', 15: 'person', 16: 'pottedplant',
    17: 'sheep', 18: 'sofa', 19: 'train', 20: 'tvmonitor'
}

VEHICLE_CLASS_IDS = {6, 7, 14}  # bus, car, motorbike

def iou(b1, b2):
    xA = max(b1[0], b2[0])
    yA = max(b1[1], b2[1])
    xB = min(b1[2], b2[2])
    yB = min(b1[3], b2[3])
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    inter = interW * interH
    if inter == 0:
        return 0.0
    area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    return inter / float(area1 + area2 - inter + 1e-6)

def centroid(b):
    return ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)

def nms_boxes(boxes, scores, iou_thresh=0.4):
    if not boxes:
        return [], []

    boxes_np = np.array(boxes, dtype=np.float32)
    scores_np = np.array(scores, dtype=np.float32)

    x1 = boxes_np[:, 0]
    y1 = boxes_np[:, 1]
    x2 = boxes_np[:, 2]
    y2 = boxes_np[:, 3]
    areas = (x2 - x1) * (y2 - y1)

    order = scores_np.argsort()[::-1]
    keep = []

    while order.size > 0:
        i = order[0]
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

    kept_boxes = [boxes[k] for k in keep]
    kept_scores = [scores[k] for k in keep]
    return kept_boxes, kept_scores

class Track:
    def __init__(self, track_id, bbox):
        self.id = track_id
        self.bbox = bbox
        self.missed = 0
        self.prev_c = centroid(bbox)
        self.curr_c = centroid(bbox)
        self.counted = False

    def update(self, bbox):
        self.bbox = bbox
        self.missed = 0
        self.prev_c = self.curr_c
        self.curr_c = centroid(bbox)

class IoUTracker:
    def __init__(self, iou_match_thresh=0.15, max_missed=25):
        self.iou_match_thresh = iou_match_thresh
        self.max_missed = max_missed
        self.tracks = {}
        self.next_id = 1

    def update(self, detections):
        if len(self.tracks) == 0:
            for d in detections:
                self.tracks[self.next_id] = Track(self.next_id, d)
                self.next_id += 1
            return list(self.tracks.values())

        track_ids = list(self.tracks.keys())
        track_boxes = [self.tracks[tid].bbox for tid in track_ids]

        iou_mat = np.zeros((len(track_boxes), len(detections)), dtype=np.float32)
        for r, tb in enumerate(track_boxes):
            for c, db in enumerate(detections):
                iou_mat[r, c] = iou(tb, db)

        matched_tracks = set()
        matched_dets = set()

        while True:
            if iou_mat.size == 0:
                break
            r, c = np.unravel_index(np.argmax(iou_mat), iou_mat.shape)
            best = iou_mat[r, c]
            if best < self.iou_match_thresh:
                break

            tid = track_ids[r]
            self.tracks[tid].update(detections[c])
            matched_tracks.add(tid)
            matched_dets.add(c)

            iou_mat[r, :] = -1
            iou_mat[:, c] = -1

        for tid in track_ids:
            if tid not in matched_tracks:
                self.tracks[tid].missed += 1

        to_delete = [tid for tid, tr in self.tracks.items() if tr.missed > self.max_missed]
        for tid in to_delete:
            del self.tracks[tid]

        for di, d in enumerate(detections):
            if di not in matched_dets:
                self.tracks[self.next_id] = Track(self.next_id, d)
                self.next_id += 1

        return list(self.tracks.values())

def main():
    cap = cv2.VideoCapture("autopista_video1.mp4")

    net = cv2.dnn.readNetFromCaffe(
        "MobileNetSSD_deploy.prototxt.txt",
        "MobileNetSSD_deploy.caffemodel"
    )

    tracker = IoUTracker(iou_match_thresh=0.25, max_missed=12)
    total_count = 0
    fuente = cv2.FONT_HERSHEY_SIMPLEX

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        altura, ancho = frame.shape[:2]

        # ---------------------------
        # ROI: mitad IZQUIERDA
        # ---------------------------
        x0 = ancho // 2
        roi = frame[:, 0:x0]  # solo izquierda
        roi_h, roi_w = roi.shape[:2]

        # (opcional) dibujar el ROI en rojo para verlo
        cv2.rectangle(frame, (0, 0), (x0 - 1, altura - 1), (0, 0, 255), 2)

        # línea de conteo (solo dentro del ROI)
        posicionY_linea = int(altura / 2) + 35

        # ---------------------------
        # DNN sobre ROI (no sobre el frame completo)
        # ---------------------------
        roi_resized = cv2.resize(roi, (300, 300))
        blob = cv2.dnn.blobFromImage(
            roi_resized, 0.007843, (300, 300),
            (127.5, 127.5, 127.5), swapRB=False
        )
        net.setInput(blob)
        detections = net.forward()

        # factores respecto al ROI
        heightFactor = roi_h / 300.0
        widthFactor = roi_w / 300.0

        raw_boxes = []
        raw_scores = []

        for i in range(detections.shape[2]):
            confidence = float(detections[0, 0, i, 2])
            if confidence < 0.35:
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

            x1 = max(0, min(roi_w - 1, x1))
            x2 = max(0, min(roi_w - 1, x2))
            y1 = max(0, min(roi_h - 1, y1))
            y2 = max(0, min(roi_h - 1, y2))
            if x2 <= x1 or y2 <= y1:
                continue

            # OJO: en ROI izquierda NO hay offset en X (x0 no se suma)
            raw_boxes.append((x1, y1, x2, y2))
            raw_scores.append(confidence)

        boxes, scores = nms_boxes(raw_boxes, raw_scores, iou_thresh=0.4)
        tracks = tracker.update(boxes)

        # dibujar línea SOLO en ROI (izquierda)
        cv2.line(frame, (0, posicionY_linea), (x0 - 1, posicionY_linea), (255, 0, 0), 4)

        for tr in tracks:
            x1, y1, x2, y2 = tr.bbox
            cx, cy = tr.curr_c
            px, py = tr.prev_c

            # autos en mitad izquierda y "alejándose": cruce de ABAJO->ARRIBA
            if (not tr.counted) and (cx < x0) and (py > posicionY_linea >= cy):
                total_count += 1
                tr.counted = True

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 255), -1)
            cv2.putText(frame, f"ID {tr.id}", (x1, max(20, y1 - 8)), fuente, 0.6, (255, 255, 255), 2)

        cv2.putText(frame, f"Autos: {total_count}", (30, 50), fuente, 1.0, (255, 255, 0), 2)

        cv2.imshow("Contador de autos (ROI izquierda)", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Total contado:", total_count)

if __name__ == "__main__":
    main()
