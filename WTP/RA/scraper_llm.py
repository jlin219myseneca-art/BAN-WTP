import openai
import json
import streamlit as st
import requests
from bs4 import BeautifulSoup

def get_text_from_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    # Clean the text
    text = soup.get_text(separator=" ").strip()
    return text


def remove_standalone_urls(text: str) -> str:
    lines = text.splitlines()
    cleaned = [
        line for line in lines
        if not line.strip().startswith("http")
    ]
    return "\n".join(cleaned)

def extract_with_llm(text_or_url: str):

    stripped = text_or_url.strip()

    # ✅ URL-only mode
    if stripped.startswith("http") and len(stripped.split()) == 1:
        text = get_text_from_url(stripped)
    else:
        text = text_or_url

    # ✅ NEW: remove standalone URL lines from JD text
    text = remove_standalone_urls(text)

    # --- proceed with LLM ---
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    
    prompt = f"""
    Analyze the following Job Description.

    Extract professional certifications and qualifications.

    IMPORTANT CONSTRAINTS:

    • Only extract certifications that are explicitly stated in the job description text.
    • Do NOT infer or assume certifications based on role seniority, responsibilities, or industry.
    • Do NOT add certifications that would be “nice to have” unless they are clearly mentioned.
    • If a certification name does not appear verbatim or as a clear abbreviation in the text, do not include it.
    • Examples such as Lean Six Sigma, PMP, or Agile certifications must be ignored unless explicitly present in the text.

    IMPORTANT RULE:
    If a term includes a belt level (e.g., "Green Belt", "Black Belt"),
    treat it as a certification.

    Return ONLY valid JSON in this exact format:
    {{
    "certs": [
        {{ "name": "Certification Name", "level": "Required/Preferred" }}
    ]
    }}

    Job Description:
    {text[:5000]}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    data = json.loads(response.choices[0].message.content)
    return data.get("certs", [])