import pandas as pd
import PyPDF2
from typing import List, Dict, Any
import io

def parse_file(uploaded_file, file_type: str) -> Any:
    """
    Parses an uploaded file (CSV, XLSX, PDF, TXT).
    Returns text for PDF/TXT, and list of dicts for CSV/XLSX.
    """
    try:
        if file_type == "csv":
            df = pd.read_csv(uploaded_file)
            return df.to_dict(orient="records")
            
        elif file_type in ["xlsx", "xls"]:
            df = pd.read_excel(uploaded_file)
            return df.to_dict(orient="records")
            
        elif file_type == "txt":
            return uploaded_file.getvalue().decode("utf-8")
            
        elif file_type == "pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
            
    except Exception as e:
        return f"Error parsing file: {e}"
