import sys, re
try:
    from pypdf import PdfReader
except Exception:
    from PyPDF2 import PdfReader

for pdf in sys.argv[1:]:
    r = PdfReader(pdf)
    text = "\n".join((p.extract_text() or "") for p in r.pages)
    tokens = re.findall(r"\{\{[^}]+\}\}", text)
    ok_len = len(text.strip())
    has_name = "Adarsh Ramanujapuram" in text
    print(f"{pdf}\n  pages={len(r.pages)} chars={ok_len} name={has_name} tokens={tokens[:5]}")
