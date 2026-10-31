import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

html_path, pdf_path = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch()
    try:
        pg = b.new_page()
        pg.goto(Path(html_path).resolve().as_uri())
        pg.pdf(path=pdf_path, format="Letter", print_background=True)
    finally:
        b.close()
print("rendered", pdf_path)
