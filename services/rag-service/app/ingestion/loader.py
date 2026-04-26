import io
import csv
from pathlib import Path
from typing import Optional

async def load_document(file_path: str, content_type: str) -> str:
    """Load document and return raw text content"""
    path = Path(file_path)
    
    if content_type in ("application/pdf", "pdf"):
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    
    elif content_type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"):
        from docx import Document
        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    
    elif content_type in ("text/csv", "csv"):
        import pandas as pd
        df = pd.read_csv(file_path)
        return df.to_string(index=False)
    
    elif content_type in ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"):
        import pandas as pd
        df = pd.read_excel(file_path, sheet_name=None)
        return "\n\n".join(f"Sheet: {name}\n{sheet.to_string(index=False)}" for name, sheet in df.items())
    
    else:
        return path.read_text(encoding="utf-8", errors="replace")
