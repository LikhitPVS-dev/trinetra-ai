"""
Test script for src/tamper_detector.py using the project's passport test image.
"""

import os
import json
from src.tamper_detector import analyze_tamper

def test_tamper_detection():
    # Target your existing test passport image path here or via relative path
    test_image_paths = [
        "test_passport.jpg",
        "tests/test_passport.jpg",
        "sample_passport.jpg"
    ]
    
    image_path = None
    for path in test_image_paths:
        if os.path.exists(path):
            image_path = path
            break

    if not image_path:
        print("[-] Warning: Default test passport image not found. Please provide a valid path if testing locally.")
        return

    # Mock sample validation result matching your pipeline output format
    mock_validation_result = {
        "status": "PASS",
        "reason": "Document fields are consistent",
        "matches": "5/5"
    }

    print(f"[*] Running tamper detector on: {image_path}")
    result = analyze_tamper(image_path, validation_result=mock_validation_result)

    print("\n--- Tamper Detector Output Report ---")
    print(json.dumps(result, indent=2))
    print("-------------------------------------")

if __name__ == "__main__":
    test_tamper_detection()