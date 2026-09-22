"""Restore entry lacquer and plan13 northwest guest-bath condenser bay."""
import bpy,math,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
# Reuse the established geometric helpers without executing its prior mutations.
helper=Path('scripts/blender-living-plan.py').read_text().split('# Elevation16:')[0]
exec(compile(helper,'living-plan-helpers','exec'))
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.name.startswith('入户侧高柜') and any(k in o.name for k in ['实体','门板','顶封板']):
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mats[38]);changed.append(o.name)
  uv=o.data.uv_layers.active or o.data.uv_layers.new(name='Cabinet UV')
  for f in o.data.polygons:
   n=o.matrix_world.to_3x3()@f.normal;axis=max(range(3),key=lambda i:abs(n[i]))
   for li in f.loop_indices:
    p=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(p.x,-p.y) if axis==2 else ((p.x,p.z) if axis==1 else (-p.y,p.z))
# Extend the existing wet-area floor cutout into the service bay.
o=bpy.data.objects['木地板基面_湿区真实留空'];o.data=o.data.copy()
cut=box((3.024,-.20,.121),(4.239,.10,.974),mats[27],0)
bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Guest service bay floor opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True);changed.append(o.name)
# Drawing13 locates the outdoor unit west of the shower in the northern recess.
# Detailed product dimensions are inferred; preserve shower and window geometry.
replace('次卫外机设备区地台',[box((3.024,-.10,.121),(4.239,-.02,.974),mats[27])],'次卫淋浴地面')
replace('次卫外机设备区顶封',[box((3.024,2.35,.121),(3.973,2.7,.974),mats[196])],'次卫铝扣板低顶')
enamel=mats[380];steel=mats[303];black=mats[306]
# Raised base rails and vibration mounts visibly support the condenser.
parts=[]
for x in [3.22,3.99]:
 parts.append(box((x-.04,-.02,.19),(x+.04,.035,.70),steel,.002))
 for z in [.25,.62]:parts.append(cb((x,.0525,z),(.07,.035,.075),black,.002))
replace('次卫中央空调外机安装底座',parts,'次卫淋浴地面')
# Sheet-metal box, 1.00m wide x .43m deep x 1.26m high, front toward bay access.
parts=[box((3.11,.07,.20),(4.11,1.33,.63),enamel,.009)]
parts += [box((3.11,1.33,.19),(4.12,1.347,.64),enamel,.003),box((3.88,.09,.632),(4.09,1.30,.640),enamel,.002)]
for y in [.15,1.22]:
 for x in [3.91,4.065]:parts.append(cylinder((x,y,.639),(x,y,.643),.004,steel,8))
replace('次卫中央空调外机机壳',parts,'次卫淋浴地面')
def guard_ring(cx,cy,z,r,tube=.002):
 verts=[];faces=[];N=48;K=6
 for i in range(N):
  a=i*2*math.pi/N
  for j in range(K):
   b=j*2*math.pi/K;rr=r+tube*math.cos(b);verts.append((cx+rr*math.cos(a),-(z+tube*math.sin(b)),cy+rr*math.sin(a)))
 for i in range(N):
  for j in range(K):faces.append((i*K+j,((i+1)%N)*K+j,((i+1)%N)*K+(j+1)%K,i*K+(j+1)%K))
 me=bpy.data.meshes.new('Continuous fan guard');me.from_pydata(verts,[],faces);me.materials.append(steel);o=bpy.data.objects.new('Guard ring',me);bpy.context.collection.objects.link(o)
 for f in me.polygons:f.use_smooth=True
 return o
