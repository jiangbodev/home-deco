"""Authored detail pass on the verified house: furniture, AV and secondary bath."""
import bpy,bmesh,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
changed=[];added=[]
def P(p):return Vector((p[0],-p[2],p[1]))
def mat(mid,name,color,rough,metal=0,coat=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m['source_material_id']=mid;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.12;return m
mats={m.get('source_material_id'):m for m in bpy.data.materials}
screen=mat(300,'Neutral black coated display glass',(.005,.006,.007),.16,.12,.8)
frame=mat(301,'Graphite TV aluminium',(.018,.019,.020),.3,.6)
ceramic=mat(302,'Warm white glazed porcelain',(.9,.885,.85),.19,0,.3)
steel=mat(303,'Satin stainless bathroom fittings',(.58,.6,.61),.24,.95)
plastic=mat(304,'Warm white AV enclosure',(.78,.79,.77),.35)
gap=mat(305,'Recessed warm shadow detail',(.065,.062,.052),.8)
rubber=mat(306,'Charcoal rubber gasket',(.018,.019,.02),.82)
paper=mat(307,'Uncoated ivory paper',(.84,.82,.78),.9)
oak=mats[15].copy();oak.name='Dining natural oak satin';oak['source_material_id']=320;oak['detail_base_material']=15;oak.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.48
# Visible imported cabinets use separate scanned material IDs from the legacy wood.
for mid in [41,45]:
 m=mats[mid];m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.55
 tex=m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node
 img=tex.image.copy();img.name='Cabinet honey oak calibrated';arr=np.empty(len(img.pixels),dtype=np.float32);img.pixels.foreach_get(arr);arr=arr.reshape(-1,4);arr[:,:3]=arr[:,:3]*.70+np.array([.65,.53,.39])*.30;img.pixels.foreach_set(arr.ravel());img.update();img.pack();tex.image=img
 for o in bpy.data.objects:
  if o.type=='MESH' and m in list(o.data.materials):changed.append(o.name)
def box(c,d,m,r=0,segments=3):
 bpy.ops.mesh.primitive_cube_add(size=1,location=P(c));o=bpy.context.object;o.dimensions=(d[0],d[2],d[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if r:
  mod=o.modifiers.new('Real softened edges','BEVEL');mod.width=r;mod.segments=segments;bpy.ops.object.modifier_apply(modifier=mod.name)
  mod=o.modifiers.new('Weighted planar normals','WEIGHTED_NORMAL');mod.keep_sharp=True;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o
def uvwood(o):
 uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
 for poly in o.data.polygons:
  n=o.matrix_world.to_3x3()@poly.normal;axis=max(range(3),key=lambda i:abs(n[i]));
  for li in poly.loop_indices:
   p=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
   uv.data[li].uv=(p.x*.8,-p.y*.8) if axis==2 else ((p.x*.8,p.z*.8) if axis==1 else (-p.y*.8,p.z*.8))
def replace(name,parts):
 o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();tmp=bpy.context.object;mesh=tmp.data.copy();mesh.transform(o.matrix_world.inverted()@tmp.matrix_world);o.data=mesh;bpy.data.objects.remove(tmp,do_unlink=True);changed.append(name);return o
# A properly proportioned off-state TV: mount, rear body, eased bezel and inset glass.
replace('餐桌侧显示屏',[
 box((5.559,1.26,4.73044),(.019,.16,.30),frame,.004),
 box((5.579,1.26,4.73044),(.034,.385,.674),frame,.004),
 box((5.597,1.263,4.73044),(.002,.35775,.636),screen,.0008),
 box((5.598,1.077,4.73044),(.0015,.002,.020),rubber,.0003)])
# Solid oak edge, realistic thickness, and a structural stretcher tying the pedestals.
part=box((6.429,.73,4.730), (1.77,.04,.85),oak,.006);uvwood(part);replace('餐桌台面',[part])
for name in ['餐桌板式支撑','餐桌板式支撑.001']:
 o=bpy.data.objects[name];ps=[o.matrix_world@v.co for v in o.data.vertices];c=((min(p.x for p in ps)+max(p.x for p in ps))/2,.365,4.73);p=box(c,(.09,.69,.50),oak,.004);uvwood(p);replace(name,[p])
name='餐桌结构横撑';template=bpy.data.objects['餐桌板式支撑'];p=box((6.429,.245,4.73),(1.12,.095,.065),oak,.003);uvwood(p);p.name=name;p['source_visible']=True;added.append({'name':name,'template':'餐桌板式支撑'})
# Replace the placeholder flat bar with a compact UST projector, including vents.
parts=[box((11.031,.512,3.795),(.56,.124,.30),plastic,.016),box((11.031,.574,3.70),(.30,.002,.072),rubber,.008),box((11.031,.576,3.705),(.145,.002,.04),screen,.006)]
for x in [10.78,11.282]:
 for z in np.linspace(3.73,3.86,8):parts.append(box((x,.52,float(z)),(.003,.042,.005),rubber,.001))
replace('超短焦投影机_产品外形示意',parts)
# Preserve ivory lacquer and provide a real recessed plinth under full-height doors.
for o in list(bpy.data.objects):
 if o.name.startswith('南侧通高柜2035门板'):
  o.data=o.data.copy();inv=o.matrix_world.inverted()
  for v in o.data.vertices:
   p=o.matrix_world@v.co
   if p.z<.07:p.z=.065+(p.z-.004)*.2
   v.co=inv@p
  o.data.update();changed.append(o.name)
p=box((6.1975,.031,6.54),(1.999,.062,.045),gap,.001);p.name='通高柜内退踢脚';p['source_visible']=True;added.append({'name':p.name,'template':'南侧通高柜2035实体底板'})
# Ceramic has its own glaze, not the counter/stone finish shader.
for o in list(bpy.data.objects):
 if o.type!='MESH':continue
 if o.name.startswith('次卫壁挂马桶') and any(s in o.name for s in ['陶瓷壳','座圈','闭合盖板','壁挂接头']):
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(ceramic)
  if '陶瓷壳' in o.name:
   bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bm.normal_update()
   for f in bm.faces:f.smooth=True
   for e in bm.edges:e.smooth=len(e.link_faces)==2 and e.calc_face_angle(0)<math.radians(50)
   bm.to_mesh(o.data);bm.free()
  changed.append(o.name)
 if (o.name in ['顶喷','顶喷出水面'] or o.name.startswith(('淋浴','手持花洒')) and not o.name.endswith(('.001','.002','.003')) or o.name in ['淋浴墙面固定臂.001','淋浴调节旋钮.001']) and o.type=='MESH':
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(rubber if '出水面' in o.name else steel);changed.append(o.name)
 if o.name.startswith('次卫淋浴透明玻璃') and ('框' in o.name):
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(steel);changed.append(o.name)
 if o.name.startswith('次卫壁挂马桶') and any(s in o.name for s in ['冲水面板','双档按钮','铰链']):
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(steel);changed.append(o.name)
# A flush drain and a restrained shower-door pull, combined in one static accessory node.
parts=[box((4.72,-.017,.29),(.40,.005,.065),steel,.004)]
for x in np.linspace(4.56,4.88,17):parts.append(box((float(x),-.0142,.29),(.004,.001,.043),rubber,.0004))
parts+=[box((4.77,1.08,1.074),(.018,.20,.018),steel,.004),box((4.77,.992,1.062),(.018,.018,.035),steel,.003),box((4.77,1.168,1.062),(.018,.018,.035),steel,.003)]
def cylinder(c,r,depth,m):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=depth,location=P(c));o=bpy.context.object;o.rotation_euler=P((0,0,1)).to_track_quat('Z','Y').to_euler();o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
parts+=[box((4.295,.70,1.755),(.09,.012,.012),steel,.003),box((4.252,.70,1.755),(.008,.05,.035),steel,.005),cylinder((4.34,.70,1.825),.048,.105,paper),cylinder((4.34,.70,1.878),.014,.0015,gap)]
bpy.ops.object.select_all(action='DESELECT')
for p in parts:p.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();p=bpy.context.object;p.name='次卫排水门把与纸架';p['source_visible']=True;added.append({'name':p.name,'template':'次卫淋浴地面'})
# Follow-up: desks/chairs and integrated washbasins, within the approved layout.
counter=mat(308,'Warm ivory fine mineral surface',(.79,.78,.745),.43)
cloth=mats[70].copy();cloth.name='Natural oatmeal study upholstery';cloth['source_material_id']=321;cloth['detail_base_material']=70;cloth.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.87
for name in ['主卧书桌_600x1750台面','主卧转角连续台面']:
 o=bpy.data.objects[name];ps=[o.matrix_world@v.co for v in o.data.vertices];lo=[min(p[i] for p in ps) for i in range(3)];hi=[max(p[i] for p in ps) for i in range(3)];c=((lo[0]+hi[0])/2,.734,-(lo[1]+hi[1])/2);d=(hi[0]-lo[0],.032,hi[1]-lo[1]);part=box(c,d,oak,.004);uvwood(part);replace(name,[part])
# The visible imported chair is distinct from hidden legacy geometry.
o=bpy.data.objects['Warm grey upholstered study chair.001'];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(cloth)
# Taper the broad upper back by 12 mm on each side for a softer manufactured profile.
inv=o.matrix_world.inverted()
for v in o.data.vertices:
 p=o.matrix_world@v.co
 if p.z>.60:
  t=min(1,max(0,(p.z-.60)/.22));p.y=-1.615+(p.y+1.615)*(1-.055*t)
 v.co=inv@p
changed.append(o.name)
# Narrow eased solid-wood bench legs retain their exact floor contact and footprint.
for o in list(bpy.data.objects):
 if o.name.startswith('条凳支腿'):
  ps=[o.matrix_world@v.co for v in o.data.vertices];lo=[min(p[i] for p in ps) for i in range(3)];hi=[max(p[i] for p in ps) for i in range(3)];p=box(((lo[0]+hi[0])/2,(lo[2]+hi[2])/2,-(lo[1]+hi[1])/2),(hi[0]-lo[0],hi[2]-lo[2],hi[1]-lo[1]),oak,.002);uvwood(p);replace(o.name,[p])
# Existing main-bath integrated sink: separate mineral deck and glazed basin.
for name in ['主卫台盆台面','主卫台盆台面连续圆角盆腔','主卫台盆台面排水盖']:
 o=bpy.data.objects[name];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(counter if name=='主卫台盆台面' else steel if '排水盖' in name else ceramic);changed.append(name)
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.name.startswith(('龙头','主卫台盆柜拉手','外置台盆下柜拉手')):
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(rubber if '起泡' in o.name else steel);changed.append(o.name)
def rr(cx,cz,w,d,r,y):
 pts=[]
 for sx,sz,ang in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
  for k in range(9):
   a=math.radians(ang+k*90/8);pts.append((cx+sx*(w/2-r)+r*math.cos(a),y,cz+sz*(d/2-r)+r*math.sin(a)))
 return pts
def surface(name,verts,faces,m):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([P(v) for v in verts],[],faces);mesh.materials.append(m);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o)
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();return o
def rings_mesh(name,rings,m,segments=None):
 n=len(rings[0]);verts=[p for ring in rings for p in ring];faces=[]
 for j in range(len(rings)-1):
  for i in (range(n) if segments is None else segments):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 return surface(name,verts,faces,m)
cx,cz=4.540306,4.495511
outer=rr(cx,4.525511,.55,.50,.005,.83);inner=rr(cx,cz,.43,.32,.045,.83)
replace('外置台盆台面',[rings_mesh('Mineral sink surround',[rr(cx,4.525511,.55,.50,.005,.78),outer,inner],counter)])
rings=[inner,rr(cx,cz,.422,.312,.045,.823),rr(cx,cz,.35,.24,.06,.704),rr(cx,cz,.31,.20,.065,.685)]
for q,name in enumerate(['外置台盆台面盆壁','外置台盆台面盆壁.001','外置台盆台面盆壁.002','外置台盆台面盆壁.003']):
 o=replace(name,[rings_mesh('Continuous rounded ceramic bowl',rings,ceramic,range(q*9,(q+1)*9))])
 for poly in o.data.polygons:poly.use_smooth=True
hole=[(cx+.019*math.cos(2*math.pi*i/36),.681,cz+.019*math.sin(2*math.pi*i/36)) for i in range(36)]
# Match round-drain vertex phases to the bowl boundary; no coplanar second bottom.
bottom=rings_mesh('Sloping basin bottom',[rings[-1],hole],ceramic)
bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=.0195,depth=.003,location=P((cx,.682,cz)));drain=bpy.context.object;drain.data.materials.append(steel)
replace('外置台盆台面盆底',[bottom,drain])

