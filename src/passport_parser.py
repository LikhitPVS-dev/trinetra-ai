import re
from datetime import datetime


def parse_passport(ocr_texts):
    """
    Convert PaddleOCR text detections into structured passport data.
    """

    # Combine all OCR detections into one searchable string
    text = "\n".join(ocr_texts)

    passport = {
        "document_type": "Passport",
        "country_code": None,
        "passport_number": None,
        "name": None,
        "nationality": None,
        "sex": None,
        "date_of_birth": None,
        "place_of_birth": None,
        "place_of_issue": None,
        "date_of_issue": None,
        "date_of_expiry": None,
        "mrz": []
    }

    # --------------------------------------------------
    # COUNTRY / NATIONALITY
    # --------------------------------------------------

    if re.search(r"\bIND\b", text):
        passport["country_code"] = "IND"

    if re.search(r"\bINDIAN\b", text, re.IGNORECASE):
        passport["nationality"] = "INDIAN"

    # --------------------------------------------------
    # PASSPORT NUMBER
    # --------------------------------------------------

    passport_match = re.search(
        r"\b[A-Z]\d{7}\b",
        text
    )

    if passport_match:
        passport["passport_number"] = passport_match.group()

    # --------------------------------------------------
    # SEX
    # --------------------------------------------------

    if re.search(r"\bM\b", text):
        passport["sex"] = "M"
    elif re.search(r"\bF\b", text):
        passport["sex"] = "F"

    # --------------------------------------------------
    # DATES
    # --------------------------------------------------

    dates = re.findall(
        r"\b\d{2}/\d{2}/\d{4}\b",
        text
    )

    if len(dates) >= 1:
        passport["date_of_birth"] = dates[0]

    if len(dates) >= 2:
        passport["date_of_issue"] = dates[1]

    if len(dates) >= 3:
        passport["date_of_expiry"] = dates[2]

    # --------------------------------------------------
    # MRZ
    # --------------------------------------------------

    for line in ocr_texts:

        # Passport MRZ normally begins with P<
        if line.startswith("P<"):
            passport["mrz"].append(line)

        # Second MRZ line begins with passport number
        elif re.match(r"^[A-Z0-9<]{30,44}$", line):
            passport["mrz"].append(line)

    return passport