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

from mathutils import Matrix
ivory=mats[38];paper=mats[307];oak=mats[320]
for name in ['玄关餐桌连接侧体','玄关后方结构柱','玄关共用背墙']:
 o=bpy.data.objects[name];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(ivory);uvwood(o);changed.append(name)
# Proper ceiling-mounted forward-throw projector, lens facing the screen (-Z).
plastic=mats[302] if 302 in mats else ivory
housing=material(342,'Warm white projector enamel',(.77,.77,.74),.36)
dark=material(343,'Projector graphite trim',(.022,.025,.028),.46)
lens=material(344,'Coated projector optical glass',(.023,.044,.064),.13)
lens.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.45
metal=material(345,'Satin aluminium ceiling bracket',(.48,.49,.48),.35)
metal.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.75
x=11.0306;z=6.12;y=2.405
parts=[box((x,y,z),(.355,.125,.285),housing,.015),box((x,y-.024,z-.137),(.318,.066,.012),dark,.009),box((x,2.69,z),(.115,.020,.105),housing,.004),box((x,2.5775,z),(.022,.205,.022),metal,.003),box((x,2.474,z),(.15,.012,.075),metal,.003)]
def cylinder(c,r,depth,m,axis='z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=depth,location=P(c));o=bpy.context.object
 if axis=='z':o.rotation_euler[0]=math.pi/2
 o.data.materials.append(m)
 mod=o.modifiers.new('Machined rim','BEVEL');mod.width=.0012;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name)
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
parts += [cylinder((x+.079,y-.010,z-.150),.035,.021,dark),cylinder((x+.079,y-.010,z-.162),.027,.002,lens)]
for i in range(10):parts.append(box((x-.069+i*.009,y-.012,z-.144),(.003,.036,.002),dark,.0004))
for xx in [x-.178,x+.178]:
 for k in range(9):parts.append(box((xx,y+.004,z-.080+k*.019),(.002,.047,.005),dark,.0007))
# A short cable runs alongside the drop tube; its ends enter bracket and body.
parts.append(box((x+.019,2.565,z+.026),(.006,.195,.006),dark,.002))
replace(bpy.data.objects['超短焦投影机_产品外形示意'],parts)
# Mixed cloth-bound volumes with cover overhang, paper gatherings and spine print.
bottom=1.475
for i,(w,h,d,dx,dz,angle,mid) in enumerate([(.300,.027,.157,0,0,-3,330),(.273,.022,.150,-.006,.002,2,332),(.245,.032,.148,.006,-.002,-1,331)]):
 cx=11.57+dx;cz=6.772+dz;t=.0016;c=mats[mid]
 parts=[box((cx,bottom+t/2,cz),(w,t,d),c,.0006),box((cx,bottom+h-t/2,cz),(w,t,d),c,.0006),box((cx,bottom+h/2,cz+.001),(w-.006,h-2*t,d-.006),paper,.0007),box((cx,bottom+h/2,cz-d/2+.0014),(w,h,.0028),c,.001)]
 for k in range(1,7):parts.append(box((cx,bottom+t+(h-2*t)*k/7,cz+d/2-.002), (w-.008,.00018,.00025),mats[332],0))
 # Printed spine title and small publisher mark, flat on the cloth.
 for text,size,xx in [('INTERIORS' if i==0 else 'BOTANICAL' if i==1 else 'FORM',.0048,cx-.040),('01' if i==0 else '02' if i==1 else '03',.0038,cx+w*.35)]:
  curve=bpy.data.curves.new('Printed book spine','FONT');curve.body=text;curve.size=size;curve.extrude=0;curve.align_y='CENTER';o=bpy.data.objects.new('Spine typography',curve);bpy.context.collection.objects.link(o);o.location=P((xx,bottom+h/2,cz-d/2-.00015));o.rotation_euler=(-math.pi/2,0,0);curve.materials.append(paper);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);parts.append(o)
 pivot=P((cx,bottom,cz));transform=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(angle),4,'Z')@Matrix.Translation(-pivot)
 for o in parts:o.matrix_world=transform@o.matrix_world
 replace(bpy.data.objects['搁板薄书示意'+str(i)],parts);bottom+=h
# Restrained botanical print on the existing paper mount, following its 5-degree lean.
for i,(baseX,hh,mid) in enumerate([(-.055,.19,330),(.005,.24,330),(.059,.16,331)]):
 parts=[];z0=6.813;bx=11.0873+baseX;by=1.510
 parts.append(box((bx,by+hh/2,z0),(.0008,hh,.00018),mats[mid],0))
 for k in range(5):
  yy=by+.025+k*(hh-.05)/5;sign=-1 if k%2 else 1;verts=[]
  # Lens-shaped leaves of a printed twig, not freestanding bars.
  for j in range(18):
   a=2*math.pi*j/18;u=.014*math.cos(a);v=.005*math.sin(a)
   verts.append(P((bx+sign*.012+u*.84-v*.54,yy+.01+u*.54+v*.84,z0-.00015)))
  mesh=bpy.data.meshes.new('Printed botanical leaf');mesh.from_pydata(verts,[],[tuple(reversed(range(18)))]);mesh.materials.append(mats[mid]);o=bpy.data.objects.new('Printed leaf',mesh);bpy.context.collection.objects.link(o);parts.append(o)
 pivot=P((11.0873,1.475,6.816));transform=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(5),4,'X')@Matrix.Translation(-pivot)
 for o in parts:o.matrix_world=transform@o.matrix_world
 replace(bpy.data.objects['画芯线条示意'+('' if i==0 else '.'+str(i).zfill(3))],parts)
# Reference 15-主卧: closed joinery beneath the north return, not open legs.
# Preserve the already wall-aligned desktop footprint and the single chair.
cx=(12.4898+13.94898)/2;w=13.94898-12.4898;back=.236;front=.736
parts=[box((cx,.049,.48),(w-.055,.078,.44),oak,.001)]
parts += [box((12.500,.394,.486),(.020,.648,.500),oak,.0015),box((13.939,.394,.486),(.020,.648,.500),oak,.0015),box((cx,.394,back),(w-.040,.648,.018),oak,.001),box((cx,.087,.486),(w-.040,.018,.48),oak,.001)]
for i in range(3):
 dw=(w-.006)/3;xx=12.4898+.003+dw*(i+.5)
 parts.append(box((xx,.399,.727),(dw-.003,.634,.018),oak,.0013))
for p in parts:uvwood(p)
# Keep cabinet separate, using the countertop's existing module attachment.
name='主卧北窗转角地柜';template=bpy.data.objects['主卧转角连续台面'];o=template.copy();o.data=template.data.copy();o.name=name;bpy.context.collection.objects.link(o);replace(o,parts)
bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':[{'name':'主卧北窗转角地柜','template':'主卧转角连续台面'}],'materialImages':[]},ensure_ascii=False,indent=2));print('ENTRY SHELF PROJECTOR',changed)
