import json
import csv
import yaml
from io import StringIO
from typing import Union

from PyPDF2 import PdfReader


def extract_content(filepath: str) -> str:
    """
    Extracts text content from common file formats:
    PDF, TXT, YAML, JSON, CSV.
    
    Returns a string of extracted content.
    """
    try:
        if filepath.lower().endswith(".pdf"):
            text = []
            reader = PdfReader(filepath)
            for page in reader.pages:
                text.append(page.extract_text() or "")
            return "\n".join(text)

        elif filepath.lower().endswith(".txt"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        elif filepath.lower().endswith((".yaml", ".yml")):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = yaml.safe_load(f)
            return json.dumps(data, indent=2)

        elif filepath.lower().endswith(".json"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            return json.dumps(data, indent=2)

        elif filepath.lower().endswith(".csv"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                rows = ["\t".join(row) for row in reader]
            return "\n".join(rows)

        else:
            return f"Unsupported file format: {filepath}"

    except Exception as e:
        return f"Error reading {filepath}: {e}"


# sample usage:
if __name__ == "__main__":
    print(extract_content("sample.pdf"))
    print(extract_content("sample.txt"))
    print(extract_content("sample.yaml"))
    print(extract_content("sample.json"))
    print(extract_content("sample.csv"))
