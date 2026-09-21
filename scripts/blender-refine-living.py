"""Targeted edits from immutable main 844e976 runtime reconstruction (never previous output)."""
import bpy,bmesh,sys,json,math,random
from mathutils import Vector,Matrix
from pathlib import Path
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
changed={}; rng=random.Random(921)
def tris(o):
 o.data.calc_loop_triangles();return len(o.data.loop_triangles)
def mark(o):
 if o.name not in changed:changed[o.name]={'before':tris(o)}
def gw(o,v):
 p=o.matrix_world@v;return Vector((p.x,p.z,-p.y))
def local(o,p):return o.matrix_world.inverted()@Vector((p[0],-p[2],p[1]))
def replace(o,vs,fs,colors=None):
 mark(o);m=bpy.data.meshes.new(o.name+' refined');m.from_pydata([local(o,p) for p in vs],[],fs);m.update()
 for mat in o.data.materials:m.materials.append(mat)
 o.data=m
 if colors:
  a=m.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
  for d,c in zip(a.data,colors):d.color=(*c,1)
def box(v,f,center,size):
 k=len(v);x,y,z=center;a,b,c=[t/2 for t in size];v.extend([(x+i*a,y+j*b,z+l*c) for i,j,l in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]);f.extend([tuple(k+i for i in q) for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]])
def tube(o,points,radii,sides=7):
 vs=[];fs=[]
 for i,p in enumerate(points):
  t=(points[min(i+1,len(points)-1)]-points[max(i-1,0)]).normalized();a=t.cross(Vector((1,0,0))).normalized();b=t.cross(a)
  for j in range(sides):vs.append(p+radii[i]*(a*math.cos(j*math.tau/sides)+b*math.sin(j*math.tau/sides)))
 for i in range(len(points)-1):
  for j in range(sides):fs.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
 fs += [tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))];replace(o,vs,fs)
 for p in o.data.polygons:p.use_smooth=True
# Clear genuinely coplanar liner faces; move the remaining lining 1.5 mm into the recess.
for o in list(bpy.data.objects):
 if o.type!='MESH':continue
 if o.name.startswith('壁龛靠'):
  mark(o);o.data=o.data.copy();o.data.calc_loop_triangles();vs=[gw(o,v.co) for v in o.data.vertices];fs=[]
  for t in o.data.loop_triangles:
   q=[vs[i] for i in t.vertices];n=(q[1]-q[0]).cross(q[2]-q[0]);z=sum(p.z for p in q)/3
   if max(p.z for p in q)-min(p.z for p in q)<.00001 and (abs(z-6.360545)<.00003 or abs(z-6.061225)<.00003) and n.z>0:continue
   fs.append(tuple(t.vertices))
  for p in vs:
   if abs(p.z-6.360545)<.00003 or abs(p.z-6.801022)<.00003:p.z-=.0015
   if abs(p.x-12.4898)<.00005:p.x+=.0015
  replace(o,vs,fs)
 if o.name.startswith(('地毯短边包带','地毯长边包带')):
  mark(o);o.data=o.data.copy()
  for v in o.data.vertices:
   p=gw(o,v.co);p.y+=.0015;v.co=local(o,p)
 if o.name.startswith('树木_'):
  mark(o);o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(o.data);bm.free()
  m=o.modifiers.new('Window-distance tree LOD from 844e976','DECIMATE');m.ratio=.35 if 'leaves' in o.name or 'branches' in o.name else .5;m.use_collapse_triangulate=True
