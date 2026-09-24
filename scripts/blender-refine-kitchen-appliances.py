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

smoke = material(420, 'Smoke grey tempered hood glass', (.048, .053, .055), .24, .10, .48)
steel = material(421, 'Satin brushed appliance steel', (.47, .50, .51), .34, .90)
dark = material(422, 'Graphite enamel filter and burner', (.038, .043, .044), .48, .45)
white = material(423, 'Soft white control marks', (.58, .62, .61), .57)
glass = material(424, 'Black ceramic glass hob', (.020, .022, .023), .20, .08, .58)
changed = []
added = []
hidden = []

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

# The old facade was almost uniformly black. Give it a readable metal filter,
# a narrow control fascia, and a distinct lower glass pane like the design view.
front = bpy.data.objects['烟机黑玻璃斜面']
front.data = front.data.copy()
front.data.materials.clear()
front.data.materials.append(smoke)
changed.append(front.name)
parts = [
    face_strip(.055, .095, 1.278, 2.026, steel),
    face_strip(.172, .184, 1.286, 2.018, steel),
    face_strip(.210, .410, 1.301, 2.003, dark, .009),
    face_strip(.421, .437, 1.286, 2.018, steel),
    face_strip(.930, .948, 1.286, 2.018, steel),
]
# A real-looking, restrained intake grid: 18 slots across the hood, attached to
# the sloped opening, rather than a repeated paper-thin white pattern.
for i in range(18):
    z = 1.317 + i * .039
    parts.append(face_strip(.241, .381, z, z + .005, steel, .011))
for z in (1.315, 1.665, 2.005):
    parts.append(face_strip(.218, .405, z, z + .006, steel, .012))
# Low-profile control marks and a small warm task light under the lower lip.
for z in (1.855, 1.903, 1.951):
    parts.append(face_strip(.111, .116, z, z + .019, white, .009))
parts.append(box((7.082, 1.205, 1.65), (.007, .004, .39), white, .001))
join(parts, '厨房烟机进风滤网与灯', '烟机黑玻璃斜面')
# The legacy 23 slats occupied the same few millimetres as the newly formed
# filter. Retire them so there is one surface depth and one visual rhythm.
for o in bpy.data.objects:
    if o.name.startswith(('烟机进风网筋', '烟机触控示意')) or o.name == '烟机长条进风口':
        o['source_visible'] = False
        o.hide_render = True
        hidden.append(o.name)

# Keep the slim inset two-burner dimensions. Distinct lip and enamel hardware
# make the burners legible at normal walking distance without high-poly detail.
hob = bpy.data.objects['灶具']
hob.data = hob.data.copy()
hob.data.materials.clear()
hob.data.materials.append(glass)
changed.append(hob.name)
parts = [
    box((6.650, .831, 1.652), (.003, .002, .675), steel, .0005),
    box((7.120, .831, 1.652), (.003, .002, .675), steel, .0005),
    box((6.885, .831, 1.293), (.405, .002, .003), steel, .0005),
    box((6.885, .831, 2.011), (.405, .002, .003), steel, .0005),
]
for z in (1.4864, 1.8265):
    parts.append(torus((6.915, .851, z), .062, .0018, steel))
    parts.append(torus((6.915, .855, z), .045, .0015, dark))
    for i in range(24):
        angle = 2 * math.pi * i / 24
        x = 6.915 + .053 * math.cos(angle)
        zz = z + .053 * math.sin(angle)
        parts.append(cyl((x, .853, zz), .0022, .0015, dark, 8))
    parts.append(cyl((6.985, .850, z + .020), .0035, .015, white, 10))
for z in (1.4864, 1.8265):
    parts.append(torus((6.715, .8314, z), .028, .0015, steel, 24))
    parts.append(box((6.744, .8316, z), (.011, .0008, .0018), white, .0003))
join(parts, '厨房灶具金属边框与点火细节', '灶具')

# Both burners were completely hidden by cookware. Leave the saucepan in use and
# park the shallow pan on the adjacent counter, where it reads as a separate item.
pan = bpy.data.objects['厨房灶台锅具']
pan.data = pan.data.copy()
inv = pan.matrix_world.inverted()
for vertex in pan.data.vertices:
    world = pan.matrix_world @ vertex.co
    runtime_z = -world.y
    if runtime_z > 1.68:
        world.y -= .54
        world.z -= .061
        vertex.co = inv @ world
pan.data.update()
changed.append(pan.name)

