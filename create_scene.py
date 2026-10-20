import bpy, math, os
from mathutils import Vector

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), 'previews'))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, color, rough=0.45, metallic=0.0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough; bs.inputs['Metallic'].default_value=metallic
    return m
wood=mat('Warm oak',(0.24,0.09,0.035),.32); wall=mat('Lime plaster',(0.58,0.52,0.43),.8); cream=mat('Boucle upholstery',(0.72,0.66,0.55),.9); dark=mat('Charcoal metal',(0.025,0.03,0.035),.28,.7); green=mat('Plant leaves',(0.08,0.22,0.09),.75); ceramic=mat('Ceramic',(0.5,0.52,0.48),.3); glass=mat('Glass',(0.1,0.16,0.18),.12,.15); accent=mat('Accent fabric',(0.18,0.24,0.28),.85); brass=mat('Brushed brass',(0.42,0.22,0.06),.25,.65); art=mat('Abstract art',(0.12,0.18,0.22),.7)

def cube(n, loc, scale, material, bevel=.04):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=n; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('Soft edges','BEVEL'); mod.width=bevel; mod.segments=3
    o.data.materials.append(material); return o
def cyl(n, loc, r, depth, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r, depth=depth, location=loc); o=bpy.context.object; o.name=n; o.data.materials.append(material); return o

# room shell
cube('Floor',(0,0,-.08),(4.8,4.0,.08),wood,.02); cube('Back skirting',(0,3.84,.18),(4.75,.06,.18),dark,.02); cube('Left skirting',(-4.64,0,.18),(.06,3.8,.18),dark,.02); cube('Back wall',(0,4.0,2.6),(4.8,.08,2.7),wall,.02); cube('Left wall',(-4.8,0,2.6),(.08,4.0,2.7),wall,.02)
# window and frame on back wall
cube('Window recess',(1.3,3.88,2.65),(2.1,.035,1.55),glass,.01)
for x in [-.8,3.4]: cube('Window jamb',(x,3.78,2.65),(.06,.12,1.7),dark,.01)
for z in [1.0,4.3]: cube('Window sill',(1.3,3.78,z),(2.2,.12,.06),dark,.01)
cube('Curtain left',(-1.05,3.62,2.65),(.42,.035,1.62),accent,.05); cube('Curtain right',(3.65,3.62,2.65),(.42,.035,1.62),accent,.05)
cyl('Curtain rod',(1.3,3.5,4.42),.025,5.0,brass); bpy.context.object.rotation_euler[1]=math.radians(90)
cube('Artwork',(-4.68,1.65,2.45),(.025,1.0,.75),art,.02); cube('Frame top',(-4.64,1.65,3.28),(.025,1.1,.05),brass,.015); cube('Frame bottom',(-4.64,1.65,1.62),(.025,1.1,.05),brass,.015); cube('Frame left',(-4.64,.60,2.45),(.025,.05,.78),brass,.015); cube('Frame right',(-4.64,2.70,2.45),(.025,.05,.78),brass,.015)
# rug
rug=mat('Wool rug',(0.34,0.30,0.25),.95); cube('Rug',(0,-.1,.045),(2.9,2.0,.025),rug,.03)
# sofa
cube('Sofa base',(-1.5,.4,.65),(2.0,.75,.35),cream,.16); cube('Sofa back',(-1.5,1.05,1.45),(2.0,.18,.85),cream,.14)
for x in [-3.1,-1.5,.1]: cube('Sofa cushion',(x,.35,1.12),(.72,.62,.12),cream,.12)
for x,rot in [(-2.5,-.18),(-.65,.2)]:
    p=cube('Accent cushion',(x,.73,1.22),(.34,.12,.34),accent,.12); p.rotation_euler[1]=rot
# coffee table
cube('Table top',(1.0,-.25,.72),(1.25,.7,.10),wood,.06)
for x in [.15,1.85]:
  for y in [-.72,.22]: cyl('Table leg',(x,y,.31),.055,.62,dark)
# sideboard
cube('Sideboard',(3.35,2.65,.8),(1.1,.42,.7),wood,.05)
for x in [2.8,3.35,3.9]: cube('Sideboard door',(x,2.18,.8),(.22,.03,.48),dark,.02)
# decor and plants
cyl('Vase',(3.35,2.7,1.75),.22,.5,ceramic); cyl('Plant pot',(-3.55,2.4,.55),.38,.65,ceramic)
for i in range(9):
    a=i*0.7; leaf=cube('Leaf',(-3.55+math.cos(a)*.35,2.4+math.sin(a)*.35,1.45+0.22*(i%3)),(.05,.3,.05),green,.03); leaf.rotation_euler=(.2*math.sin(a),.4*math.cos(a),a)
# pendant
cyl('Pendant cord',(0,0,4.8),.015,1.6,dark); bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(0,0,3.95), scale=(.42,.42,.22)); bpy.context.object.data.materials.append(ceramic)
# lighting
bpy.ops.object.light_add(type='AREA', location=(0,1.0,4.7)); bpy.context.object.data.energy=900; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=4.0
bpy.ops.object.light_add(type='AREA', location=(1.3,3.1,3.0)); key=bpy.context.object; key.data.energy=1200; key.data.size=3.0; key.rotation_euler=(math.radians(65),0,math.radians(180))
bpy.ops.object.light_add(type='AREA', location=(-3.8,-1.5,2.5)); fill=bpy.context.object; fill.data.energy=500; fill.data.size=2.0; fill.rotation_euler=(math.radians(70),0,math.radians(-55))
# cameras
def camera(name, loc, target):
    bpy.ops.object.camera_add(location=loc); c=bpy.context.object; c.name=name; c.data.lens=42; c.data.sensor_width=36; c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler(); return c
cams=[camera('View 1',(7,-8,5.2),(0,.5,1.5)), camera('View 2',(-6,-6,3.7),(.4,.4,1.4)), camera('View 3',(0,-7.0,2.8),(0,.7,1.25))]
scene=bpy.context.scene; scene.render.engine='BLENDER_EEVEE_NEXT'; scene.render.resolution_x=512; scene.render.resolution_y=384; scene.render.resolution_percentage=100
scene.render.image_settings.color_mode='RGBA'
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.world=bpy.data.worlds.new('World') if scene.world is None else scene.world
scene.world.color=(0.035,0.04,0.05)
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-0.7
for c in cams:
    scene.camera=c; scene.render.filepath=os.path.join(OUT,c.name.replace(' ','_')+'.png'); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(__file__),'interior_scene.blend'))
