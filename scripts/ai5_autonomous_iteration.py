#!/usr/bin/env python3
"""Bounded AI-assisted Blender visual iteration using the OpenAI Responses API.

Safety model:
- Never reads repository secrets except OPENAI_API_KEY from the environment.
- The model may propose a unified diff only for scripts/ai5_modern_residence.py.
- Every diff is checked by git apply --check and path allowlisting before application.
- Maximum rounds are capped; each round's images, review JSON, patch, and logs are retained.
- This script does not push or commit model-generated code.
"""
from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path.cwd()
SCENE = Path("scripts/ai5_modern_residence.py")
OUT = Path("outputs/autonomous")
API_URL = "https://api.openai.com/v1/responses"
MODEL = os.getenv("OPENAI_MODEL", "").strip()
API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MAX_ROUNDS = max(1, min(int(os.getenv("MAX_ITERATIONS", "2")), 3))
BLENDER = os.getenv("BLENDER_BIN", "blender")
CAMERAS = ["CAM_01_Wide.png", "CAM_02_Lounge.png", "CAM_03_Dining.png"]


def api_text(payload: dict, label: str) -> str:
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    if not MODEL:
        raise RuntimeError("OPENAI_MODEL is not configured. Set it to a model available to your API project.")
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=body, method="POST",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=240) as response:
                data = json.loads(response.read().decode("utf-8"))
            texts = []
            for item in data.get("output", []):
                if item.get("type") == "message":
                    for part in item.get("content", []):
                        if part.get("type") in ("output_text", "text") and part.get("text"):
                            texts.append(part["text"])
            if not texts:
                raise RuntimeError(f"{label}: API returned no text. Response keys: {list(data.keys())}")
            return "\n".join(texts).strip()
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", "replace")[:2000]
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            raise RuntimeError(f"{label}: OpenAI API HTTP {exc.code}: {details}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            raise RuntimeError(f"{label}: OpenAI API request failed: {exc}") from exc
    raise RuntimeError(f"{label}: retry budget exhausted")


def extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^\s*```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise RuntimeError("Model response did not contain a JSON object.")
    return json.loads(cleaned[start:end + 1])


def run_render(round_dir: Path, round_no: int) -> None:
    render_dir = Path("outputs/ai5")
    if render_dir.exists():
        shutil.rmtree(render_dir)
    render_dir.mkdir(parents=True, exist_ok=True)
    log_path = round_dir / "blender.log"
    cmd = [BLENDER, "-b", "-t", "4", "--python", str(SCENE)]
    print(f"[round {round_no}] Running: {' '.join(cmd)}", flush=True)
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", flush=True)
            log.write(line)
        code = proc.wait()
    if code != 0:
        raise RuntimeError(f"Blender exited with code {code}; inspect {log_path}")
    blend = render_dir / "modern_residence_blockout.blend"
    if not blend.is_file() or blend.stat().st_size < 10000:
        raise RuntimeError("Expected .blend output is missing or too small.")
    for name in CAMERAS:
        image = render_dir / name
        if not image.is_file() or image.stat().st_size < 10000:
            raise RuntimeError(f"Expected render missing or too small: {image}")
        shutil.copy2(image, round_dir / name)
    shutil.copy2(blend, round_dir / blend.name)
    shutil.copy2(log_path, render_dir / "blender.log")


def image_content(round_dir: Path, instruction: str) -> list[dict]:
    parts: list[dict] = [{"type": "input_text", "text": instruction}]
    for name in CAMERAS:
        path = round_dir / name
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        parts.append({"type": "input_text", "text": f"Camera image: {name}"})
        parts.append({"type": "input_image", "detail": "high", "image_url": f"data:image/png;base64,{encoded}"})
    return parts


def review_images(round_dir: Path, round_no: int) -> dict:
    instruction = f"""You are reviewing a procedural Blender modern-residence scene. This is visual QA round {round_no}.
Inspect all three attached actual renders against these criteria:
- no black/blocked camera views;
- plausible furniture proportions and circulation;
- no obvious floating, wall/floor embedding, or visible intersections;
- balanced exposure and lighting, no major clipped highlights;
- coherent materials, camera composition, and credible high-end architectural visualization.
Return ONLY JSON with keys:
decision: "accept" or "revise"
findings: array of objects with severity ("critical"|"major"|"minor"), camera, issue, concrete_fix
summary: concise string
Do not claim geometric certainty from images alone. If any meaningful visible issue remains, choose revise. "accept" means only that these images have no obvious remaining visual blockers, not final commercial certification."""
    response = api_text({
        "model": MODEL,
        "input": [{"role": "user", "content": image_content(round_dir, instruction)}],
        "max_output_tokens": 1800,
    }, "visual review")
    (round_dir / "visual_review_raw.txt").write_text(response, encoding="utf-8")
    report = extract_json(response)
    (round_dir / "visual_review.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def extract_diff(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^\s*```(?:diff|patch)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    index = text.find("diff --git ")
    if index < 0:
        raise RuntimeError("Model did not return a unified git diff.")
    return text[index:].strip() + "\n"


def create_and_apply_patch(report: dict, round_dir: Path) -> None:
    current = SCENE.read_text(encoding="utf-8")
    prompt = f"""You are a senior Blender Python technical artist. Make a minimal, targeted revision to fix the visible issues in the attached QA report.
Return ONLY a unified git diff (no explanation, no Markdown fences) that changes exactly one file:
scripts/ai5_modern_residence.py
Do not add dependencies, download assets, run shell commands, access secrets, or modify workflows/tests. Preserve the three camera names, output filenames, editable .blend generation, Cycles renderer and all three renders. Prefer concrete scene/material/light/camera corrections; do not weaken quality checks.
QA report:
{json.dumps(report, ensure_ascii=False)}
Current scene script:
---BEGIN CURRENT SCRIPT---
{current}
---END CURRENT SCRIPT---"""
    response = api_text({
        "model": MODEL,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "max_output_tokens": 5000,
    }, "patch generation")
    (round_dir / "proposed_patch_raw.txt").write_text(response, encoding="utf-8")
    patch = extract_diff(response)
    patch_path = round_dir / "proposed.patch"
    patch_path.write_text(patch, encoding="utf-8")

    # Strict allowlist: exactly one file may be touched.
    headers = re.findall(r"^diff --git a/(.*?) b/(.*?)$", patch, flags=re.MULTILINE)
    if headers != [(str(SCENE), str(SCENE))]:
        raise RuntimeError(f"Rejected patch: only {SCENE} may be changed; found {headers}")
    for line in patch.splitlines():
        if line.startswith(("rename from ", "rename to ", "copy from ", "copy to ")):
            raise RuntimeError("Rejected patch containing rename/copy operations.")
    subprocess.run(["git", "apply", "--check", str(patch_path)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "apply", str(patch_path)], check=True, capture_output=True, text=True)
    compile_result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(SCENE)],
        capture_output=True, text=True,
    )
    if compile_result.returncode:
        # Roll back only the proposed file edit; preserve logs and patch as evidence.
        subprocess.run(["git", "apply", "-R", str(patch_path)], check=False, capture_output=True, text=True)
        raise RuntimeError(f"Rejected patch: Python syntax check failed: {compile_result.stderr}")
    print(f"Applied checked patch to {SCENE}", flush=True)


