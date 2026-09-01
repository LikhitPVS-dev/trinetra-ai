from src.mrz_parser import parse_mrz


mrz_lines = [
    "P<INDALAM<<MAQS0OD<<<<<<<<<<<<<<<<<<<<<<<<<<",
    "H9137927<31ND7308141M2002178<<<<<<<<<<<<<<<4"
]


result = parse_mrz(mrz_lines)


print("\n===== MRZ TEST =====")

for key, value in result.items():
    print(f"{key}: {value}")

print("\n===== TEST COMPLETE =====")