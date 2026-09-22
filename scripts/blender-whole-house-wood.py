"""Reference-led joinery finish and guest-bath blind, from immutable approved source."""
import bpy,sys,json,math,re
from pathlib import Path
from mathutils import Vector
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
mats={m.get('source_material_id'):m for m in bpy.data.materials}
oak=mats[25].copy();oak.name='Natural oak joinery with directional grain';oak['source_material_id']=370;oak['detail_base_material']=25
oak.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.48
changed=[];added=[];changes=[]
def P(p):return Vector((p[0],-p[2],p[1]))
def visible(o):
 while o:
  if o.get('source_visible',True)==False:return False
  o=o.parent
 return True
# Only named joinery; ivory paint, upholstery, metal, glass and door-gap backings stay separate.
pattern=re.compile(r'^(厨房|主卧|床侧书柜|次卧右衣柜|次卧床床架|外置台盆|主卫台盆柜|主卫镜柜|玄关下柜|玄关层板|洗衣区台面|主卫客厅窗木窗台)')
for o in list(bpy.data.objects):
 if o.type!='MESH' or not visible(o) or not (pattern.search(o.name) or o.name in ['Warm walnut - real oak scan tinted.004','Warm walnut - real oak scan tinted.005','Warm walnut - real oak scan tinted.007']):continue
 slots=[i for i,m in enumerate(o.data.materials) if m and m.get('source_material_id') in [9,15,41,45,69,75,320]]
 if not slots:continue
 o.data=o.data.copy()
 for i in slots:o.data.materials[i]=oak
 # Actual world-metre coordinates, not distorted inherited per-face charts.
 uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
 pts=[o.matrix_world@v.co for v in o.data.vertices];dims=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)]
 horizontal=('层板' in o.name or '台面' in o.name or '窗台' in o.name or '床架' in o.name or '砧板' in o.name or '底板' in o.name or '顶封板' in o.name)
 grain_axis=0 if dims[0]>=dims[1] else 1
 for f in o.data.polygons:
  if f.material_index not in slots:continue
  normal=o.matrix_world.to_3x3().inverted().transposed()@f.normal;axis=max(range(3),key=lambda i:abs(normal[i]))
  for li in f.loop_indices:
   p=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co;x,y,z=p.x,p.z,-p.y
   if horizontal:
    if grain_axis==0:coord=(z/.78,x/1.9) if axis==2 else ((y/.78,x/1.9) if axis==1 else (z/.78,y/1.9))
    else:coord=(x/.78,z/1.9) if axis==2 else ((y/.78,z/1.9) if axis==0 else (x/.78,y/1.9))
   else:coord=((z if axis==0 else x)/.78,y/1.9) if axis!=2 else ((z/.78,x/1.9) if grain_axis==0 else (x/.78,z/1.9))
   uv.data[li].uv=coord
 # Small tangible arris on previously sharp solid boards; no silhouette redesign.
 if len(o.data.vertices)<=32 and len(slots)==len(o.data.materials):
  bpy.context.view_layer.objects.active=o
  bevel=o.modifiers.new('Joinery fine eased edge','BEVEL');bevel.width=.0009;bevel.segments=2;bevel.limit_method='ANGLE'
  bpy.ops.object.modifier_apply(modifier=bevel.name)
  normal=o.modifiers.new('Stable board normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=normal.name)
 changed.append(o.name);changes.append({'name':o.name,'grain':'horizontal' if horizontal else 'vertical'})
# Reference 16 has a venetian blind in the guest-bath exterior window.
def mat(mid,name,rgb,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;m['source_material_id']=mid;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=rough;return m
slat=mat(371,'Warm ivory aluminium blind',(.62,.59,.53),.48);cord=mat(372,'Blind ladder tape',(.43,.40,.35),.8)
def box(c,d,m,r=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=P(c));o=bpy.context.object;o.dimensions=(d[0],d[2],d[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if r:
  b=o.modifiers.new('Soft manufactured edge','BEVEL');b.width=r;b.segments=2;bpy.ops.object.modifier_apply(modifier=b.name)
 return o
parts=[box((4.7245,2.331,.166),(.937,.043,.044),slat,.002)]
for i in range(49):
 o=box((4.7245,2.288-i*.032,.172),(.917,.0014,.040),slat);o.rotation_euler.x=math.radians(28);parts.append(o)
parts.append(box((4.7245,.717,.172),(.919,.016,.041),slat,.002))
for x in [4.408,5.041]:
 for z in [.154,.190]:parts.append(box((x,1.51,z),(.0045,1.60,.0014),cord))
for x in [4.285,5.164]:parts.append(box((x,2.329,.135),(.024,.040,.030),slat,.001))
bpy.ops.object.select_all(action='DESELECT')
for p in parts:p.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name='次卫外窗百叶帘';o['source_visible']=True
added.append({'name':o.name,'template':'次卫北窗下砖'})
bpy.ops.object.select_all(action='DESELECT')
for name in changed+[a['name'] for a in added]:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':added,'materialImages':[],'hidden':[],'materialTexcoords':{370:0},'grain':changes},ensure_ascii=False,indent=2))
print('JOINERY',len(changed),'BLIND',len(added))
