from pathlib import Path
import sys
import io

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app

client = TestClient(app)

def create_dummy_image(format='JPEG'):
    """Helper to generate valid image bytes for upload tests."""
    img = Image.new('RGB', (10, 10), color='blue')
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "TRINETRA API is running"}

def test_missing_passport():
    response = client.post("/analyze")
    # FastAPI returns 422 Unprocessable Entity for missing required form fields
    assert response.status_code == 422 

def test_unsupported_file_type():
    files = {"passport": ("test.txt", b"fake text data", "text/plain")}
    response = client.post("/analyze", files=files)
    assert response.status_code == 400
    assert "Unsupported passport file type" in response.json()["detail"]

def test_corrupted_image():
    files = {"passport": ("bad.jpg", b"corrupted bytes", "image/jpeg")}
    response = client.post("/analyze", files=files)
    assert response.status_code == 400
    assert "Invalid or corrupted passport image" in response.json()["detail"]

def test_valid_passport_only():
    img_bytes = create_dummy_image()
    files = {"passport": ("test.jpg", img_bytes, "image/jpeg")}
    response = client.post("/analyze", files=files)
    
    assert response.status_code == 200
    data = response.json()
    # Pydantic contract dictates these fields must exist
    assert data["face_verification"]["status"] == "NOT_PROVIDED"
    assert data["risk_assessment"]["risk_level"] == "LOW RISK" # Default scenario

def test_passport_and_face():
    passport_path = "tests/test_face.jpg"
    face_path = "tests/test_face_same_person.jpg"

    with open(passport_path, "rb") as passport_file, \
         open(face_path, "rb") as face_file:

        files = {
            "passport": (
                "passport.jpg",
                passport_file,
                "image/jpeg"
            ),
            "face": (
                "face.jpg",
                face_file,
                "image/jpeg"
            )
        }

        response = client.post(
            "/analyze",
            files=files,
            data={"scenario": "REAL"}
        )

    assert response.status_code == 200    
    result = response.json()

    assert result["face_verification"]["status"] == "SUCCESS"
    assert result["face_verification"]["provided"] is True
    assert result["face_verification"]["is_match"] is True
    assert result["face_verification"]["match_score"] is not None

# Test Demo Scenarios over HTTP
def test_demo_scenarios():
    img_bytes = create_dummy_image()
    scenarios = ["LOW RISK", "REVIEW", "HIGH RISK", "INSUFFICIENT EVIDENCE"]
    
    for scenario in scenarios:
        files = {"passport": ("test.jpg", img_bytes, "image/jpeg")}
        data = {"scenario": scenario}
        
        response = client.post("/analyze", files=files, data=data)
        assert response.status_code == 200
        
        # Verify the backend responded with the requested mock scenario
        assert response.json()["risk_assessment"]["risk_level"] == scenario