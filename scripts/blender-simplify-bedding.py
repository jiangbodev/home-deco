"""Reconstruct an editable Blender scene from the original runtime GLB and simplify only bedding.
blender -b --python scripts/blender-simplify-bedding.py -- SOURCE.glb OUTPUT.blend OUTPUT.glb REPORT.json
The .blend is a reconstructed source, not the missing original authoring project.
"""
import bpy, bmesh, json, sys
from pathlib import Path
source, blend, exported, report_path = map(lambda p: str(Path(p).resolve()), sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=source)
names={'fabric 1','Fur_black','White Fabric','fabric 1.001','Fur_black.001','White Fabric.001'}
report=[]
for o in list(bpy.data.objects):
    if o.type!='MESH' or o.name not in names: continue
    o.data=o.data.copy()
    o.data.calc_loop_triangles(); before=len(o.data.loop_triangles)
    bm=bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.000001)
    bm.to_mesh(o.data); bm.free(); o.data.update()
    mod=o.modifiers.new('Bedding 20 percent - editable','DECIMATE'); mod.decimate_type='COLLAPSE'; mod.ratio=0.2; mod.use_collapse_triangulate=True
    evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=evaluated.to_mesh(); mesh.calc_loop_triangles(); after=len(mesh.loop_triangles); evaluated.to_mesh_clear()
    report.append({'name':o.name,'before':before,'after':after,'ratio':mod.ratio})
assert len(report)==6, report
# Re-create the runtime's authored visibility flags in the editable scene.
for o in bpy.data.objects:
    if o.get('source_visible') is False:
        o.hide_render=True; o.hide_set(True)
bpy.context.scene['source_provenance']='Reconstructed from original runtime modules at git 8fcd1e1; not original authoring .blend.'
bpy.context.scene['bedding_workflow']='Original welded mesh retained; non-destructive Decimate modifiers at 0.2; textures packed.'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=blend,compress=True)
# Export only changed objects; the integration script retains original module hierarchy/materials.
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.name in names:o.hide_set(False);o.select_set(True)
bpy.ops.export_scene.gltf(filepath=exported,export_format='GLB',use_selection=True,export_apply=True,export_extras=True,export_tangents=True)
Path(report_path).write_text(json.dumps({'blender':bpy.app.version_string,'source':source,'objects':report},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
