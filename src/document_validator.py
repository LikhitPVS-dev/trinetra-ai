from paddleocr import PaddleOCR
from .tamper_detector import analyze_tamper
import time
from .passport_parser import parse_passport
from .mrz_parser import parse_mrz
from .cross_validator import cross_validate


# Create OCR engine once
ocr = PaddleOCR(
    lang="en",
    use_doc_orientation_classify=True,
    use_doc_unwarping=True,
    use_textline_orientation=True,
    enable_mkldnn=False
)

def extract_ocr_texts(image_path):
    results = ocr.predict(image_path)

    ocr_texts = []

    for result in results:
        # PaddleOCR / PaddleX OCRResult behaves like a dictionary
        data = dict(result)

        texts = data.get("rec_texts", [])

        for text in texts:
            if text and str(text).strip():
                ocr_texts.append(str(text).strip())

    print(f"OCR detected {len(ocr_texts)} text items.")

    print("OCR TEXTS:")
    for text in ocr_texts:
        print(f"  {text}")

    return ocr_texts


def validate_document(image_path):
    stage_start = time.time()

    print("\n===================================")
    print("       TRINETRA DOCUMENT CHECK")
    print("===================================")

    # 1. OCR
    print("\n[1/5] Running OCR...")
    ocr_texts = extract_ocr_texts(image_path)
    print(f"[PERF-P1] OCR: {time.time() - stage_start:.2f}s")
    stage_start = time.time()

    if not ocr_texts:
        return {
            "status": "REVIEW",
            "reason": "No text detected",
            "ocr_texts": []
        }

    # 2. Visual passport extraction
    print("[2/5] Extracting passport fields...")
    passport_data = parse_passport(ocr_texts)

    # 3. MRZ parsing
    print("[3/5] Parsing MRZ...")

    mrz_lines = passport_data.get("mrz", [])

    if len(mrz_lines) < 2:
        return {
            "status": "REVIEW",
            "reason": "MRZ not detected",
            "passport_data": passport_data,
            "ocr_texts": ocr_texts
        }

    mrz_data = parse_mrz(mrz_lines)

    # 4. Cross-validation
    print("[4/5] Cross-validating document...")

    validation = cross_validate(
        passport_data,
        mrz_data
    )
    print("[5/5] Running tamper detection...")

    tamper_result=analyze_tamper(image_path,validation)
    print(f"[PERF-P1] Tampering: {time.time() - stage_start:.2f}s")
    # Final decision
    if not mrz_data.get("valid", False):
        status = "REVIEW"
        reason = "MRZ validation failed"

    elif validation.get("all_match", False):
        status = "PASS"
        reason = "Document fields are consistent"

    else:
        status = "REVIEW"
        reason = "Document fields do not fully match"

    return {
    "status": status,
    "reason": reason,
    "passport_data": passport_data,
    "mrz_data": mrz_data,
    "cross_validation": validation,
    "tamper": tamper_result,
    "ocr_texts": ocr_texts
}