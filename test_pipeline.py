from paddleocr import PaddleOCR
from src.passport_parser import parse_passport

IMAGE_PATH = "data/test/passport_001.jpg"

print("===================================")
print("       TRINETRA DOCUMENT OCR")
print("===================================")

# Start OCR
ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False
)

print("\n[1/2] Running OCR...")
result = ocr.predict(IMAGE_PATH)

# Extract recognized text
ocr_texts = []

for res in result:
    if hasattr(res, "json"):
        data = res.json

        if callable(data):
            data = data()

        if isinstance(data, dict):
            ocr_texts.extend(
                data.get("res", {}).get("rec_texts", [])
            )

print(f"Detected {len(ocr_texts)} text regions.")

# Parse passport
print("\n[2/2] Extracting passport fields...")

passport = parse_passport(ocr_texts)

print("\n===================================")
print("       PASSPORT INFORMATION")
print("===================================")

for field, value in passport.items():
    print(f"{field:20}: {value}")

print("\n===================================")
print("       PIPELINE COMPLETE")
print("===================================")