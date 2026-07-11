import os
import pytesseract
from pdf2image import convert_from_path

# Windows Poppler BIN folder
POPPLER_PATH = r"C:\Users\Nadir\Downloads\Release-26.02.0-0\poppler-26.02.0\Library\bin"

# Optional: Tesseract path (agar PATH me nahi hai to)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text(file_path: str):
    """
    Extract text from PDF using Poppler + Tesseract OCR
    """

    if not os.path.exists(file_path):
        raise Exception(f"PDF file not found: {file_path}")

    if not os.path.exists(POPPLER_PATH):
        raise Exception(f"Poppler folder not found: {POPPLER_PATH}")

    pages = convert_from_path(
        file_path,
        dpi=300,
        poppler_path=POPPLER_PATH
    )

    text = ""

    for page in pages:
        text += pytesseract.image_to_string(page)
        text += "\n"

    return text.strip()