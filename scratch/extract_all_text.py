import os

pdf_files = [
    "114年第四梯次初級AI應用規劃師第一科人工智慧基礎概論(當次試題公告114_20251226000442.pdf",
    "114年第四梯次初級AI應用規劃師第二科生成式AI應用與規劃(當次試題公告114_20251226000507.pdf",
    "115年第一次初級AI應用規劃師_第一科_人工智慧基礎概論_公告試題_20260410164304.pdf",
    "115年第一次初級AI應用規劃師_第二科_生成式AI應用與規劃_公告試題_20260410164328.pdf",
    "iPAS+AI應用規劃師初級能力鑑定-考試樣題(114年9月版).pdf",
    "iPAS+AI應用規劃師能力鑑定(初級)_樣題(114年3月版).pdf",
    "iPAS+AI應用規劃師能力鑑定(初級)_樣題參考.pdf"
]

os.makedirs("scratch/txt", exist_ok=True)

def extract_text_pypdf(pdf_path, txt_path):
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for i, page in enumerate(reader.pages):
            text += f"\n=== PAGE {i+1} ===\n"
            text += page.extract_text() or ""
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Extracted {pdf_path} to {txt_path} using pypdf")
        return True
    except Exception as e:
        print(f"Failed pypdf for {pdf_path}: {e}")
        return False

def extract_text_fitz(pdf_path, txt_path):
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text = ""
        for i, page in enumerate(doc):
            text += f"\n=== PAGE {i+1} ===\n"
            text += page.get_text() or ""
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Extracted {pdf_path} to {txt_path} using fitz")
        return True
    except Exception as e:
        print(f"Failed fitz for {pdf_path}: {e}")
        return False

for pdf in pdf_files:
    if not os.path.exists(pdf):
        print(f"Not found: {pdf}")
        continue
    
    base_name = os.path.splitext(pdf)[0]
    txt_path = f"scratch/txt/{base_name}.txt"
    
    if not extract_text_pypdf(pdf, txt_path):
        extract_text_fitz(pdf, txt_path)

print("Done extracting all text!")
