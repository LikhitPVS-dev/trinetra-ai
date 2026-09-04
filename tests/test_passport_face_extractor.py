from pathlib import Path

import cv2
import numpy as np

from src.extractor.passport_face_extractor import extract_passport_face


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "face_detection_yunet_2026may.onnx"


def test_passport_001():
    image = cv2.imread(str(PROJECT_ROOT / "data" / "test" / "passport_001.jpg"))

    result = extract_passport_face(image)

    assert result["status"] == "success"
    assert result["bbox"] == [121, 48, 66, 82]
    assert result["crop_array"] is not None
    assert result["crop_array"].dtype == np.uint8
    assert result["crop_array"].shape == (82, 66, 3)


def test_passport_002():
    image = cv2.imread(str(PROJECT_ROOT / "data" / "test" / "passport_002.jpg"))

    result = extract_passport_face(image)

    assert result["status"] == "success"
    assert result["bbox"] == [41, 268, 37, 47]
    assert result["crop_array"] is not None
    assert result["crop_array"].dtype == np.uint8
    assert result["crop_array"].shape == (47, 37, 3)


def test_tampered_passport():
    image = cv2.imread(
        str(PROJECT_ROOT / "data" / "test" / "passport_tampered.jpg")
    )

    result = extract_passport_face(image)

    assert result["status"] == "success"
    assert result["bbox"] is not None
    assert result["crop_array"] is not None


def test_no_face():
    image = np.zeros((500, 500, 3), dtype=np.uint8)

    result = extract_passport_face(image)

    assert result["status"] == "no_face"
    assert result["crop_array"] is None
    assert result["bbox"] is None
    assert result["landmarks"] is None
    assert result["confidence"] is None


def test_invalid_input():
    result = extract_passport_face(None)

    assert result["status"] == "error"
    assert result["crop_array"] is None
    assert result["bbox"] is None
    assert result["landmarks"] is None
    assert result["confidence"] is None


def test_missing_model():
    image = cv2.imread(str(PROJECT_ROOT / "data" / "test" / "passport_001.jpg"))

    result = extract_passport_face(
        image,
        PROJECT_ROOT / "models" / "does_not_exist.onnx",
    )

    assert result["status"] == "error"
    assert result["crop_array"] is None
    assert result["bbox"] is None
    assert result["landmarks"] is None
    assert result["confidence"] is None


def test_ambiguous_two_faces():
    image = cv2.imread(str(PROJECT_ROOT / "data" / "test" / "face1.png"))

    result = extract_passport_face(image)

    assert result["status"] == "ambiguous"
    assert result["crop_array"] is None
    assert result["bbox"] is None
    assert result["landmarks"] is None
    assert result["confidence"] is None
def test_corrupt_model():
    image = cv2.imread(str(PROJECT_ROOT / "data" / "test" / "passport_001.jpg"))

    corrupt_model = PROJECT_ROOT / "data" / "test" / "corrupt_yunet.onnx"
    corrupt_model.write_bytes(b"this is not a valid onnx model")

    result = extract_passport_face(image, corrupt_model)

    assert result["status"] == "error"
    assert result["crop_array"] is None
    assert result["bbox"] is None
    assert result["landmarks"] is None
    assert result["confidence"] is None

    corrupt_model.unlink()