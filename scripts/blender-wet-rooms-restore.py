"""Restore kitchen and bathroom omissions from plan03 and elevations18/22/23.
World arguments are glTF metres (X,Y height,Z); preserve sink/circulation.
"""
import bpy,bmesh,sys,json
from pathlib import Path
from mathutils import Vector
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
mats={m.get('source_material_id'):m for m in bpy.data.materials};changed=[];added=[]
def box(lo,hi,mat,r=.0006):
 c=[(a+b)/2 for a,b in zip(lo,hi)];d=[b-a for a,b in zip(lo,hi)]
 bpy.ops.mesh.primitive_cube_add(size=1,location=(c[0],-c[2],c[1]));o=bpy.context.object;o.dimensions=(d[0],d[2],d[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if r:
  m=o.modifiers.new('Fine manufactured edge','BEVEL');m.width=r;m.segments=2;bpy.ops.object.modifier_apply(modifier=m.name)
  m=o.modifiers.new('Face normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=m.name)
 uv=o.data.uv_layers.active
 for face in o.data.polygons:
  axis=max(range(3),key=lambda i:abs(face.normal[i]))
  for li in face.loop_indices:
   p=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
   uv.data[li].uv=(p.x*.8,-p.y*.8) if axis==2 else ((p.x*.8,p.z*.8) if axis==1 else (-p.y*.8,p.z*.8))
 return o
def replace(name,parts,template=None):
 if template:
  origin=bpy.data.objects[template];o=origin.copy();o.data=origin.data.copy();o.name=name;bpy.context.collection.objects.link(o);added.append({'name':name,'template':template})
 else:o=bpy.data.objects[name]
 bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();tmp=bpy.context.object;mesh=tmp.data.copy();mesh.transform(o.matrix_world.inverted()@tmp.matrix_world);o.data=mesh;bpy.data.objects.remove(tmp,do_unlink=True);changed.append(name)
wood=mats[370];tile=mats[27];metal=mats[303];porcelain=mats[302];slat=mats[371];cord=mats[372];dark=mats[306]
def cb(c,d,m,r=.001):return box(tuple(c[i]-d[i]/2 for i in range(3)),tuple(c[i]+d[i]/2 for i in range(3)),m,r)
def cylinder(a,b,r,m,vertices=16):
 a=Vector((a[0],-a[2],a[1]));b=Vector((b[0],-b[2],b[1]));v=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 return o
# Construction elevation18: west run is three 355mm bays; north bay is a 1050mm-high cupboard.
# The old two shelves incorrectly continued through this bay, with the cupboard omitted.
for name,y in [('厨房开放层板',1.32),('厨房开放层板.001',1.68)]:
 replace(name,[box((5.32998,y,1.174728),(5.62998,y+.06,1.889728),wood,.0015)])
parts=[box((5.32998,1.32,.819728),(5.34798,2.37,1.174728),wood),box((5.34798,1.32,.819728),(5.61198,2.37,.837728),wood),box((5.34798,1.32,1.156728),(5.61198,2.37,1.174728),wood),box((5.34798,1.32,.837728),(5.61198,1.338,1.156728),wood),box((5.34798,2.352,.837728),(5.61198,2.37,1.156728),wood),box((5.61198,1.322,.821728),(5.62998,2.368,1.172728),wood)]
replace('厨房西侧355封闭吊柜',parts,'厨房开放层板')
# Move the existing bowls onto the surviving shelf, rather than leave them in the new cupboard.
o=bpy.data.objects['厨房层板叠碗'];o.data=o.data.copy();offset=o.matrix_world.to_3x3().inverted()@Vector((0,-.32,0))
for v in o.data.vertices:v.co+=offset
changed.append(o.name)
# Plan03 labels a niche in the west shower return. Subtract an actual backed recess.
wall=bpy.data.objects['管井转角墙'];cut=box((4.036,.98,.75),(4.26,1.62,1.005),tile,0)
bpy.context.view_layer.objects.active=wall;mod=wall.modifiers.new('Actual shower niche opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True);changed.append(wall.name)
parts=[box((4.036,.98,.75),(4.045,1.62,1.005),tile,0),box((4.045,.98,.75),(4.2398,.992,1.005),tile,0),box((4.045,1.608,.75),(4.2398,1.62,1.005),tile,0),box((4.045,.992,.75),(4.2398,1.608,.759),tile,0),box((4.045,.992,.996),(4.2398,1.608,1.005),tile,0),box((4.045,1.293,.759),(4.2398,1.308,.996),tile,.0004)]
replace('次卫淋浴内凹壁龛及层板',parts,'次卫西墙砖')
# Plan03 also identifies a wall radiator beside the main-bath WC.
parts=[cb((7.424,1.24,1.295),(.07,.91,.28),porcelain,.004)]
for z in [1.18+i*.028 for i in range(9)]:parts.append(cb((7.463,1.24,z),(.008,.865,.006),porcelain,.001))
for y in [.90,1.60]:parts.append(cb((7.405,y,1.295),(.038,.032,.22),metal,.002))
replace('主卫马桶侧暖气片',parts,'主卫西墙砖南')
# Kitchen blind, same small shared slat materials as guest bathroom.
parts=[cb((6.3342,2.331,.173),(.751,.043,.045),slat,.002)]
for i in range(44):
 o=cb((6.3342,2.288-i*.032,.179),(.731,.0014,.04),slat,0);o.rotation_euler.x=.488692;parts.append(o)
parts.append(cb((6.3342,.897,.179),(.733,.016,.041),slat,.002))
for x in [6.08,6.59]:
 for z in [.161,.197]:parts.append(cb((x,1.604,z),(.0045,1.42,.0014),cord,0))
for x in [5.999,6.669]:parts.append(cb((x,2.329,.144),(.024,.040,.030),slat,.001))
replace('厨房北窗百叶帘',parts,'厨房北窗窗下实体')
# Reference09 wall appliance: no speculative brand or interface text.
parts=[cb((7.114,1.20,2.425),(.125,.52,.34),porcelain,.018),cb((7.047,1.30,2.425),(.008,.13,.14),dark,.006),cb((7.022,1.065,2.425),(.105,.026,.065),porcelain,.006),cb((7.013,.958,2.425),(.14,.025,.18),porcelain,.008),cb((7.176,1.22,2.425),(.01,.35,.20),metal,.001)]
replace('厨房参考壁挂饮水设备',parts,'厨房吊柜背板')
# Close the unintended 30mm break between the north and west worktops.
parts=[box((5.359034,.79,.789388),(5.685034,.82,.819728),mats[308]),box((5.359034,.04,.789388),(5.685034,.79,.819728),wood)]
replace('厨房北西台面转角补板',parts,'厨房左窄柜_深326浅色台面')
# Main-bath bathtub filler on the solid wall BELOW the north window sill.
parts=[cb((7.94,.735,.237),(.17,.10,.019),metal,.003),cylinder((7.94,.735,.246),(7.94,.735,.415),.017,metal),cylinder((7.94,.735,.415),(7.94,.697,.415),.017,metal),cb((8.005,.765,.264),(.022,.016,.070),metal,.002)]
replace('主卫浴缸壁装龙头',parts,'浴缸前裙')
# Electric towel rail shown on the east wall of the main bathroom, clear of the door.
parts=[]
for z in [1.305,1.755]:
 parts.append(cylinder((9.365,.83,z),(9.365,1.52,z),.012,metal))
 for y in [.90,1.44]:parts.append(cylinder((9.440,y,z),(9.365,y,z),.013,metal))
for y in [.87,.98,1.09,1.20,1.31,1.42,1.50]:parts.append(cylinder((9.365,y,1.305),(9.365,y,1.755),.009,metal))
parts.append(cb((9.383,.837,1.742),(.031,.06,.047),dark,.004))
replace('主卫电热毛巾架',parts,'主卫东墙砖北')
# Both reference shower elevations show one leaf, not a two-bay mullioned screen.
for prefix,x0,x1,z,template in [('次卫',4.2648,5.1841,1.03743,'次卫淋浴透明玻璃竖框'),('主卫',8.6044,9.4239,1.12075,'主卫淋浴透明玻璃竖框')]:
 parts=[]
 for y in [.5,1.92]:parts.append(cb((x1-.008,y,z),(.045,.065,.036),metal,.003))
 for y in [1.05,1.25]:parts.append(cylinder((x0+.075,y,z-.024),(x0+.075,y,z+.048),.008,metal))
 for zz in [z-.025,z+.049]:parts.append(cylinder((x0+.075,1.025,zz),(x0+.075,1.275,zz),.009,metal))
 replace(prefix+'淋浴单扇门铰链及拉手',parts,template)
# Retire only the old mid-leaf pull from the combined guest-bath accessory mesh.
# Preserve its existing floor drain and toilet-paper holder.
o=bpy.data.objects['次卫排水门把与纸架'];o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data)
remove=[]
for v in bm.verts:
 p=o.matrix_world@v.co;x,y,z=p.x,p.z,-p.y
 if 4.75<x<4.79 and .97<y<1.19 and 1.04<z<1.09:remove.append(v)
assert remove,'Expected old guest shower pull'
bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(o.data);bm.free();changed.append(o.name)
# Existing main-bath ceramic parts were still assigned the generic countertop material.
for name in ['主卫壁挂马桶壁挂接头','主卫壁挂马桶座圈','主卫壁挂马桶闭合盖板','主卫壁挂马桶陶瓷壳']:
 o=bpy.data.objects[name];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(porcelain);changed.append(name)
bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':added,'materialImages':[],'hidden':['主卫淋浴透明玻璃竖框.001','次卫淋浴透明玻璃竖框.001']},ensure_ascii=False,indent=2))
