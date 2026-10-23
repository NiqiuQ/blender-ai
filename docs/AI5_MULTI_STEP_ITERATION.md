# AI-5 Multi-step Iteration Protocol (Work/Codex independent)

## Goal
Run the modern-residence scene through repeatable Blender renders on GitHub-hosted runners, preserve every run's evidence, and use ChatGPT in an ordinary conversation for visual review and the next revision. ChatGPT Work and Codex are not required.

## Loop
1. Change the scene script on `ai-5-modern-residence-modeling`.
2. Push the change. The validation workflow runs Blender, renders all three cameras, validates file formats/resolution, and uploads the `.blend`, PNGs, Blender log, and machine-readable report.
3. Inspect the run and download/open the artifact. Provide the three PNGs (or artifact contents) in the ChatGPT conversation for visual review.
4. ChatGPT records visual findings and proposes a targeted script change. Do not mark visual acceptance based on file checks alone.
5. Commit the change and repeat. Preserve each run's artifact as iteration evidence.
6. Only mark AI-5/AI-8 Done after all three views pass visual review against `REBUILD_SPEC.md`.

## What is automated vs. human/model reviewed
- Automated: Blender installation/version, CPU/GPU availability probe, scene generation, Cycles render, output presence, PNG headers/resolution, blend header, run metadata and artifact upload.
- Visual review required: black/blocked views, furniture scale and clearance, visible intersections/floating objects, lighting/exposure, material quality, composition and commercial photorealism.
- No self-modifying code or automatic visual pass is allowed in this first phase. A new run is triggered by a code push or manual workflow dispatch; ChatGPT makes the creative revision in a later conversation turn.

## Environment constraints
GitHub-hosted runners are ephemeral. Blender is installed on each fresh run; artifacts are retained for 14 days. The standard Ubuntu runner is expected to be CPU-only unless the GPU probe proves otherwise. This is not a persistent Blender server and cannot execute continuously between workflow runs.

## Recovery
- If rendering fails, inspect `outputs/ai5/blender.log` and the failed job log.
- If image/file checks pass but appearance is poor, create a visual-review finding and change the script; do not weaken checks just to get green CI.
- If a run is cancelled, rerun it from Actions after checking the runner queue and time limits.