# Twin recessed fan fields with manufactured guards; no transparent materials.
parts=[]
for cy in [.39,1.01]:
 cx=3.49;r=.255
 parts.append(cylinder((cx,cy,.631),(cx,cy,.635),r,black,48))
 # Three curved-looking paddles, swept by radial stations behind safety grille.
 for k in range(3):
  verts=[]
  for radius,offset,w in [(.055,0,.026),(.15,.22,.06),(.224,.46,.038)]:
   a=k*2*math.pi/3+offset
   for da in [-w/radius,w/radius]:verts.append((cx+radius*math.cos(a+da),-.639,cy+radius*math.sin(a+da)))
  me=bpy.data.meshes.new('Fan blade');me.from_pydata(verts,[],[(0,1,3,2),(2,3,5,4)]);me.materials.append(steel);o=bpy.data.objects.new('Blade',me);bpy.context.collection.objects.link(o);parts.append(o)
 for radius in [.07,.12,.17,.22,.255]:
  parts.append(guard_ring(cx,cy,.655,radius))
 for k in range(8):
  a=k*math.pi/4;parts.append(cylinder((cx,cy,.655),(cx+.254*math.cos(a),cy+.254*math.sin(a),.655),.0025,steel,6))
 parts.append(cylinder((cx,cy,.642),(cx,cy,.662),.046,enamel,24))
# Side heat-exchanger vents readable from shower entrance.
parts.append(box((4.111,.20,.245),(4.113,1.20,.585),black,0))
for i in range(26):parts.append(box((4.113,.20+i*.038,.245),(4.12,.207+i*.038,.585),enamel,0))
replace('次卫中央空调外机风扇及格栅',parts,'次卫淋浴地面')
# Two insulated refrigerant runs to the existing north service wall.
parts=[]
for x in [3.96,4.015]:
 parts.append(cylinder((x,.25,.19),(x,.25,.14),.012,black,12))
 parts.append(cylinder((x,.25,.14),(x,2.23,.14),.012,black,12))
 parts.append(cylinder((x,2.23,.14),(x,2.23,.121),.015,enamel,12))
replace('次卫中央空调外机保温管',parts,'次卫淋浴地面')
# Separate the wet shower from the service bay. Fixed gasketed service panel
# is intentionally not an opening animation; removal/installation are not simulated.
replace('次卫设备区挡水坎',[box((4.16,-.02,.121),(4.239,.10,.695),mats[27],.001)],'次卫淋浴地面')
parts=[]
for z in [.137,.679]:parts.append(box((4.19,.10,z-.016),(4.222,2.35,z+.016),enamel,.001))
for y in [.116,2.334]:parts.append(box((4.19,y-.016,.137),(4.222,y+.016,.679),enamel,.001))
replace('次卫设备区防溅隔断框',parts,'次卫淋浴地面')
replace('次卫设备区密封检修玻璃',[box((4.201,.132,.153),(4.209,2.318,.663),mats[10],0)],'次卫淋浴地面')
parts=[]
for z in [.155,.661]:parts.append(box((4.198,.13,z-.002),(4.212,2.32,z+.002),mats[312],0))
for y in [.132,2.318]:parts.append(box((4.198,y-.002,.153),(4.212,y+.002,.663),mats[312],0))
for y in [.21,1.22,2.24]:
 for z in [.136,.680]:parts.append(cylinder((4.222,y,z),(4.225,y,z),.004,steel,8))
replace('次卫设备区密封及检修固定件',parts,'次卫淋浴地面')
# Turn the fan discharge toward a real exterior opening, away from shower glass.
pivot=Vector((3.615,-.42,0));rotation=Matrix.Translation(pivot)@Matrix.Rotation(math.pi,4,'Z')@Matrix.Translation(-pivot)
for name in ['次卫中央空调外机机壳','次卫中央空调外机风扇及格栅']:
 o=bpy.data.objects[name];o.data.transform(o.matrix_world.inverted()@rotation@o.matrix_world)
# Keep north utility wall, only cut the screened outdoor ventilation aperture.
o=bpy.data.objects['次卫北管井侧墙'];o.data=o.data.copy();cut=box((3.08,.12,-.03),(4.17,2.16,.15),enamel,0)
bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Exterior service ventilation','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True);changed.append(o.name)
parts=[]
for x in [3.082,4.168]:parts.append(box((x-.012,.11,-.01),(x+.012,2.17,.13),enamel,.001))
for y in [.12,2.16]:parts.append(box((3.082,y-.012,-.01),(4.168,y+.012,.13),enamel,.001))
for i in range(35):
 y=.16+i*.057;v=box((3.094,y,-.01),(4.156,y+.012,.09),enamel,.001);v.rotation_euler.x=math.radians(-30);parts.append(v)
