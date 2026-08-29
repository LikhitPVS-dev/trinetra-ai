import streamlit as st
from PIL import Image
import datetime
from SecurityEngine import SecurityEngine

# ==========================================
# UI RENDERING FUNCTIONS
# ==========================================

def render_header():
    st.title("🛡️ TRINETRA")
    st.markdown("### AI-ASSISTED PASSPORT SCREENING")
    st.caption("SIH 2026 • Problem Statement 26188 | Multimodal document screening and risk assessment for authorized officers.")
    st.divider()

def render_sidebar():
    with st.sidebar:
        st.header("TRINETRA")
        st.markdown("**Screening Mode:**\nPassport")
        st.markdown("**System Status:**\nPrototype")
        st.markdown("**Pipeline Version:**\nv0.1")
        st.divider()
        st.subheader("Demo Controls")
        SecurityEngine.demo_scenario = st.selectbox(
            "DEMO MODE SCENARIO", 
            ["LOW RISK", "REVIEW", "HIGH RISK", "INSUFFICIENT EVIDENCE"],
            help="Forces the mock engine to output specific deterministic results for UI testing."
        )

def render_upload_section():
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Passport Document")
        passport_file = st.file_uploader("Upload Passport Page", type=['png', 'jpg', 'jpeg'])
    with col2:
        st.subheader("Presented Person Image")
        face_file = st.file_uploader("Upload Live Face Photo (Optional)", type=['png', 'jpg', 'jpeg'])
    
    analyze_btn = st.button("ANALYZE DOCUMENT", type="primary", use_container_width=True)
    return passport_file, face_file, analyze_btn

def render_processing_status(processing_time: float):
    st.success(f"Processing completed in {processing_time} seconds")

def render_document_info(doc_info: dict):
    st.subheader("DOCUMENT INFORMATION")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Document Type", doc_info.get("document_type", "N/A"))
        c2.metric("Issuing Country", doc_info.get("issuing_country", "N/A"))
        c3.metric("Document Number", doc_info.get("document_number", "N/A"))
        c4, c5 = st.columns(2)
        c4.metric("Surname", doc_info.get("surname", "N/A"))
        c5.metric("Given Names", doc_info.get("given_names", "N/A"))

def render_ocr_results(ocr: dict):
    st.subheader("OCR ANALYSIS")
    with st.container(border=True):
        status = ocr.get("status")
        st.markdown(f"**Status:** {status}")
        if status == "SUCCESS":
            st.code(ocr.get("extracted_text", ""), language="text")
            st.progress(ocr.get("confidence_score", 0.0), text=f"OCR Confidence: {ocr.get('confidence_score', 0.0)*100:.1f}%")
        else:
            st.warning("OCR Extraction Failed or Insufficient Evidence.")

def render_mrz_results(mrz: dict):
    st.subheader("MRZ VALIDATION")
    with st.container(border=True):
        st.markdown(f"**MRZ Status:** {mrz.get('status')}")
        c1, c2, c3 = st.columns(3)
        c1.metric("MRZ Valid", str(mrz.get("is_valid")))
        c2.metric("DOB Match", str(mrz.get("dob_match")))
        c3.metric("Expiry Match", str(mrz.get("expiry_match")))
        st.metric("Checksums", f"{mrz.get('checksums_passed')} / {mrz.get('total_checksums')}")

def render_tampering_results(tamp: dict):
    st.subheader("TAMPERING ANALYSIS")
    with st.container(border=True):
        st.markdown(f"**Status:** {tamp.get('status')}")
        if tamp.get("status") == "SUCCESS":
            st.metric("Tampering Detected", str(tamp.get("tampering_detected")))
            st.metric("Tamper Score", str(tamp.get("tamper_score")))
            if tamp.get("anomalies"):
                st.error(f"**Anomalies:** {', '.join(tamp.get('anomalies'))}")
            else:
                st.success("No anomalies detected.")
        else:
            st.warning("Tampering analysis could not be completed.")

def render_face_results(face: dict):
    st.subheader("IDENTITY VERIFICATION")
    with st.container(border=True):
        status = face.get("status")
        st.markdown(f"**Status:** {status}")
        if status == "NOT_PROVIDED":
            st.info("Face verification not performed (No image provided).")
        elif status == "SUCCESS":
            st.metric("Match Score", f"{face.get('match_score')}%")
            st.metric("Match Result", str(face.get("is_match")))
        else:
            st.warning("Face verification failed.")

def render_risk_assessment(risk: dict):
    st.subheader("RISK ASSESSMENT")
    
    level = risk.get("risk_level")
    if level == "LOW RISK":
        color = "green"
    elif level == "REVIEW":
        color = "orange"
    elif level == "HIGH RISK":
        color = "red"
    else:
        color = "gray"
        
    with st.container(border=True):
        st.markdown(f"### <span style='color:{color}'>{level}</span>", unsafe_allow_html=True)
        st.metric("RISK SCORE", f"{risk.get('overall_score')} / 100")
        
        st.markdown("**Evidence:**")
        for ev in risk.get("evidence", []):
            st.markdown(f"- {ev}")
            
        st.markdown(f"**Recommendation:**\n> {risk.get('recommendation')}")

def render_officer_review(recommendation: str):
    st.subheader("OFFICER REVIEW")
    with st.container(border=True):
        st.markdown(f"**System Recommendation:** {recommendation}")
        st.markdown("Please log your final decision:")
        c1, c2, c3 = st.columns(3)
        c1.button("Continue Screening", use_container_width=True)
        c2.button("Secondary Review", use_container_width=True)
        c3.button("Recapture Document", use_container_width=True)

def render_audit_information(processing: dict):
    with st.expander("Screening Information"):
        st.markdown(f"**Timestamp:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.markdown(f"**Processing Time:** {processing.get('processing_time')}s")
        st.markdown(f"**Pipeline Version:** {processing.get('pipeline_version')}")
        st.markdown("**Document Type:** Passport")

# ==========================================
# MAIN APPLICATION LOGIC
# ==========================================
def main():
    st.set_page_config(page_title="TRINETRA | Passport Screening", layout="wide")
    
    render_sidebar()
    render_header()
    
    passport_file, face_file, analyze_btn = render_upload_section()
    
    if analyze_btn:
        if not passport_file:
            st.error("Please upload a passport document to begin screening.")
            return
            
        try:
            # Convert files to PIL Images for backend processing
            passport_img = Image.open(passport_file)
            face_img = Image.open(face_file) if face_file else None
            
            with st.spinner("Processing document..."):
                # Strictly calling the defined interface
                result = SecurityEngine.analyze_document(passport_img, face_img)
                
            render_processing_status(result["processing"]["processing_time"])
            
            # Layout the data
            col_left, col_right = st.columns([1, 1], gap="large")
            
            with col_left:
                render_risk_assessment(result["risk_assessment"])
                render_document_info(result["document_info"])
                render_face_results(result["face_verification"])
                
            with col_right:
                render_tampering_results(result["tampering"])
                render_mrz_results(result["mrz"])
                render_ocr_results(result["ocr"])
                
            st.divider()
            render_officer_review(result["risk_assessment"]["recommendation"])
            render_audit_information(result["processing"])

        except Exception as e:
            st.error("A system error occurred during analysis. Please contact technical support.")
            st.info("System logs: The uploaded file may be corrupted or in an unsupported format.")

if __name__ == "__main__":
    main()