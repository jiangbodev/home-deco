"""Local-only follow-up: clean quilt, calibrated walnut albedo and remove stale sofa AO."""
import bpy,bmesh,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
changed=[];removed=[];materials=[];added=[];transforms=[]
def local(o,p):return o.matrix_world.inverted()@Vector((p[0],-p[2],p[1]))
# The two original cushions carried AO painted for their old pillow placement.
# Remove that obsolete occlusion; runtime contact is recomputed for the current mesh.
for m in bpy.data.materials:
 mid=m.get('source_material_id')
 if mid in [95,96,97]:
  for node in m.node_tree.nodes:
   if node.type=='GROUP' and 'Occlusion' in node.inputs:
    for link in list(node.inputs['Occlusion'].links):m.node_tree.links.remove(link)
    node.inputs['Occlusion'].default_value=1
  m['remove_obsolete_occlusion']=True;materials.append(mid)
 if mid==15:
  p=m.node_tree.nodes.get('Principled BSDF');tex=p.inputs['Base Color'].links[0].from_node;assert tex.type=='TEX_IMAGE'
  img=tex.image.copy();img.name='Warm medium oak calibrated albedo';arr=np.empty(len(img.pixels),dtype=np.float32);img.pixels.foreach_get(arr);arr=arr.reshape(-1,4)
  # Lift the wood itself, preserving its grain and hue variation (no emissive fill).
  arr[:,:3]=arr[:,:3]*.50+np.array([.78,.66,.51])*.50
  img.pixels.foreach_set(arr.ravel());img.update();img.pack();tex.image=img;materials.append(mid)
# Rebuild only the primary duvet node; remove pillows/throw meshes including legacy copies.
for name,x0,x1,z0,z1 in [('fabric 1',10.098639,11.898685,.244388,2.244388),('fabric 1.001',.295068,1.79503,2.095239,4.095239)]:
 o=bpy.data.objects[name];nx,nz=24,28;vs=[];faces=[]
 for j in range(nz+1):
  t=j/nz;z=z0+.012+t*(z1-z0+.045)
  for i in range(nx+1):
   u=i/nx;x=x0-.035+u*(x1-x0+.07);edge=max(0,(abs(u-.5)*2-.9)/.1);foot=max(0,(t-.92)/.08)
   y=.54+.025*math.sin(math.pi*u)*math.sin(math.pi*t)-.105*edge*edge-.07*foot*foot+.003*math.sin(u*15+t*8)*math.sin(math.pi*u)*math.sin(math.pi*t)
   vs.append(local(o,(x,y,z)))
 for j in range(nz):
  for i in range(nx):
   a=j*(nx+1)+i;faces.append((a,a+nx+1,a+nx+2,a+1))
 mesh=bpy.data.meshes.new(name+' simple full quilt');mesh.from_pydata(vs,[],faces);mesh.update();material=o.data.materials[0].copy();material.name=name+' solid navy cotton';p=material.node_tree.nodes.get('Principled BSDF')
 for link in list(p.inputs['Base Color'].links):material.node_tree.links.remove(link)
 p.inputs['Base Color'].default_value=(.012,.022,.045,1);p.inputs['Roughness'].default_value=.94;p.inputs['Sheen Weight'].default_value=0
 for link in list(p.inputs['Normal'].links):material.node_tree.links.remove(link)
 mesh.materials.append(material);o.data=mesh;uv=mesh.uv_layers.new(name='UVMap')
 for poly in mesh.polygons:
  poly.use_smooth=True
  for li in poly.loop_indices:
   vi=mesh.loops[li].vertex_index;uv.data[li].uv=(vi%(nx+1)/nx,vi//(nx+1)/nz)
 mod=o.modifiers.new('Quilt thickness 12 mm','SOLIDIFY');mod.thickness=.012;mod.offset=-1
 changed.append(name);materials.append(material.get('source_material_id'))
for o in list(bpy.data.objects):
 if o.type=='MESH' and (o.name.startswith(('White Fabric','Fur_black')) or ('床' in o.name and any(s in o.name for s in ['枕头','床尾毯','被子']))):
  removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
# Remove the tabletop flower arrangement and vase, as requested.
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.name.startswith(('Curved pointed leaf','Bent woody sprig','Fine petiole','样板花器枝条','样板餐桌玻璃花器','Hollow glass vase','Water with visible surface','样板花器小叶')):
  removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
# Turn the full-width privacy sheet into two sliding panes, initially open.
glass=bpy.data.objects['主卫内部压纹隔断'];fixed=glass.copy();fixed.data=glass.data.copy();fixed.name='主卫内部压纹隔断固定扇';bpy.context.collection.objects.link(fixed)
added.append({'name':fixed.name,'template':glass.name})
def pane(o,x0,x1):
 vs=[local(o,(x,y,z)) for x,y,z in [(x0,.025,2.022912),(x1,.025,2.022912),(x1,2.345,2.022912),(x0,2.345,2.022912),(x0,.025,2.034948),(x1,.025,2.034948),(x1,2.345,2.034948),(x0,2.345,2.034948)]]
 mesh=bpy.data.meshes.new(o.name+' pane');mesh.from_pydata(vs,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]);mesh.materials.append(o.data.materials[0]);mesh.update();o.data=mesh;changed.append(o.name)
 uv=mesh.uv_layers.new(name='UVMap')
 for loop in mesh.loops:
  v=o.matrix_world@mesh.vertices[loop.vertex_index].co
  uv.data[loop.index].uv=((v.x-8.00856)/1.4154,(v.z-.025)/2.32)