replace('次卫设备区对外通风百叶',parts,'次卫北管井侧墙')
# Concept discharge shroud to the exterior opening, separate from upper intake.
# Not a certified manufacturer's duct design.
parts=[box((3.43,.085,.00),(3.445,1.32,.20),enamel,0),box((4.035,.085,.00),(4.05,1.32,.20),enamel,0),box((3.43,1.305,.00),(4.05,1.32,.20),enamel,0),box((3.43,.085,.00),(4.05,.10,.20),enamel,0)]
replace('次卫外机朝外排风导流罩',parts,'次卫淋浴地面')
# User confirms exterior is steel louvres, not a glass window. Keep the
# external frame; add a separate closed inner shower sash with sealing/hardware.
parts=[]
for i in range(28):
 y=.685+i*.059
 v=box((4.257,y,.019),(5.191,y+.016,.108),enamel,.001);v.rotation_euler.x=math.radians(-30);parts.append(v)
replace('次卫外窗',parts)
parts=[]
for x in [4.252,5.197]:parts.append(box((x-.012,.65,.193),(x+.012,2.35,.229),enamel,.001))
for y in [.666,2.334]:parts.append(box((4.252,y-.016,.193),(5.197,y+.016,.229),enamel,.001))
# Fixed lower light + upper ventilation sash, both currently closed.
parts.append(box((4.264,1.718,.193),(5.185,1.742,.229),enamel,.001))
replace('次卫淋浴内窗密封窗框',parts,'次卫北窗下砖')
replace('次卫淋浴内窗玻璃',[box((4.268,.686,.209),(5.181,1.714,.217),mats[10],0),box((4.268,1.746,.209),(5.181,2.314,.217),mats[10],0)],'次卫北窗下砖')
parts=[]
for lo,hi in [(.686,1.714),(1.746,2.314)]:
 for x in [4.269,5.180]:parts.append(box((x-.002,lo,.205),(x+.002,hi,.221),mats[312],0))
 for y in [lo,hi]:parts.append(box((4.267,y-.002,.205),(5.183,y+.002,.221),mats[312],0))
for x in [4.39,5.06]:parts.append(box((x-.025,2.309,.218),(x+.025,2.333,.235),steel,.002))
parts.append(box((4.70,1.739,.228),(4.75,1.754,.26),steel,.002))
replace('次卫淋浴内窗密封条及执手',parts,'次卫北窗下砖')
# User revised projector mount: high on sofa wall, not ceiling suspended.
o=bpy.data.objects['超短焦投影机_产品外形示意'];tmp=o.copy();tmp.data=o.data.copy();bpy.context.collection.objects.link(tmp)
bm=bmesh.new();bm.from_mesh(tmp.data);pending=set(bm.verts);remove=[]
while pending:
 seed=pending.pop();group={seed};stack=[seed]
 while stack:
  v=stack.pop()
  for edge in v.link_edges:
   q=edge.other_vert(v)
   if q in pending:pending.remove(q);group.add(q);stack.append(q)
 if max((tmp.matrix_world@v.co).z for v in group)>2.468:remove.extend(group)
bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(tmp.data);bm.free()
shift=Matrix.Translation(Vector((0,-.54,-.305)));tmp.data.transform(tmp.matrix_world.inverted()@shift@tmp.matrix_world)
x=11.0306;parts=[tmp]
parts += [box((x-.075,2.035,6.841),(x+.075,2.285,6.861),mats[345],.003),box((x-.195,2.0225,6.5),(x+.195,2.0375,6.82),mats[342],.003),box((x-.02,2.005,6.64),(x+.02,2.023,6.849),mats[345],.002)]
parts.append(cylinder((x,2.025,6.59),(x,2.14,6.846),.012,mats[345],12))
for xx in [x-.052,x+.052]:
 for yy in [2.07,2.25]:parts.append(cylinder((xx,yy,6.839),(xx,yy,6.844),.005,mats[343],8))
parts.append(cylinder((x+.07,2.15,6.80),(x+.07,2.15,6.86),.004,mats[343],10))
replace('超短焦投影机_产品外形示意',parts)
bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':added,'materialImages':[],'hidden':['次卫外窗百叶帘','次卫外窗嵌玻密封条']},ensure_ascii=False,indent=2))
