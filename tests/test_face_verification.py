import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from face_verification import TRINETRAFaceVerifier

@pytest.fixture
def mock_opencv_env():
    """Mocks OpenCV DNN loading so tests run instantly without ONNX models present."""
    with patch("os.path.exists", return_value=True), \
         patch("cv2.FaceDetectorYN.create") as mock_detector_create, \
         patch("cv2.FaceRecognizerSF.create") as mock_recognizer_create:
         
        mock_detector = MagicMock()
        mock_detector_create.return_value = mock_detector
        
        mock_recognizer = MagicMock()
        mock_recognizer_create.return_value = mock_recognizer
        
        yield mock_detector, mock_recognizer

def test_missing_face(mock_opencv_env):
    mock_detector, _ = mock_opencv_env
    mock_detector.detect.return_value = (True, []) # OpenCV returns empty
    
    verifier = TRINETRAFaceVerifier()
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    result = verifier.verify(dummy_img, dummy_img)
    assert result["status"] == "FAILED"
    assert result["is_match"] is None

def test_multiple_faces_rejects(mock_opencv_env):
    mock_detector, _ = mock_opencv_env
    # OpenCV finds two faces
    mock_detector.detect.return_value = (True, [np.array([]), np.array([])]) 
    
    verifier = TRINETRAFaceVerifier()
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    result = verifier.verify(dummy_img, dummy_img)
    assert result["status"] == "FAILED"

def test_matching_faces(mock_opencv_env):
    mock_detector, mock_recognizer = mock_opencv_env
    mock_detector.detect.return_value = (True, [np.array([])])
    
    # Mocking perfect mathematical cosine similarity (1.0)
    mock_recognizer.match.return_value = 1.0 
    
    verifier = TRINETRAFaceVerifier()
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    result = verifier.verify(dummy_img, dummy_img)
    
    assert result["status"] == "SUCCESS"
    assert result["is_match"] is True
    assert result["match_score"] == 100.0

def test_non_matching_faces(mock_opencv_env):
    mock_detector, mock_recognizer = mock_opencv_env
    mock_detector.detect.return_value = (True, [np.array([])])
    
    # Mocking mathematically opposite cosine similarity (0.0 distance -> 50% normalized)
    mock_recognizer.match.return_value = 0.0 
    
    verifier = TRINETRAFaceVerifier()
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    result = verifier.verify(dummy_img, dummy_img)
    
    assert result["status"] == "SUCCESS"
    assert result["is_match"] is False
    assert result["match_score"] == 50.0 

def test_invalid_image_type():
    verifier = TRINETRAFaceVerifier()
    result = verifier.verify("non_existent_file.jpg", "non_existent_file2.jpg")
    assert result["status"] == "FAILED"

def test_missing_model_handling():
    with patch("os.path.exists", return_value=False):
        verifier = TRINETRAFaceVerifier()
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = verifier.verify(dummy_img, dummy_img)
        assert result["status"] == "FAILED"