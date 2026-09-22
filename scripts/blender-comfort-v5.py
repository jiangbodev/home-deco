"""Chair silhouette, wool rug edge, and constructed book details; immutable v4 input."""
import bpy,bmesh,math,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
exec(compile(Path('scripts/blender-living-plan.py').read_text().split('# Elevation16:')[0],'helpers','exec'))
def softbox(c,d,m,r):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(c[0],-c[2],c[1]));o=bpy.context.object;o.dimensions=(d[0],d[2],d[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 b=o.modifiers.new('Upholstery eased corners','BEVEL');b.width=r;b.segments=6;bpy.ops.object.modifier_apply(modifier=b.name)
 for f in o.data.polygons:f.use_smooth=True
 b=o.modifiers.new('Weighted panel normals','WEIGHTED_NORMAL');b.keep_sharp=True;bpy.ops.object.modifier_apply(modifier=b.name)
 return o
# A padded, gently concave back. No horseshoe wrap or lower notch.
seat=softbox((13.126,.461,1.6144),(.435,.060,.452),mats[321],.029)
back=softbox((12.946,.643,1.6144),(.067,.336,.449),mats[321],.029)
for v in back.data.vertices:
 p=back.matrix_world@v.co;p.x+=.030*((-p.y-1.6144)/.2245)**2-.025*((p.z-.475)/.336)
 v.co=back.matrix_world.inverted()@p
replace('Warm grey upholstered study chair.001',[seat,back])
# Keep floor contacts, remove shiny silver ferrules on the understated dark frame.
o=bpy.data.objects['Warm walnut - real oak scan tinted.007'];o.data=o.data.copy()
for i,m in enumerate(o.data.materials):
 if m and m.get('source_material_id')==303:o.data.materials[i]=mats[306]
changed.append(o.name)
# Short wool pile: rounded textile slab, all four edges seated on the floor.
# Fine loop-pile relief is handled by the distance-filtered runtime material.
x0,x1,z0,z1=10.097336,12.247336,4.281236,6.231236
rug=softbox(((x0+x1)/2,.0095,(z0+z1)/2),(x1-x0,.013,z1-z0),mats[51],.005)
# Consistent metre UVs for the retained source textile maps.
uv=rug.data.uv_layers.active
for f in rug.data.polygons:
 for li in f.loop_indices:
  p=rug.matrix_world@rug.data.vertices[rug.data.loops[li].vertex_index].co;uv.data[li].uv=((p.x-x0)/(x1-x0),(-p.y-z0)/(z1-z0))
replace('客厅地毯_效果06至08',[rug])
# Narrow bound edge; physically rounded instead of broad flat strips.
for name,lo,hi in [('地毯短边包带',(x0,.003,z0),(x0+.010,.017,z1)),('地毯短边包带.001',(x1-.010,.003,z0),(x1,.017,z1)),('地毯长边包带',(x0+.010,.003,z0),(x1-.010,.017,z0+.010)),('地毯长边包带.001',(x0+.010,.003,z1-.010),(x1-.010,.017,z1))]:
 c=[(a+b)/2 for a,b in zip(lo,hi)];d=[b-a for a,b in zip(lo,hi)];replace(name,[softbox(c,d,mats[100],.003)])
# Existing bookshelf page blocks: assign UV.x along each block's page-stack axis.
# Author per connected block; independent of upright vs stacked placement and tilt.
page_nodes=[]
for o in list(bpy.data.objects):
 if o.type!='MESH' or not o.name.startswith('Warm page edges') or o.get('source_visible') is False:continue
 o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(o.data);bm.free();me=o.data
 adj={v.index:set() for v in me.vertices}
 for e in me.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
 unseen=set(adj);axes={}
 while unseen:
  root=next(iter(unseen));group={root};todo=[root];unseen.remove(root)
  while todo:
   for q in adj[todo.pop()]:
    if q in unseen:unseen.remove(q);group.add(q);todo.append(q)
  edges=[(me.vertices[b].co-me.vertices[a].co) for a in group for b in adj[a] if b in group]
  axis=min((v for v in edges if v.length>1e-6),key=lambda v:v.length).normalized()
  for i in group:axes[i]=axis
 uv=me.uv_layers.active or me.uv_layers.new(name='Page spacing metres')
 for li,l in enumerate(me.loops):uv.data[li].uv=(me.vertices[l.vertex_index].co.dot(axes[l.vertex_index]),0)
 changed.append(o.name);page_nodes.append(o.name)
# Close the existing protruding end face with a proper L-shaped return.
# Keep the original continuous niche-facing plane; no new rear step.
for h in [.6,.93]:
 pts=[(12.22959,6.35904),(12.61966,6.35904),(12.61966,6.79952),(12.49130,6.79952),(12.49130,6.38704),(12.22959,6.38704)]
 vv=[(x,-z,y) for y in [h,h+.30] for x,z in pts];ff=[tuple(reversed(range(6))),tuple(range(6,12))]+[(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
 me=bpy.data.meshes.new('Closed L return');me.from_pydata(vv,[],ff);me.materials.append(mats[38]);bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new('Niche return',me);bpy.context.collection.objects.link(ob);replace('壁龛靠沙发端'+str(round(h*1000)),[ob])
for h in [.6,.93]:
 replace('壁龛背部'+str(round(h*1000)),[box((12.61966,h,6.061224),(12.64964,h+.30,6.80102),mats[38],.002)])
# Rounded slim duroplast toilet lids, separate from the glazed bowl material.
lidmat=bpy.data.materials.new('Warm white satin thermoset toilet seat');lidmat.use_nodes=True;lidmat['source_material_id']=401
bs=lidmat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.87,.855,.825,1);bs.inputs['Roughness'].default_value=.30
for prefix in ['主卫壁挂马桶','次卫壁挂马桶']:
 ob=bpy.data.objects[prefix+'闭合盖板'];ps=[ob.matrix_world@v.co for v in ob.data.vertices];x0=min(p.x for p in ps);x1=max(p.x for p in ps);z0=-max(p.y for p in ps);z1=-min(p.y for p in ps);cx=(x0+x1)/2;cz=(z0+z1)/2;rad=(z1-z0)/2
 pts=[]
 # Flat rear with 25mm corners and a continuous semicircular front.
 for ax,az,a0,a1,r in [(x0+.025,z0+.025,180,270,.025),(x1-rad,cz,270,450,rad),(x0+.025,z1-.025,90,180,.025)]:
  steps=32 if r==rad else 8
  for k in range(steps+1):
   a=math.radians(a0+(a1-a0)*k/steps);pts.append((ax+r*math.cos(a),az+r*math.sin(a)))
 verts=[];faces=[];N=len(pts)
 for scale,y in [(.982,.428),(1,.431),(1,.439),(.985,.444),(.85,.447),(.35,.449)]:
  verts.extend([(cx+(x-cx)*scale,-(cz+(z-cz)*scale),y) for x,z in pts])
 for j in range(5):
  for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 faces.extend([tuple(reversed(range(N))),tuple(range(5*N,6*N))]);me=bpy.data.meshes.new('Domed thin D lid');me.from_pydata(verts,[],faces);me.materials.append(lidmat)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();tmp=bpy.data.objects.new('D lid',me);bpy.context.collection.objects.link(tmp)
 for f in me.polygons:f.use_smooth=len(f.vertices)==4
 replace(prefix+'闭合盖板',[tmp])
 ob=bpy.data.objects[prefix+'座圈'];ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(lidmat);changed.append(ob.name)
 for suffix in ['缓降铰链','缓降铰链.001','冲水面板','双档按钮','双档按钮.001']:
  ob=bpy.data.objects[prefix+suffix];ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(metal);changed.append(ob.name)
# Ease the bath apron and rim edges, retaining the measured envelope.
for name in ['浴缸侧裙','浴缸前裙','浴缸外包1275x840']:
 ob=bpy.data.objects[name];ob.data=ob.data.copy();bpy.context.view_layer.objects.active=ob
 if ob.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.dissolve_limit(bm,angle_limit=.001,verts=list(bm.verts),edges=list(bm.edges));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 mod=ob.modifiers.new('Rolled acrylic edge','BEVEL');mod.width=.002;mod.segments=3;mod.limit_method='ANGLE';bpy.ops.object.modifier_apply(modifier=mod.name)
 for f in ob.data.polygons:f.use_smooth=True
 mod=ob.modifiers.new('Planar panel and rounded edges','WEIGHTED_NORMAL');mod.keep_sharp=True;bpy.ops.object.modifier_apply(modifier=mod.name);changed.append(name)
# User asks to keep the bedroom shelves empty.
hidden=['主卧层板书册1','主卧层板书册2','主卧层板陶碗1','主卧层板陶碗2']
for name in hidden:
 o=bpy.data.objects[name];o['source_visible']=False;o.hide_render=True
# Existing lacquer carries a roughness map; newly closed returns need UVs.
for name in changed:
 o=bpy.data.objects[name]
 if o.data.uv_layers:continue
 uv=o.data.uv_layers.new(name='Metre surface UV')
 for f in o.data.polygons:
  n=o.matrix_world.to_3x3()@f.normal;axis=max(range(3),key=lambda i:abs(n[i]))
  for li in f.loop_indices:
   p=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
   uv.data[li].uv=(p.x,-p.y) if axis==2 else ((p.x,p.z) if axis==1 else (-p.y,p.z))
checks=[]
for name in changed:
 o=bpy.data.objects[name]
 if name.startswith('Warm page'):continue
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
 checks.append({'name':name,'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'degenerateFaces':sum(f.calc_area()<1e-12 for f in bm.faces)});bm.free()
 if name in ['Warm grey upholstered study chair.001','客厅地毯_效果06至08'] or name.startswith(('地毯','壁龛')) or name.endswith('闭合盖板'):assert checks[-1]['nonManifoldEdges']==0 and checks[-1]['degenerateFaces']==0,checks[-1]
bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':[],'materialImages':[],'hidden':hidden,'pageNodes':page_nodes,'meshChecks':checks},ensure_ascii=False,indent=2))