# Kitchen: usable cookware, a clear prep surface and a drawn stainless sink.
cast=mat(309,'Seasoned charcoal cookware',(.022,.024,.023),.68,.55)
potmetal=mat(310,'Brushed cookware stainless',(.57,.59,.60),.28,.96)
stoneware=mat(311,'Warm ivory stoneware',(.76,.74,.67),.24,0,.28)
def lathe(c,profile,m,segments=64):
 verts=[];faces=[]
 for r,h in profile:
  for i in range(segments):
   a=2*math.pi*i/segments;verts.append((c[0]+r*math.cos(a),c[1]+h,c[2]+r*math.sin(a)))
 for j in range(len(profile)-1):
  for i in range(segments):faces.append((j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i))
 o=surface('Turned kitchen form',verts,faces,m)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for poly in o.data.polygons:poly.use_smooth=True
 return o
def tube(points,m,r=.006):
 curve=bpy.data.curves.new('Bent stainless handle','CURVE');curve.dimensions='3D';curve.resolution_u=2;curve.bevel_depth=r;curve.bevel_resolution=2;sp=curve.splines.new('POLY');sp.points.add(len(points)-1)
 for dst,src in zip(sp.points,points):dst.co=(*P(src),1)
 o=bpy.data.objects.new('Bent cookware handle',curve);bpy.context.collection.objects.link(o);o.data.materials.append(m);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');return bpy.context.object
