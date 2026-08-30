from pydantic import BaseModel, Field, model_validator
from typing import Literal, Any

class ProcessingResult(BaseModel):
    status: str
    processing_time: float
    pipeline_version: str

class DocumentInfo(BaseModel):
    document_type: str
    issuing_country: str
    document_number: str
    surname: str
    given_names: str
    date_of_birth: str | None = None
    expiry_date: str | None = None

class OCRResult(BaseModel):
    status: str
    extracted_text: str
    confidence_score: float = Field(ge=0.0, le=1.0)

class MRZResult(BaseModel):
    status: str
    is_valid: bool
    dob_match: bool
    expiry_match: bool
    checksums_passed: int = Field(ge=0)
    total_checksums: int = Field(ge=0)

    @model_validator(mode='after')
    def validate_checksums(self):
        if self.checksums_passed > self.total_checksums:
            raise ValueError(f"checksums_passed ({self.checksums_passed}) cannot exceed total_checksums ({self.total_checksums})")
        return self

class TamperingResult(BaseModel):
    status: str
    tampering_detected: bool
    tamper_score: float = Field(ge=0.0, le=1.0)
    anomalies: list[str]
    regions: list[Any] = Field(default_factory=list)

class FaceVerificationResult(BaseModel):
    status: str
    provided: bool
    match_score: float | None = Field(default=None, ge=0.0, le=100.0)
    is_match: bool | None = None

class RiskAssessment(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    risk_level: Literal["LOW RISK", "REVIEW", "HIGH RISK", "INSUFFICIENT EVIDENCE"]
    evidence: list[str]
    recommendation: str

class ScreeningResult(BaseModel):
    processing: ProcessingResult
    document_info: DocumentInfo
    ocr: OCRResult
    mrz: MRZResult
    tampering: TamperingResult
    face_verification: FaceVerificationResult
    risk_assessment: RiskAssessment