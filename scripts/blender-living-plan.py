"""Drawing-first living/dining/balcony restoration; immutable wet-room input."""
import math
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
# Elevation16: stone window sill, seated on the existing 580mm parapet.
replace('阳台石材窗台',[box((13.919,.58,3.613),(14.047,.600,6.058),mats[308],.0015)],'客厅东窗窗下实体')
# Same ivory joinery on the bookcase end return; no grey trim material.
for name in ['书架沙发侧60圆角收口','入门柜门套侧圆角收口']:
 o=bpy.data.objects[name];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mats[38]);changed.append(name)
 uv=o.data.uv_layers.active or o.data.uv_layers.new(name='Cabinet finish UV')
 for li,loop in enumerate(o.data.loops):
  p=o.matrix_world@o.data.vertices[loop.vertex_index].co;uv.data[li].uv=(p.x,p.z)
# The two original chair frames float ~12mm above the floor. Extend only the
# last 45mm of the legs; keep seat/back/cane and all interaction matrices fixed.
for name in ['Warm walnut - real oak scan tinted.001','Warm walnut - real oak scan tinted.002']:
 o=bpy.data.objects[name];o.data=o.data.copy();low=min((o.matrix_world@v.co).z for v in o.data.vertices);inv=o.matrix_world.inverted()
 for v in o.data.vertices:
  p=o.matrix_world@v.co
  if p.z<low+.045:p.z-=low*max(0,1-(p.z-low)/.045);v.co=inv@p
 changed.append(name)
# Close the physical gap between each dining pendant socket and timber cap.
parts=[]
for x in [6.0092,6.8492]:parts.append(cylinder((x,1.688,4.7304),(x,1.704,4.7304),.012,metal))
replace('餐厅吊灯灯口连接套',parts,'餐桌吊灯灯口')
# Three appliances already occupy the plan-defined laundry slots. Give them a
# real recessed loading opening instead of a ring placed on an uncut white box.
enamel=bpy.data.materials.new('Warm white appliance enamel');enamel.use_nodes=True;enamel['source_material_id']=380
p=enamel.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.82,.84,.83,1);p.inputs['Metallic'].default_value=.12;p.inputs['Roughness'].default_value=.32
# Opaque polished dark glazing: no extra transmission render pass.
glass=bpy.data.materials.new('Laundry smoked door glass');glass.use_nodes=True;glass['source_material_id']=381
p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.018,.029,.034,1);p.inputs['Metallic'].default_value=.22;p.inputs['Roughness'].default_value=.16

def ring(cx,cy,profile,mat):
 verts=[];faces=[];N=48
 for r,z in profile:
  for i in range(N):
   a=i*2*math.pi/N;verts.append((cx+r*math.cos(a),-z,cy+r*math.sin(a)))
 for j in range(len(profile)):
  for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,((j+1)%len(profile))*N+(i+1)%N,((j+1)%len(profile))*N+i))
 me=bpy.data.meshes.new('Machined loading rim');me.from_pydata(verts,[],faces);me.materials.append(mat);o=bpy.data.objects.new('Loading rim',me);bpy.context.collection.objects.link(o)
 for f in me.polygons:f.use_smooth=True
 return o
for prefix,cx,cy,zfront,outer,inner in [('洗衣机',12.992,.45,6.126,.232,.167),('干衣机',13.606,.45,6.126,.232,.167),('壁挂洗衣机',12.992,1.52,6.441,.20,.142)]:
 name=prefix+'外形';o=bpy.data.objects[name];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(enamel)
 cut=cylinder((cx,cy,zfront-.05),(cx,cy,zfront+.17),inner,metal,48)
 bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Recessed loading aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True);changed.append(name)
 replace(prefix+'门圈',[ring(cx,cy,[(inner,zfront+.016),(outer-.010,zfront+.016),(outer,zfront+.004),(outer-.004,zfront-.016),(outer-.022,zfront-.026),(inner+.010,zfront-.023),(inner,zfront-.006)],mats[301])])
 parts=[ring(cx,cy,[(inner-.001,zfront-.002),(inner-.001,zfront+.14),(inner-.010,zfront+.14),(inner-.010,zfront-.002)],mats[306]),cylinder((cx,cy,zfront+.115),(cx,cy,zfront+.119),inner-.012,glass,48)]
 # Recessed drum rear and a shallow asymmetric highlight rim establish depth
 # without adding transparent layers or a simulated drum interior.
 parts.append(ring(cx,cy,[(inner-.008,zfront+.102),(inner-.006,zfront+.108),(inner-.016,zfront+.112),(inner-.016,zfront+.104)],metal))
 replace(prefix+'内凹舱门玻璃',parts,prefix+'门圈')
 if prefix!='壁挂洗衣机':
  parts=[cylinder((cx+.193,.766,6.112),(cx+.193,.766,6.123),.022,metal,24),cb((cx-.202,.752,6.122),(.128,.053,.007),enamel,.002),cb((cx-.202,.733,6.116),(.095,.005,.007),mats[306],.0008)]
  for xx in [cx-.24,cx+.24]:parts.append(cb((xx,.0075,6.65),(.025,.015,.035),mats[306],.002))
  replace(prefix+'旋钮抽屉及支脚',parts,prefix+'外形')
parts=[]
for x in [12.79,13.19]:parts.append(cb((x,1.63,6.7905),(.04,.30,.021),metal,.001))
replace('壁挂洗衣机背部固定座',parts,'壁挂洗衣机外形')
# Save the editable source; exporter contains only changed/additional geometry.
bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':added,'materialImages':[],'hidden':[]},ensure_ascii=False,indent=2))
