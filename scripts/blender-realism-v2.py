"""Incremental realism pass: constructed entry objects, smooth foliage and timber edges."""
import bpy,bmesh,sys,json,math
from pathlib import Path
from mathutils import Vector
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
changed=[];mats={m.get('source_material_id'):m for m in bpy.data.materials}
def P(p):return Vector((p[0],-p[2],p[1]))
def material(mid,name,color,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;m['source_material_id']=mid;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
stone=material(340,'Warm ivory stoneware glaze',(.64,.61,.54),.31)
leafmat=material(341,'Natural broad leaf satin green',(.065,.155,.029),.46)
leafmat.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.13
paper=mats[307];covers=[mats[330],mats[332],mats[331],mats[333],mats[332]]
def bounds(o):
 ps=[o.matrix_world@v.co for v in o.data.vertices];return [min(p[i] for p in ps) for i in range(3)],[max(p[i] for p in ps) for i in range(3)]
def box(c,d,m,r=.0006):
 bpy.ops.mesh.primitive_cube_add(size=1,location=P(c));o=bpy.context.object;o.dimensions=(d[0],d[2],d[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if r:
  mod=o.modifiers.new('Soft edge','BEVEL');mod.width=r;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name)
  mod=o.modifiers.new('Planar normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=mod.name)
 return o
def replace(o,parts):
 bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();tmp=bpy.context.object;mesh=tmp.data.copy();mesh.transform(o.matrix_world.inverted()@tmp.matrix_world);o.data=mesh;bpy.data.objects.remove(tmp,do_unlink=True);changed.append(o.name)
def uvwood(o):
 uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
 for poly in o.data.polygons:
  n=o.matrix_world.to_3x3()@poly.normal;axis=max(range(3),key=lambda i:abs(n[i]))
  for li in poly.loop_indices:
   p=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
   uv.data[li].uv=(p.x*.8,-p.y*.8) if axis==2 else ((p.x*.8,p.z*.8) if axis==1 else (-p.y*.8,p.z*.8))
for o in list(bpy.data.objects):
 if o.type!='MESH':continue
 if o.name.startswith('玄关书籍_陈设示意'):
  lo,hi=bounds(o);i=0 if '.' not in o.name else int(o.name.rsplit('.',1)[1]);c=covers[i];x=(lo[0]+hi[0])/2;z=-(lo[1]+hi[1])/2;y=(lo[2]+hi[2])/2;w=hi[0]-lo[0];h=hi[2]-lo[2];d=hi[1]-lo[1];t=.0018
  parts=[box((x-w/2+t/2,y,z),(t,h,d),c),box((x+w/2-t/2,y,z),(t,h,d),c),box((x,y,z-.0015),(w-2*t,h-.004,d-.005),paper),box((x,y,z+d/2-t/2),(w,h,t),c)]
  # Shallow bands printed into the spine; no text-shaped extruded blocks.
  for yy in [y+h*.24,y-h*.30]:parts.append(box((x,yy,z+d/2+.00015),(w*.65,.0011,.0003),paper,0))
  replace(o,parts)
 if o.name.startswith('玄关陶器_陈设示意'):
  lo,hi=bounds(o);cx=(lo[0]+hi[0])/2;cy=(lo[1]+hi[1])/2;bottom=lo[2];h=hi[2]-lo[2];r=(hi[0]-lo[0])/2
  # Revolved closed ceramic body, open neck, inner wall and recessed foot.
  profile=[(.68,.0),(.72,.015),(.84,.04),(.96,.12),(1,.23),(.97,.36),(.84,.52),(.65,.68),(.42,.81),(.36,.89),(.36,.98),(.34,1),(.25,1),(.25,.96),(.26,.90),(.33,.82),(.56,.67),(.75,.51),(.88,.35),(.9,.23),(.84,.12),(.68,.06),(0,.06),(0,0),(.68,0)]
  verts=[(cx+r*rr*math.cos(k*2*math.pi/64),cy+r*rr*math.sin(k*2*math.pi/64),bottom+h*yy) for rr,yy in profile for k in range(64)];faces=[]
  for j in range(len(profile)-1):
   for k in range(64):faces.append((j*64+k,j*64+(k+1)%64,(j+1)*64+(k+1)%64,(j+1)*64+k))
  mesh=bpy.data.meshes.new('Wheel-thrown ceramic vessel');mesh.from_pydata(verts,[],faces);mesh.materials.append(stone);tmp=bpy.data.objects.new('Ceramic shell',mesh);bpy.context.collection.objects.link(tmp)
  bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
  for f in mesh.polygons:f.use_smooth=True
  replace(o,[tmp])
 if o.name.startswith('Curved broad leaf'):
  o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000015);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  # Keep the authored tip/stem and silhouette, smooth the faceted shading.
  for f in bm.faces:f.smooth=True
  bm.to_mesh(o.data);bm.free();o.data.materials.clear();o.data.materials.append(leafmat);changed.append(o.name)
 if o.name.startswith(('玄关层板_1070','玄关层板_1430','玄关层板_1790','主卧转角开放层板','厨房开放层板','床侧书柜层板')):
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mats[320]);bpy.context.view_layer.objects.active=o
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bm.to_mesh(o.data);bm.free()
  if len(o.data.polygons)<40:
   mod=o.modifiers.new('Small solid timber edge radius','BEVEL');mod.width=.0015;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name)
   mod=o.modifiers.new('Weighted manufactured normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=mod.name)
  uvwood(o);changed.append(o.name)
bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':[],'materialImages':[]},ensure_ascii=False,indent=2));print('REALISM V2',len(changed))
