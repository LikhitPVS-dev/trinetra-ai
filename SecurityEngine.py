import time

class SecurityEngine:
    # Valid options: "LOW RISK", "REVIEW", "HIGH RISK", "INSUFFICIENT EVIDENCE"
    demo_scenario = "LOW RISK" 

    @staticmethod
    def analyze_document(passport_img, face_img=None) -> dict:
        """
        Main interface for the TRINETRA screening pipeline.
        Returns deterministic mock data based on SecurityEngine.demo_scenario.
        """
        start_time = time.time()
        
        # TEMPORARY MOCK BEHAVIOR: Artificial delay to simulate AI inference
        time.sleep(1.2) 
        
        # Base deterministic template (LOW RISK)
        result = {
            "processing": {
                "status": "SUCCESS",
                "processing_time": 0.0,
                "pipeline_version": "0.1"
            },
            "document_info": {
                "document_type": "PASSPORT",
                "issuing_country": "IND",
                "document_number": "Z9876543",
                "surname": "SHARMA",
                "given_names": "ROHAN",
                "date_of_birth": "1990-01-01",
                "expiry_date": "2031-12-28"
            },
            "ocr": {
                "status": "SUCCESS",
                "extracted_text": "P<INDSHARMA<<ROHAN<<<<<<<<<<<<<<<<<<<<<<<\nZ9876543<8IND9001015M2812316<<<<<<<<<<<<<<02",
                "confidence_score": 0.985
            },
            "mrz": {
                "status": "SUCCESS",
                "is_valid": True,
                "dob_match": True,
                "expiry_match": True,
                "checksums_passed": 2,
                "total_checksums": 2
            },
            "tampering": {
                "status": "SUCCESS",
                "tampering_detected": False,
                "tamper_score": 0.12,
                "anomalies": [],
                "regions": []
            },
            "face_verification": {
                "status": "NOT_PROVIDED",
                "provided": False,
                "match_score": None,
                "is_match": None
            },
            "risk_assessment": {
                "overall_score": 12,
                "risk_level": "LOW RISK",
                "evidence": ["MRZ checks passed", "Document fields are consistent", "No significant anomalies detected"],
                "recommendation": "Continue normal screening"
            }
        }

        # Handle face verification input
        if face_img is not None:
            result["face_verification"].update({
                "status": "SUCCESS",
                "provided": True,
                "match_score": 92.5,
                "is_match": True
            })
            result["risk_assessment"]["evidence"].append("Live face match verified")

        # Apply deterministic scenario modifiers
        if SecurityEngine.demo_scenario == "HIGH RISK":
            result["tampering"].update({
                "tampering_detected": True,
                "tamper_score": 0.88,
                "anomalies": ["Digital splicing detected near photo", "Inconsistent ELA compression"]
            })
            result["risk_assessment"].update({
                "overall_score": 95,
                "risk_level": "HIGH RISK",
                "evidence": ["Severe tampering anomalies detected in photo region"],
                "recommendation": "Secondary review recommended before further processing"
            })
            if face_img:
                result["face_verification"].update({"match_score": 42.1, "is_match": False})
                result["risk_assessment"]["evidence"].append("Live face does not match document photo")

        elif SecurityEngine.demo_scenario == "REVIEW":
            result["mrz"].update({
                "is_valid": False,
                "checksums_passed": 1,
                "expiry_match": False
            })
            result["risk_assessment"].update({
                "overall_score": 65,
                "risk_level": "REVIEW",
                "evidence": ["MRZ checksum mismatch", "Expiry date validation failed"],
                "recommendation": "Additional verification recommended"
            })

        elif SecurityEngine.demo_scenario == "INSUFFICIENT EVIDENCE":
            result["processing"]["status"] = "INSUFFICIENT_EVIDENCE"
            result["ocr"]["status"] = "FAILED"
            result["mrz"]["status"] = "FAILED"
            result["tampering"]["status"] = "INSUFFICIENT_EVIDENCE"
            result["risk_assessment"].update({
                "overall_score": 0,
                "risk_level": "INSUFFICIENT EVIDENCE",
                "evidence": ["Image quality too low for automated processing", "OCR extraction failed"],
                "recommendation": "Recapture document image for further analysis"
            })

        result["processing"]["processing_time"] = round(time.time() - start_time, 2)
        return result