# Rebuild existing four-book groups in place, with different sizes, depths and selected horizontal stacks.
groups=sorted([o for o in bpy.data.objects if o.name.startswith('Blender书架增补书组')],key=lambda o:o.name)
for gi,g in enumerate(groups):
 covers=sorted([o for o in g.children if o.name.startswith('Cloth cover')],key=lambda o:o.name);page=next(o for o in g.children if o.name.startswith('Warm page'))
 old=[gw(o,v.co) for o in covers for v in o.data.vertices];x0=min(p.x for p in old);floor=min(p.y for p in old);front=6.515+rng.uniform(-.022,.018);stack=gi in [2,4,7,10,13];pv=[];pf=[];cursor=0
 for j,o in enumerate(covers):
  w=rng.uniform(.018,.044);h=rng.uniform(.175,.285);d=rng.uniform(.135,.197);cv=[];cf=[]
  # Local book axes: thickness, height, depth. Covers extend beyond inset page block.
  box(cv,cf,(-w/2+.0012,h/2,d/2),(.0024,h,d));box(cv,cf,(w/2-.0012,h/2,d/2),(.0024,h,d));box(cv,cf,(0,h/2,.0015),(w,h,.003))
  vv=[];ff=[];box(vv,ff,(0,h/2,d/2+.0015),(w-.005,h-.006,d-.007))
  # Subtle raised publisher rule, differing positions and lengths, sharing the cover material.
  col=[(rng.uniform(.65,.9),)*3 for _ in cv]
  if j%3!=1:
   k=len(cv);box(cv,cf,(0,h*(.72 if j%2 else .82),-.00025),(w*.58,.0012,.0006));col += [(.98,.98,.9)]*(len(cv)-k)
  tilt=rng.uniform(-.065,.065) if not stack else rng.uniform(-.025,.025)
  def place(p):
   x,y,z=p
   if stack:return Vector((x0+.11+y*math.cos(tilt)+(z-d/2)*math.sin(tilt)-h/2,floor+cursor+x+w/2,front+z*math.cos(tilt)-y*math.sin(tilt)))
   xx=x*math.cos(tilt)+y*math.sin(tilt);yy=y*math.cos(tilt)-x*math.sin(tilt)+abs(w/2*math.sin(tilt));return Vector((x0+cursor+w/2+xx,floor+yy,front+z))
  replace(o,[place(p) for p in cv],cf,col);off=len(pv);pv += [place(p) for p in vv];pf += [tuple(off+i for i in f) for f in ff];cursor+=w+(rng.uniform(.0008,.004) if stack else rng.uniform(.003,.011))
 replace(page,pv,pf)
# Three asymmetric woody branches, attached petioles, folded leaves of varied size/orientation.
base=Vector((6.91922,.778,4.81045));angles=[.15,2.65,4.35];heights=[.405,.49,.45];spread=[.115,.085,.055]
def branch(k,t):return base+Vector((math.cos(angles[k])*spread[k]*t*t+.008*math.sin(t*5+k)*t,heights[k]*t,math.sin(angles[k])*spread[k]*t*t))
def named(prefix,i):return bpy.data.objects[prefix+('' if i==0 else '.%03d'%i)]
for k in range(3):
 tube(named('Bent woody sprig',k),[branch(k,i/18) for i in range(19)],[.0014*(1-i/22) for i in range(19)])
 for j in range(6):
  i=k*6+j;t=.46+j*.087+rng.uniform(-.018,.018);origin=branch(k,t);az=angles[k]+(1.05 if j%2 else -1.35)+rng.uniform(-.45,.45);direction=Vector((math.cos(az),rng.uniform(-.3,.55),math.sin(az))).normalized();root=origin+direction*.011
  tube(named('Fine petiole',i),[origin,(origin+root)/2+Vector((0,.001,0)),root],[.00065,.0005,.00035],5)
  length=rng.uniform(.035,.067)*(1-.2*j/6);width=length*rng.uniform(.22,.37);side=direction.cross(Vector((0,1,0))).normalized();up=side.cross(direction).normalized();vs=[];fs=[];colors=[]
  for a in range(9):
   s=a/8;center=root+direction*(length*s)+up*(math.sin(math.pi*s)*.008-.012*s*s)
   for b in [-1,0,1]:
    vs.append(center+side*(b*width*math.sin(math.pi*s)*(.88+.12*math.cos(s*9+i)))-up*(abs(b)*.004*math.sin(math.pi*s)))
    tone=(.46 if b else .7)*(1-.12*s);colors.append((tone,tone*.95,tone*.88))
  for a in range(8):
   for b in range(2):fs.append((a*3+b,(a+1)*3+b,(a+1)*3+b+1,a*3+b+1))
  o=named('Curved pointed leaf',i);replace(o,vs,fs,colors)
  for p in o.data.polygons:p.use_smooth=True
# Preserve the existing hollow glass vessel and water (no new transmissive draws).
for o in bpy.data.objects:
 if o.get('source_visible') is False:o.hide_render=True;o.hide_set(True)
bpy.context.scene['source_provenance']='Runtime reconstructed from main 844e976; targeted living-area repairs, not original authoring file.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for name,data in changed.items():
 o=bpy.data.objects[name];o.hide_set(False);o.select_set(True);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();data['after']=len(m.loop_triangles);ev.to_mesh_clear()
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_apply=True,export_extras=True,export_tangents=True)
Path(report).write_text(json.dumps(changed,ensure_ascii=False,indent=2)+'\n');print('CHANGED',len(changed))
