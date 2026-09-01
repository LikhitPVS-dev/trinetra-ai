from pathlib import Path

import cv2
import numpy as np


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent

# Model path
YUNET_MODEL = PROJECT_ROOT / "models" / "face_detection_yunet_2026may.onnx"
SFACE_MODEL = PROJECT_ROOT / "models" / "face_recognition_sface_2021dec.onnx"


class FaceVerifier:
    COSINE_THRESHOLD = 0.363
    def __init__(self):
        if not YUNET_MODEL.exists():
            raise FileNotFoundError(
                f"YuNet model not found: {YUNET_MODEL}"
            )

        self.detector = cv2.FaceDetectorYN.create(
            model=str(YUNET_MODEL), 
            config="",
            input_size=(320, 320),
            score_threshold=0.6,
            nms_threshold=0.3,
            top_k=5000,
        )
        if not SFACE_MODEL.exists():
            raise FileNotFoundError(
                f"SFace model not found: {SFACE_MODEL}"
            )
        self.recognizer = cv2.FaceRecognizerSF.create(
            model=str(SFACE_MODEL),
            config=""
        )

    def detect_faces(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray):
            raise ValueError("Invalid image")

        if image.size == 0:
            raise ValueError("Empty image")

        height, width = image.shape[:2]

        # Tell YuNet the actual image dimensions.
        self.detector.setInputSize((width, height))

        _, faces = self.detector.detect(image)

        if faces is None:
            return np.empty((0, 15), dtype=np.float32)

        return faces
    def get_single_face(self, image: np.ndarray) -> np.ndarray:
        faces = self.detect_faces(image)

        if len(faces) == 0:
            raise ValueError("No face detected")

        if len(faces) > 1:
            raise ValueError(
                f"Multiple faces detected: {len(faces)}"
            )

        return faces[0]
    def align_face(self, image: np.ndarray, face: np.ndarray) -> np.ndarray:
        return self.recognizer.alignCrop(image, face)
    def extract_features(self, aligned_face: np.ndarray) -> np.ndarray:
        if aligned_face is None or aligned_face.size == 0:
            raise ValueError("Invalid aligned face")

        features = self.recognizer.feature(aligned_face)

        return features
    def compare_features(self,features1: np.ndarray,features2: np.ndarray) -> float:
        if features1 is None or features2 is None:
            raise ValueError("Features cannot be None")

        if features1.size == 0 or features2.size == 0:
            raise ValueError("Features cannot be empty")

        score = self.recognizer.match(
            features1,
            features2,
            cv2.FaceRecognizerSF_FR_COSINE
        )

        return float(score)
    def is_match(self, score: float) -> bool:
        return score >= self.COSINE_THRESHOLD