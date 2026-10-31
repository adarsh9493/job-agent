"""Render and verify every job folder that has a `tailoring.json`.

    python scripts/tailoring/build_all.py                  # every job in data/applications/current
    python scripts/tailoring/build_all.py <job key> ...    # specific jobs (current or history)

Each job's configuration is read from `<job folder>/tailoring.json`; the shared master-derived
content comes from `data/profile/tailoring-base.json`. Nothing is invented: `gen.py` renders only
the content in those two files.
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen  # noqa: E402  (sibling module)
from file_ops import publish_file  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPS = PROJECT_ROOT / "data" / "applications" / "current"

RENDER = os.path.join(HERE, "render_pdf.py")
VERIFY = os.path.join(HERE, "verify_pdf.py")

targets = sys.argv[1:] or gen.job_keys(current_only=True)
if not targets:
    print(
        "No local tailoring configurations are available. Use the tailoring skill "
        "to build this job from the user's profile and master resume.",
        file=sys.stderr,
    )
    sys.exit(2)

configs = []
for target in targets:
    config = gen.load_job_config(target)
    if config is None:
        print(f"Unknown job config: {target}", file=sys.stderr)
        sys.exit(2)
    configs.append(config)

name_parts = gen.profile_identity()["legal_name"].split()
if len(name_parts) < 2:
    print("Profile legal name must include first and last name", file=sys.stderr)
    sys.exit(2)
file_stem = f"{name_parts[0]}_{name_parts[-1]}"

for cfg in configs:
    key = cfg["key"]
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
        publish_file(temp_rpdf, rpdf)
        publish_file(temp_cpdf, cpdf)
        print("-" * 80)
    finally:
        rh.unlink(missing_ok=True)
        ch.unlink(missing_ok=True)
        temp_rpdf.unlink(missing_ok=True)
        temp_cpdf.unlink(missing_ok=True)
