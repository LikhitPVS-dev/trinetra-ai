import cv2
import numpy as np
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_YUNET_MODEL = (
    PROJECT_ROOT
    / "models"
    / "face_detection_yunet_2026may.onnx"
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


def _no_face_result(
    message: str = "No face detected."
) -> dict[str, Any]:
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

    x, y, w, h = [
        int(round(v))
        for v in values[:4]
    ]

    confidence = float(values[14])

    landmarks = [
        [
            int(round(values[4])),
            int(round(values[5]))
        ],
        [
            int(round(values[6])),
            int(round(values[7]))
        ],
        [
            int(round(values[8])),
            int(round(values[9]))
        ],
        [
            int(round(values[10])),
            int(round(values[11]))
        ],
        [
            int(round(values[12])),
            int(round(values[13]))
        ],
    ]

    return {
        "bbox": [x, y, w, h],
        "landmarks": landmarks,
        "confidence": confidence,
    }



def _rotate_image(
    image: np.ndarray,
    angle: int,
) -> np.ndarray:
    if angle == 0:
        return image

    if angle == 90:
        return cv2.rotate(
            image,
            cv2.ROTATE_90_CLOCKWISE
        )

    if angle == 180:
        return cv2.rotate(
            image,
            cv2.ROTATE_180
        )

    if angle == 270:
        return cv2.rotate(
            image,
            cv2.ROTATE_90_COUNTERCLOCKWISE
        )

    raise ValueError(
        f"Unsupported rotation angle: {angle}"
    )


def extract_passport_face(
    image: np.ndarray,
    model_path: str | Path = DEFAULT_YUNET_MODEL,
) -> dict[str, Any]:

    if (
        image is None
        or not isinstance(image, np.ndarray)
        or image.size == 0
    ):
        return _error_result(
            "Invalid or empty image."
        )

    if image.ndim != 3 or image.shape[2] != 3:
        return _error_result(
            "Expected a BGR color image."
        )

    model_path = Path(model_path)

    if not model_path.exists():
        return _error_result(
            f"YuNet model not found: {model_path}"
        )

    valid_detections = []
    ambiguous_found = False

    for angle in (0, 90, 180, 270):

        rotated = _rotate_image(
            image,
            angle
        )

        try:
            detector = cv2.FaceDetectorYN.create(
                str(model_path),
                "",
                (
                    rotated.shape[1],
                    rotated.shape[0]
                ),
                0.6,
                0.3,
                5000,
            )

            detector.setInputSize(
                (
                    rotated.shape[1],
                    rotated.shape[0]
                )
            )

            _, faces = detector.detect(
                rotated
            )

        except Exception as exc:
            return _error_result(
                f"Face detection failed at "
                f"{angle}°: {exc}"
            )

        if faces is None or len(faces) == 0:
            continue

        parsed_faces = [
            _parse_detection(face)
            for face in faces
        ]

        parsed_faces.sort(
            key=lambda item: item["confidence"],
            reverse=True,
        )

        best = parsed_faces[0]

        # Ambiguity is checked ONLY within this orientation.
        if len(parsed_faces) > 1:

            second = parsed_faces[1]

            confidence_gap = (
                best["confidence"]
                - second["confidence"]
            )

            if confidence_gap < AMBIGUITY_THRESHOLD:
                ambiguous_found = True
                continue

        valid_detections.append(
            {
                "angle": angle,
                "image": rotated,
                "detection": best,
            }
        )

    # No clear single-face detection was found.
    if not valid_detections:

        if ambiguous_found:
            return _ambiguous_result(
                "Multiple plausible portrait detections "
                "have insufficient confidence separation."
            )

        return _no_face_result(
            "No face detected in any supported orientation."
        )

    # Choose the strongest detection across orientations.
    best_result = max(
        valid_detections,
        key=lambda item: item["detection"]["confidence"],
    )

    best_detection = best_result["detection"]
    rotated_image = best_result["image"]

    x, y, w, h = best_detection["bbox"]

    image_h, image_w = rotated_image.shape[:2]

    x1 = max(0, x)
    y1 = max(0, y)

    x2 = min(
        image_w,
        x + w
    )

    y2 = min(
        image_h,
        y + h
    )

    if x1 >= x2 or y1 >= y2:
        return _error_result(
            "Detected face bounding box is invalid."
        )

    crop_array = rotated_image[
        y1:y2,
        x1:x2
    ].copy()

    if crop_array.size == 0:
        return _error_result(
            "Extracted portrait crop is empty."
        )

    return {
        "status": "success",
        "crop_array": crop_array,
        "bbox": best_detection["bbox"],
        "landmarks": best_detection["landmarks"],
        "confidence": best_detection["confidence"],
        "rotation": best_result["angle"],
        "message": (
            "Portrait extracted successfully "
            f"using {best_result['angle']}° orientation."
        ),
    }