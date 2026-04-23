import re
import pandas as pd
import streamlit as st
import plotly.express as px

from scraper import extract_from_html
from scraper_llm import extract_with_llm
from db_utils import (
    init_db,
    save_job_data,
    generate_content_hash,
    get_connection,
)

# ==================================================
# App Init
# ==================================================

init_db()
st.set_page_config(page_title="Certification & Skill Strategic Insights", layout="wide")
st.title("🎓 Certification & Skill Strategic Insights")

# ==================================================
# Session State
# ==================================================

if "jd_text" not in st.session_state:
    st.session_state["jd_text"] = ""
if "llm_results" not in st.session_state:
    st.session_state["llm_results"] = None

# ==================================================
# Utils
# ==================================================

URL_REGEX = r"https?://[^\s)\"]+"

def extract_urls(text):
    return re.findall(URL_REGEX, text)

def extract_job_title(text):
    blacklist = [
        "job id", "posting id", "location", "department",
        "salary", "employment type", "position type"
    ]
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("http"):
            continue
        if any(b in s.lower() for b in blacklist):
            continue
        if 10 <= len(s) <= 100:
            return s
    return "Job Posting"

# ==================================================
# Sidebar
# ==================================================

with st.sidebar:
    choice = st.radio(
        "Navigation",
        ["📈 Dashboard", "📥 Batch Import", "🤖 AI Skill Discovery"]
    )

    if st.button("⚠️ Clear All Data"):
        conn = get_connection()
        conn.execute("DELETE FROM requirements")
        conn.execute("DELETE FROM jobs")
        conn.commit()
        conn.close()
        st.rerun()

    if st.button("🧹 Clear Job Description"):
        st.session_state["jd_text"] = ""
        st.session_state["llm_results"] = None
        st.rerun()

# ==================================================
# Batch Import
# ==================================================

if choice == "📥 Batch Import":
    st.header("📥 Batch Import")

    url_input = st.text_input("Enter URL (optional)")
    jd_text = st.text_area(
        "Paste job description text",
        height=300,
        value=st.session_state["jd_text"],
    )
    st.session_state["jd_text"] = jd_text

    if st.button("Process"):
        if not jd_text or len(jd_text) < 50:
            st.error("Paste a valid job description.")
            st.stop()

        urls = extract_urls(jd_text)
        source_url = urls[0] if urls else url_input or None

        content_hash = generate_content_hash(jd_text)

        job_record = {
            "job_id": f"JD_{content_hash[:12]}",
            "title": extract_job_title(jd_text),
            "url": source_url,
            "source_type": "batch",
            "content_hash": content_hash,
        }

        certs = extract_from_html(jd_text)
        save_job_data(job_record, certs)

        st.success("Saved to dashboard.")
        st.write(certs)

# ==================================================
# AI Skill Discovery
# ==================================================

elif choice == "🤖 AI Skill Discovery":
    st.header("🤖 AI Skill Discovery")

    url_input = st.text_input("Enter URL (optional)")
    jd_text = st.text_area(
        "Paste job description text",
        height=300,
        value=st.session_state["jd_text"],
    )
    st.session_state["jd_text"] = jd_text

    if st.button("Analyze with AI"):
        if not jd_text or len(jd_text) < 50:
            st.warning("Paste a valid job description.")
        else:
            st.session_state["llm_results"] = extract_with_llm(jd_text)
            st.json(st.session_state["llm_results"])

    if st.session_state["llm_results"]:
        if st.button("Save to Dashboard"):
            content_hash = generate_content_hash(jd_text)

            job_record = {
                "job_id": f"AI_{content_hash[:12]}",
                "title": extract_job_title(jd_text),
                "url": url_input or None,
                "source_type": "ai",
                "content_hash": content_hash,
            }

            certs = st.session_state["llm_results"]
            if isinstance(certs, dict) and "certs" in certs:
                certs = certs["certs"]

            text_lower = jd_text.lower()
            certs = [
                c for c in certs
                if c.get("name", "").lower() in text_lower
            ]

            save_job_data(job_record, certs)

            st.session_state["llm_results"] = None
            st.success("Saved to dashboard.")

# ==================================================
# Dashboard
# ==================================================

