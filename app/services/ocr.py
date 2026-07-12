"""
CAFlow OCR Service
Enterprise-grade text extraction from invoice PDFs and images.
"""

import os
import shutil
import logging
from pathlib import Path

import pytesseract
from PIL import Image
from pdf2image import convert_from_path

logger = logging.getLogger("caflow.ocr")

SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
SUPPORTED_PDF_EXTS = {".pdf"}


def _resolve_tesseract_cmd() -> str:
    env_path = os.getenv("TESSERACT_CMD")
    if env_path and Path(env_path).exists():
        return env_path

    found = shutil.which("tesseract")
    if found:
        return found

    windows_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.name == "nt" and Path(windows_default).exists():
        return windows_default

    raise RuntimeError(
        "Tesseract binary not found. Set TESSERACT_CMD env var, install tesseract "
        "and ensure it's on PATH, or install to the default Windows location."
    )


def _resolve_poppler_path() -> str | None:
    env_path = os.getenv("POPPLER_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    if shutil.which("pdftoppm"):
        return None

    if os.name == "nt":
        raise RuntimeError(
            "Poppler not found. Install Poppler for Windows and set POPPLER_PATH "
            "to its 'bin' directory, or add it to PATH."
        )

    raise RuntimeError(
        "Poppler (pdftoppm) not found on PATH. On Render/Linux this should be "
        "installed via the Dockerfile (poppler-utils)."
    )


pytesseract.pytesseract.tesseract_cmd = _resolve_tesseract_cmd()


def _ocr_image(image: Image.Image) -> str:
    return pytesseract.image_to_string(image, lang="eng")


def _extract_from_pdf(file_path: str) -> str:
    poppler_path = _resolve_poppler_path()
    pages = convert_from_path(
        file_path,
        dpi=300,
        poppler_path=poppler_path,
    )

    if not pages:
        raise ValueError(f"No pages could be rendered from PDF: {file_path}")

    text_chunks = []
    for i, page in enumerate(pages, start=1):
        page_text = _ocr_image(page)
        text_chunks.append(f"--- Page {i} ---\n{page_text.strip()}")

    return "\n\n".join(text_chunks)


def _extract_from_image(file_path: str) -> str:
    with Image.open(file_path) as img:
        return _ocr_image(img).strip()


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()

    try:
        if ext in SUPPORTED_PDF_EXTS:
            text = _extract_from_pdf(file_path)
        elif ext in SUPPORTED_IMAGE_EXTS:
            text = _extract_from_image(file_path)
        else:
            raise ValueError(
                f"Unsupported file type '{ext}'. Supported: "
                f"{sorted(SUPPORTED_PDF_EXTS | SUPPORTED_IMAGE_EXTS)}"
            )
    except (FileNotFoundError, ValueError, RuntimeError):
        raise
    except Exception as e:
        logger.exception("OCR extraction failed for %s", file_path)
        raise RuntimeError(f"OCR extraction failed: {e}") from e

    if not text.strip():
        logger.warning("OCR produced empty text for %s", file_path)

    return text