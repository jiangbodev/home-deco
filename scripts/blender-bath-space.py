"""Remove condenser props while preserving shower / inner glass / outer louvres."""
import bpy,sys,json
from pathlib import Path
src,blend,out,report=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
hidden=['次卫中央空调外机机壳','次卫中央空调外机风扇及格栅','次卫中央空调外机安装底座','次卫中央空调外机保温管','次卫外机朝外排风导流罩']
for name in hidden:
 o=bpy.data.objects[name];o['source_visible']=False;o.hide_render=True;o.hide_set(True)
# Preserve all architectural relationships; no extra trims or equipment.
bpy.ops.object.select_all(action='DESELECT')
o=bpy.data.objects['次卫淋浴内窗玻璃'];o.hide_set(False);o.select_set(True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(Path(blend).resolve()),compress=True)
bpy.ops.export_scene.gltf(filepath=str(Path(out).resolve()),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
Path(report).write_text(json.dumps({'changed':[],'added':[],'materialImages':[],'hidden':hidden},ensure_ascii=False,indent=2))