elif choice == "📈 Dashboard":
    conn = get_connection()

    df = pd.read_sql(
        """
        SELECT
            j.job_id,
            j.job_title,
            j.url,
            j.date_scraped,
            r.certification
        FROM jobs j
        LEFT JOIN requirements r
        ON j.job_id = r.job_id
        """,
        conn
    )
    conn.close()

    if df.empty:
        st.info("No data available.")
        st.stop()

    df["date_scraped"] = pd.to_datetime(df["date_scraped"])
    df["certification"] = df["certification"].fillna("")

    # ---------- Time grouping ----------
    st.sidebar.markdown("---")
    st.sidebar.subheader("Time Analysis")

    time_res = st.sidebar.radio(
        "Group trends by:",
        ["Month", "Quarter", "Year"],
        index=0
    )

    res_map = {
        "Month": "M",
        "Quarter": "Q",
        "Year": "Y",
    }

    df["period"] = df["date_scraped"].dt.to_period(
        res_map[time_res]
    ).astype(str)

    # ---------- Executive Summary ----------
    summary = (
        df[df["certification"] != ""]
        ["certification"]
        .value_counts()
        .reset_index()
    )
    summary.columns = ["Certification / Skill", "Total Mentions"]

    st.subheader("Executive Summary")
    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True
    )

    fig = px.bar(
        summary,
        x="Total Mentions",
        y="Certification / Skill",
        orientation="h",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---------- Trend Chart ----------
    with st.expander("📈View demand trends over time", expanded=False):
        trend_df = (
            df[df["certification"] != ""]
            .groupby(["period", "certification"])
            .size()
            .reset_index(name="count")
        )

        fig_trend = px.bar(
            trend_df,
            x="period",
            y="count",
            color="certification",
            barmode="group",
        )

        st.plotly_chart(fig_trend, use_container_width=True)

   
    # ---------- UI Style for Drill‑Down Tables ----------
    st.markdown(
        """
        <style>
        /* DataFrame font consistency */
        div[data-testid="stDataFrame"] table {
            font-size: 0.95rem;
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI",
                        Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        /* Header row */
        div[data-testid="stDataFrame"] thead th {
            font-weight: 600;
            font-size: 0.95rem;
        }

        /* Row height */
        div[data-testid="stDataFrame"] tbody td {
            line-height: 1.4;
            padding-top: 0.4rem;
            padding-bottom: 0.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


     # ---------- Drill Down ----------
    cert_options = ["All"] + summary["Certification / Skill"].tolist()
    st.markdown("### 🔍 Drill down by certification")

    selected = st.selectbox(
        label="",
        options=cert_options
    )
    

    conn = get_connection()
    if selected == "All":
        drill_df = pd.read_sql(
            """
            SELECT
                j.job_id,
                j.job_title,
                j.url,
                j.date_scraped,
                COALESCE(GROUP_CONCAT(r.certification, ', '), '') AS Certifications
            FROM jobs j
            LEFT JOIN requirements r
            ON j.job_id = r.job_id
            GROUP BY j.job_id, j.job_title, j.url, j.date_scraped
            ORDER BY j.date_scraped DESC;
            """,
            conn
        )
        title = "📄 All jobs in dataset"
    else:
        drill_df = pd.read_sql(
            """
            SELECT
                j.job_id,
                j.job_title,
                j.url,
                j.date_scraped,
                GROUP_CONCAT(r.certification, ', ') AS Certifications
            FROM jobs j
            JOIN requirements r
            ON j.job_id = r.job_id
            WHERE r.certification = ?
            GROUP BY j.job_id, j.job_title, j.url, j.date_scraped
            ORDER BY j.date_scraped DESC;
            """,
            conn,
            params=(selected,)
        )
        title = f"📄 Jobs mentioning '{selected}'"
    conn.close()

    with st.expander(f"**{title}**", expanded=True):
        if drill_df.empty:
            st.info("No jobs found.")
        else:
            drill_df["Job Ref"] = drill_df["job_id"].str[-6:]
            drill_df["Date"] = pd.to_datetime(drill_df["date_scraped"]).dt.date
            drill_df["Link"] = drill_df["url"].fillna("")

            cols = ["Job Ref", "job_title", "Certifications", "Date", "Link"]

            st.dataframe(
                drill_df[cols].rename(columns={"job_title": "Job Title"}),
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇️ Export jobs to CSV",
                drill_df[cols]
                .rename(columns={"job_title": "Job Title"})
                .to_csv(index=False),
                file_name="jobs_export.csv",
                mime="text/csv",
            )