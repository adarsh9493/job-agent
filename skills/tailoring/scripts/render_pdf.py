import sys
from playwright.sync_api import sync_playwright

html_path, pdf_path = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto("file:///" + html_path.replace("\\", "/"))
    pg.pdf(path=pdf_path, format="Letter", print_background=True)
    b.close()
print("rendered", pdf_path)
