"""Visible dining furniture: directional oak UVs and constructed trestle table."""
import bpy,bmesh,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
mats={m.get('source_material_id'):m for m in bpy.data.materials};changed=[]
def P(p):return Vector((p[0],-p[2],p[1]))
def box(c,d,m,r=.002):
 bpy.ops.mesh.primitive_cube_add(size=1,location=P(c));o=bpy.context.object;o.dimensions=(d[0],d[2],d[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if r:
  b=o.modifiers.new('Joinery edge radius','BEVEL');b.width=r;b.segments=3;bpy.ops.object.modifier_apply(modifier=b.name);b=o.modifiers.new('Face normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=b.name)
 return o
# Recover oak grain contrast from the existing original scan, in linear colour.
for mid in [25,32,35]:
 m=mats[mid];p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.48
 
 for n in m.node_tree.nodes:
  if n.type=='UVMAP':n.uv_map='UVMap'
 tex=p.inputs['Base Color'].links[0].from_node;img=tex.image.copy();img.name='Dining oak grain '+str(mid)
 a=np.empty(len(img.pixels),dtype=np.float32);img.pixels.foreach_get(a);a=a.reshape(-1,4);rgb=a[:,:3];mean=rgb.mean(axis=0);rgb[:]=np.clip((rgb-mean)*1.85+mean*1.28,.018,.88);img.pixels.foreach_set(a.ravel());img.update();img.pack();tex.image=img

def uv(o,long_axis='x'):
 layer=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
 for f in o.data.polygons:
  norm=o.matrix_world.to_3x3()@f.normal;axis=max(range(3),key=lambda i:abs(norm[i]))
  for li in f.loop_indices:
   q=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co;x,y,z=q.x,q.z,-q.y
   # Scan fibres run along V. Horizontal rails/top run X; uprights run Y.
   if long_axis=='x':coord=(z/.78,x/1.9) if axis==2 else ((y/.78,x/1.9) if axis==1 else (z/.78,y/1.9))
   else:coord=(x/.78,y/1.9) if axis==1 else (z/.78,y/1.9)
   layer.data[li].uv=coord

def replace(name,parts):
 o=bpy.data.objects[name];assert o.get('source_visible',True),name;bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();tmp=bpy.context.object;mesh=tmp.data.copy();mesh.transform(o.matrix_world.inverted()@tmp.matrix_world);o.data=mesh;bpy.data.objects.remove(tmp,do_unlink=True);changed.append(name)

m=mats[25];cx=6.4292178;cz=4.7304427
parts=[box((cx,.7275,cz),(1.77,.045,.85),m,.0045)]
uv(parts[-1])
for xx in [cx-.56,cx+.56]:
 # Solid tapered trestle with a waisted inner silhouette and a broad foot.
 profile=[(-.28,.05),(-.28,.095),(-.215,.12),(-.17,.24),(-.19,.52),(-.255,.66),(-.255,.705),(.255,.705),(.255,.66),(.19,.52),(.17,.24),(.215,.12),(.28,.095),(.28,.05)]
 verts=[P((xx+side*.043,y,cz+z)) for side in [-1,1] for z,y in profile];n=len(profile);faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh=bpy.data.meshes.new('Solid oak waisted trestle');mesh.from_pydata(verts,[],faces);mesh.materials.append(m);o=bpy.data.objects.new('Trestle',mesh);bpy.context.collection.objects.link(o)
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();bpy.context.view_layer.objects.active=o;b=o.modifiers.new('Rounded trestle edges','BEVEL');b.width=.003;b.segments=3;bpy.ops.object.modifier_apply(modifier=b.name);b=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=b.name);uv(o,'y');parts.append(o)
 foot=box((xx,.025,cz),(.13,.05,.60),m,.003);uv(foot);parts.append(foot)
rail=box((cx,.23,cz),(1.04,.075,.065),m,.002);uv(rail);parts.append(rail)
replace('Warm walnut - real oak scan tinted',parts)
# Retain existing chair and bench silhouettes; restore their actual wood material and UV scale.
for name in ['Warm walnut - real oak scan tinted.001','Warm walnut - real oak scan tinted.002','Warm walnut - real oak scan tinted.003']:
 o=bpy.data.objects[name];assert o.get('source_visible',True);o.data=o.data.copy();uv(o,'y' if not name.endswith('.003') else 'x');changed.append(name)
# Curved cane dining armchairs: real open weave, continuous bent rim and tapered legs.
def newmat(mid,name,rgb,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;m['source_material_id']=mid;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=rough;return m
canes=[newmat(351,'Natural cane fibre honey',(.48,.36,.22),.63),newmat(352,'Natural cane fibre light',(.57,.45,.29),.65),newmat(353,'Natural cane fibre toasted',(.40,.29,.17),.61)]
for m in canes:m.use_backface_culling=False

def tube(points,r,mat,name='Bent timber rail',sides=10):
 verts=[];faces=[]
 for i,point in enumerate(points):
  p=P(point);t=P(points[min(i+1,len(points)-1)])-P(points[max(i-1,0)]);t.normalize();up=Vector((0,0,1)) if abs(t.z)<.9 else Vector((1,0,0));u=t.cross(up).normalized();v=t.cross(u).normalized()
  for k in range(sides):verts.append(p+r*(u*math.cos(k*2*math.pi/sides)+v*math.sin(k*2*math.pi/sides)))
 for j in range(len(points)-1):
  for k in range(sides):faces.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
 faces.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+k for k in range(sides))]);mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(mat)
 for f in mesh.polygons:f.use_smooth=len(f.vertices)==4
 o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);uv(o,'y');return o