def addition(name,parts,template):
 bpy.ops.object.select_all(action='DESELECT')
 for part in parts:part.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;o['source_visible']=True;added.append({'name':name,'template':template});return o
parts=[]
# 28 cm frying pan: genuine interior, rolled rim, stable base on the grate.
parts.append(lathe((6.915,.884,1.827),[(0,0),(.085,0),(.10,.004),(.14,.045),(.142,.05),(.135,.052),(.127,.044),(.085,.009),(0,.009)],cast))
handle=box((6.745,.933,1.997),(.025,.022,.21),rubber,.008);handle.rotation_euler.z=-math.pi/4;parts.append(handle)
parts.append(tube([(6.826,.925,1.916),(6.802,.931,1.94),(6.784,.933,1.958)],potmetal,.009))
# 22 cm lidded saucepan, with attached loop handles and a cool-touch knob.
parts.append(lathe((6.915,.884,1.486),[(0,0),(.087,0),(.105,.008),(.11,.12),(.113,.132),(.106,.136),(.101,.127),(.098,.015),(0,.015)],potmetal))
parts.append(lathe((6.915,1.018,1.486),[(0,.012),(.025,.012),(.097,.002),(.114,0),(.114,.005),(.098,.009),(.026,.024),(0,.024)],potmetal))
parts.append(lathe((6.915,1.042,1.486),[(0,0),(.013,0),(.017,.012),(.021,.018),(.020,.025),(0,.025)],rubber,40))
for sign in [-1,1]:
 parts.append(tube([(6.915+sign*.107,.991,1.45),(6.915+sign*.15,1.002,1.45),(6.915+sign*.16,1.006,1.486),(6.915+sign*.15,1.002,1.522),(6.915+sign*.107,.991,1.522)],potmetal,.006))
