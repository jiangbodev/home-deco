"""Consistent ivory joinery and physically constructed shelf display; incremental source."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
changed=[]
mats={m.get('source_material_id'):m for m in bpy.data.materials};ivory=mats[38];paper=mats[307]
def P(p):return Vector((p[0],-p[2],p[1]))
def mat(mid,name,c):
 m=bpy.data.materials.new(name);m.use_nodes=True;m['source_material_id']=mid;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.72;return m
green=mat(330,'Muted olive linen book cloth',(.12,.155,.12));clay=mat(331,'Clay cloth book cover',(.29,.135,.08));cream=mat(332,'Warm linen book cloth',(.59,.53,.42));ink=mat(333,'Charcoal printed ink',(.034,.043,.041));oak=mats[320]
def box(c,d,m,r=.001):
 bpy.ops.mesh.primitive_cube_add(size=1,location=P(c));o=bpy.context.object;o.dimensions=(d[0],d[2],d[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if r:
  mod=o.modifiers.new('Soft manufactured edge','BEVEL');mod.width=r;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name)
  mod=o.modifiers.new('Planar normals','WEIGHTED_NORMAL');mod.keep_sharp=True;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o
def replace(name,parts):
 o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();tmp=bpy.context.object;mesh=tmp.data.copy();mesh.transform(o.matrix_world.inverted()@tmp.matrix_world);o.data=mesh;bpy.data.objects.remove(tmp,do_unlink=True);changed.append(name)
# Cabinet wraps/liners must use the same lacquer as the cabinet, not plaster.
for o in list(bpy.data.objects):
 if o.type!='MESH':continue
 if o.name.startswith(('圆弧包覆实体层','壁龛背部','壁龛靠沙发端','洗衣隐藏门板')) or o.name in ['玄关左侧圆弧包覆','玄关前拱框','玄关层板_700','通高柜内退踢脚']:
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(ivory);changed.append(o.name)
# A 36 mm shelf with eased edges, mounted into the wall; keep its original top.
replace('沙发上方浅色层板',[box((11.2857,1.457,6.77055),(1.55896,.036,.180),ivory,.002)])
# Three closed books, each with cover boards, spine and inset page block.
for i,(w,h,zshift,c) in enumerate([(.240,.023,0,green),(.225,.018,-.009,cream),(.207,.025,.005,clay)]):
 bottom=1.475+sum([.023,.018,.025][:i]);x=11.5833+[0,-.008,.010][i];z=6.775+zshift;depth=.145
 parts=[box((x,bottom+.0012,z),(w,.0024,depth),c,.0006),box((x,bottom+h-.0012,z),(w,.0024,depth),c,.0006),box((x,bottom+h/2,z+.003),(w-.007,h-.0048,depth-.008),paper,.0005),box((x,bottom+h/2,z-depth/2+.0016),(w,h,.0032),c,.0007)]
 # Subtle page gatherings on the side; no painted block masquerading as a book.
 for y in [bottom+h*.32,bottom+h*.53,bottom+h*.73]:parts.append(box((x+w/2-.0032,y,z+.003),(.0005,.00025,depth-.011),cream,0))
 # Small printed spine label, flush with the cloth.
 parts.append(box((x-.028,bottom+h/2,z-depth/2-.00015),(.042,.004,.0002),paper,0))
 replace('搁板薄书示意'+str(i),parts)
# A real four-rail oak frame, recessed paper mount, backing and leaning support.
x=11.0873;bottom=1.475;h=.315;w=.235;z=6.816
parts=[box((x,bottom+h/2,z+.012),(w-.012,h-.012,.006),cream,.0005)]
for xx in [x-w/2+.007,x+w/2-.007]:parts.append(box((xx,bottom+h/2,z),(.014,h,.022),oak,.001))
for yy in [bottom+.007,bottom+h-.007]:parts.append(box((x,yy,z),(w-.028,.014,.022),oak,.001))
parts.append(box((x,bottom+.032,z+.026),(.045,.064,.030),cream,.001))
replace('展示画框背板',parts)
replace('展示画框画芯',[box((x,bottom+h/2,z+.002),(w-.029,h-.029,.0015),paper,.0002)])
# Restrained printed composition instead of three protruding vertical sticks.
for i,(dx,yy,ww,hh,m) in enumerate([(-.035,.11,.047,.105,green),(.025,.14,.071,.085,clay),(0,.06,.145,.0015,ink)]):
 replace('画芯线条示意'+('' if i==0 else '.'+str(i).zfill(3)),[box((x+dx,bottom+yy,z+.0011),(ww,hh,.0002),m,.00005)])
# Incline the complete frame toward the wall by five degrees; bottom still rests on shelf.
from mathutils import Matrix
pivot=P((x,bottom,z));rot=Matrix.Rotation(math.radians(5),4,'X')
for name in ['展示画框背板','展示画框画芯','画芯线条示意','画芯线条示意.001','画芯线条示意.002']:
 o=bpy.data.objects[name];transform=Matrix.Translation(pivot)@rot@Matrix.Translation(-pivot);o.data.transform(o.matrix_world.inverted()@transform@o.matrix_world)
frame_names=['展示画框背板','展示画框画芯','画芯线条示意','画芯线条示意.001','画芯线条示意.002']
low=min((bpy.data.objects[n].matrix_world@v.co).z for n in frame_names for v in bpy.data.objects[n].data.vertices)
for name in frame_names:
 o=bpy.data.objects[name];o.data.transform(o.matrix_world.inverted()@Matrix.Translation(P((0,1.475-low,-.004)))@o.matrix_world)
# Existing repaired shells may lack UVs because plaster had no source texture.
# The shared lacquer contains a roughness texture, so provide metre-scale UVs.
for name in changed:
 o=bpy.data.objects[name]
 if not o.data.uv_layers:
  uv=o.data.uv_layers.new(name='UVMap')
  for poly in o.data.polygons:
   n=o.matrix_world.to_3x3()@poly.normal;axis=max(range(3),key=lambda i:abs(n[i]))
   for li in poly.loop_indices:
    p=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
    uv.data[li].uv=(p.x,-p.y) if axis==2 else ((p.x,p.z) if axis==1 else (-p.y,p.z))
bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':[],'materialImages':[]},ensure_ascii=False,indent=2));print('FOLLOWUP',len(changed))
