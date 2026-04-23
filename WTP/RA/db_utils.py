import os
import re
import sqlite3
import hashlib

from normalization import (
    normalize_cert_name,
    apply_cloud_precedence,
)

# --------------------------------------------------
# Option 2: Normalize core job text BEFORE hashing
# --------------------------------------------------

def normalize_job_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    boilerplate_patterns = [
        r"equal opportunity employer.*$",
        r"we are an equal opportunity.*$",
        r"all qualified applicants.*$",
        r"how to apply.*$",
        r"apply now.*$",
        r"accommodation available.*$",
        r"privacy statement.*$",
        r"terms and conditions.*$",
        r"benefits include.*$",
        r"salary.*benefits.*$",
    ]

    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text)

    return text.strip()


def generate_content_hash(text: str) -> str:
    core_text = normalize_job_text(text)
    return hashlib.sha256(core_text.encode("utf-8")).hexdigest()

# --------------------------------------------------
# Database setup
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "job_market_research_v2.db")


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            job_title TEXT,
            organization TEXT,
            url TEXT,                      -- ✅ NOT UNIQUE
            source_type TEXT,
            content_hash TEXT UNIQUE,      -- ✅ job identity
            date_scraped DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            certification TEXT NOT NULL,
            requirement_level TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        );
        """)

        conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_job_cert
        ON requirements (job_id, certification);
        """)

# --------------------------------------------------
# Persist job + certifications safely
# --------------------------------------------------


def save_job_data(job_record, cert_list):
    with get_connection() as conn:

        # 1. Insert job safely (dedup by content_hash)
        conn.execute(
            """
            INSERT OR IGNORE INTO jobs (
                job_id,
                job_title,
                url,
                source_type,
                content_hash
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                job_record["job_id"],
                job_record.get("title"),
                job_record.get("url"),
                job_record.get("source_type"),
                job_record.get("content_hash"),
            )
        )

        # 2. Resolve canonical job_id
        row = conn.execute(
            "SELECT job_id FROM jobs WHERE content_hash = ?",
            (job_record["content_hash"],)
        ).fetchone()

        if row is None:
            raise RuntimeError("Job row not found after insert")

        job_id = row[0]

        # 3. Normalize certifications (supports BOTH Batch & AI)
        normalized_certs = []

        for cert in cert_list:
            # Batch Import → string
            if isinstance(cert, str):
                cert_name = cert.strip()

            # AI Discovery → dict
            elif isinstance(cert, dict) and "name" in cert:
                cert_name = cert["name"].strip()

            else:
                continue  # skip unexpected shapes safely

            if cert_name:
                normalized_certs.append(normalize_cert_name(cert_name))

        # 4. Apply precedence + deduplicate
        normalized_certs = apply_cloud_precedence(normalized_certs)
        normalized_certs = list(set(normalized_certs))

        # 5. Insert into requirements
        for cert_name in normalized_certs:
            conn.execute(
                """
                INSERT OR IGNORE INTO requirements (
                    job_id,
                    certification,
                    requirement_level
                ) VALUES (?, ?, ?)
                """,
                (
                    job_id,
                    cert_name,
                    "mentioned",
                )
            )
