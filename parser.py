import os
import hashlib
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from docx import Document
from io import BytesIO

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


def download_docx(docx_url):
    response = requests.get(docx_url, timeout=60)
    response.raise_for_status()

    file_hash = hashlib.sha256(response.content).hexdigest()

    return response.content, file_hash


def extract_docx_tables(docx_content):
    document = Document(BytesIO(docx_content))

    print("Tables found:", len(document.tables))

    for i, table in enumerate(document.tables):
        print("TABLE", i + 1, "ROWS:", len(table.rows), "COLS:", len(table.columns))

        for row in table.rows[:5]:
            values = [cell.text.replace("\n", " ").strip() for cell in row.cells]
            print(values)


if __name__ == "__main__":
    docx_url = get_docx_url()
    print("DOCX URL:", docx_url)

    docx_content, file_hash = download_docx(docx_url)
    print("File hash:", file_hash)

    extract_docx_tables(docx_content)
