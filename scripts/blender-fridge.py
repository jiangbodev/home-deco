"""Built-in side-by-side refrigerator, preserving the existing cabinet opening."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];src,blend,out,report=args[:4];niche_width=float(args[4]) if len(args)>4 else .9
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
changed=[]
def P(p):return Vector((p[0],-p[2],p[1]))
def mat(mid,name,c,rough,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m['source_material_id']=mid;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
white=mat(360,'Fridge pearl silver brushed metal',(.48,.49,.48),.32,.58)
edge=mat(361,'Fridge warm anodised aluminium',(.53,.54,.52),.31,.72)
seal=mat(362,'Fridge recessed graphite seal',(.028,.031,.032),.78)
body=mat(363,'Fridge inner housing',(.59,.60,.58),.55)
def box(c,d,m,r=.001):
 bpy.ops.mesh.primitive_cube_add(size=1,location=P(c));o=bpy.context.object;o.dimensions=(d[0],d[2],d[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if r:
  b=o.modifiers.new('Manufactured edge radius','BEVEL');b.width=r;b.segments=3;bpy.ops.object.modifier_apply(modifier=b.name);b=o.modifiers.new('Planar face normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=b.name)
 return o
def replace(name,parts):
 o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();tmp=bpy.context.object;mesh=tmp.data.copy();mesh.transform(o.matrix_world.inverted()@tmp.matrix_world);o.data=mesh;bpy.data.objects.remove(tmp,do_unlink=True);changed.append(name)
# Keep the outer run footprint; resize its divider and adjacent storage bay together.
# The width is an explicit authored parameter, not a manufacturer specification.
end_z=3.339796;old_start=2.619796;new_start=end_z-niche_width;storage_start=1.989796
hidden=['冰箱外包拉手','冰箱外包门后暗缝底']
for o in list(bpy.data.objects):
 if o.type!='MESH' or o.name in hidden or o.name=='冰箱外包门板1' or o.get('source_visible') is False:continue
 is_fridge=o.name.startswith('冰箱外包');is_storage=o.name.startswith('冰箱旁高柜')
 if not(is_fridge or is_storage):continue
 mesh=o.data.copy();inverse=o.matrix_world.inverted()
 for v in mesh.vertices:
  q=o.matrix_world@v.co;z=-q.y
  z=end_z+(z-end_z)*niche_width/.72 if is_fridge else storage_start+(z-storage_start)*(new_start-storage_start)/.63
  q.y=-z;v.co=inverse@q
 o.data=mesh;changed.append(o.name)
z=(new_start+end_z)/2;w=niche_width-.060
parts=[box((3.794,.922,z),(.518,1.686,w),body,.006)]
# Two full-height vertical appliance doors with distinct rubber reveals.
for side in [-1,1]:
 door_w=(w-.014)/2;zz=z+side*(door_w/2+.004)
 parts.append(box((4.064,.941,zz),(.012,1.652,door_w+.003),seal,.003))
 parts.append(box((4.087,.941,zz),(.046,1.636,door_w-.003),white,.007))
 # Slim return-mounted vertical pulls leave a real finger gap.
 hz=z+side*.041
 parts.append(box((4.142,1.105,hz),(.015,.710,.014),edge,.005))
 for yy in [.780,1.430]:parts.append(box((4.122,yy,hz),(.040,.018,.014),edge,.003))
parts.append(box((4.066,.062,z),(.012,.060,w-.05),seal,.001))
for y in [.041,.057,.073,.089]:parts.append(box((4.074,y,z),(.006,.009,w-.054),body,.001))
replace('冰箱外包门板1',parts)
for name in hidden:bpy.data.objects[name]['source_visible']=False;bpy.data.objects[name].hide_render=True
bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':[],'materialImages':[],'hidden':hidden,'dimensions':{'nicheWidth':niche_width,'nicheHeight':1.8,'nicheDepth':.620,'applianceWidth':w,'frontX':4.15}},ensure_ascii=False,indent=2))
