from PIL import Image
import cv2

from SecurityEngine import SecurityEngine
from src.extractor.passport_face_extractor import extract_passport_face
from face_verification import FaceVerifier


passport_path = "data/test/passport_001.jpg"
presented_path = "securityengine_portrait.jpg"

# --------------------------------------------------
# Load images
# --------------------------------------------------

passport_img = Image.open(passport_path)
presented_img = Image.open(presented_path)

print("Original passport size:", passport_img.size)
print("Presented portrait size:", presented_img.size)


# --------------------------------------------------
# Reproduce SecurityEngine orientation normalization
# --------------------------------------------------

normalized_passport = (
    SecurityEngine._normalize_document_orientation(
        passport_img
    )
)

print(
    "Normalized passport size:",
    normalized_passport.size
)


# --------------------------------------------------
# Convert to OpenCV
# --------------------------------------------------

passport_array = SecurityEngine._pil_to_cv2(
    normalized_passport
)

presented_array = SecurityEngine._pil_to_cv2(
    presented_img
)


print(
    "Passport OpenCV shape:",
    passport_array.shape
)

print(
    "Presented OpenCV shape:",
    presented_array.shape
)


# --------------------------------------------------
# Extract passport portrait
# --------------------------------------------------

portrait_result = extract_passport_face(
    passport_array
)

print()
print("========== YUNET ==========")

print(
    "Status:",
    portrait_result["status"]
)

print(
    "Message:",
    portrait_result["message"]
)

print(
    "Confidence:",
    portrait_result["confidence"]
)

print(
    "Bounding box:",
    portrait_result["bbox"]
)


if portrait_result["crop_array"] is None:
    raise RuntimeError(
        "YuNet did not produce a portrait."
    )


passport_face = portrait_result["crop_array"]


print(
    "Extracted crop shape:",
    passport_face.shape
)


# Save exactly what SecurityEngine is giving SFace
cv2.imwrite(
    "securityengine_portrait.jpg",
    passport_face
)

print(
    "Saved SecurityEngine portrait as "
    "securityengine_portrait.jpg"
)


# --------------------------------------------------
# Direct SFace comparison
# --------------------------------------------------

verifier = FaceVerifier()

result = verifier.verify(
    passport_face,
    presented_array
)


print()
print("========== DIRECT SFACE ==========")

print(
    "Status:",
    result["status"]
)

print(
    "Score:",
    result["match_score"]
)

print(
    "Match:",
    result["is_match"]
)