from src.mrz_parser import parse_mrz
from src.cross_validator import cross_validate


passport_data = {
    "passport_number": "H9137927",
    "country_code": "IND",
    "sex": "M",
    "date_of_birth": "14/08/1973",
    "date_of_expiry": "17/02/2020"
}


mrz_lines = [
    "P<INDALAM<<MAQS0OD<<<<<<<<<<<<<<<<<<<<<<<<<<",
    "H9137927<31ND7308141M2002178<<<<<<<<<<<<<<<4"
]


mrz_data = parse_mrz(mrz_lines)

validation = cross_validate(
    passport_data,
    mrz_data
)


print("\n===================================")
print("       CROSS VALIDATION")
print("===================================")

for result in validation["results"]:

    status = "MATCH" if result["match"] else "MISMATCH"

    print(
        f"{result['field']:20} : "
        f"{status}"
    )

    print(
        f"  Visual : {result['visual_value']}"
    )

    print(
        f"  MRZ    : {result['mrz_value']}"
    )

print("-----------------------------------")

print(
    f"Matches: "
    f"{validation['matches']}/"
    f"{validation['total']}"
)

print(
    f"All fields match: "
    f"{validation['all_match']}"
)

print("===================================")