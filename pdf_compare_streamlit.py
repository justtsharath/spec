import streamlit as st
from difflib import SequenceMatcher
from PyPDF2 import PdfReader
import re

# Regular expression to capture test name, limit, and result from lines
ENTRY_RE = re.compile(
    r"^(?P<test>[\w\s/]+)\s+(?P<limit>[\d\.\–\%\s]+)\s+(?P<result>[\d\.\%\s]+)$"
)

@st.cache_data
def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extracts and concatenates text from all pages of a PDF file.
    """
    reader = PdfReader(uploaded_file)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)

def highlight_differences(text1: str, text2: str, threshold: float = 0.9):
    """
    Prints best fuzzy match and its ratio for each non-empty line in text1 against text2.
    """
    for line1 in filter(None, (l.strip() for l in text1.splitlines())):
        best_ratio = 0.0
        best_line2 = None
        for line2 in filter(None, (l.strip() for l in text2.splitlines())):
            ratio = SequenceMatcher(None, line1.lower(), line2.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_line2 = line2
        st.write(f"Comparing ▶️ '{line1}'")
        st.write(f"  Best match ▶️ '{best_line2}' (ratio={best_ratio:.3f})")
        if best_ratio < threshold:
            st.error(f"❌ Below threshold ({threshold}) for: '{line1}' -> '{best_line2}' (ratio={best_ratio:.3f})")

def parse_entries(text: str) -> dict:
    """
    Parses lines matching ENTRY_RE into a dict of test -> {limit, result}.
    """
    data = {}
    for line in text.splitlines():
        m = ENTRY_RE.match(line.strip())
        if m:
            test_name = m.group("test").strip().lower()
            data[test_name] = {
                "limit": m.group("limit").strip(),
                "result": m.group("result").strip()
            }
    return data

def compare_structured(fps_data: dict, coa_data: dict):
    """
    Compares structured FPS vs CoA data and logs mismatches or successes.
    """
    any_errors = False
    for test, spec in fps_data.items():
        coa_spec = coa_data.get(test)
        if not coa_spec:
            st.error(f"❌ Missing in CoA: {test}")
            any_errors = True
            continue
        # Compare limits exactly
        if spec["limit"] != coa_spec["limit"]:
            st.error(f"❌ Limit mismatch for '{test}': FPS={spec['limit']} vs CoA={coa_spec['limit']}")
            any_errors = True
        else:
            st.success(f"✅ Limit match for '{test}': {spec['limit']}")
        # Compare results/reportrange or numerical as needed
        st.write(f"   ▶ Result FPS={spec['result']} | CoA={coa_spec['result']}")

    if not any_errors:
        st.success("🎉 All specified tests and limits match exactly.")

# --- Streamlit App ---
st.title("CoA vs. Finished Product Spec Comparison")
st.write("Upload your Certificate of Analysis (CoA) and Finished Product Spec (FPS) PDFs to compare test names, limits, and results.")

coa_file = st.file_uploader("Upload CoA PDF", type="pdf")
fps_file = st.file_uploader("Upload FPS PDF", type="pdf")
threshold = st.slider("Fuzzy-match threshold", min_value=0.5, max_value=1.0, value=0.9, step=0.05)

if coa_file and fps_file:
    # 1. Extract text
    coa_text = extract_text_from_pdf(coa_file)
    fps_text = extract_text_from_pdf(fps_file)

    # 2. (Optional) Debug snippets
    with st.expander("Show raw text snippets for debugging"):
        st.write("--- CoA snippet ---")
        st.write(coa_text[:500])
        st.write("--- FPS snippet ---")
        st.write(fps_text[:500])

    # 3. Fuzzy-match diagnostics
    with st.expander("Fuzzy-match diagnostics"):
        highlight_differences(fps_text, coa_text, threshold)

    # 4. Structured parse & compare
    fps_data = parse_entries(fps_text)
    coa_data = parse_entries(coa_text)
    compare_structured(fps_data, coa_data)
else:
    st.info("Please upload both PDF files to begin comparison.")
