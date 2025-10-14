# app/utils.py
from pypdf import PdfReader # type: ignore
from typing import List
import os

def extract_text_from_pdf(path: str) -> str:
    text = []
    reader = PdfReader(path)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)
    return "\n".join(text)

def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext in {".txt", ".md"}:
        return read_text_file(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")