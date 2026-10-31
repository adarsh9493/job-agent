"""Safe publishing helpers for generated application documents."""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path


def publish_file(source: Path, destination: Path) -> Path:
    """Copy to a same-volume temporary file, then atomically replace the destination.

    The renderer's temp directory may be on another Windows drive, where ``os.replace``
    raises ``EXDEV``. Copying into the destination directory first avoids that failure and
    leaves an existing destination intact if copying or publishing fails.
    """
    source = Path(source)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=destination.parent, prefix=f".{destination.name}.",
            suffix=".tmp", delete=False,
        ) as target:
            temporary = Path(target.name)
            with source.open("rb") as original:
                shutil.copyfileobj(original, target)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, destination)
        source.unlink()
        return destination
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
