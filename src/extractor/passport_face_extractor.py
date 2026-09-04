import cv2
import numpy as np
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_YUNET_MODEL = (
    PROJECT_ROOT / "models" / "face_detection_yunet_2026may.onnx"
)

AMBIGUITY_THRESHOLD = 0.15


def _error_result(message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "crop_array": None,
        "bbox": None,
        "landmarks": None,
        "confidence": None,
        "message": message,
    }


def _no_face_result(message: str = "No face detected.") -> dict[str, Any]:
    return {
        "status": "no_face",
        "crop_array": None,
        "bbox": None,
        "landmarks": None,
        "confidence": None,
        "message": message,
    }


def _ambiguous_result(
    message: str = "Multiple plausible portraits detected."
) -> dict[str, Any]:
    return {
        "status": "ambiguous",
        "crop_array": None,
        "bbox": None,
        "landmarks": None,
        "confidence": None,
        "message": message,
    }


def _parse_detection(face: np.ndarray) -> dict[str, Any]:
    values = face.flatten().tolist()

    x, y, w, h = [int(round(v)) for v in values[:4]]
    confidence = float(values[14])

    landmarks = [
        [int(round(values[4])), int(round(values[5]))],
        [int(round(values[6])), int(round(values[7]))],
        [int(round(values[8])), int(round(values[9]))],
        [int(round(values[10])), int(round(values[11]))],
        [int(round(values[12])), int(round(values[13]))],
    ]

    return {
        "bbox": [x, y, w, h],
        "landmarks": landmarks,
        "confidence": confidence,
    }


def extract_passport_face(
    image: np.ndarray,
    model_path: str | Path = DEFAULT_YUNET_MODEL,
) -> dict[str, Any]:
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return _error_result("Invalid or empty image.")

    if image.ndim != 3 or image.shape[2] != 3:
        return _error_result("Expected a BGR color image.")

    model_path = Path(model_path)

    if not model_path.exists():
        return _error_result(f"YuNet model not found: {model_path}")

    try:
        detector = cv2.FaceDetectorYN.create(
            str(model_path),
            "",
            (image.shape[1], image.shape[0]),
            0.6,
            0.3,
            5000,
        )
    except Exception as exc:
        return _error_result(f"YuNet model loading failed: {exc}")

    try:
        detector.setInputSize((image.shape[1], image.shape[0]))
        _, faces = detector.detect(image)
    except Exception as exc:
        return _error_result(f"Face detection failed: {exc}")

    if faces is None or len(faces) == 0:
        return _no_face_result()

    parsed_faces = [_parse_detection(face) for face in faces]
    parsed_faces.sort(key=lambda item: item["confidence"], reverse=True)

    best = parsed_faces[0]

    if len(parsed_faces) > 1:
        second = parsed_faces[1]
        confidence_gap = best["confidence"] - second["confidence"]

        if confidence_gap < AMBIGUITY_THRESHOLD:
            return _ambiguous_result(
                "Top face detections have insufficient confidence separation."
            )

    x, y, w, h = best["bbox"]

    image_h, image_w = image.shape[:2]

    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(image_w, x + w)
    y2 = min(image_h, y + h)

    if x1 >= x2 or y1 >= y2:
        return _error_result("Detected face bounding box is invalid.")

    crop_array = image[y1:y2, x1:x2].copy()

    if crop_array.size == 0:
        return _error_result("Extracted portrait crop is empty.")

    return {
        "status": "success",
        "crop_array": crop_array,
        "bbox": best["bbox"],
        "landmarks": best["landmarks"],
        "confidence": best["confidence"],
        "message": "Portrait extracted successfully.",
    }