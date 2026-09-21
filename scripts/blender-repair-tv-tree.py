"""Fill the dining TV wall head and restore uncollapsed woody tree meshes.
Inputs are immutable current modules and the original pre-LOD tree source.
"""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
src,original,blend,out,report=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
current=list(bpy.data.objects);trees=[o for o in current if o.type=='MESH' and o.name.startswith(('树木_branches','树木_trunk'))];names={o:o.name for o in current}
for o in current:o.name='CURRENT_'+o.name
bpy.ops.import_scene.gltf(filepath=str(Path(original).resolve()))
imported=[o for o in bpy.data.objects if o not in current];prototype={};changes=[]
for o in trees:
 name=names[o];donor=bpy.data.objects[name];key=donor.data.as_pointer()
 if key not in prototype:
  prototype[key]=donor.data.copy();prototype[key].name='Connected original woody structure'
 old=len(o.data.polygons);o.data=prototype[key];changes.append({'name':name,'beforeFaces':old,'afterFaces':len(o.data.polygons),'method':'Restore original woody topology; keep reduced foliage and tree transforms'})
for o in imported:bpy.data.objects.remove(o,do_unlink=True)
for o,name in names.items():o.name=name
wall=bpy.data.objects['玄关餐桌连接侧体'];wall.data=wall.data.copy();inv=wall.matrix_world.inverted();old=[]
for v in wall.data.vertices:
 p=wall.matrix_world@v.co;old.append(tuple(p))
 if p.z>2.36:p.z=2.7
 # A continuous front 4 mm ahead of the adjacent arch/soffit avoids coplanar overlap.
 if p.x>5.54:p.x=5.5483
 v.co=inv@p
for poly in wall.data.polygons:poly.use_smooth=False
wall.data.update();changes.append({'name':wall.name,'oldTop':max(p[2] for p in old),'newTop':2.7,'frontX':5.5483,'method':'Extend existing solid to ceiling; keep TV clear of wall'})
bpy.ops.object.select_all(action='DESELECT')
for o in trees+[wall]:o.select_set(True)
bpy.context.view_layer.objects.active=wall
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps(changes,ensure_ascii=False,indent=2));print(json.dumps(changes,ensure_ascii=False))
