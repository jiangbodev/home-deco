"""Fixture form corrections from immutable 085b161; metre-space closed solids."""
import bpy,bmesh,math,sys,json
from pathlib import Path
from mathutils import Vector
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
exec(compile(Path('scripts/blender-living-plan.py').read_text().split('# Elevation16:')[0],'helpers','exec'))
def rounded(lo,hi,y,r):
 points=[]
 for x,z,a in [(hi[0]-r,hi[1]-r,0),(lo[0]+r,hi[1]-r,90),(lo[0]+r,lo[1]+r,180),(hi[0]-r,lo[1]+r,270)]:
  for j in range(9):
   t=math.radians(a+j*90/8);points.append((x+r*math.cos(t),y,z+r*math.sin(t)))
 return points
def mesh(name,verts,faces,mat,smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata([(x,-z,y) for x,y,z in verts],[],faces);me.materials.append(mat)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 if smooth:
  for f in me.polygons:f.use_smooth=len(f.vertices)==4
 return o
def bridge(faces,a,b,N,reverse=False):
 for i in range(N):
  f=(a+i,a+(i+1)%N,b+(i+1)%N,b+i);faces.append(tuple(reversed(f)) if reverse else f)
# Retain measured opening/deck envelope, add a manufactured rounded basin interior.
inner=[rounded((7.369422,.315),(8.514421,1.025),.570,.085),rounded((7.437,.395),(8.443,.945),.220,.10),rounded((7.475,.433),(8.405,.907),.155,.115)]
outer=[rounded((7.361422,.307),(8.522421,1.033),.564,.093),rounded((7.429,.387),(8.451,.953),.214,.108),rounded((7.467,.425),(8.413,.915),.145,.123)]
N=len(inner[0]);verts=sum(inner+outer,[]);faces=[]
for a,b in [(0,N),(N,2*N),(3*N,4*N),(4*N,5*N)]:bridge(faces,a,b,N)
faces.extend([tuple(range(2*N,3*N)),tuple(reversed(range(5*N,6*N)))]);bridge(faces,0,3*N,N)
replace('浴缸深内腔',[mesh('Continuous rounded bath well',verts,faces,porcelain,True)])
# Continuous rounded rim. Top interface shares inner cavity edge; no overlapping coplanar cap.
rings=[rounded((7.304422,.250),(8.577422,1.08804),.570,.018),inner[0],rounded((7.304422,.250),(8.577422,1.08804),.505,.018),rounded((7.369422,.315),(8.514421,1.025),.505,.085)]
faces=[]
for a,b in [(0,N),(2*N,3*N),(0,2*N),(N,3*N)]:bridge(faces,a,b,N)
replace('浴缸外包1275x840',[mesh('Rounded bath rim',sum(rings,[]),faces,porcelain)])
# The new lower sidewall slopes differently: reseat existing overflow on its surface.
o=bpy.data.objects['浴缸溢水口'];o.data=o.data.copy()
for v in o.data.vertices:
 p=o.matrix_world@v.co;p.x=7.369422+(.570-p.z)*(.067578/.350)+(p.x-7.378921633)+.0002;v.co=o.matrix_world.inverted()@p
for name in ['浴缸溢水口','浴缸排水盖']:
 o=bpy.data.objects[name];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(metal);changed.append(name)
# Existing 180 mm rainfall heads and handheld plates stay in place; no live water effect.
nozzle=bpy.data.materials.new('Graphite silicone shower jets');nozzle.use_nodes=True;nozzle['source_material_id']=400
p=nozzle.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.09,.095,.10,1);p.inputs['Roughness'].default_value=.82
for suffix in ['', '.001']:
 name='顶喷出水面'+suffix;ob=bpy.data.objects[name];ps=[ob.matrix_world@v.co for v in ob.data.vertices];cx=(min(p.x for p in ps)+max(p.x for p in ps))/2;cz=-(min(p.y for p in ps)+max(p.y for p in ps))/2
 parts=[box((cx-.0725,2.071,cz-.0725),(cx+.0725,2.073,cz+.0725),metal,.00035)]
 for i in range(7):
  for j in range(7):
   x=cx+(i-3)*.018;z=cz+(j-3)*.018;parts.append(cylinder((x,2.0697,z),(x,2.0715,z),.0017,nozzle,8))
 replace(name,parts)
 name='手持花洒出水面'+suffix;ob=bpy.data.objects[name];ps=[ob.matrix_world@v.co for v in ob.data.vertices]
 if suffix:
  cx=(min(p.x for p in ps)+max(p.x for p in ps))/2;cz=.3603
  parts=[box((cx-.0225,1.350,cz-.001),(cx+.0225,1.435,cz+.001),metal,.00035)]
  for i in range(3):
   for j in range(6):
    x=cx+(i-1)*.012;y=1.36+j*.013;parts.append(cylinder((x,y,cz+.0008),(x,y,cz+.0024),.0014,nozzle,8))
 else:
  cx=5.07058;cz=-(min(p.y for p in ps)+max(p.y for p in ps))/2
  parts=[box((cx-.001,1.350,cz-.0225),(cx+.001,1.435,cz+.0225),metal,.00035)]
  for i in range(3):
   for j in range(6):
    z=cz+(i-1)*.012;y=1.36+j*.013;parts.append(cylinder((cx-.0008,y,z),(cx-.0024,y,z),.0014,nozzle,8))
 replace(name,parts)
# Explicit refrigerator factors were previously masked by importer's material reuse.
for mid,col,rough,metallic in [(360,(.58,.59,.60),.255,.96),(361,(.67,.68,.69),.20,.98)]:
 p=mats[mid].node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metallic
changed.append('冰箱外包门板1')
# One continuous external steel-louvre facade, all shower additions remain indoors.
hidden=['次卫设备区对外通风百叶','次卫外窗横框','次卫外窗横框.001','次卫外窗横框.002','次卫外窗竖框','次卫外窗竖框.001']
for name in hidden:
 o=bpy.data.objects[name];o['source_visible']=False;o.hide_render=True
def frame_loop(x0,x1,y0,y1,z):return [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
loops=[frame_loop(3.024,5.225,.08,2.370,z) for z in [-.110,-.004]]+[frame_loop(3.070,5.185,.120,2.330,z) for z in [-.110,-.004]]
faces=[]
for a,b in [(0,4),(8,12),(0,8),(4,12)]:bridge(faces,a,b,4)
parts=[mesh('Single welded steel perimeter',sum(loops,[]),faces,mats[380])]
slats=[]
for i in range(39):
 y=.15+i*.057;v=box((3.070,y,-.104),(5.185,y+.012,-.014),mats[380],.001);v.rotation_euler.x=math.radians(-30);parts.append(v);slats.append({'x':[3.070,5.185],'centerY':y+.006,'pitch':.057})
# Rear stiffener is inside the outer skin, not a dividing front window frame.
parts.append(box((4.198,.12,-.004),(4.222,2.33,.018),mats[380],.001))
replace('次卫外窗',parts)
# Validate new authored mesh shells before glTF splits normals/material vertices.
checks=[]
for name in changed:
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0000001)
 bad=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-12 for f in bm.faces);bm.free()
 checks.append({'name':name,'nonManifoldEdges':bad,'degenerateFaces':deg})
 if name not in ['浴缸溢水口','浴缸排水盖','冰箱外包门板1']:assert bad==0 and deg==0,(name,bad,deg)
bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':added,'materialImages':[],'hidden':hidden,'facadeSlats':slats,'materialOverrides':[360,361],'meshChecks':checks},ensure_ascii=False,indent=2))
