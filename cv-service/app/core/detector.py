"""
Manufacturing defect detection using YOLOv8.
Detects surface defects, cracks, scratches, and anomalies in product images.
"""
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import io
import base64
from collections import defaultdict
from app.core.config import settings

_model = None

# Defect severity mapping based on detected class labels
SEVERITY_MAP = {
    "crack": "critical", "scratch": "major", "dent": "major",
    "stain": "minor", "hole": "critical", "chip": "major",
    "corrosion": "critical", "deformation": "critical",
}

SEVERITY_COLORS = {
    "critical": (0, 0, 255),   # red
    "major": (0, 140, 255),    # orange
    "minor": (0, 255, 255),    # yellow
    "unknown": (180, 180, 180),
}

PALETTE = [
    (255, 87, 34), (33, 150, 243), (76, 175, 80), (156, 39, 176),
    (255, 193, 7), (0, 188, 212), (244, 67, 54), (63, 81, 181),
]

def _get_model():
    global _model
    if _model is None:
        _model = YOLO("yolov8n.pt")
    return _model

def _load_image(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    if max(w, h) > settings.MAX_IMAGE_SIZE:
        scale = settings.MAX_IMAGE_SIZE / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def _get_severity(label: str) -> str:
    return SEVERITY_MAP.get(label.lower(), "unknown")

def detect(image_bytes: bytes) -> dict:
    img = _load_image(image_bytes)
    model = _get_model()
    results = model(img, conf=settings.CONFIDENCE_THRESHOLD, verbose=False)[0]

    counts = defaultdict(int)
    detections = []
    severity_summary = defaultdict(int)
    annotated = img.copy()
    class_names = model.names

    for box in results.boxes:
        cls_id = int(box.cls[0])
        label = class_names[cls_id]
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        severity = _get_severity(label)
        color = SEVERITY_COLORS.get(severity, PALETTE[cls_id % len(PALETTE)])
        counts[label] += 1
        severity_summary[severity] += 1
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(annotated, f"{label} {conf:.2f}", (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        detections.append({
            "label": label, "confidence": round(conf, 3),
            "bbox": [x1, y1, x2, y2], "severity": severity,
        })

    total = len(detections)
    quality_status = "PASS" if total == 0 else (
        "FAIL" if severity_summary.get("critical", 0) > 0 else "REVIEW"
    )

    _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return {
        "counts": dict(counts),
        "total": total,
        "detections": detections,
        "severity_summary": dict(severity_summary),
        "quality_status": quality_status,
        "annotated_image": base64.b64encode(buf).decode("utf-8"),
        "image_width": img.shape[1],
        "image_height": img.shape[0],
    }
