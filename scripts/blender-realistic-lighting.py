"""Cycles reference and reusable authored lighting for the existing runtime house.
Usage: blender -b --python scripts/blender-realistic-lighting.py -- SOURCE.glb OUTPUT_DIR
"""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];source,out=map(Path,args[:2]);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
def point(p):return Vector((p[0],-p[2],p[1]))
# Blender parent render visibility does not cascade like Three.js visibility.
for o in bpy.data.objects:
 p=o;visible=True
 while p:
  if p.get('source_visible') is False:visible=False
  p=p.parent
 o.hide_render=not visible
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=True;scene.cycles.adaptive_threshold=.025
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
scene.cycles.device='GPU';scene.cycles.max_bounces=8;scene.cycles.diffuse_bounces=5;scene.cycles.glossy_bounces=4;scene.cycles.transmission_bounces=8
scene.cycles.use_light_tree=True
scene.world=bpy.data.worlds.new('Open sky daylight');scene.world.use_nodes=True
nodes=scene.world.node_tree.nodes;links=scene.world.node_tree.links;bg=nodes.get('Background');bg.inputs['Strength'].default_value=1.1
sky=nodes.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_disc=False;sky.sun_elevation=math.radians(38);sky.sun_rotation=math.radians(110);sky.altitude=.08;links.new(sky.outputs['Color'],bg.inputs['Color'])
sun=bpy.data.lights.new('Daylight sun','SUN');sun.energy=2.0;sun.angle=math.radians(4);sun.color=(1,.92,.8);obj=bpy.data.objects.new(sun.name,sun);scene.collection.objects.link(obj);obj.rotation_euler=Vector((-1,.35,-.75)).to_track_quat('-Z','Y').to_euler()
# Shadow rays transmit through thin exterior glass without refractive-caustic noise.
for m in bpy.data.materials:
 if m.name!='外窗清玻璃':continue
 nt=m.node_tree;p=nt.nodes.get('Principled BSDF');output=nt.nodes.get('Material Output');transparent=nt.nodes.new('ShaderNodeBsdfTransparent');ray=nt.nodes.new('ShaderNodeLightPath');mix=nt.nodes.new('ShaderNodeMixShader');nt.links.new(ray.outputs['Is Shadow Ray'],mix.inputs[0]);nt.links.new(p.outputs['BSDF'],mix.inputs[1]);nt.links.new(transparent.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],output.inputs['Surface'])
# Match actual pendant locations; restrained warm fill, not fictitious room-centre lights.
for i,pos in enumerate([[6.0092,1.625,4.7304],[6.8492,1.625,4.7304]]):
 data=bpy.data.lights.new('Dining pendant %d'%i,'AREA');data.energy=10;data.color=(1,.88,.72);data.shape='DISK';data.size=.11;o=bpy.data.objects.new(data.name,data);scene.collection.objects.link(o);o.location=point(pos)
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.5
scene.render.resolution_x=1024;scene.render.resolution_y=768;scene.render.resolution_percentage=100
camera=bpy.data.cameras.new('Reference camera');co=bpy.data.objects.new('Reference camera',camera);scene.collection.objects.link(co);scene.camera=co;camera.sensor_fit='VERTICAL';camera.sensor_height=32;camera.lens=32/(2*math.tan(math.radians(65)/2));camera.clip_start=.035
scene['source_provenance']='Exact runtime GLB SHA256 '+hashlib.sha256(source.read_bytes()).hexdigest()
co.location=point([11.7,1.5,5.1]);co.rotation_euler=(point([8,1.3,4.8])-co.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str((out/'daylight-study.blend').resolve()),compress=True)
views=[('living',[11.7,1.5,5.1],[8,1.3,4.8]),('desk',[12,1.5,2.5],[13.2,.9,1.35]),('shelves',[8,1.5,5.3],[7,1.5,6.8])]
if '--sofa-only' in args:views=[('sofa',[11.03,1.25,4.6],[11.03,.43,6.4])]
for name,pos,target in views:
 co.location=point(pos);co.rotation_euler=(point(target)-co.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