addition('厨房灶台锅具',parts,'灶具')
# A removable board on the north counter; keep most preparation surface free.
board=box((6.0,.831,.51),(.38,.022,.25),oak,.011);uvwood(board);addition('厨房备餐砧板',[board],'厨房北操作台_深570浅色台面')
parts=[]
for y in [1.38,1.417]:parts.append(lathe((5.525,y,1.13),[(0,0),(.038,0),(.048,.01),(.077,.062),(.079,.068),(.074,.071),(.071,.063),(.043,.014),(0,.012)],stoneware,48))
addition('厨房层板叠碗',parts,'厨房开放层板')
# Keep the oven/hob off. Refine authored glass and brushed controls, without fake flames.
for o in list(bpy.data.objects):
 if o.type!='MESH':continue
 if o.name=='灶具':
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(screen);changed.append(o.name)
 elif o.name.startswith(('灶具控制旋钮','燃气炉头底座','厨房水槽排水盖')):
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(potmetal);changed.append(o.name)
 elif o.name.startswith(('铸铁锅架','锅架承托')):
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(cast);changed.append(o.name)
# Match the inset bowl exactly to the current worktop opening and drain.
cx,cz=6.1103,3.0110
outer=rr(5.9653,cz,1.24,.6,.005,.82);inner=rr(cx,cz,.79,.44,.035,.82)
replace('厨房南水槽台_1240x600浅色台面',[rings_mesh('Sink mineral surround',[rr(5.9653,cz,1.24,.6,.005,.79),outer,inner],counter)])
rings=[inner,rr(cx,cz,.78,.43,.035,.812),rr(cx,cz,.71,.36,.045,.685),rr(cx,cz,.67,.32,.06,.666)]
for q,name in enumerate(['厨房南水槽台_1240x600浅色台面盆壁','厨房南水槽台_1240x600浅色台面盆壁.001','厨房南水槽台_1240x600浅色台面盆壁.002','厨房南水槽台_1240x600浅色台面盆壁.003']):
 o=replace(name,[rings_mesh('Drawn stainless sink',rings,potmetal,range(q*9,(q+1)*9))])
 for poly in o.data.polygons:poly.use_smooth=True