pane(fixed,8.00856,8.71627);pane(glass,8.71627,9.42396)
for o in [glass,bpy.data.objects['主卫内部压纹隔断竖框.001']]:
 matrix=o.matrix_world.copy();matrix.translation+=Vector((-.708,-.045,0));o.matrix_world=matrix;transforms.append(o.name)
# These two bright vertical infill panels are not part of the intended niche.
# Remove the original sheets as well as the later thickened replacements.
for name in ['壁龛靠柜端600','壁龛靠柜端930']:
 o=bpy.data.objects.get(name)
 if o:removed.append(name);bpy.data.objects.remove(o,do_unlink=True)
# Weld split imported corners and smooth only rounded plaster transitions; retain sharp caps.
for name in ['圆弧包覆实体层0','圆弧包覆实体层900','圆弧包覆实体层1230','玄关前拱框','玄关左侧圆弧包覆']:
 o=bpy.data.objects[name];o.data=o.data.copy();bpy.context.view_layer.objects.active=o
 if o.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.normal_update()
 for f in bm.faces:f.smooth=True
 for e in bm.edges:e.smooth=len(e.link_faces)==2 and e.calc_face_angle(0)<math.radians(35)
 bm.to_mesh(o.data);bm.free();o.data.update();changed.append(name)
# Move the two trees outside the living-room/balcony glazing, preserving prototypes.
trees=['实物贴图窗外树_0','实物贴图窗外树_1']
for name in trees:
 o=bpy.data.objects[name];matrix=o.matrix_world.copy();matrix.translation+=Vector((1.8,0,.9));o.matrix_world=matrix
# Export material users as well, preserving IDs for exact modular integration.
selected=[]
for o in bpy.data.objects:
 if o.type=='MESH' and (o.parent and o.parent.name in trees or o.name in changed or o.name in transforms or any(m and m.get('source_material_id') in materials for m in o.data.materials)):selected.append(o)
for o in bpy.data.objects:
 p=o;visible=True
 while p:
  if p.get('source_visible') is False:visible=False
  p=p.parent
 o.hide_render=not visible
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in selected+[bpy.data.objects[name] for name in trees]:o.hide_set(False);o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_apply=True,export_extras=True,export_tangents=True)
Path(report).write_text(json.dumps({'geometry':changed,'removed':removed,'materials':materials,'trees':trees,'added':added,'transforms':transforms,'treeOffsetWorld':[1.8,.9,0]},ensure_ascii=False,indent=2)+'\n');print('Changed',changed,'removed',removed)
