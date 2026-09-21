"""Repair observed surface conflicts from the immutable three-cushion sofa checkpoint."""
import bpy,bmesh,sys,json
from pathlib import Path
from mathutils import Vector
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
changed={}
def world(o,v):
 p=o.matrix_world@v;return Vector((p.x,p.z,-p.y))
def local(o,p):return o.matrix_world.inverted()@Vector((p[0],-p[2],p[1]))
def bounds(o):
 ps=[world(o,v.co) for v in o.data.vertices];return [[min(p[i] for p in ps) for i in range(3)],[max(p[i] for p in ps) for i in range(3)]]
def mark(o,reason):
 if o.name not in changed:changed[o.name]={'before':bounds(o),'repairs':[]};o.data=o.data.copy()
 changed[o.name]['repairs'].append(reason)
def inset(name,axis,side,delta):
 o=bpy.data.objects[name];b=bounds(o);edge=b[side][axis];mark(o,f'Inset boundary {axis}/{side} by {delta} m')
 for v in o.data.vertices:
  p=world(o,v.co)
  if abs(p[axis]-edge)<.0004:p[axis]+=delta
  v.co=local(o,p)
# The roof used to be a sky-facing, zero-thickness plane. Keep the 2.7 m underside.
o=bpy.data.objects['原顶_高度待核'];mark(o,'Closed 60 mm roof slab above original interior height')
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
result=bmesh.ops.solidify(bm,geom=list(bm.faces),thickness=.06)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
# Solidify orientation is checked; shift the slab so its lower face remains at 2.7 m.
low=bounds(o)[0][1]
for v in o.data.vertices:
 p=world(o,v.co);p.y+=2.70000041045-low;v.co=local(o,p)
# Keep the primary arch/wall as the continuous visible finish; recess secondary caps.
inset('外置台盆背防水饰面',2,1,-.002)
inset('玄关餐桌连接侧体',2,1,-.002)
inset('玄关餐桌连接侧体',2,0,.002)
inset('玄关餐桌连接侧体',0,1,-.002)
inset('玄关左侧圆弧包覆',0,0,.002)
inset('玄关左侧圆弧包覆',0,1,-.002)
# Carcass fronts were coincident with the beveled door fronts. Recess just the front
# edge, leaving every door, hinge transform, cabinet footprint and back untouched.
for o in list(bpy.data.objects):
 if o.type!='MESH' or not any(s in o.name for s in ['实体侧板','实体顶板','实体底板','顶封板']):continue
 prefix=o.name.split('实体')[0].split('顶封板')[0];doors=[d for d in bpy.data.objects if d.type=='MESH' and d.name.startswith(prefix+'门板')]
 for door in doors:
  db=bounds(door);axis=min(range(3),key=lambda i:db[1][i]-db[0][i])
  if axis==1:continue
  ob=bounds(o);center=(ob[0][axis]+ob[1][axis])/2;front=1 if (db[0][axis]+db[1][axis])/2>center else 0
  if abs(ob[front][axis]-db[front][axis])<.0004:
   inset(o.name,axis,front,-.002 if front else .002);break
# The passage soffit overlaps the structural column along a vertical boundary.
o=bpy.data.objects['过道玄关连续低顶'];mark(o,'Recess soffit side behind the continuous structural column')
for v in o.data.vertices:
 p=world(o,v.co)
 if abs(p.x-5.44382)<.0004:p.x-=.002
 if abs(p.x-5.54406)<.0004:p.x-=.002
 if abs(p.z-5.2057)<.0004:p.z-=.002
 v.co=local(o,p)
# Window frame terminates inside the solid wall instead of intersecting its exposed face.
inset('主卧东窗竖框',2,0,.018)
# The tub rim owns the top edge; apron caps terminate 2 mm below it.
inset('浴缸侧裙',1,1,-.002);inset('浴缸前裙',1,1,-.002)
inset('浴缸外包1275x840',2,1,-.002);inset('浴缸外包1275x840',0,1,-.002)
for name,r in changed.items():
 o=bpy.data.objects[name];o.data.update();r['after']=bounds(o)
for o in bpy.data.objects:
 p=o;visible=True
 while p:
  if p.get('source_visible') is False:visible=False
  p=p.parent
 o.hide_render=not visible
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for name in changed:
 o=bpy.data.objects[name];o.hide_set(False);o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_tangents=True)
Path(report).write_text(json.dumps(changed,ensure_ascii=False,indent=2)+'\n');print('REPAIRED',len(changed))
