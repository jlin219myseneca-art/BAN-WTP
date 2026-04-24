import requests
from bs4 import BeautifulSoup
import re



# Added a more comprehensive list
CERT_REGEX = {

    # ==========================
    # Project Management
    # ==========================
    "PMP": r"\bpmp\b|project management professional|\bpmbok\b",

    # ==========================
    # Agile / Scrum
    # ==========================
    "Agile/Scrum": (
        r"\bscrum\b|"
        r"\bkanban\b|"
        r"\bsafe\b|"
        r"scaled agile framework|"
        r"certified scrum master|"
        r"scrum master certification"
    ),

    # ==========================
    # IT Service Management
    # ==========================
    "ITIL": r"\bitil\b|information technology infrastructure library",

    # ==========================
    # Security
    # ==========================
    "CISSP": r"\bcissp\b|certified information systems security professional",

    # ==========================
    # Cloud – Vendor Specific
    # ==========================
    "AWS": (
        r"\baws\b|"
        r"amazon web services|"
        r"aws certified|"
        r"solutions architect"
    ),

    "Azure": (
        r"\bazure\b|"
        r"microsoft azure|"
        r"\baz-900\b|"
        r"\baz-104\b|"
        r"\baz-305\b"
    ),

    # ==========================
    # Cloud – Vendor Neutral
    # ==========================
    "Cloud Platforms": (
        r"cloud platform(s)?|"
        r"cloud computing|"
        r"cloud infrastructure|"
        r"multi-?cloud|"
        r"hybrid cloud|"
        r"\bgcp\b|"
        r"google cloud"
    ),

    # ==========================
    # Data & Analytics
    # ==========================
    "Data Science/Analytics": (
        r"data science|"
        r"data analytics|"
        r"predictive analytics|"
        r"statistical modeling|"
        r"data analysis"
    ),

    # ==========================
    # Programming Languages
    # ==========================
    "Python": r"\bpython\b",

    "R": r"\br\b|\br language\b|\br programming\b",

    # ==========================
    # AI / Machine Learning
    # ==========================
    "AI/ML": (
        r"artificial intelligence|"
        r"machine learning|"
        r"deep learning|"
        r"neural networks|"
        r"\bllm\b|"
        r"natural language processing|\bnlp\b"
    ),

    # ==========================
    # Business Analysis
    # ==========================
    "Business Analysis": (
        r"\bcbap\b|"
        r"\bpmi-pba\b|"
        r"business analysis|"
        r"business analyst"
    ),

    # ==========================
    # Data / BI Tools
    # ==========================
    "Data Tools": (
        r"power bi|"
        r"tableau|"
        r"\bsql\b(?!\w)|"
        r"snowflake|"
        r"\bsas\b"
    ),

    # ==========================
    # Geospatial (FIXED)
    # ==========================
    "Geospatial": (
        r"\bgis\b|"
        r"geospatial|"
        r"\barcgis\b|"
        r"\bqgis\b"
    ),


    # ==========================
    # Finance Certifications
    # ==========================
    "CPA": (
        r"\bcpa\b|"
        r"chartered professional accountant"
    ),

    "CFA": (
        r"\bcfa\b|"
        r"chartered financial analyst"
    ),

}

import requests
from bs4 import BeautifulSoup

def fetch_url(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return True, response.text # Return Success + Content
        else:
            return False, f"Status Code: {response.status_code}"
    except Exception as e:
        return False, str(e)

def extract_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    # Keep the text as is (don't force lowercase here if you want to use IGNORECASE)
    text = soup.get_text(separator=" ")
    text = " ".join(text.split()) 
    
    found_certs = []
    seen = set()
    
    for cert, pattern in CERT_REGEX.items():
        # re.IGNORECASE makes sure 'PMP' matches 'pmp' or 'PMP'
        match = re.search(pattern, text, re.IGNORECASE) 
        print(f"Checking {cert}: Found? {bool(match)}") 
        
        if match:
            if cert not in seen:
                found_certs.append({"name": cert, "level": "mentioned"})
                seen.add(cert)
    return found_certs