hole=[(6.1253+.035*math.cos(2*math.pi*i/36),.662,cz+.035*math.sin(2*math.pi*i/36)) for i in range(36)]
replace('厨房南水槽台_1240x600浅色台面盆底',[rings_mesh('Sink falls to waste',[rings[-1],hole],potmetal)])
for name in ['厨房北操作台_深570浅色台面','厨房右柜_深600浅色台面','厨房左窄柜_深326浅色台面']:
 o=bpy.data.objects[name];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(counter);changed.append(name)

# Joinery detail: glazing rebates, seal lines, softened profiles and actual levers.
seal=mat(312,'Graphite glazing weather seal',(.065,.072,.068),.75)
frost=mat(314,'Neutral translucent privacy glass',(.91,.94,.92),.30)
frost.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.78
frost.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.46
# Keep the original pressed-glass relief while removing its opaque tan albedo.
original_normal=mats[14].node_tree.nodes.get('Principled BSDF').inputs['Normal']
if original_normal.is_linked:
 normal_source=original_normal.links[0].from_node
 if normal_source.type=='NORMAL_MAP' and normal_source.inputs['Color'].is_linked:
  image_source=normal_source.inputs['Color'].links[0].from_node
  if image_source.type=='TEX_IMAGE':
   tex=frost.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image_source.image;nm=frost.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.3;frost.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color']);frost.node_tree.links.new(nm.outputs['Normal'],frost.node_tree.nodes.get('Principled BSDF').inputs['Normal'])

# Replace the opaque tan texture used for privacy glass; preserve all pane geometry.
for o in list(bpy.data.objects):
 if o.type=='MESH' and any(m and m.get('source_material_id')==14 for m in o.data.materials):
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(frost);changed.append(o.name)
def world_bounds(o):
 pts=[o.matrix_world@v.co for v in o.data.vertices];pts=[(p.x,p.z,-p.y) for p in pts];return [min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]
