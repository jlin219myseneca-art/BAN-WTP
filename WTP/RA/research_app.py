import streamlit as st
import pandas as pd
from scraper_llm import extract_with_llm
from db_utils import init_db, save_job_data

init_db()

st.set_page_config(page_title="AI Skill Discovery", layout="wide")
st.title("🤖 AI-Powered Skill Discovery")

input_type = st.radio("Input method:", ["URL", "Paste Text"])

if input_type == "URL":
    jd_input = st.text_input("Paste Job URL:")
else:
    jd_input = st.text_area("Paste Job Description Text:", height=300)

# -----------------------------
# Analyze
# -----------------------------
if st.button("Analyze with AI"):
    if jd_input:
        with st.spinner("AI is analyzing..."):
            try:
                results = extract_with_llm(jd_input)
                st.session_state["llm_results"] = results
                st.json(results)
            except Exception as e:
                st.error(f"Error: {e}")


# -------------------------------------------------
# SAVE TO DATABASE (safe across Streamlit reruns)
# -------------------------------------------------
if "llm_results" in st.session_state and st.session_state["llm_results"]:

    if st.button("Save to Dashboard Database"):

        job_id = f"AI_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"

        job_record = {
            "job_id": job_id,
            "title": "AI Research",
            "url": None,          # ✅ NULL avoids UNIQUE conflicts
            "source_type": "llm"
        }

        try:
            save_job_data(job_record, st.session_state["llm_results"])
            st.success("✅ Saved to database!")

            # Optional: prevent accidental re‑save
            st.session_state["llm_results"] = None

        except Exception as e:
            st.error(f"❌ Failed to save: {e}")
