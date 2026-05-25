import os

pdf_files = [
    "114年第四梯次初級AI應用規劃師第一科人工智慧基礎概論(當次試題公告114_20251226000442.pdf",
    "114年第四梯次初級AI應用規劃師第二科生成式AI應用與規劃(當次試題公告114_20251226000507.pdf",
    "115年第一次初級AI應用規劃師_第一科_人工智慧基礎概論_公告試題_20260410164304.pdf",
    "115年第一次初級AI應用規劃師_第二科_生成式AI應用與規劃_公告試題_20260410164328.pdf",
    "iPAS+AI應用規劃師初級能力鑑定-考試樣題(114年9月版).pdf",
    "iPAS+AI應用規劃師能力鑑定(初級)_樣題(114年3月版).pdf"
]

print("Starting inspection of PDF files...\n")

def test_pypdf(path):
    try:
        import pypdf
        reader = pypdf.PdfReader(path)
        text = ""
        for i in range(min(5, len(reader.pages))):
            text += f"\n--- Page {i+1} ---\n" + reader.pages[i].extract_text()
        return text
    except Exception as e:
        return f"pypdf error: {e}"

def test_pdfplumber(path):
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(path) as pdf:
            for i in range(min(5, len(pdf.pages))):
                text += f"\n--- Page {i+1} ---\n" + (pdf.pages[i].extract_text() or "")
        return text
    except Exception as e:
        return f"pdfplumber error: {e}"

def test_fitz(path):
    try:
        import fitz
        doc = fitz.open(path)
        text = ""
        for i in range(min(5, len(doc))):
            text += f"\n--- Page {i+1} ---\n" + doc[i].get_text()
        return text
    except Exception as e:
        return f"fitz (PyMuPDF) error: {e}"

for pdf in pdf_files:
    path = os.path.join(".", pdf)
    if not os.path.exists(path):
        print(f"File not found: {pdf}")
        continue
    
    print("="*60)
    print(f"Inspecting file: {pdf}")
    print("="*60)
    
    # Try pypdf first
    res = test_pypdf(path)
    if "pypdf error" not in res:
        print("Used pypdf successfully!")
        print(res[:2000]) # print first 2000 chars
    else:
        # Try fitz
        res = test_fitz(path)
        if "fitz error" not in res:
            print("Used fitz (PyMuPDF) successfully!")
            print(res[:2000])
        else:
            # Try pdfplumber
            res = test_pdfplumber(path)
            print("Used pdfplumber:")
            print(res[:2000])
    print("\n" + "#"*60 + "\n")
