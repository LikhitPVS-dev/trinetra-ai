import cv2

from src.extractor.passport_face_extractor import extract_passport_face


passport_path = "data/test/passport_001.jpg"

image = cv2.imread(passport_path)

if image is None:
    raise FileNotFoundError(
        f"Could not load passport image: {passport_path}"
    )

result = extract_passport_face(image)

print("Status:", result["status"])
print("Message:", result["message"])
print("Bounding box:", result["bbox"])
print("Confidence:", result["confidence"])

if result["crop_array"] is not None:
    cv2.imwrite(
        "passport_portrait_test.jpg",
        result["crop_array"]
    )

    print("Portrait saved as passport_portrait_test.jpg")