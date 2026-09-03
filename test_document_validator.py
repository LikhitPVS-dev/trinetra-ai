from src.document_validator import validate_document


IMAGE_PATH = "data/test/passport_001.jpg"


result = validate_document(IMAGE_PATH)

print("\n===================================")
print("       FINAL RESULT")
print("===================================")

print("Status :", result["status"])
print("Reason :", result["reason"])

print("\nPassport data:")
print(result.get("passport_data"))

print("\nMRZ data:")
print(result.get("mrz_data"))

print("\nCross validation:")
print(result.get("cross_validation"))

print("\n===================================")