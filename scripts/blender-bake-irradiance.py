"""Bake diffuse direct+indirect light (without albedo) from the Cycles study.
No runtime mesh, vertex, UV or module is changed. Outputs raw linear float arrays.
"""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
blend,planfile,outdir=sys.argv[sys.argv.index('--')+1:];out=Path(outdir);out.mkdir(parents=True,exist_ok=True);plan=json.loads(Path(planfile).read_text())
bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()));scene=bpy.context.scene;scene.cycles.samples=1024;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
scene.cycles.device='GPU';scene.render.bake.use_pass_direct=True;scene.render.bake.use_pass_indirect=True;scene.render.bake.use_pass_color=False;scene.render.bake.margin=3;scene.render.bake.use_clear=True
# Pin original texture coordinates explicitly; the bake target uses a separate UV layer.
for o in bpy.data.objects:
 if o.type=='MESH' and o.data.uv_layers:o.data.uv_layers[0].name='UVMap'
for m in bpy.data.materials:
 if not m.use_nodes:continue
 nt=m.node_tree;uvnode=nt.nodes.new('ShaderNodeUVMap');uvnode.uv_map='UVMap'
 for node in list(nt.nodes):
  if node.type=='TEX_IMAGE' and not node.inputs['Vector'].is_linked:nt.links.new(uvnode.outputs['UV'],node.inputs['Vector'])
# Resume only identical bake inputs. Never silently reuse old lighting for new geometry.
previous_plan=out/'plan.json'
if any((out/(kind+'.rgba32f')).exists() for kind in ['floor','wall']):
 if not previous_plan.exists() or json.loads(previous_plan.read_text())!=plan:
  raise RuntimeError('Existing bake belongs to different inputs; use a fresh output directory')
# Full-resolution atlas; four-pixel gutters preserve chart isolation.
previous_plan.write_text(json.dumps(plan,ensure_ascii=False,indent=2))
for kind in ['floor','wall']:
 if (out/(kind+'.rgba32f')).exists():continue
 info=plan[kind];width,height=info['width'],info['height'];img=bpy.data.images.new('Cycles irradiance '+kind,width,height,alpha=True,float_buffer=True);img.colorspace_settings.name='Non-Color';selected=[]
 bpy.ops.object.select_all(action='DESELECT')
 for r in info['receivers']:
  o=bpy.data.objects.get(r['name']);assert o and o.type=='MESH',r['name'];o.data=o.data.copy();
  if not o.data.uv_layers:o.data.uv_layers.new(name='UVMap')
  o.data.uv_layers[0].name='UVMap';o.data.uv_layers[0].active_render=True
  uv=o.data.uv_layers.new(name='LightingBake');o.data.uv_layers.active_index=0
  for poly in o.data.polygons:
   normal=o.matrix_world.to_3x3().inverted().transposed()@poly.normal;norm=Vector((normal.x,normal.z,-normal.y));axis=max(range(3),key=lambda i:abs(norm[i]));face=axis*2+(0 if norm[axis]>=0 else 1)
   for li in poly.loop_indices:
    v=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co;p=(v.x,v.z,-v.y)
    if kind=='floor':
     b=info['bounds'];u=(p[0]-b[0])/(b[2]-b[0]);vv=(p[2]-b[1])/(b[3]-b[1]);coord=(u,1-vv) if norm.y>.9 else (-2,-2)
    else:
     axes=[2,1] if face<2 else [0,2] if face<4 else [0,1];rect=r['rects'][face];u=(p[axes[0]]-r['min'][axes[0]])/max(.000001,r['max'][axes[0]]-r['min'][axes[0]]);vv=(p[axes[1]]-r['min'][axes[1]])/max(.000001,r['max'][axes[1]]-r['min'][axes[1]]);coord=(rect[0]+u*rect[2],1-(rect[1]+vv*rect[3]))
    uv.data[li].uv=coord
  for m in o.data.materials:
   nodes=m.node_tree.nodes;node=nodes.get('BakeTarget') or nodes.new('ShaderNodeTexImage');node.name='BakeTarget';node.image=img;nodes.active=node
  o.hide_set(False);o.select_set(True);selected.append(o)
 bpy.context.view_layer.objects.active=selected[0]
 # One transient bake receiver avoids rerendering the entire atlas per object.
 bpy.ops.object.join()
 bpy.context.object.data.uv_layers['UVMap'].active_render=True
 print('BAKE START',kind,len(selected),width,height,flush=True)
 bpy.ops.object.bake(type='DIFFUSE',pass_filter={'DIRECT','INDIRECT'},uv_layer='LightingBake',use_clear=True,margin=3)
 pixels=np.empty(width*height*4,dtype=np.float32);img.pixels.foreach_get(pixels);pixels=pixels.reshape(height,width,4)[::-1].copy();pixels.tofile(out/(kind+'.rgba32f'))
 print('BAKE END',kind,'rgb min/max',float(pixels[:,:,:3].min()),float(pixels[:,:,:3].max()),flush=True)
 # A raw high dynamic range archival output; production encoding is separate.
 img.filepath_raw=str((out/(kind+'.exr')).resolve());img.file_format='OPEN_EXR';img.save()
Path(out/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