def canePoint(cx,t,v,offset=0):
 top=.655+.142*math.cos(t);y=.518+v*(top-.518);return (cx+(.226+offset)*math.sin(t),y,4.355-(.235+offset)*math.cos(t))
hidden=[]
for index,cx in enumerate([6.1792178,6.6792178]):
 suffix='' if index==0 else '.001';frameName='Warm walnut - real oak scan tinted.'+str(index+1).zfill(3);m=mats[32];parts=[]
 for sx in [-1,1]:
  for rear in [False,True]:
   ztop=4.19 if rear else 4.50;zfloor=ztop+(-.04 if rear else .035)
   a=(cx+sx*.202,.014,zfloor);b=(cx+sx*.175,.441,ztop);parts.append(tube([a,b],.014,m,'Tapered oak leg',12))
 for z in [4.18,4.51]:parts.append(box((cx,.43,z),(.38,.04,.027),m,.003))
 for sx in [-1,1]:parts.append(box((cx+sx*.18,.43,4.345),(.024,.04,.33),m,.003))
 angles=np.linspace(-1.75,1.75,49)
 for v,radius in [(0,.010),(1,.012)]:parts.append(tube([canePoint(cx,float(t),v) for t in angles],radius,m,'Continuous bent oak rim',10))
 for t in [-1.75,1.75]:
  x,y,z=canePoint(cx,t,1);parts.append(tube([(cx+math.copysign(.175,t),.44,4.50),(x,.54,z+.012),(x,y,z)],.011,m,'Arm support',10))
 for t in [-1.75,1.75]:parts.append(tube([canePoint(cx,t,0),canePoint(cx,t,1)],.009,m,'Closed cane end post',10))
 for t in [-.9,.9]:
  x,y,z=canePoint(cx,t,0);parts.append(tube([(cx+math.copysign(.175,t),.435,4.19),(x,y,z)],.011,m,'Rear backrest support',10))
 for o in parts:uv(o,'y')
 replace(frameName,parts)
 # Interlaced ribbons, not an opaque printed rectangle. Thin strips retain actual holes.
 verts=[];faces=[];ids=[];count=40;rows=12
 for k in range(count+1):
  t=-1.70+3.40*k/count;start=len(verts)
  for j in range(rows*2+1):
   v=j/(rows*2);wave=.0011*math.cos(v*rows*math.pi*2+k*math.pi)
   for dt in [-.007,.007]:verts.append(P(canePoint(cx,t+dt,v,wave)))
  for j in range(rows*2):faces.append((start+j*2,start+j*2+1,start+j*2+3,start+j*2+2));ids.append(k%3)
 for j in range(1,rows):
  v=j/rows;start=len(verts)
  for k in range(count*2+1):
   t=-1.70+3.40*k/(count*2);wave=-.0011*math.cos(k*math.pi+j*math.pi)
   for dv in [-.008,.008]:verts.append(P(canePoint(cx,t,v+dv,wave)))
  for k in range(count*2):faces.append((start+k*2,start+k*2+1,start+k*2+3,start+k*2+2));ids.append((j+1)%3)
 mesh=bpy.data.meshes.new('Open woven cane shell');mesh.from_pydata(verts,[],faces)
 for m in canes:mesh.materials.append(m)
 for f,mid in zip(mesh.polygons,ids):f.material_index=mid;f.use_smooth=True
 o=bpy.data.objects.new('Open cane',mesh);bpy.context.collection.objects.link(o);replace('Natural woven cane'+suffix,[o])
 # Legacy flat weave and edging would intersect the new curved shell.
 for o in list(bpy.data.objects):
  if o.name.startswith('餐椅'+str(index+1)) and any(s in o.name for s in ['斜向藤编','靠背边条','靠背软包包边缝线']):hidden.append(o.name);o['source_visible']=False;o.hide_render=True

bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':[],'materialImages':[25,32,35],'hidden':hidden,'materialTexcoords':{25:0,32:0,35:0},'clearOcclusionMaterials':[33]},ensure_ascii=False,indent=2))
