"""Restore the main-bath mirror storage enclosure from plan 03 and elevation 23.
World arguments are glTF metres (X,Y height,Z); preserve sink/circulation.
"""
import bpy,sys,json
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
wood=mats[370];tile=mats[27]
# Rear storage shell, not a freestanding mirror with a paper-thin floating backing.
# Existing mirror face, width, height and front rails stay at their original coordinates.
parts=[box((7.389,1.25,2.079932),(7.409,2.37,2.989932),wood),
 box((7.409,1.25,2.079932),(8.0,2.37,2.114932),wood),
 box((7.409,1.25,2.954932),(8.0,2.37,2.989932),wood),
 box((7.409,1.25,2.114932),(8.0,1.285,2.954932),wood),
 box((7.409,2.335,2.114932),(8.0,2.37,2.954932),wood)]
replace('主卫镜柜',parts)
for i,y in enumerate([1.59,1.95]):replace('主卫镜柜内部层板'+('' if i==0 else '.001'),[box((7.409,y,2.114932),(8.155,y+.018,2.954932),wood)])
# Cabinet backing / plumbing chase follows the stepped structural column footprint.
# Tile face meets sink rear X=8.049319; mirror cabinet above provides front access.
parts=[box((7.389,0,2.079932),(8.049319,1.25,2.101932),tile),
 box((7.775,0,3.225),(8.049319,2.37,3.24688),tile),
 box((8.0,0,2.101932),(8.049319,1.25,3.225),tile),
 box((8.0,1.25,2.989932),(8.049319,2.37,3.225),tile),
 box((7.389,1.228,2.101932),(8.0,1.25,2.989932),tile),
 box((7.389,2.35,2.989932),(8.0,2.37,3.02),tile),
 box((7.775,2.35,3.02),(8.0,2.37,3.225),tile),
 box((7.389,0,2.989932),(7.411,2.37,3.02),tile),
 box((7.389,0,3.0),(7.795,2.37,3.02),tile),
 box((7.775,0,3.02),(7.795,2.35,3.225),tile)]
replace('主卫镜柜后方封闭柜身及台盆背衬',parts,'主卫台盆柜实体背板')
bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':added,'materialImages':[]},ensure_ascii=False,indent=2))