# The curved cabinet bay shares a pier with the laundry recess. Separate meshes
# overlapped throughout the three solid shelf bands; at the front their faces
# were only 0.1 mm apart. Union the whole built-in as one solid, so no hidden
# pier surface can reappear while the camera moves.
ivory = next(m for m in bpy.data.materials if m.get('source_material_id') == 38)
plaster = next(m for m in bpy.data.materials if m.get('source_material_id') == 2)
source_shell = bpy.data.objects['圆弧包覆实体层0']
pieces = []
for name in ('圆弧包覆实体层0', '圆弧包覆实体层900',
             '圆弧包覆实体层1230', '洗衣区西侧结构柱'):
    original = bpy.data.objects[name]
    duplicate = original.copy()
    duplicate.data = original.data.copy()
    duplicate.data.materials.clear()
    duplicate.data.materials.append(ivory)
    bpy.context.collection.objects.link(duplicate)
    if name == '洗衣区西侧结构柱':
        # Cross the shell faces by 1.5 mm before the Exact Boolean. The source
        # pier shared a front corner line with them, which leaves open edges
        # when two solids merely touch at that line.
        inverse = duplicate.matrix_world.inverted()
        for vertex in duplicate.data.vertices:
            point = duplicate.matrix_world @ vertex.co
            point.x += -.0015 if point.x < 12.35 else .0015
            point.y += .0015 if point.y > -6.58 else -.0015
            vertex.co = inverse @ point
        duplicate.data.update()
    pieces.append(duplicate)
for level in (600, 930):
    bottom = level / 1000
    pieces.append(box((12.5547, bottom + .150, 6.3738),
                      (.1318, .304, .0285), ivory))
    pieces.append(box((12.6348, bottom + .150, 6.2241),
                      (.0324, .304, .3278), ivory))
combined = pieces[0]
for index, tool in enumerate(pieces[1:]):
    bpy.ops.object.select_all(action='DESELECT')
    combined.select_set(True)
    bpy.context.view_layer.objects.active = combined
    modifier = combined.modifiers.new(f'Solid union {index}', 'BOOLEAN')
    modifier.operation = 'UNION'
    modifier.solver = 'EXACT'
    modifier.object = tool
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(tool, do_unlink=True)
# Imported glTF custom split normals are no longer valid after the Boolean.
# Rebuild them with smooth curved segments and crisp manufactured corners.
bpy.ops.object.select_all(action='DESELECT')
combined.select_set(True)
bpy.context.view_layer.objects.active = combined
if combined.data.has_custom_normals:
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
bm = bmesh.new()
bm.from_mesh(combined.data)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
for face in bm.faces:
    face.smooth = abs(face.normal.z) < .9
for edge in bm.edges:
    if edge.is_manifold:
        edge.smooth = edge.calc_face_angle(0) < math.radians(28)
bm.to_mesh(combined.data)
bm.free()
combined.data.update()
# The short portion above the lacquered cabinet is ordinary plaster.
combined.data.materials.clear()
combined.data.materials.append(ivory)
combined.data.materials.append(plaster)
for polygon in combined.data.polygons:
    world_center = combined.matrix_world @ polygon.center
    polygon.material_index = 1 if world_center.z > 2.371 else 0
# Exact Boolean retains the source shell's UVs. Do not world-project the lacquer
# texture across the curved rim: that makes its normal map form visible bands.
mesh = combined.data.copy()
mesh.transform(source_shell.matrix_world.inverted() @ combined.matrix_world)
source_shell.data = mesh
bpy.data.objects.remove(combined, do_unlink=True)
changed.append(source_shell.name)
for name in ('圆弧包覆实体层900', '圆弧包覆实体层1230',
             '洗衣区西侧结构柱', '壁龛靠沙发端600', '壁龛靠沙发端930',
             '壁龛背部600', '壁龛背部930'):
    o = bpy.data.objects[name]
    o['source_visible'] = False
    o.hide_render = True
    hidden.append(name)

Path(blend_path).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend_path).resolve()))
bpy.ops.export_scene.gltf(filepath=str(Path(glb_path).resolve()), export_format='GLB',
    export_extras=True, export_keep_originals=False, export_yup=True)
Path(spec_path).write_text(json.dumps({'changed': changed, 'added': added,
    'hidden': hidden, 'materialImages': []}, ensure_ascii=False, indent=2))
print('KITCHEN_REFINED', json.dumps({'changed': changed, 'added': added}, ensure_ascii=False))