def main() -> int:
    if not API_KEY:
        print("OPENAI_API_KEY missing; cannot run autonomous visual review.", file=sys.stderr)
        return 2
    if not MODEL:
        print("OPENAI_MODEL missing; configure a model ID enabled for your API project.", file=sys.stderr)
        return 2
    if not SCENE.is_file():
        print(f"Scene script not found: {SCENE}", file=sys.stderr)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    initial_script = SCENE.read_text(encoding="utf-8")
    summary = {"model": MODEL, "max_rounds": MAX_ROUNDS, "rounds": [], "final_decision": "not_run"}
    try:
        for round_no in range(1, MAX_ROUNDS + 1):
            round_dir = OUT / f"round_{round_no:02d}"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "scene_script_before.py").write_text(SCENE.read_text(encoding="utf-8"), encoding="utf-8")
            run_render(round_dir, round_no)
            report = review_images(round_dir, round_no)
            entry = {
                "round": round_no,
                "decision": report.get("decision", "unknown"),
                "summary": report.get("summary", ""),
                "findings": report.get("findings", []),
                "render_dir": str(round_dir),
            }
            summary["rounds"].append(entry)
            (OUT / "iteration_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[round {round_no}] visual decision: {entry['decision']}; {entry['summary']}", flush=True)
            if entry["decision"] == "accept":
                summary["final_decision"] = "visual_review_accept"
                break
            if round_no == MAX_ROUNDS:
                summary["final_decision"] = "max_rounds_reached_with_findings"
                break
            try:
                create_and_apply_patch(report, round_dir)
            except Exception as exc:
                summary["final_decision"] = "patch_rejected_or_failed"
                summary["patch_error"] = str(exc)
                raise
        (OUT / "final_scene_script.py").write_text(SCENE.read_text(encoding="utf-8"), encoding="utf-8")
        (OUT / "iteration_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        return 0
    except Exception as exc:
        summary["error"] = str(exc)
        summary["final_decision"] = summary.get("final_decision", "failed")
        (OUT / "iteration_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        (OUT / "final_scene_script.py").write_text(SCENE.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Autonomous iteration stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
