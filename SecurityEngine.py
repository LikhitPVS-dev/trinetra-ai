import streamlit as st
from PIL import Image
import time
import random
class SecurityEngine:
    @staticmethod
    def analyze_document(passport_img, face_img=None):
        """Mocks the AI analysis pipeline."""
        # Simulate processing delay
        time.sleep(2)
        
        # Generate slightly randomized mock data for demo purposes
        is_tampered = random.choice([True, False, False, False]) # 25% chance of fake
        
        return {
            "document_info": {
                "document_type": "P (Passport)",
                "issuing_country": "IND",
                "document_number": "Z9876543",
                "surname": "SHARMA",
                "given_names": "ROHAN",
            },
            "ocr": {
                "extracted_text": "P<INDSHARMA<<ROHAN<<<<<<<<<<<<<<<<<<<<<<<\nZ9876543<8IND9001015M2812316<<<<<<<<<<<<<<02",
                "confidence_score": 98.5
            },
            "mrz": {
                "is_valid": True,
                "checksums_passed": 5,
                "total_checksums": 5,
                "dob_match": True,
                "expiry_match": True
            },
            "tampering": {
                "tampering_detected": is_tampered,
                "ela_score": 0.85 if is_tampered else 0.12,
                "anomalies": ["Inconsistent compression near photo"] if is_tampered else ["None detected"]
            },
            "face_verification": {
                "provided": face_img is not None,
                "match_score": random.uniform(85.0, 99.0) if face_img else None,
                "is_match": True if face_img else False,
            },
            "risk_assessment": {
                "overall_score": 85 if is_tampered else 12,
                "risk_level": "HIGH RISK" if is_tampered else "CLEARED",
                "evidence": ["High ELA anomaly detected"] if is_tampered else ["All security checks passed"]
            }
        }