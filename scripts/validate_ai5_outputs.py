"""Validate AI-5 Blender render artifacts beyond file existence."""
from pathlib import Path
import json
import struct
import sys

root = Path("outputs/ai5")
expected = ["CAM_01_Wide.png", "CAM_02_Lounge.png", "CAM_03_Dining.png"]
report = {"checks": {}, "status": "pass", "limitations": ["Image appearance, collisions and commercial photorealism require visual review."]}

def check_png(path):
    with path.open("rb") as f:
        header = f.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n", f"Invalid PNG: {path}"
    assert header[12:16] == b"IHDR", f"Missing IHDR: {path}"
    width, height = struct.unpack(">II", header[16:24])
    assert width >= 1280 and height >= 800, f"Low resolution: {width}x{height}"
    assert path.stat().st_size > 10000, f"Suspiciously small PNG: {path}"
    return {"width": width, "height": height, "bytes": path.stat().st_size}

try:
    blend = root / "modern_residence_blockout.blend"
    assert blend.exists() and blend.stat().st_size > 10000, "Missing or tiny blend"
    with blend.open("rb") as f:
        assert f.read(7) == b"BLENDER", "Invalid blend header"
    report["checks"]["blend"] = {"bytes": blend.stat().st_size}
    for name in expected:
        report["checks"][name] = check_png(root / name)
except (AssertionError, OSError, ValueError) as exc:
    report["status"] = "fail"
    report["error"] = str(exc)
finally:
    root.mkdir(parents=True, exist_ok=True)
    (root / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
sys.exit(0 if report["status"] == "pass" else 1)
