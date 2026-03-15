import pdfplumber
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

files = [
    "thong-tin-tuyen-sinh-dai-hoc-nam-can-tho-2025.pdf",
    "Thong_bao_diem_chuan_2025_-_DNC-_22-8-2025.pdf"
]

with open('pdf_output_utf8.txt', 'w', encoding='utf-8') as out:
    for fname in files:
        out.write(f"\n{'='*80}\n")
        out.write(f"FILE: {fname}\n")
        out.write(f"{'='*80}\n")
        try:
            with pdfplumber.open(fname) as pdf:
                for i, page in enumerate(pdf.pages):
                    out.write(f"\n--- Page {i+1} ---\n")
                    text = page.extract_text()
                    if text:
                        out.write(text + "\n")
                    tables = page.extract_tables()
                    if tables:
                        for t_idx, table in enumerate(tables):
                            out.write(f"\n[Table {t_idx+1}]\n")
                            for row in table:
                                cleaned = [str(c).strip() if c else "" for c in row]
                                out.write(" | ".join(cleaned) + "\n")
        except Exception as e:
            out.write(f"Error: {e}\n")

print("Done")
