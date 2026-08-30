import cv2
import numpy as np
import os
from typing import Union, Dict, Any

class TRINETRAFaceVerifier:
    def __init__(self, 
                 detection_model_path: str = "models/face_detection_yunet_2021dec.onnx",
                 recognition_model_path: str = "models/face_recognition_sface_2021dec.onnx"):
        
        self.detection_model_path = detection_model_path
        self.recognition_model_path = recognition_model_path
        
        # SFace official benchmark threshold for Cosine Similarity
        self.threshold_cosine = 0.363
        
        self.models_loaded = os.path.exists(self.detection_model_path) and os.path.exists(self.recognition_model_path)
        
        if self.models_loaded:
            # Recognizer can be initialized once
            self.recognizer = cv2.FaceRecognizerSF.create(self.recognition_model_path, "")

    def _extract_face_feature(self, image: np.ndarray):
        """
        Detects face, aligns/crops it using OpenCV SFace, and extracts the 128D feature embedding.
        Returns (feature, error_status).
        """
        img_height, img_width = image.shape[:2]
        
        # Detector is initialized per-image because it requires the explicit image shape
        detector = cv2.FaceDetectorYN.create(
            self.detection_model_path, "", (img_width, img_height),
            score_threshold=0.9, nms_threshold=0.3, top_k=5000
        )
        
        retval, faces = detector.detect(image)
        
        if faces is None or len(faces) == 0:
            return None, "NO_FACE_DETECTED"
            
        # SECURITY CONFORMITY: Do not silently accept ambiguous inputs
        if len(faces) > 1:
            return None, "MULTIPLE_FACES_DETECTED"
            
        face = faces[0]
        
        # SFace Native Preprocessing (Align and Crop)
        aligned_face = self.recognizer.alignCrop(image, face)
        
        # Extract 128D feature embedding
        feature = self.recognizer.feature(aligned_face)
        
        return feature, None

    def verify(self, passport_img: Union[str, np.ndarray, None], presented_img: Union[str, np.ndarray, None]) -> Dict[str, Any]:
        """
        Performs face verification. 
        
        IMPORTANT: 'match_score' is a normalized cosine similarity score (0-100 scale), 
        NOT a probability that the two people are identical. Final identity claims 
        must rely on aggregated evidence.
        """
        if passport_img is None or presented_img is None:
            return {
                "status": "NOT_PROVIDED" if presented_img is None else "FAILED",
                "provided": presented_img is not None,
                "match_score": None,
                "is_match": None
            }

        if not self.models_loaded:
            return {
                "status": "FAILED", 
                "provided": True,
                "match_score": None,
                "is_match": None
            }

        # Handle disk path inputs gracefully
        if isinstance(passport_img, str):
            passport_img = cv2.imread(passport_img)
        if isinstance(presented_img, str):
            presented_img = cv2.imread(presented_img)
            
        if not isinstance(passport_img, np.ndarray) or not isinstance(presented_img, np.ndarray):
            return {
                "status": "FAILED",
                "provided": True,
                "match_score": None,
                "is_match": None
            }

        try:
            # 1. Feature Extraction Pipeline
            feat1, err1 = self._extract_face_feature(passport_img)
            feat2, err2 = self._extract_face_feature(presented_img)

            if err1 is not None or err2 is not None:
                return {
                    "status": "FAILED",
                    "provided": True,
                    "match_score": None,
                    "is_match": None
                }

            # 2. Raw Distance Measurement
            try:
                # Use OpenCV optimized distance function
                cosine_similarity = self.recognizer.match(feat1, feat2, cv2.FaceRecognizerSF_FR_COSINE)
            except AttributeError:
                # Safe fallback if cv2 constants differ in local environment
                f1 = feat1[0] / np.linalg.norm(feat1[0])
                f2 = feat2[0] / np.linalg.norm(feat2[0])
                cosine_similarity = np.dot(f1, f2)
                
            # 3. Normalization (Linear mapping from Cosine [-1, 1] to Score [0, 100])
            normalized_score = max(0.0, min(100.0, ((cosine_similarity + 1.0) / 2.0) * 100.0))
            is_match = cosine_similarity >= self.threshold_cosine

            return {
                "status": "SUCCESS",
                "provided": True,
                "match_score": round(float(normalized_score), 2),
                "is_match": bool(is_match)
            }
        except Exception:
            # Catch unpredictable C++ DNN faults
            return {
                "status": "FAILED",
                "provided": True,
                "match_score": None,
                "is_match": None
            }