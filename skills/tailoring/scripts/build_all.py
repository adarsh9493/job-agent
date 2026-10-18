import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen  # noqa: E402  (sibling module: skills/tailoring/scripts/gen.py)

APPS = r"F:\Agentic WorkFlows\job-agent\data\applications\current"

RENDER = os.path.join(HERE, "render_pdf.py")
VERIFY = os.path.join(HERE, "verify_pdf.py")

keys = sys.argv[1:] or list(gen.JOBS.keys())
for key in keys:
    cfg = gen.JOBS[key]
    folder = os.path.join(APPS, cfg["folder"])
    os.makedirs(folder, exist_ok=True)
    rh = os.path.join(gen.TEMP, f"resume_{key}.html")
    ch = os.path.join(gen.TEMP, f"cover_{key}.html")
    os.makedirs(gen.TEMP, exist_ok=True)
    with open(rh, "w", encoding="utf-8") as f:
        f.write(gen.render_resume(cfg))
    with open(ch, "w", encoding="utf-8") as f:
        f.write(gen.render_cover(cfg))
    rpdf = os.path.join(folder, "Adarsh_Ramanujapuram_Resume.pdf")
    cpdf = os.path.join(folder, "Adarsh_Ramanujapuram_CoverLetter.pdf")
    for src, dst in ((rh, rpdf), (ch, cpdf)):
        r = subprocess.run([sys.executable, RENDER, src, dst], capture_output=True, text=True)
        if r.returncode != 0:
            print("RENDER FAIL", key, src, r.stdout[-300:], r.stderr[-300:])
        else:
            os.remove(src)  # file hygiene: drop the intermediate HTML
    r = subprocess.run([sys.executable, VERIFY, rpdf, cpdf], capture_output=True, text=True)
    print(r.stdout.strip())
    print("-" * 80)
