import streamlit as st
#from PIL import Image
import requests
import datetime
#from SecurityEngine import SecurityEngine

# ==========================================
# UI CONFIGURATION & CSS
# ==========================================
st.set_page_config(page_title="TRINETRA | Terminal", layout="wide", initial_sidebar_state="expanded")

# Minimal CSS to format the prominent screening result card and status badges
st.markdown("""
<style>
    .result-card {
        padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid;
    }
    .result-low { background-color: #0b2e13; border-color: #1e7e34; color: #d4edda; }
    .result-review { background-color: #3e3104; border-color: #d39e00; color: #fff3cd; }
    .result-high { background-color: #421015; border-color: #dc3545; color: #f8d7da; }
    .result-insufficient { background-color: #2b2f32; border-color: #6c757d; color: #e2e3e5; }
    .pipeline-step {
        text-align: center; font-size: 0.85rem; padding: 0.5rem; background-color: #1e1e1e; border-radius: 4px; border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# COMPONENT RENDERERS
# ==========================================
def render_sidebar():
    with st.sidebar:
        st.markdown("### TRINETRA")
        st.markdown("**Screening Mode:** Passport")
        st.markdown("**System Status:** Prototype")
        st.markdown("**Pipeline Version:** v0.1")
        st.divider()
        
        with st.expander("⚙ Developer / Demo Mode", expanded=False):
            st.caption("Developer testing only — does not perform real document analysis.")
            # Changed to store in session_state instead of setting SecurityEngine directly
            st.session_state.demo_scenario = st.selectbox(
                "Scenario Control", 
                ["REAL","LOW RISK", "REVIEW", "HIGH RISK", "INSUFFICIENT EVIDENCE"],
                label_visibility="collapsed"
            )

def render_header():
    st.markdown("## INTELLIGENT DOCUMENT SCREENING")
    st.markdown("#### AI-assisted passport verification and risk assessment")
    st.caption("TRINETRA | SIH 2026 • Problem Statement 26188")
    st.divider()

def render_upload_section():
    st.subheader("DOCUMENT INPUT")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**PASSPORT DOCUMENT**")
        passport_file = st.file_uploader("Upload Passport (Max 10MB)", type=['png', 'jpg', 'jpeg'], key="pass_up", label_visibility="collapsed")
        if passport_file:
            # Check programmatic file size (Fallback)
            if passport_file.size > 10 * 1024 * 1024:
                st.error("File exceeds 10MB limit.")
                passport_file = None
            else:
                st.image(passport_file, caption="Passport Preview", use_container_width=True)
                
    with c2:
        st.markdown("**PRESENTED PERSON**")
        face_file = st.file_uploader("Upload Face (Max 10MB)", type=['png', 'jpg', 'jpeg'], key="face_up", label_visibility="collapsed")
        st.caption("Optional — used for identity verification")
        if face_file:
            if face_file.size > 10 * 1024 * 1024:
                st.error("File exceeds 10MB limit.")
                face_file = None
            else:
                st.image(face_file, caption="Live Capture Preview", width=250)

    st.markdown("<br/>", unsafe_allow_html=True)
    analyze_btn = st.button("ANALYZE DOCUMENT", type="primary", use_container_width=True)
    return passport_file, face_file, analyze_btn

def render_screening_result(risk: dict):
    level = risk.get("risk_level")
    
    css_class = {
        "LOW RISK": "result-low",
        "REVIEW": "result-review",
        "HIGH RISK": "result-high",
        "INSUFFICIENT EVIDENCE": "result-insufficient"
    }.get(level, "result-insufficient")
    
    st.markdown(f"""
        <div class="result-card {css_class}">
            <h4 style="margin:0; opacity: 0.9;">SCREENING RESULT</h4>
            <h1 style="margin: 5px 0;">{level}</h1>
            <h3 style="margin: 0; opacity: 0.8;">{risk.get('overall_score')} / 100</h3>
            <p style="margin-top: 15px; font-weight: bold; font-size: 1.1rem;">{risk.get('recommendation')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Evidence Summary under the card
    for ev in risk.get("evidence", []):
        icon = "✓" if level == "LOW RISK" else "⚠️" if level == "REVIEW" else "🚩"
        st.markdown(f"**{icon}** {ev}")

def render_verification_pipeline(res: dict):
    st.markdown("<br/>", unsafe_allow_html=True)
    st.subheader("VERIFICATION PIPELINE")
    cols = st.columns(7)
    
    img_qual = "FAIL" if res["processing"]["status"] == "INSUFFICIENT_EVIDENCE" else "PASS"
    doc_val = "PASS" if res["mrz"]["is_valid"] else "FAIL"
    ocr_stat = f"{res['ocr']['confidence_score']*100:.1f}%" if res["ocr"]["status"] == "SUCCESS" else "FAIL"
    mrz_stat = f"{res['mrz']['checksums_passed']} / {res['mrz']['total_checksums']}" if res["mrz"]["status"] == "SUCCESS" else "FAIL"
    tamp_stat = "HIGH" if res["tampering"]["tampering_detected"] else ("FAIL" if res["tampering"]["status"] != "SUCCESS" else "LOW")
    
    face = res["face_verification"]
    id_stat = "NOT PROVIDED" if face["status"] == "NOT_PROVIDED" else ("MATCH" if face["is_match"] else "MISMATCH")
    
    steps = [
        ("IMAGE QUALITY", img_qual), ("OCR", ocr_stat), ("MRZ", mrz_stat),
        ("VALIDATION", doc_val), ("TAMPERING", tamp_stat), ("IDENTITY", id_stat),
        ("RISK", res["risk_assessment"]["risk_level"])
    ]
    
    for col, (label, status) in zip(cols, steps):
        with col:
            color = "#dc3545" if status in ["FAIL", "HIGH", "MISMATCH", "HIGH RISK"] else "#ffc107" if status in ["REVIEW"] else "#28a745" if status not in ["NOT PROVIDED", "INSUFFICIENT EVIDENCE"] else "#6c757d"
            st.markdown(f"""
            <div class="pipeline-step">
                <div style="font-weight: bold; margin-bottom: 5px;">{label}</div>
                <div style="color: {color}; font-weight: 900;">{status}</div>
            </div>
            """, unsafe_allow_html=True)
    st.divider()

def render_document_information(doc: dict):
    st.subheader("DOCUMENT INFORMATION")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.caption("Document Type"); c1.write(doc.get("document_type"))
        c2.caption("Issuing Country"); c2.write(doc.get("issuing_country"))
        c3.caption("Document Number"); c3.write(doc.get("document_number"))
        
        c4, c5, c6, c7 = st.columns(4)
        c4.caption("Surname"); c4.write(doc.get("surname"))
        c5.caption("Given Names"); c5.write(doc.get("given_names"))
        c6.caption("Date of Birth"); c6.write(doc.get("date_of_birth"))
        c7.caption("Expiry Date"); c7.write(doc.get("expiry_date"))

def render_document_integrity(ocr: dict, mrz: dict):
    st.subheader("DOCUMENT INTEGRITY")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("**OCR ANALYSIS**")
            st.caption(f"Status: {ocr.get('status')}")
            if ocr.get("status") == "SUCCESS":
                st.code(ocr.get("extracted_text", ""), language="text")
                st.write(f"Confidence: **{ocr.get('confidence_score', 0)*100:.1f}%**")
    with c2:
        with st.container(border=True):
            st.markdown("**MRZ VALIDATION**")
            st.caption(f"Status: {mrz.get('status')}")
            if mrz.get("status") == "SUCCESS":
                st.write(f"Checksums Passed: **{mrz.get('checksums_passed')} / {mrz.get('total_checksums')}**")
                st.write(f"MRZ Valid: **{'Yes' if mrz.get('is_valid') else 'No'}**")
                st.write(f"DOB Match: **{'Yes' if mrz.get('dob_match') else 'No'}**")
                st.write(f"Expiry Match: **{'Yes' if mrz.get('expiry_match') else 'No'}**")

def render_tampering_analysis(tamp: dict):
    st.subheader("TAMPERING ANALYSIS")
    with st.container(border=True):
        st.markdown(f"**Status:** {tamp.get('status')}")
        if tamp.get("status") == "SUCCESS":
            c1, c2 = st.columns(2)
            c1.metric("Tampering Detected", "Yes" if tamp.get("tampering_detected") else "No")
            c2.metric("Tamper Score", f"{tamp.get('tamper_score', 0):.2f}")
            
            st.markdown("**Anomalies:**")
            if tamp.get("anomalies"):
                for a in tamp.get("anomalies"): st.error(f"🚩 {a}")
            else:
                st.success("No anomalies detected.")
                
            st.markdown("**Suspicious Regions:**")
            if not tamp.get("regions"):
                st.info("No suspicious regions reported.")
            else:
                st.warning("Regions highlighted on image (Integration Pending)")

def render_identity_verification(face: dict):
    st.subheader("IDENTITY VERIFICATION")
    with st.container(border=True):
        if face.get("status") == "NOT_PROVIDED":
            st.markdown("### NOT PROVIDED")
            st.info("Upload a presented-person image to perform identity verification.")
        elif face.get("status") == "SUCCESS":
            c1, c2 = st.columns(2)
            c1.metric("Match Score", f"{face.get('match_score')}%")
            c2.metric("Match Result", "MATCH" if face.get("is_match") else "MISMATCH")
            st.caption("DOCUMENT PHOTO  |  PRESENTED PERSON (Image mapping ready)")
        else:
            st.error("Face verification failed.")

def render_evidence_and_analysis(risk: dict):
    st.subheader("EVIDENCE & ANALYSIS")
    with st.container(border=True):
        # A simple keyword categorization for the UI list
        positives = [e for e in risk.get("evidence", []) if "passed" in e or "consistent" in e or "No" in e or "verified" in e]
        negatives = [e for e in risk.get("evidence", []) if e not in positives]
        
        if positives:
            st.markdown("**Positive Indicators**")
            for p in positives: st.success(p)
        if negatives:
            st.markdown("**Warnings / Negative Indicators**")
            for n in negatives: st.error(n)

def render_officer_review(recommendation: str):
    st.subheader("OFFICER REVIEW")
    with st.container(border=True):
        st.markdown(f"**Screening Recommendation:** {recommendation}")
        st.markdown("<br/>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.button("Continue Screening", use_container_width=True)
        c2.button("Secondary Review", use_container_width=True)
        c3.button("Recapture Document", use_container_width=True)

def render_screening_information(processing: dict):
    st.subheader("SCREENING INFORMATION")
    with st.container(border=True):
        st.write(f"**Timestamp:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"**Processing Time:** {processing.get('processing_time')}s")
        st.write(f"**Pipeline Version:** {processing.get('pipeline_version')}")

# ==========================================
# MAIN EXECUTION
# ==========================================
def main():
    # Ensure session state has a default
    if "demo_scenario" not in st.session_state:
        st.session_state.demo_scenario = "LOW RISK"

    render_sidebar()
    render_header()
    
    passport_file, face_file, analyze_btn = render_upload_section()
    
    if analyze_btn:
        if not passport_file:
            st.error("Operation Blocked: Passport document is required for screening.")
            return
            
        try:
            with st.spinner("Processing document through API..."):
                # 1. Prepare files for HTTP Multipart Form upload
                files = {
                    "passport": (passport_file.name, passport_file.getvalue(), passport_file.type)
                }
                if face_file:
                    files["face"] = (face_file.name, face_file.getvalue(), face_file.type)
                
                # 2. Pass the selected scenario as form data
                data = {"scenario": st.session_state.demo_scenario}
                
                # 3. HTTP POST to FastAPI
                api_url = "http://127.0.0.1:8000/analyze"
                response = requests.post(api_url, files=files, data=data)
            
            # 4. Handle HTTP Responses
            if response.status_code == 200:
                result = response.json() # Automatically parsed into a dict
                
                # --- FULL WIDTH LAYOUT ORDER (Exactly as before) ---
                render_screening_result(result["risk_assessment"])
                render_verification_pipeline(result)
                render_document_information(result["document_info"])
                render_document_integrity(result["ocr"], result["mrz"])
                render_tampering_analysis(result["tampering"])
                render_identity_verification(result["face_verification"])
                render_evidence_and_analysis(result["risk_assessment"])
                render_officer_review(result["risk_assessment"]["recommendation"])
                render_screening_information(result["processing"])
                
            else:
                # Handle API-level errors (400, 500)
                error_detail = response.json().get("detail", "Unknown API error")
                st.error(f"API Error ({response.status_code}): {error_detail}")

        except requests.exceptions.ConnectionError:
            st.error("API Unavailable: Cannot connect to the TRINETRA backend. Ensure FastAPI is running.")
        except Exception as e:
            st.error(f"System Fault: An unexpected UI error occurred.")

if __name__ == "__main__":
    main()