# Low-cost actual edge radii on the existing rectangular aluminium profiles.
for o in list(bpy.data.objects):
 if o.type!='MESH' or not ('框' in o.name and ('窗' in o.name or '玻璃' in o.name)):continue
 if len(o.data.polygons)>12:continue
 lo,hi=world_bounds(o);d=[hi[i]-lo[i] for i in range(3)]
 if min(d)<.009 or min(d)>.10:continue
 old=o.data.materials[0];part=box(tuple((lo[i]+hi[i])/2 for i in range(3)),d,old,.0015,2);replace(o.name,[part])
# Add subtle seal lines inside each existing glass edge. Attach to the pane's
# original parent, so door seals travel with the leaf rather than floating in space.
for o in list(bpy.data.objects):
 if o.type!='MESH' or not ('窗' in o.name or '玻璃' in o.name or '压纹隔断' in o.name):continue
 ids={m.get('source_material_id') for m in o.data.materials if m}
 if not ids.intersection({5,7,10,11,314}):continue
 lo,hi=world_bounds(o);d=[hi[i]-lo[i] for i in range(3)];axis=0 if d[0]<d[2] else 2;span=2 if axis==0 else 0
 if d[1]<.3 or d[span]<.25 or d[axis]>.04:continue
 parts=[];middle=[(lo[i]+hi[i])/2 for i in range(3)]
 for side in [-1,1]:
  for face in [-1,1]:
   c=middle.copy();c[span]=lo[span]+.003 if side<0 else hi[span]-.003;c[axis]=middle[axis]+face*(d[axis]/2+.0006);dims=[.006,.006,.006];dims[axis]=.0012;dims[1]=d[1]-.012;parts.append(box(c,dims,seal))
   c=middle.copy();c[1]=lo[1]+.003 if side<0 else hi[1]-.003;c[axis]=middle[axis]+face*(d[axis]/2+.0006);dims=[.006,.006,.006];dims[axis]=.0012;dims[span]=d[span];parts.append(box(c,dims,seal))
 addition(o.name+'嵌玻密封条',parts,o.name)
# Replace rectangular handle placeholders with rose, stem and rounded lever.
def axis_cylinder(c,r,depth,direction,m):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=depth,location=P(c));o=bpy.context.object;o.rotation_euler=P(direction).to_track_quat('Z','Y').to_euler();o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
for o in list(bpy.data.objects):
 if o.type!='MESH' or not ('门' in o.name and '执手' in o.name):continue
 lo,hi=world_bounds(o);d=[hi[i]-lo[i] for i in range(3)];axis=0 if d[0]<d[2] else 2;along=2 if axis==0 else 0;c=[(lo[i]+hi[i])/2 for i in range(3)];parent=o.parent
 # Determine which side of the leaf the original handle sits on.
 frame_vertices=[p for child in parent.children_recursive if child.type=='MESH' and '框' in child.name for p in [world_bounds(child)]] if parent else []
 plane=sum((a[axis]+b[axis])/2 for a,b in frame_vertices)/len(frame_vertices) if frame_vertices else c[axis]+.03;sign=-1 if c[axis]<plane else 1
 anchor=c.copy();anchor[along]=lo[along]+.016;anchor[axis]=c[axis]-sign*.012;direction=[0,0,0];direction[axis]=1
 parts=[axis_cylinder(anchor,.022,.007,direction,potmetal)]
 stem=anchor.copy();stem[axis]+=sign*.014;parts.append(axis_cylinder(stem,.008,.028,direction,potmetal))
 lever=c.copy();lever[axis]=anchor[axis]+sign*.029;lever[along]=anchor[along]+.039;dims=[.018,.016,.018];dims[along]=.10;parts.append(box(lever,dims,potmetal,.006));replace(o.name,parts)

# Export only changed meshes and additions; keep existing hierarchy/interaction identities on integration.
bpy.ops.object.select_all(action='DESELECT');changed=list(dict.fromkeys(changed))
for name in changed+[a['name'] for a in added]:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':added,'materialImages':[41,45],'customMaterials':[300,301,302,303,304,305,306,307,308,309,310,311,312,314,320,321]},ensure_ascii=False,indent=2));print('DETAIL EXPORT',len(changed),'changed;',len(added),'added')
