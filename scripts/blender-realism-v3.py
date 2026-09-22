"""Drawing/effect-reference corrections after 90a1833; immutable source."""
import bpy,bmesh,math,sys,json
from pathlib import Path
from mathutils import Vector
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
exec(compile(Path('scripts/blender-living-plan.py').read_text().split('# Elevation16:')[0],'helpers','exec'))
hidden=[]
# Elevation19: three continuous 740 mm wide / 300 mm deep / 40 mm thick shelves.
for h in [1200,1540,1920]:
 replace('主卧转角开放层板_'+str(h),[box((13.64898,h/1000,.219388),(13.94898,h/1000+.04,.959388),wood,.0015)])
# Close the measured 8 mm unsupported gap under the desktop; retain floor feet.
for name in ['主卧书桌支架','主卧书桌支架.001']:
 o=bpy.data.objects[name];o.data=o.data.copy()
 for v in o.data.vertices:
  p=o.matrix_world@v.co
  if p.z>.68:p.z+=.009*(p.z-.68)/.03;v.co=o.matrix_world.inverted()@p
 changed.append(name)
# Porcelain/acrylic bath body must not inherit the mineral countertop grey shader.
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.name in ['浴缸侧裙','浴缸前裙','浴缸外包1275x840','浴缸深内腔']:
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mats[302]);changed.append(o.name)
# Preserve white shower design but use actual satin enamel with metallic hardware.
white_names=['顶喷.001','手持花洒头.001','手持花洒柄.001','淋浴混水阀.001']
metal_names=['手持花洒软管.001','淋浴墙面固定臂.002','淋浴墙面固定臂.003','淋浴立管.001','淋浴调节旋钮.002','淋浴调节旋钮.003']
for name in white_names+metal_names:
 o=bpy.data.objects[name];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mats[380 if name in white_names else 303]);changed.append(name)
# A single upholstered wrap-back study chair, like effect15; same center/facing.
# Shape is authored at metre scale, not another chair in the aisle.
cx,cz=13.15,1.6144;verts=[];N=24
for i in range(N+1):
 t=-math.pi/2+math.pi*i/N;upper=.81-.145*abs(math.sin(t))
 for thick,y in [(0,.462),(0,upper),(.026,upper),(.026,.462)]:
  x=cx-(.244+thick)*math.cos(t);z=cz+(.241+thick)*math.sin(t);verts.append((x,-z,y))
faces=[]
for i in range(N):
 for j in range(4):faces.append((i*4+j,(i+1)*4+j,(i+1)*4+(j+1)%4,i*4+(j+1)%4))
faces.extend([(3,2,1,0),(N*4,N*4+1,N*4+2,N*4+3)])
me=bpy.data.meshes.new('Upholstered continuous chair shell');me.from_pydata(verts,[],faces);me.materials.append(mats[321]);o=bpy.data.objects.new('Chair shell',me);bpy.context.collection.objects.link(o)
for i,f in enumerate(me.polygons):f.use_smooth=(i<N*4 and i%4 in [0,2])
replace('Warm grey upholstered study chair.001',[o,box((12.917,.434,1.391),(13.335,.484,1.838),mats[321],.02)])
parts=[]
for x in [12.955,13.283]:
 for z in [1.427,1.802]:
  bx=x+(-.025 if x<13.1 else .025);bz=z+(-.025 if z<1.6 else .025)
  parts.append(cylinder((bx,.015,bz),(x,.440,z),.012,mats[306],12));parts.append(cylinder((bx,0,bz),(bx,.022,bz),.012,mats[303],12))
for z in [1.427,1.802]:parts.append(cylinder((12.955,.430,z),(13.283,.430,z),.012,mats[306],12))
replace('Warm walnut - real oak scan tinted.007',parts)
hidden+=['主卧书桌椅软座包边缝线','主卧书桌椅靠背软包包边缝线']
# Headboard shown in effect14. Kept behind mattress, no pillows or throws added.
leather=bpy.data.materials.new('Warm tobacco headboard upholstery');leather.use_nodes=True;leather['source_material_id']=390
p=leather.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.15,.092,.062,1);p.inputs['Roughness'].default_value=.72
replace('主卧床头软包靠板',[box((10.104,.499,.219388),(10.992,.965,.287),leather,.035),box((11.005,.499,.219388),(11.893,.965,.287),leather,.035)],'主卧床床架')
# Two modest book stacks and ceramic bowls on the shelves, per effect15.
# Actual covers, inset page blocks and closed bowl walls; no dining props.
covers=[]
for mid,col in [(391,(.18,.23,.20)),(392,(.31,.19,.13))]:
 m=bpy.data.materials.new('Cloth book cover '+str(mid));m.use_nodes=True;m['source_material_id']=mid;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=.86;covers.append(m)
