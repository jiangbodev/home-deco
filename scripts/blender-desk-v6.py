"""Two true 27-inch 16:9 monitors and a compact workstation on the existing bedroom desk."""
import bpy,bmesh,math,sys,json
from pathlib import Path
from mathutils import Vector
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
exec(compile(Path('scripts/blender-living-plan.py').read_text().split('# Elevation16:')[0],'helpers','exec'))
def material(name,id,color,rough,metallic=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m['source_material_id']=id
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metallic
 return m
shell=material('Graphite monitor polymer',410,(.022,.026,.029),.40)
screen=material('Powered-off anti-glare display',411,(.012,.019,.024),.24,.12)
aluminum=material('Satin charcoal aluminum stand',412,(.06,.07,.077),.31,.72)
keymat=material('Charcoal keycaps',413,(.09,.10,.11),.58)
padmat=material('Woven charcoal mouse mat',414,(.045,.048,.05),.93)
legend=material('Warm gray keyboard legends',415,(.49,.50,.48),.65)
parts=[];measurements=[]
# Active display dimensions: 27 inches at 16:9 (597.7 x 336.2 mm).
w=27*.0254*16/math.sqrt(16**2+9**2);h=w*9/16
for i,z in enumerate([1.281,1.903],1):
 p=[cb((13.835,1.075,z),(.035,.356,.614),shell,.006),cb((13.816,1.078,z),(.004,h,w),screen,.002)]
 p+=[cb((13.77,.756,z),(.21,.012,.22),aluminum,.005),cb((13.846,.886,z),(.024,.25,.04),aluminum,.004),cb((13.851,1.036,z),(.028,.07,.07),shell,.005)]
 # Rear ventilation and ports with a visible routed power/display lead.
 for k in range(11):p.append(cb((13.853,1.17,z-.11+k*.022),(.0015,.018,.008),dark,.0005))
 p.append(cb((13.855,.972,z),(.003,.014,.028),dark,.001))
 p.extend([cylinder((13.86,.967,z),(13.885,.84,z),.0023,shell,8),cylinder((13.885,.84,z),(13.91,.754,z+.065),.0023,shell,8)])
 replace('主卧27寸显示器'+str(i),p,'主卧书桌_600x1750台面')
 measurements.append({'name':'主卧27寸显示器'+str(i),'activeWidthM':w,'activeHeightM':h,'diagonalInches':27,'front':'-X','supportY':.75})
# Keyboard: TKL scale, individual keycaps, modifier widths and separated navigation cluster.
p=[cb((13.493,.758,1.52),(.139,.016,.367),shell,.005)]
for row in range(6):
 x=13.546-row*.020
 for col in range(15):
  if row==5 and 3<=col<=8:continue
  if col==12:continue
  z=1.35+col*.024
  width=.136 if row==5 and col==2 else .020
  if row==5 and col==2:z=1.476
  p.append(cb((x,.771,z),(.016,.009,width),keymat,.0015))
  if not(row==5 and col==2):
   # Small subdued legend strokes, not noisy fake branding.
   p.append(cb((x+.001,.7757,z-.003),(.003,.0004,.005),legend,.0001))
replace('主卧紧凑键盘',p,'主卧书桌_600x1750台面')
replace('主卧鼠标垫',[cb((13.488,.7515,1.92),(.224,.003,.23),padmat,.007)],'主卧书桌_600x1750台面')
# Smooth low dome with a flat contacting underside and distinct buttons/wheel.
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=(13.49,-1.91,.770));o=bpy.context.object;o.scale=(.056,.033,.020);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
for v in o.data.vertices:
 if v.co.z<-.016:v.co.z=-.016
for f in o.data.polygons:f.use_smooth=True
o.data.materials.append(shell)
p=[o,cb((13.517,.7895,1.91),(.035,.0015,.0012),dark,.0003),cylinder((13.523,.789,1.906),(13.523,.789,1.914),.005,keymat,16)]
replace('主卧无线鼠标',p,'主卧书桌_600x1750台面')
checks=[]
for name in changed:
 o=bpy.data.objects[name];ps=[o.matrix_world@v.co for v in o.data.vertices];lo=[min(p[i] for p in ps) for i in range(3)];hi=[max(p[i] for p in ps) for i in range(3)]
 checks.append({'name':name,'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]})
 assert lo[0]>=13.3489 and hi[0]<=13.9491 and -hi[1]>=.7393 and -lo[1]<=2.4895,checks[-1]
 # Keep monitors clear of shelf occupying z <= .9594.
 if '显示器' in name:assert -hi[1]>.96
bpy.ops.object.select_all(action='DESELECT')
for name in changed:bpy.data.objects[name].select_set(True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':changed,'added':added,'materialImages':[],'hidden':[],'measurements':measurements,'bounds':checks},ensure_ascii=False,indent=2))
