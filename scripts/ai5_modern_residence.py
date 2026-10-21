"""AI-5: procedural modern residence blockout.
Run: blender -b -t 4 --python scripts/ai5_modern_residence.py
No external models or image assets are used.
"""
import bpy
import math
from mathutils import Vector
from pathlib import Path

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def material(name, color, roughness=0.65, metallic=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = roughness
    p.inputs["Metallic"].default_value = metallic
    return m

plaster = material("Warm ivory plaster", (0.77, 0.74, 0.68))
wood = material("Walnut", (0.22, 0.105, 0.055), 0.5)
fabric = material("Sand woven fabric", (0.58, 0.53, 0.46), 0.9)
stone = material("Pale limestone", (0.67, 0.65, 0.59))
metal = material("Dark anodized metal", (0.08, 0.085, 0.09), 0.32, 0.7)
glass = material("Glass tint", (0.22, 0.30, 0.33), 0.16)
rug = material("Wool rug", (0.49, 0.43, 0.37), 0.98)

def box(name, loc, scale, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if bevel:
        mod = ob.modifiers.new("Soft edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        ob.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return ob

# 9m x 7m living room; front and right sides are open for clear views.
box("Floor slab", (0, 0, -0.13), (9.4, 7.4, 0.26), stone)
box("Rear wall", (0, 3.6, 1.55), (9.4, 0.18, 3.1), plaster)
box("Left wall", (-4.6, 0, 1.55), (0.18, 7.4, 3.1), plaster)
box("Ceiling perimeter left", (-4.0, 0, 3.08), (1.1, 7.3, 0.12), plaster)
box("Ceiling perimeter rear", (0, 3.05, 3.08), (9.3, 1.1, 0.12), plaster)
# Sofa, facing toward the center; furniture rests on the floor.
box("Sofa seat", (-1.9, 1.45, 0.45), (3.1, 0.98, 0.48), fabric, 0.09)
box("Sofa back", (-1.9, 1.98, 0.86), (3.1, 0.25, 0.9), fabric, 0.09)
for x in (-3.38, -0.42):
    box("Sofa arm", (x, 1.45, 0.68), (0.24, 1.1, 0.72), fabric, 0.06)
for x in (-2.85, -1.85, -0.85):
    box("Seat cushion", (x, 1.33, 0.73), (0.91, 0.82, 0.14), fabric, 0.07)
box("Wool area rug", (-1.0, -0.35, 0.025), (4.6, 3.5, 0.05), rug, 0.02)
box("Coffee table top", (-1.0, -0.3, 0.42), (1.55, 0.82, 0.10), wood, 0.035)
for x in (-1.58, -0.42):
    for y in (-0.58, -0.02):
        box("Coffee table leg", (x, y, 0.205), (0.075, 0.075, 0.35), metal)
box("Media console", (1.85, 3.12, 0.45), (3.3, 0.45, 0.7), wood, 0.025)
box("Television", (1.85, 3.33, 1.75), (2.4, 0.08, 1.35), metal, 0.02)
box("TV screen", (1.85, 3.28, 1.75), (2.28, 0.018, 1.24), glass, 0.005)
box("Dining tabletop", (2.45, -1.6, 0.76), (2.2, 1.0, 0.10), wood, 0.035)
for x in (1.58, 3.32):
    for y in (-1.94, -1.26):
        box("Dining table leg", (x, y, 0.35), (0.08, 0.08, 0.7), metal)
for x in (1.6, 3.3):
    for y in (-2.45, -0.75):
        box("Dining chair seat", (x, y, 0.47), (0.52, 0.48, 0.12), fabric, 0.04)
        by = y + (-0.20 if y < -1.6 else 0.20)
        box("Dining chair back", (x, by, 0.86), (0.52, 0.10, 0.76), wood, 0.035)
        for dx in (-0.18, 0.18):
            for dy in (-0.16, 0.16):
                box("Chair leg", (x+dx, y+dy, 0.205), (0.04, 0.04, 0.41), metal)

world = bpy.context.scene.world
world.color = (0.3, 0.3, 0.3)
def area_light(name, loc, power, size):
    bpy.ops.object.light_add(type="AREA", location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.data.energy = power
    ob.data.shape = "DISK"
    ob.data.size = size
    ob.rotation_euler = (Vector((0,0,0.6)) - ob.location).to_track_quat("-Z", "Y").to_euler()
area_light("Large window softbox", (0, -3.0, 3.7), 1100, 5)
area_light("Interior bounce", (1.0, 1.5, 2.7), 500, 3)

def camera(name, location, target, lens):
    bpy.ops.object.camera_add(location=location)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = (Vector(target)-ob.location).to_track_quat("-Z", "Y").to_euler()
    ob.data.lens = lens
    return ob

cameras = [
    camera("CAM_01_Wide", (6.8,-8.7,4.0), (-0.3,0.2,1.1), 28),
    camera("CAM_02_Lounge", (-0.3,-6.2,2.2), (-1.3,1.1,1.0), 34),
    camera("CAM_03_Dining", (7.2,-2.6,2.9), (1.6,-0.4,1.0), 32),
]
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 48
scene.render.resolution_x = 1280
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
root = Path(bpy.path.abspath("//"))
output = root / "outputs" / "ai5"
output.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(output / "modern_residence_blockout.blend"))
for cam in cameras:
    scene.camera = cam
    scene.render.filepath = str(output / (cam.name + ".png"))
    bpy.ops.render.render(write_still=True)
print("AI-5 generated blend and three camera renders:", output)