for idx,(h,z) in enumerate([(1.24,.55),(1.58,.56)]):
 parts=[]
 for j in range(2):
  x=13.79+j*.008;zz=z-j*.018;w=.21+j*.018;d=.23-j*.012;th=.019+j*.009;y=h+j*.019
  for yy in [y+.001,y+th-.001]:parts.append(cb((x,yy,zz),(w,.002,d),covers[(idx+j)%2],.0006))
  parts.append(cb((x,y+th/2,zz+.002),(w-.012,th-.004,d-.008),mats[307],.0008))
 replace('主卧层板书册'+str(idx+1),parts,'主卧转角开放层板_'+str([1200,1540][idx]))
 # Small turned ceramic bowl, resting on the upper book cover.
 yy=h+.019+.028;vv=[];ff=[];profile=[(0,0),(.032,0),(.061,.047),(.058,.049),(.029,.006),(0,.006)]
 for r,y in profile:
  for k in range(32):
   a=k*math.pi/16;vv.append((13.79+r*math.cos(a),-(z+r*math.sin(a)),yy+y))
 for j in range(len(profile)-1):
  for k in range(32):ff.append((j*32+k,j*32+(k+1)%32,(j+1)*32+(k+1)%32,(j+1)*32+k))
 mm=bpy.data.meshes.new('Closed ceramic bowl');mm.from_pydata(vv,[],ff);mm.materials.append(mats[302]);ob=bpy.data.objects.new('Bowl',mm);bpy.context.collection.objects.link(ob)
 for f in mm.polygons:f.use_smooth=True
 replace('主卧层板陶碗'+str(idx+1),[ob],'主卧转角开放层板_'+str([1200,1540][idx]))
# Effect12: three round dark wardrobe pulls, with stems touching the door face.
for suffix in ['', '.001', '.002']:
 name='次卧右衣柜1500拉手'+suffix;ob=bpy.data.objects[name];points=[ob.matrix_world@v.co for v in ob.data.vertices];x=(min(p.x for p in points)+max(p.x for p in points))/2;y=(min(p.z for p in points)+max(p.z for p in points))/2
 parts=[cylinder((x,y,1.935),(x,y,1.949),.005,mats[306],16),cylinder((x,y,1.947),(x,y,1.957),.015,mats[306],24)]
 replace(name,parts)
# Refrigerator: neutral satin steel and brighter aluminium pulls, not grey plastic.
for mid,col,rough,metallic in [(360,(.58,.59,.60),.255,.96),(361,(.67,.68,.69),.20,.98)]:
 m=mats[mid];p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metallic
changed.append('冰箱外包门板1')
# Directional scan coordinates on new/replaced wooden boards, no end-face stretch.
for name in changed:
 ob=bpy.data.objects[name]
 if not any(m and m.get('source_material_id')==370 for m in ob.data.materials):continue
 uv=ob.data.uv_layers.active or ob.data.uv_layers.new(name='Metre grain')
 for f in ob.data.polygons:
  n=ob.matrix_world.to_3x3()@f.normal;axis=max(range(3),key=lambda i:abs(n[i]))
  for li in f.loop_indices:
   p=ob.matrix_world@ob.data.vertices[ob.data.loops[li].vertex_index].co
   uv.data[li].uv=(p.x/.78,-p.y/1.9) if axis==2 else ((p.z/.78,-p.y/1.9) if axis==0 else (p.x/.78,p.z/1.9))
for name in hidden:
 o=bpy.data.objects[name];o['source_visible']=False;o.hide_render=True
bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':added,'materialImages':[],'hidden':hidden},ensure_ascii=False,indent=2))
