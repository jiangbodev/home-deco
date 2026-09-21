"""Capture local HDR reflection references from the authored Cycles scene."""
import bpy,sys,math
from pathlib import Path
blend,outdir=sys.argv[sys.argv.index('--')+1:];out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()));s=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.cycles.samples=64;s.cycles.use_denoising=True;s.render.resolution_x=1024;s.render.resolution_y=512;s.render.resolution_percentage=100
s.render.image_settings.file_format='HDR';s.view_settings.view_transform='Standard';s.view_settings.exposure=0
c=s.camera;c.data.type='PANO';c.data.panorama_type='EQUIRECTANGULAR';c.rotation_euler=(math.pi/2,0,0)
for name,pos in [('living',(8.7,1.45,5.1)),('bedroom',(11.3,1.45,1.8)),('guest-bath',(4.72,1.4,1.65)),('kitchen',(6.05,1.4,1.85))]:
 s.render.resolution_x=512 if name in ['guest-bath','kitchen'] else 1024;s.render.resolution_y=s.render.resolution_x//2
 c.location=(pos[0],-pos[2],pos[1]);s.render.filepath=str((out/(name+'.hdr')).resolve());bpy.ops.render.render(write_still=True)
