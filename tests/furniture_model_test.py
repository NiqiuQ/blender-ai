import bpy, math
from mathutils import Vector
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
def material(name, color, rough=.55, metallic=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough; bs.inputs['Metallic'].default_value=metallic
 return m
fabric=material('Warm linen upholstery',(.57,.53,.46),.85)
wood=material('Walnut wood',(.18,.085,.038),.35)
metal=material('Brushed black metal',(.035,.035,.04),.3,.7)
floor=material('Warm oak floor',(.42,.29,.18),.65)
wall=material('Ivory wall',(.78,.75,.69),.9)
rug=material('Soft cream rug',(.67,.63,.56),.95)
def cube(name, loc, scale, mat, bevel=.04):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(mat)
 if bevel:
  mod=o.modifiers.new('Rounded corners','BEVEL'); mod.width=bevel; mod.segments=4
  o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o
cube('Floor',(0,0,-.09),(8,7,.18),floor,.015)
cube('Back wall',(0,3.5,2),(8,.16,4),wall,.02)
cube('Sofa seat',(0,.65,.57),(2.65,.92,.26),fabric,.12)
cube('Sofa back',(0,1.13,.94),(2.7,.22,.95),fabric,.10)
for x in [-1.25,1.25]:
 cube('Sofa arm',(x,.64,.82),(.23,1.12,.65),fabric,.08)
for x in [-.8,0,.8]:
 cube('Seat cushion',(x,.60,.76),(.79,.82,.15),fabric,.08)
for x in [-1.05,1.05]:
 for y in [.3,1.0]:
  cube('Sofa foot',(x,y,.20),(.09,.09,.27),wood,.01)
cube('Rug',(0,-.75,.015),(3.8,2.6,.03),rug,.03)
cube('Coffee table top',(0,-.65,.46),(1.35,.7,.09),wood,.05)
for x in [-.53,.53]:
 for y in [-.89,-.41]:
  cube('Coffee table leg',(x,y,.22),(.06,.06,.42),metal,.012)
cube('Lamp stem',(2.2,.65,.92),(.045,.045,1.8),metal,.012)
cube('Lamp base',(2.2,.65,.045),(.43,.43,.09),metal,.025)
cube('Lamp shade',(2.2,.65,1.85),(.55,.55,.40),fabric,.06)
world=bpy.context.scene.world; world.color=(.3,.3,.3)
def area(name,loc,power,size):
 bpy.ops.object.light_add(type='AREA',location=loc); o=bpy.context.object; o.name=name; o.data.energy=power; o.data.shape='DISK'; o.data.size=size; o.rotation_euler=(Vector((0,0,.65))-o.location).to_track_quat('-Z','Y').to_euler()
area('Large softbox',(-3,-3,5),1100,5)
area('Fill light',(3,0,4),650,4)
bpy.ops.object.camera_add(location=(4,-5,2.8))
cam=bpy.context.object; cam.rotation_euler=(Vector((0,.2,.7))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.context.scene.camera=cam
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=32
sc.render.resolution_x=1000; sc.render.resolution_y=700; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'; sc.render.filepath='/tmp/output/furniture_render.png'
bpy.ops.wm.save_as_mainfile(filepath='/tmp/output/furniture_test.blend')
bpy.ops.render.render(write_still=True)
