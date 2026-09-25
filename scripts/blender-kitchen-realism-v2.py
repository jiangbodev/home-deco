"""Refine the kitchen's side-draft hood and two-burner gas hob in Blender.

Input is an immutable assembled runtime GLB; imported node names stay stable so the
module importer can replace only the edited appliances. Coordinates are metres.
"""
import bpy
import bmesh
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

source, blend_path, glb_path, spec_path = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(source).resolve()))

def pos(x, y, z):
    return (x, -z, y)

def material(mid, name, rgb, roughness, metallic=0, coat=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m['source_material_id'] = mid
    shader = m.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*rgb, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Coat Weight'].default_value = coat
    return m

smoke = material(430, 'Kitchen optical black glass', (.012,.015,.018), .24, 0, .12)
steel = material(431, 'Kitchen satin nickel', (.38,.40,.42), .43, .85)
dark = material(432, 'Kitchen cast iron enamel', (.018,.022,.024), .68, .12)
white = material(433, 'Kitchen subdued ceramic legends', (.32,.34,.35), .65)
glass = smoke
changed=[]
added=[]
hidden=[]

def box(center, dimensions, mat, radius=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos(*center))
    o = bpy.context.object
    o.dimensions = (dimensions[0], dimensions[2], dimensions[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if radius:
        bevel = o.modifiers.new('Machined radius', 'BEVEL')
        bevel.width = radius
        bevel.segments = 2
        bpy.ops.object.modifier_apply(modifier=bevel.name)
        normal = o.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
        bpy.ops.object.modifier_apply(modifier=normal.name)
    return o

def face_strip(t0, t1, z0, z1, mat, offset=.007):
    # The glass leans away from the cook; a small normal offset prevents coplanar flicker.
    def pt(t, z, back=0):
        return pos(6.942 + .153*t - offset + back, 1.497 - .287*t, z)
    verts = [pt(t0,z0), pt(t0,z1), pt(t1,z1), pt(t1,z0),
             pt(t0,z0,.002), pt(t0,z1,.002), pt(t1,z1,.002), pt(t1,z0,.002)]
    mesh = bpy.data.meshes.new('Hood formed strip')
    mesh.from_pydata(verts, [], [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    mesh.materials.append(mat)
    mesh.update()
    o = bpy.data.objects.new('Hood formed strip', mesh)
    bpy.context.collection.objects.link(o)
    return o

def cyl(center, radius, depth, mat, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=pos(*center))
    o = bpy.context.object
    o.data.materials.append(mat)
    for polygon in o.data.polygons:
        polygon.use_smooth = len(polygon.vertices) == 4
    return o

def torus(center, major, minor, mat, count=32):
    bpy.ops.mesh.primitive_torus_add(major_segments=count, minor_segments=6,
        location=pos(*center), major_radius=major, minor_radius=minor)
    o = bpy.context.object
    o.data.materials.append(mat)
    for polygon in o.data.polygons:
        polygon.use_smooth = True
    return o

def join(parts, name, template=None):
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    if template:
        o['source_visible'] = True
        added.append({'name': name, 'template': template})
    else:
        original = bpy.data.objects[name]
        mesh = o.data.copy()
        mesh.transform(original.matrix_world.inverted() @ o.matrix_world)
        original.data = mesh
        bpy.data.objects.remove(o, do_unlink=True)
        changed.append(name)
    return o

# Replace meshes while retaining original runtime IDs and furniture transforms.
def replace(parts,name):
    return join(parts,name)
def assign(name,mat):
    o=bpy.data.objects[name];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mat);changed.append(name)
def bevel(o,width=.001,segments=3):
    m=o.modifiers.new('Small manufactured edge','BEVEL');m.width=width;m.segments=segments
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name)
    # Smooth cylindrical walls; keep broad end faces flat.
    for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
    return o
def retire(name):
    o=bpy.data.objects[name];o['source_visible']=False;o.hide_render=True;hidden.append(name)

# One removable sheet filter with actual slots and a dark recessed plenum.
# The glass has a matching aperture, so the slots do not terminate on glass.
replace([face_strip(0,.20,1.2652,2.0392,smoke,0),
         face_strip(.49,1,1.2652,2.0392,smoke,0),
         face_strip(.20,.49,1.2652,1.296,smoke,0),
         face_strip(.20,.49,2.009,2.0392,smoke,0)],'烟机黑玻璃斜面')
plate=face_strip(.21,.48,1.302,2.003,steel,-.001)
for i in range(34):
    z=1.314+i*.0202
    cut=face_strip(.25,.44,z,z+.0045,dark,.006)
    # Extend cutter through full sheet thickness, normal to original panel.
    # Explicit cutter thickness avoids relying on floating-point coplanarity.
    for j,v in enumerate(cut.data.vertices):
        if j>=4:v.co.x+=.024
    mod=plate.modifiers.new('Actual intake slot','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
    bpy.context.view_layer.objects.active=plate;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cut,do_unlink=True)
# Recessed backing and restrained edge gasket; no bright overlaid bars.
parts=[plate,face_strip(.20,.49,1.296,2.009,dark,-.012)]
replace(parts,'厨房烟机进风滤网与灯')
replace([face_strip(-.055,0,1.2522,2.0522,steel,0),face_strip(1,1.035,1.2522,2.0522,steel,0),face_strip(0,1,1.2522,1.2652,steel,0),face_strip(0,1,2.0392,2.0522,steel,0)],'烟机金属包边')
assign('烟机可拆集油槽',steel)
assign('烟机上沿控制面板',smoke)
assign('烟机贴墙机身',dark)
# Discrete touch symbols on the actual vertical control fascia.
parts=[]
for z in (1.83,1.88,1.93):
    o=torus((6.9325,1.485,z),.004,.00055,white,24)
    o.rotation_euler[1]=math.pi/2;parts.append(o)
join(parts,'烟机触控小圆标','烟机上沿控制面板')

# Black glass edge stays glass; remove decorative chrome perimeter/halos.
assign('灶具',smoke)
retire('厨房灶具金属边框与点火细节')
for suffix,z in [('',1.4864),('.001',1.8265)]:
    # A low satin drip cup, stepped burner body and distinct black cap.
    replace([bevel(cyl((6.915,.832,z),.076,.005,steel,64),.001)],'燃气炉头底座'+suffix)
    replace([bevel(cyl((6.915,.841,z),.055,.013,dark,64),.0007)],'燃气燃烧器'+suffix)
    replace([bevel(cyl((6.915,.851,z),.061,.006,dark,64),.001)],'燃气火盖'+suffix)
    # Smooth tapered control with a tactile grip, not a faceted chrome token.
    base=bevel(cyl((6.715,.842,z),.0185,.024,steel,64),.002,4)
    grip=box((6.715,.855,z),(.025,.006,.007),dark,.002)
    replace([base,grip],'灶具控制旋钮'+suffix)
    replace([box((6.744,.8298,z),(.008,.0006,.0012),white)],'旋钮指示线'+suffix)
# Dedicated low-gloss materials avoid unrelated cookware calibration.
for o in list(bpy.data.objects):
    if o.name.startswith(('铸铁锅架','锅架支')):assign(o.name,dark)

Path(blend_path).parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend_path).resolve()))
bpy.ops.export_scene.gltf(filepath=str(Path(glb_path).resolve()),export_format='GLB',export_extras=True,export_yup=True)
Path(spec_path).write_text(json.dumps({'changed':changed,'added':added,'hidden':hidden,'materialImages':[]},ensure_ascii=False,indent=2))
print('REFINED',changed)
