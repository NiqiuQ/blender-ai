"""Write machine-readable iteration metadata; never claim visual approval automatically."""
from pathlib import Path
import json
import os
import platform
import subprocess
from datetime import datetime, timezone

root = Path("outputs/ai5")
root.mkdir(parents=True, exist_ok=True)

def git_value(*args):
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None

validation_path = root / "validation_report.json"
try:
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
except Exception as exc:
    validation = {"status": "unknown", "error": f"Could not read validation report: {exc}"}

pngs = sorted(p.name for p in root.glob("CAM_*.png") if p.is_file())
manifest = {
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "repository": os.getenv("GITHUB_REPOSITORY"),
    "branch": os.getenv("GITHUB_REF_NAME"),
    "commit": os.getenv("GITHUB_SHA") or git_value("rev-parse", "HEAD"),
    "run_id": os.getenv("GITHUB_RUN_ID"),
    "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
    "run_url": (
        f'{os.getenv("GITHUB_SERVER_URL", "https://github.com")}/'
        f'{os.getenv("GITHUB_REPOSITORY", "")}/actions/runs/{os.getenv("GITHUB_RUN_ID", "")}'
    ),
    "workflow": os.getenv("GITHUB_WORKFLOW"),
    "platform": platform.platform(),
    "python_version": platform.python_version(),
    "gpu_probe": os.getenv("GPU_STATUS", "not_probed"),
    "automated_validation": validation.get("status", "unknown"),
    "automated_validation_details": validation,
    "rendered_camera_files": pngs,
    "visual_review": {
        "status": "pending",
        "required": True,
        "note": "File/format checks do not prove visual quality. Review all three PNGs against REBUILD_SPEC.md."
    }
}
(root / "iteration_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
lines = [
    "# AI-5 Iteration Report",
    "",
    f'- Automated validation: **{manifest["automated_validation"]}**',
    f'- GPU probe: **{manifest["gpu_probe"]}**',
    f'- Branch / commit: `{manifest.get("branch")}` / `{manifest.get("commit")}`',
    f'- Run: {manifest["run_url"]}',
    f'- Rendered camera files: {", ".join(pngs) if pngs else "none found"}',
    "- Visual review: **PENDING — not inferred from automated checks**",
    "",
    "Review the three rendered views for occlusion, intersections, floating objects, proportions, materials, exposure and composition.",
]
(root / "iteration_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({"manifest": str(root / "iteration_manifest.json"), "report": str(root / "iteration_report.md"), "validation": manifest["automated_validation"], "gpu_probe": manifest["gpu_probe"]}, indent=2))
