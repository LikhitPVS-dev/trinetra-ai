import io
from fastapi.testclient import TestClient
from PIL import Image
from pathlib import Path

# Import the FastAPI app
from backend.main import app

client = TestClient(app)

def create_dummy_image(format='JPEG'):
    """Helper to generate valid image bytes for upload tests."""
    img = Image.new('RGB', (10, 10), color='blue')
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()
def load_test_image(filename):
    image_path = Path("tests") / filename
    with open(image_path, "rb") as image_file:
        return image_file.read()

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
    passport_bytes = load_test_image("test_face.jpg")
    face_bytes = load_test_image("test_face_same_person.jpg")

    files = {
        "passport": ("pass.jpg", passport_bytes, "image/jpeg"),
        "face": ("face.jpg", face_bytes, "image/jpeg")
    }

    response = client.post("/analyze", files=files)

    assert response.status_code == 200

    face_result = response.json()["face_verification"]
    print(f"\nFACE API RESULT: {face_result}")
    assert face_result["status"] == "SUCCESS"
    assert face_result["provided"] is True
    assert face_result["match_score"] is not None
    assert 0.0 <= face_result["match_score"] <= 100.0
    assert face_result["is_match"] is True
def test_passport_and_different_face():
    passport_bytes = load_test_image("test_face.jpg")
    face_bytes = load_test_image("test_face_same.jpg")

    files = {
        "passport": ("pass.jpg", passport_bytes, "image/jpeg"),
        "face": ("face.jpg", face_bytes, "image/jpeg")
    }

    response = client.post("/analyze", files=files)

    assert response.status_code == 200

    face_result = response.json()["face_verification"]

    assert face_result["status"] == "SUCCESS"
    assert face_result["provided"] is True
    assert face_result["match_score"] is not None
    assert 0.0 <= face_result["match_score"] <= 100.0
    assert face_result["is_match"] is False
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