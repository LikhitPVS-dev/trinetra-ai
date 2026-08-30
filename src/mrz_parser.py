import re


def mrz_char_value(char):
    """
    Convert an MRZ character into its ICAO numeric value.

    0-9 -> their numeric value
    A-Z -> 10-35
    <   -> 0
    """

    if char == "<":
        return 0

    if char.isdigit():
        return int(char)

    if "A" <= char <= "Z":
        return ord(char) - ord("A") + 10

    return 0


def mrz_check_digit(data):
    """
    Calculate the ICAO MRZ check digit.
    """

    weights = [7, 3, 1]

    total = 0

    for index, char in enumerate(data):
        total += mrz_char_value(char) * weights[index % 3]

    return str(total % 10)


def validate_check_digit(data, expected_digit):
    """
    Compare calculated and expected MRZ check digits.
    """

    calculated = mrz_check_digit(data)

    return calculated == expected_digit


def clean_mrz_line(line):
    """
    Clean OCR output so it can be processed as MRZ text.
    """

    line = line.upper().strip()

    # Keep only valid MRZ characters.
    line = re.sub(r"[^A-Z0-9<]", "", line)

    return line


def parse_mrz(mrz_lines):
    """
    Parse a two-line passport MRZ.
    """

    if len(mrz_lines) < 2:
        return {
            "valid": False,
            "error": "Two MRZ lines required"
        }

    line1 = clean_mrz_line(mrz_lines[0])
    line2 = clean_mrz_line(mrz_lines[1])

    # Standard TD3 passport MRZ lines should normally contain 44 characters.
    if len(line1) != 44 or len(line2) != 44:
        return {
            "valid": False,
            "error": (
                f"Unexpected MRZ length: "
                f"line1={len(line1)}, line2={len(line2)}"
            ),
            "line1": line1,
            "line2": line2
        }

    # ---------------------------------------------
    # LINE 1
    # ---------------------------------------------

    document_type = line1[0]
    issuing_country = line1[2:5]

    name_section = line1[5:]

    name_parts = name_section.split("<<")

    surname = name_parts[0].replace("<", " ").strip()

    given_names = ""

    if len(name_parts) > 1:
        given_names = name_parts[1].replace("<", " ").strip()

    # ---------------------------------------------
    # LINE 2
    # ---------------------------------------------

    passport_number = line2[0:9].replace("<", "")
    passport_number_check = line2[9]

    nationality = line2[10:13]

    date_of_birth = line2[13:19]
    date_of_birth_check = line2[19]

    sex = line2[20]

    expiry_date = line2[21:27]
    expiry_date_check = line2[27]

    optional_data = line2[28:43]

    overall_check = line2[43]

    # ---------------------------------------------
    # CHECK DIGITS
    # ---------------------------------------------

    passport_check_valid = validate_check_digit(
        line2[0:9],
        passport_number_check
    )

    dob_check_valid = validate_check_digit(
        line2[13:19],
        date_of_birth_check
    )

    expiry_check_valid = validate_check_digit(
        line2[21:27],
        expiry_date_check
    )

    # Composite check digit.
    composite_data = (
        line2[0:10]
        + line2[13:20]
        + line2[21:28]
        + line2[28:43]
    )

    overall_check_valid = validate_check_digit(
        composite_data,
        overall_check
    )

    all_checks_valid = (
        passport_check_valid
        and dob_check_valid
        and expiry_check_valid
        and overall_check_valid
    )

    return {
        "valid": all_checks_valid,

        "document_type": document_type,

        "issuing_country": issuing_country,

        "surname": surname,

        "given_names": given_names,

        "passport_number": passport_number,

        "nationality": nationality,

        "date_of_birth": date_of_birth,

        "sex": sex,

        "expiry_date": expiry_date,

        "optional_data": optional_data,

        "checks": {
            "passport_number": passport_check_valid,
            "date_of_birth": dob_check_valid,
            "expiry_date": expiry_check_valid,
            "overall": overall_check_valid
        },

        "raw_mrz": [
            line1,
            line2
        ]
    }