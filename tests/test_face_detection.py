from pathlib import Path

import cv2

from face_verification import FaceVerifier
import numpy as np


def test_yunet_model_loads():
    verifier = FaceVerifier()

    assert verifier.detector is not None


def test_face_detection():
    image_path = Path("tests") / "test_face.jpg"

    image = cv2.imread(str(image_path))

    assert image is not None, "Test image could not be loaded"

    verifier = FaceVerifier()
    faces = verifier.detect_faces(image)

    print(f"\nDetected faces: {len(faces)}")

    assert len(faces) >= 1
def test_single_face_contains_landmarks():
    image_path = Path("tests") / "test_face.jpg"

    image = cv2.imread(str(image_path))

    assert image is not None

    verifier = FaceVerifier()
    face = verifier.get_single_face(image)

    assert face.shape == (15,)

    # Five landmarks = ten coordinate values
    landmarks = face[4:14]

    assert landmarks.shape == (10,)

    print(f"\nFace detection data: {face}")
    print(f"Landmarks: {landmarks}")
def test_sface_alignment():
    image_path = Path("tests") / "test_face.jpg"

    image = cv2.imread(str(image_path))

    assert image is not None

    verifier = FaceVerifier()

    face = verifier.get_single_face(image)
    aligned = verifier.align_face(image, face)

    assert aligned is not None
    assert aligned.shape == (112, 112, 3)

    print(f"\nAligned face shape: {aligned.shape}")
def test_sface_feature_extraction():
    image_path = Path("tests") / "test_face.jpg"

    image = cv2.imread(str(image_path))

    assert image is not None

    verifier = FaceVerifier()

    face = verifier.get_single_face(image)
    aligned = verifier.align_face(image, face)
    features = verifier.extract_features(aligned)

    assert features is not None
    assert features.shape == (1, 128)

    print(f"\nFeature shape: {features.shape}")
def test_sface_comparison():
    image1 = cv2.imread("tests/test_face.jpg")
    image2 = cv2.imread("tests/test_face_same.jpg")

    assert image1 is not None
    assert image2 is not None

    verifier = FaceVerifier()

    face1 = verifier.get_single_face(image1)
    face2 = verifier.get_single_face(image2)

    aligned1 = verifier.align_face(image1, face1)
    aligned2 = verifier.align_face(image2, face2)

    features1 = verifier.extract_features(aligned1)
    features2 = verifier.extract_features(aligned2)

    score = verifier.compare_features(features1, features2)

    print(f"\nCosine similarity: {score:.6f}")

    assert np.isfinite(score)
def test_sface_same_person_comparison():
    image1 = cv2.imread("tests/test_face.jpg")
    image2 = cv2.imread("tests/test_face_same_person.jpg")

    assert image1 is not None
    assert image2 is not None

    verifier = FaceVerifier()

    face1 = verifier.get_single_face(image1)
    face2 = verifier.get_single_face(image2)

    aligned1 = verifier.align_face(image1, face1)
    aligned2 = verifier.align_face(image2, face2)

    features1 = verifier.extract_features(aligned1)
    features2 = verifier.extract_features(aligned2)

    score = verifier.compare_features(features1, features2)

    print(f"\nSame-person cosine similarity: {score:.6f}")

    assert np.isfinite(score)
def test_match_decision():
    verifier = FaceVerifier()

    assert verifier.is_match(0.729695) is True
    assert verifier.is_match(-0.036237) is False
    assert verifier.is_match(0.363) is True
    assert verifier.is_match(0.362999) is False