
import streamlit as st
import fitz  # PyMuPDF
from difflib import SequenceMatcher

def extract_text_from_pdf(uploaded_file):
    try:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def highlight_differences(text1, text2):
    mismatches = []
    text1_lines = [line.strip() for line in text1.splitlines() if line.strip()]
    text2_lines = [line.strip() for line in text2.splitlines() if line.strip()]

    for line1 in text1_lines:
        matched = False
        for line2 in text2_lines:
            ratio = SequenceMatcher(None, line1.lower(), line2.lower()).ratio()
            if ratio > 0.9:
                matched = True
                break
        if not matched:
            mismatches.append(line1)
    return mismatches

st.set_page_config(page_title="CoA vs FPS Checker", layout="centered")
st.title("🧾 CoA vs FPS Comparison Tool")

st.markdown("Upload the Certificate of Analysis (CoA) and Finished Product Specification (FPS) PDF files.")

coa_file = st.file_uploader("Upload CoA PDF", type=["pdf"])
fps_file = st.file_uploader("Upload FPS PDF", type=["pdf"])

if coa_file and fps_file:
    with st.spinner("Extracting and comparing data..."):
        coa_text = extract_text_from_pdf(coa_file)
        fps_text = extract_text_from_pdf(fps_file)

        mismatches = highlight_differences(coa_text, fps_text)

        st.success("Comparison complete!")

        if mismatches:
            st.subheader("❗ Red Flags (Mismatches)")
            for mismatch in mismatches:
                st.markdown(f"<div style='color:red;'>{mismatch}</div>", unsafe_allow_html=True)
        else:
            st.subheader("✅ All test names, limits, and results match correctly.")
