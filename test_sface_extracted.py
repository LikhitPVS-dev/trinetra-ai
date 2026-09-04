import cv2

from src.extractor.passport_face_extractor import extract_passport_face
from face_verification import FaceVerifier


passport_path = "data/test/passport_001.jpg"
presented_path = "passport_portrait_test.jpg"


# Load passport
passport = cv2.imread(passport_path)

if passport is None:
    raise FileNotFoundError(passport_path)


# Load the extracted portrait
presented = cv2.imread(presented_path)

if presented is None:
    raise FileNotFoundError(presented_path)


# Extract portrait from passport
result = extract_passport_face(passport)

print("Extraction status:", result["status"])
print("Extraction message:", result["message"])
print("Confidence:", result["confidence"])
print("Bounding box:", result["bbox"])


if result["crop_array"] is None:
    raise RuntimeError("No passport portrait was extracted.")


passport_face = result["crop_array"]


# Create SFace verifier
verifier = FaceVerifier()


# Compare:
# passport portrait extracted by YuNet
# vs
# the saved extracted portrait
face_result = verifier.verify(
    passport_face,
    presented
)


print()
print("========== SFACE RESULT ==========")
print("Status:", face_result["status"])
print("Score:", face_result["match_score"])
print("Match:", face_result["is_match"])