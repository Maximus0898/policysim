import io
import logging
import pdfplumber
from docx import Document
from typing import Optional

logger = logging.getLogger(__name__)

def extract_text_from_file(file_bytes: bytes, filename: str) -> Optional[str]:
    """
    Extracts plain text from PDF, DOCX, or TXT files.
    """
    ext = filename.split(".")[-1].lower()
    
    try:
        if ext == "pdf":
            return _extract_from_pdf(file_bytes)
        elif ext == "docx":
            return _extract_from_docx(file_bytes)
        elif ext == "txt":
            return file_bytes.decode("utf-8")
        else:
            logger.warning(f"Unsupported file extension: {ext}")
            return None
    except Exception as e:
        logger.error(f"Failed to parse {filename}: {str(e)}")
        return None

def _extract_from_pdf(file_bytes: bytes) -> str:
    text_content = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
    return "\n\n".join(text_content)

def _extract_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])
