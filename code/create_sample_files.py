# generate_samples.py
import json
import yaml
import csv
from reportlab.pdfgen import canvas

def create_txt():
    with open("sample.txt", "w") as f:
        f.write("This is a plain text file.\nIt has two lines.")

def create_json():
    data = {"username": "alice", "password": "s3cr3t"}
    with open("sample.json", "w") as f:
        json.dump(data, f, indent=2)

def create_yaml():
    data = {"database": {"user": "bob", "password": "hunter2"}}
    with open("sample.yaml", "w") as f:
        yaml.safe_dump(data, f)

def create_csv():
    rows = [
        ["id", "name", "email"],
        [1, "Alice", "alice@example.com"],
        [2, "Bob", "bob@example.com"]
    ]
    with open("sample.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def create_pdf():
    c = canvas.Canvas("sample.pdf")
    c.drawString(100, 750, "This is a PDF file.")
    c.drawString(100, 730, "It has multiple lines of text.")
    c.save()

if __name__ == "__main__":
    create_txt()
    create_json()
    create_yaml()
    create_csv()
    create_pdf()
    print("Sample files created!")