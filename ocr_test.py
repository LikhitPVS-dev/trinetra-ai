from paddleocr import PaddleOCR

IMAGE_PATH = "data/test/passport_001.jpg"

print("Starting TRINETRA OCR...")

ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False
)

result = ocr.predict(IMAGE_PATH)

print("\n===== OCR RESULT =====")

for res in result:
    print(res)

print("\n===== OCR TEST COMPLETE =====")