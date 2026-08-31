from datetime import datetime


def normalize_text(value):
    """Normalize text for comparison."""
    if value is None:
        return ""

    value = (
        str(value)
        .upper()
        .replace(" ", "")
        .replace("<", "")
    )

    # Common MRZ OCR character correction
    value = value.replace("1", "I")

    return value


def normalize_date(date_string):
    """
    Convert DD/MM/YYYY into YYMMDD for comparison with MRZ.
    """

    if not date_string:
        return ""

    try:
        date_obj = datetime.strptime(date_string, "%d/%m/%Y")
        return date_obj.strftime("%y%m%d")

    except ValueError:
        return ""


def compare_field(field_name, visual_value, mrz_value):
    """
    Compare a visual passport field against its MRZ value.
    """

    visual = normalize_text(visual_value)
    mrz = normalize_text(mrz_value)

    return {
        "field": field_name,
        "visual_value": visual_value,
        "mrz_value": mrz_value,
        "match": visual == mrz
    }


def cross_validate(passport_data, mrz_data):
    """
    Compare passport OCR fields against parsed MRZ fields.
    """

    results = []

    # Passport number
    results.append(
        compare_field(
            "passport_number",
            passport_data.get("passport_number"),
            mrz_data.get("passport_number")
        )
    )

    # Nationality
    results.append(
        compare_field(
            "nationality",
            passport_data.get("country_code"),
            mrz_data.get("nationality")
        )
    )

    # Sex
    results.append(
        compare_field(
            "sex",
            passport_data.get("sex"),
            mrz_data.get("sex")
        )
    )

    # Date of birth
    visual_dob = normalize_date(
        passport_data.get("date_of_birth")
    )

    results.append(
        compare_field(
            "date_of_birth",
            visual_dob,
            mrz_data.get("date_of_birth")
        )
    )

    # Expiry date
    visual_expiry = normalize_date(
        passport_data.get("date_of_expiry")
    )

    results.append(
        compare_field(
            "date_of_expiry",
            visual_expiry,
            mrz_data.get("expiry_date")
        )
    )

    matches = sum(
        result["match"]
        for result in results
    )

    total = len(results)

    return {
        "matches": matches,
        "total": total,
        "all_match": matches == total,
        "results": results
    }