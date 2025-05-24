
import streamlit as st
from difflib import SequenceMatcher
from PyPDF2 import PdfReader
import re
import numpy as np

# Flexible regex for parsing test name, limit, and result
ENTRY_RE = re.compile(r"^(?P<test>.+?)\s{2,}(?P<limit>.+?)\s{2,}(?P<result>.+)$")

@st.cache_data
def extract_text_from_pdf(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(text)
        else:
            st.warning(f"No text found on page {i + 1}")
    return "\n".join(pages)

def highlight_differences(text1: str, text2: str, threshold: float = 0.9):
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
    data = {}
    for line in text.splitlines():
        m = ENTRY_RE.match(line.strip())
        if m:
            test_name = m.group("test").strip().lower()
            data[test_name] = {
                "original_name": m.group("test").strip(),
                "limit": m.group("limit").strip(),
                "result": m.group("result").strip()
            }
    return data

def is_within_limit(limit: str, result: str):
    try:
        limit_value = float(re.findall(r"[\d\.]+", limit)[-1])
        result_value = float(re.findall(r"[\d\.]+", result)[-1])
        if "NMT" in limit.upper() or "≤" in limit:
            return result_value <= limit_value
        elif "NLT" in limit.upper() or "≥" in limit:
            return result_value >= limit_value
        return np.isclose(result_value, limit_value, atol=0.01)
    except Exception:
        return None

def compare_structured(fps_data: dict, coa_data: dict):
    any_errors = False
    for test, spec in fps_data.items():
        coa_spec = coa_data.get(test)
        if not coa_spec:
            st.error(f"❌ Missing in CoA: {spec['original_name']}")
            any_errors = True
            continue
        if spec["limit"] != coa_spec["limit"]:
            st.error(f"❌ Limit mismatch for '{spec['original_name']}': FPS={spec['limit']} vs CoA={coa_spec['limit']}")
            any_errors = True
        else:
            st.success(f"✅ Limit match for '{spec['original_name']}': {spec['limit']}")

        st.write(f"   ▶ Result FPS={spec['result']} | CoA={coa_spec['result']}")
        oos_check = is_within_limit(spec["limit"], coa_spec["result"])
        if oos_check is False:
            st.error(f"❌ OOS for '{spec['original_name']}': Result {coa_spec['result']} not within limit {spec['limit']}")
            any_errors = True
        elif oos_check is None:
            st.warning(f"⚠️ Could not determine OOS status for '{spec['original_name']}'")
        else:
            st.success(f"✅ Result within limit for '{spec['original_name']}'")

    if not any_errors:
        st.success("🎉 All specified tests and limits match exactly.")

# Streamlit UI
st.title("CoA vs. Finished Product Spec Comparison")
st.write("Upload your Certificate of Analysis (CoA) and Finished Product Spec (FPS) PDFs to compare test names, limits, and results.")

coa_file = st.file_uploader("Upload CoA PDF", type="pdf")
fps_file = st.file_uploader("Upload FPS PDF", type="pdf")
threshold = st.slider("Fuzzy-match threshold", min_value=0.5, max_value=1.0, value=0.9, step=0.05)

if coa_file and fps_file:
    coa_text = extract_text_from_pdf(coa_file)
    fps_text = extract_text_from_pdf(fps_file)

    with st.expander("Show raw text snippets for debugging"):
        st.write("--- CoA snippet ---")
        st.write(coa_text[:500])
        st.write("--- FPS snippet ---")
        st.write(fps_text[:500])

    with st.expander("Fuzzy-match diagnostics"):
        highlight_differences(fps_text, coa_text, threshold)

    fps_data = parse_entries(fps_text)
    coa_data = parse_entries(coa_text)
    compare_structured(fps_data, coa_data)

else:
    st.info("Please upload both PDF files to begin comparison.")
