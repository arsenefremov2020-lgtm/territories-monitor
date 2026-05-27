import os
import hashlib
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from bs4 import BeautifulSoup
from urllib.parse import urljoin

DATABASE_URL = os.environ["DATABASE_URL"]
PRINT_URL = "https://zakon.rada.gov.ua/laws/show/z0380-25/print"

engine = create_engine(DATABASE_URL)


def get_docx_url():
    html = requests.get(PRINT_URL, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.endswith(".docx"):
            return urljoin(PRINT_URL, href)

    raise Exception("DOCX link not found")


def save_document_record(docx_url):
    response = requests.get(docx_url, timeout=60)
    response.raise_for_status()

    file_hash = hashlib.sha256(response.content).hexdigest()

    with engine.begin() as conn:
        existing = conn.execute(
            text("select id from documents where file_hash = :file_hash"),
            {"file_hash": file_hash},
        ).fetchone()

        if existing:
            print("Document already exists, no new record created")
            return

        conn.execute(
            text("""
                insert into documents
                (source_name, source_url, document_number, document_date, file_hash)
                values
                (:source_name, :source_url, :document_number, :document_date, :file_hash)
            """),
            {
                "source_name": "Верховна Рада України / zakon.rada.gov.ua",
                "source_url": docx_url,
                "document_number": "376",
                "document_date": "2025-02-28",
                "file_hash": file_hash,
            },
        )

    print("New document saved")


if __name__ == "__main__":
    docx_url = get_docx_url()
    print("DOCX URL:", docx_url)
    save_document_record(docx_url)
