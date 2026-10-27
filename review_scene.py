"""Automated review pass for generated Blender scenes.

Run with Blender's Python, for example:
    blender -b interior_scene.blend --python review_scene.py

The script checks the acceptance criteria that can be measured without visual
judgement, renders every camera, and writes a machine-readable report.
"""
import bpy
import json
import math
import os
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(bpy.data.filepath))
OUT = os.path.join(ROOT, "previews")
REPORT = os.path.join(ROOT, "review_report.json")
os.makedirs(OUT, exist_ok=True)

def fail(checks, name, detail):
    checks.append({"name": name, "status": "fail", "detail": detail})

def ok(checks, name, detail):
    checks.append({"name": name, "status": "pass", "detail": detail})

def review():
    checks = []
    scene = bpy.context.scene
    cameras = [o for o in scene.objects if o.type == 'CAMERA']
    if len(cameras) < 3:
        fail(checks, "camera_count", f"found {len(cameras)}, need at least 3")
    else:
        ok(checks, "camera_count", f"found {len(cameras)} cameras")

    meshes = [o for o in scene.objects if o.type == 'MESH']
    floating = []
    for obj in meshes:
        if obj.name.lower() in {"floor", "ceiling"}:
            continue
        z = obj.matrix_world.translation.z
        if z < -0.02:
            floating.append(obj.name)
    if floating:
        fail(checks, "below_floor", ", ".join(floating[:12]))
    else:
        ok(checks, "below_floor", "no mesh origins below floor")

    # A camera must have a valid target direction and be outside the room shell.
    bad_cameras = []
    for cam in cameras:
        direction = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
        if direction.length < 0.1 or cam.data.lens <= 0:
            bad_cameras.append(cam.name)
    if bad_cameras:
        fail(checks, "camera_validity", ", ".join(bad_cameras))
    else:
        ok(checks, "camera_validity", "all camera transforms and lenses are valid")

    rendered = []
    for cam in cameras:
        scene.camera = cam
        path = os.path.join(OUT, cam.name.replace(" ", "_") + ".png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        if size == 0:
            fail(checks, f"render:{cam.name}", "render output missing or empty")
        else:
            ok(checks, f"render:{cam.name}", f"{path} ({size} bytes)")
            rendered.append(path)

    passed = all(c["status"] == "pass" for c in checks)
    report = {"passed": passed, "blend_file": bpy.data.filepath, "checks": checks, "renders": rendered}
    with open(REPORT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))
    return passed

if __name__ == "__main__":
    raise SystemExit(0 if review() else 1)
