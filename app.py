import streamlit as st
from PIL import Image
import time
import random
from SecurityEngine import SecurityEngine
def set_aesthetic():
    """Applies a professional, high-contrast security theme."""
    st.set_page_config(
        page_title="TRINETRA | AI Screening",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def main():
    set_aesthetic()

    st.title("🛡️ TRINETRA")
    st.markdown("**SIH26188** | AI-Assisted Passport & Identity Screening System")
    st.divider()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("Officer Terminal")
        st.caption("Active Session: Officer ID #492")
        
        st.subheader("1. Primary Document")
        passport_file = st.file_uploader("Upload Passport Page (JPEG/PNG)", type=['jpg', 'jpeg', 'png'])
        
        st.subheader("2. Live Capture (Optional)")
        face_file = st.file_uploader("Upload Live Face Photo", type=['jpg', 'jpeg', 'png'])
        
        analyze_btn = st.button("Run Security Analysis", type="primary", use_container_width=True)

    # --- MAIN LAYOUT ---
    if not passport_file:
        st.info("Awaiting document upload. Please use the terminal on the left to begin screening.")
        return

    # Split screen: Left for input preview, Right for results
    col_preview, col_results = st.columns([1, 2], gap="large")

    with col_preview:
        st.subheader("Document Preview")
        passport_img = Image.open(passport_file)
        st.image(passport_img, caption="Scanned Document", use_container_width=True)
        
        if face_file:
            face_img = Image.open(face_file)
            st.image(face_img, caption="Live Capture", width=150)
        else:
            face_img = None

    with col_results:
        if analyze_btn:
            with st.spinner("Analyzing document security features..."):
                results = SecurityEngine.analyze_document(passport_img, face_img)
            
            # --- RISK ASSESSMENT HEADER ---
            risk = results["risk_assessment"]
            if risk["risk_level"] == "CLEARED":
                st.success(f"### Assessment: {risk['risk_level']} (Score: {risk['overall_score']}/100)")
            else:
                st.error(f"### Assessment: {risk['risk_level']} (Score: {risk['overall_score']}/100)")
            
            st.markdown(f"**Evidence:** {', '.join(risk['evidence'])}")
            
            # --- TABS FOR DETAILED RESULTS ---
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Identity Data", "MRZ & OCR", "Tampering / ELA", "Face Auth", "Officer Actions"
            ])
            
            with tab1:
                st.subheader("Extracted Document Information")
                doc = results["document_info"]
                c1, c2, c3 = st.columns(3)
                c1.metric("Doc Type", doc["document_type"])
                c2.metric("Country", doc["issuing_country"])
                c3.metric("Doc Number", doc["document_number"])
                
                c4, c5 = st.columns(2)
                c4.metric("Surname", doc["surname"])
                c5.metric("Given Names", doc["given_names"])
                
            with tab2:
                st.subheader("Machine Readable Zone")
                mrz = results["mrz"]
                ocr = results["ocr"]
                
                st.code(ocr["extracted_text"], language="text")
                st.progress(ocr["confidence_score"] / 100, text=f"OCR Confidence: {ocr['confidence_score']}%")
                
                if mrz["is_valid"]:
                    st.success(f"MRZ Valid: {mrz['checksums_passed']}/{mrz['total_checksums']} Checksums Passed")
                else:
                    st.error("MRZ Validation Failed!")
                    
            with tab3:
                st.subheader("Image Anomaly Detection")
                tamper = results["tampering"]
                st.metric("Error Level Analysis (ELA) Risk", f"{tamper['ela_score']:.2f}")
                if tamper["tampering_detected"]:
                    st.error(f"⚠️ Anomalies Found: {', '.join(tamper['anomalies'])}")
                else:
                    st.success("No visual tampering detected.")
                    
            with tab4:
                st.subheader("Biometric Verification")
                face = results["face_verification"]
                if face["provided"]:
                    st.metric("Face Match Score", f"{face['match_score']:.1f}%")
                    if face["is_match"]:
                        st.success("Live face matches passport photograph.")
                    else:
                        st.error("Face mismatch. Manual verification required.")
                else:
                    st.warning("No live capture provided for biometric verification.")
                    
            with tab5:
                st.subheader("System Recommendation")
                if risk["risk_level"] == "CLEARED":
                    st.success("**PROCEED:** Document appears authentic. Passenger may proceed.")
                else:
                    st.error("**INTERCEPT:** Flagged for secondary inspection. Do not process automatically.")
                    
                st.button("Print Evidence Report", use_container_width=True)

if __name__ == "__main__":
    main()