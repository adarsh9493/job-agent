import os
import subprocess
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen  # noqa: E402  (sibling module: skills/tailoring/scripts/gen.py)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
APPS = PROJECT_ROOT / "data" / "applications" / "current"

RENDER = os.path.join(HERE, "render_pdf.py")
VERIFY = os.path.join(HERE, "verify_pdf.py")

keys = sys.argv[1:] or list(gen.JOBS.keys())
if not keys:
    print(
        "No local tailoring configurations are available. Use the tailoring skill "
        "to build this job from the user's profile and master resume.",
        file=sys.stderr,
    )
    sys.exit(2)

for key in keys:
    if key not in gen.JOBS:
        print(f"Unknown job config: {key}", file=sys.stderr)
        sys.exit(2)

    cfg = gen.JOBS[key]
    name_parts = gen.profile_identity()["legal_name"].split()
    if len(name_parts) < 2:
        print("Profile legal name must include first and last name", file=sys.stderr)
        sys.exit(2)
    file_stem = f"{name_parts[0]}_{name_parts[-1]}"
    folder = APPS / cfg["folder"]
    os.makedirs(folder, exist_ok=True)
    rh = Path(gen.TEMP) / f"resume_{key}.html"
    ch = Path(gen.TEMP) / f"cover_{key}.html"
    os.makedirs(gen.TEMP, exist_ok=True)
    rpdf = folder / f"{file_stem}_Resume.pdf"
    cpdf = folder / f"{file_stem}_CoverLetter.pdf"
    temp_rpdf = Path(gen.TEMP) / f"resume_{key}.pdf"
    temp_cpdf = Path(gen.TEMP) / f"cover_{key}.pdf"

    try:
        rh.write_text(gen.render_resume(cfg), encoding="utf-8")
        ch.write_text(gen.render_cover(cfg), encoding="utf-8")
        for src, dst in ((rh, temp_rpdf), (ch, temp_cpdf)):
            result = subprocess.run(
                [sys.executable, RENDER, str(src), str(dst)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode:
                print(f"RENDER FAIL {key}: {result.stderr[-500:]}", file=sys.stderr)
                sys.exit(result.returncode)

        result = subprocess.run(
            [sys.executable, VERIFY, str(temp_rpdf), str(temp_cpdf)],
            capture_output=True,
            text=True,
            check=False,
        )
        print(result.stdout.strip())
        if result.returncode:
            print(result.stderr[-500:], file=sys.stderr)
            sys.exit(result.returncode)
        os.replace(temp_rpdf, rpdf)
        os.replace(temp_cpdf, cpdf)
        print("-" * 80)
    finally:
        rh.unlink(missing_ok=True)
        ch.unlink(missing_ok=True)
        temp_rpdf.unlink(missing_ok=True)
        temp_cpdf.unlink(missing_ok=True)
