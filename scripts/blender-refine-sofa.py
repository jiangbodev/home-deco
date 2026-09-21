"""Targeted sofa revision from immutable 038122d geometry; three seat cushions within the existing mesh node."""
import bpy,bmesh,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
source,blend,export,report=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(source).resolve()))
root=bpy.data.objects['Blender暖灰实物沙发'];objects=[o for o in root.children_recursive if o.type=='MESH'];print('SOFA PARTS',[(o.name,o.type) for o in objects],flush=True);assert {o.name for o in objects}>={'Sofa','Sofa Cushion','Pillow'}
center=11.03061199;factor=2.32/2.2;images={};records=[]
for o in objects:
 o.data=o.data.copy();before=[o.matrix_world@v.co for v in o.data.vertices]
 for v in o.data.vertices:
  p=o.matrix_world@v.co;p.x=center+(p.x-center)*factor;v.co=o.matrix_world.inverted()@p
 if o.name=='Sofa Cushion':
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00002)
  components=[];seen=set()
  for v in bm.verts:
   if v in seen:continue
   part=[];stack=[v];seen.add(v)
   while stack:
    a=stack.pop();part.append(a)
    for edge in a.link_edges:
     b=edge.other_vert(a)
     if b not in seen:seen.add(b);stack.append(b)
   components.append(part)
  assert len(components)==2
  xmin=min((o.matrix_world@v.co).x for v in bm.verts);xmax=max((o.matrix_world@v.co).x for v in bm.verts)
  left=min(components,key=lambda part:sum((o.matrix_world@v.co).x for v in part)/len(part))
  bmesh.ops.delete(bm,geom=[v for v in bm.verts if v not in set(left)],context='VERTS')
  sourceMin=min((o.matrix_world@v.co).x for v in bm.verts);sourceMax=max((o.matrix_world@v.co).x for v in bm.verts)
  base=list(bm.verts)+list(bm.edges)+list(bm.faces);sets=[list(bm.verts)]
  for _ in range(2):sets.append([v for v in bmesh.ops.duplicate(bm,geom=base)['geom'] if isinstance(v,bmesh.types.BMVert)])
  gap=.012;width=(xmax-xmin-gap*2)/3
  for i,vs in enumerate(sets):
   for v in vs:
    p=o.matrix_world@v.co;p.x=xmin+i*(width+gap)+(p.x-sourceMin)/(sourceMax-sourceMin)*width;v.co=o.matrix_world.inverted()@p
  mesh=bpy.data.meshes.new('Three tailored seat cushions')
  for m in o.data.materials:mesh.materials.append(m)
  bm.to_mesh(mesh);bm.free();mesh.update();o.data=mesh
  for face in mesh.polygons:face.use_smooth=True
 if o.name in ['Sofa','Sofa Cushion','Pillow']:
  for i,material in enumerate(o.data.materials):
   m=material.copy();o.data.materials[i]=m;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.92
   link=p.inputs['Base Color'].links[0];node=link.from_node;assert node.type=='TEX_IMAGE'
   old=node.image
   if old.name not in images:
    img=old.copy();img.name='Sofa warm ivory woven base';a=np.empty(len(img.pixels),dtype=np.float32);img.pixels.foreach_get(a);a=a.reshape(-1,4);a[:,:3]=a[:,:3]*.60+np.array([.90,.89,.87])*.40;img.pixels.foreach_set(a.ravel());img.update();img.pack();images[old.name]=img
   node.image=images[old.name]
 after=[o.matrix_world@v.co for v in o.data.vertices];o.data.calc_loop_triangles();records.append({'name':o.name,'triangles':len(o.data.loop_triangles),'widthBefore':max(v.x for v in before)-min(v.x for v in before),'widthAfter':max(v.x for v in after)-min(v.x for v in after)})
for o in bpy.data.objects:
 p=o;visible=True
 while p:
  if p.get('source_visible') is False:visible=False
  p=p.parent
 o.hide_render=not visible
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.hide_set(False);o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(Path(export).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_image_format='AUTO')
Path(report).write_text(json.dumps({'source':'038122d','widthMetres':2.32,'colorMix':.40,'seatCushions':3,'seatGapMetres':.012,'objects':records},indent=2))
