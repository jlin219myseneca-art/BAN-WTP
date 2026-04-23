"""
Canonical normalization library for certifications and skills.

Purpose:
- Collapse equivalent names into canonical buckets
- Ensure consistent analytics & dashboards
- Prevent LLM / scraper variability from polluting data

Rule:
- The CANONICAL KEY is what appears in the dashboard
- Aliases are matched via substring (case-insensitive)
"""

CERT_NORMALIZATION_MAP = {

    # ==================================================
    # PROJECT & PROGRAM MANAGEMENT
    # ==================================================
    "PMP": [
        "pmp",
        "project management professional",
        "project management certification",
        "pm certification",
        "pmi certification",
    ],

    "Prince2": [
        "prince2",
        "prince ii",
        "projects in controlled environments",
    ],

    "CBAP": [
        "cbap",
        "certified business analysis professional",
        "business analysis certification",
    ],

    # ==================================================
    # AGILE / SCRUM / DELIVERY
    # ==================================================
    "Agile/Scrum": [
        "agile",
        "scrum",
        "certified scrum master",
        "professional scrum master",
        "csm",
        "psm",
        "safe",
        "scaled agile framework",
        "agile certification",
        "scrum master",
    ],

    # ==================================================
    # CLOUD – VENDOR NEUTRAL
    # ==================================================
    "Cloud Platforms": [
        "cloud platform",
        "cloud platforms",
        "cloud computing",
        "cloud experience",
        "multi-cloud",
        "hybrid cloud",
        "cloud infrastructure",
    ],


    # ==================================================
    # DATA & ANALYTICS
    # ==================================================
    "Data Analytics": [
        "data analytics",
        "data analysis",
        "business intelligence",
        "bi tools",
        "analytics",
    ],

    "SQL": [
        "sql",
        "structured query language",
        "tsql",
        "pl/sql",
    ],

    "Power BI": [
        "power bi",
        "microsoft power bi",
        "powerbi",
    ],

    "Tableau": [
        "tableau",
        "tableau desktop",
        "tableau server",
    ],

    # ==================================================
    # DATA SCIENCE & AI
    # ==================================================
    "Data Science": [
        "data science",
        "data scientist",
        "predictive analytics",
        "modeling",
    ],

    "Machine Learning": [
        "machine learning",
        "ml",
        "deep learning",
        "neural networks",
    ],

    "Artificial Intelligence": [
        "artificial intelligence",
        "ai",
        "llm",
        "large language model",
        "nlp",
        "natural language processing",
    ],

    # ==================================================
    # SOFTWARE / DEVELOPMENT
    # ==================================================
    "Python": [
        "python",
        "python programming",
    ],

    "R": [
        " r ",
        " r language",
        " r programming",
    ],

    "DevOps": [
        "devops",
        "ci/cd",
        "continuous integration",
        "continuous deployment",
        "infrastructure as code",
    ],

    # ==================================================
    # IT SERVICE MANAGEMENT & SECURITY
    # ==================================================
    "ITIL": [
        "itil",
        "information technology infrastructure library",
    ],

    "CISSP": [
        "cissp",
        "certified information systems security professional",
    ],

    "Cybersecurity": [
        "cybersecurity",
        "information security",
        "infosec",
        "security engineering",
    ],

    # ==================================================
    # GEOSPATIAL
    # ==================================================
    "Geospatial": [
        "geospatial",
        "gis",
        "geographic information systems",
        "arcgis",
        "qgis",
    ],
}



def normalize_cert_name(name: str) -> str:
    if not name:
        return name

    name_lower = name.lower().strip()

    for canonical, aliases in CERT_NORMALIZATION_MAP.items():
        if name_lower == canonical.lower():
            return canonical

        for alias in aliases:
            if alias in name_lower:
                return canonical

    return name

def apply_cloud_precedence(cert_names: list[str]) -> list[str]:
    """
    If vendor-specific cloud certs exist (Azure/AWS/GCP),
    remove generic 'Cloud Platforms' to avoid double counting.
    """
    vendor_clouds = {"Azure", "AWS", "GCP"}

    has_vendor_cloud = any(cert in vendor_clouds for cert in cert_names)

    if has_vendor_cloud:
        cert_names = [
            cert for cert in cert_names
            if cert != "Cloud Platforms"
        ]

    return cert_names