"""Lossless partition of GLB payloads; no decoding, simplification or re-encoding."""
import json,struct,hashlib,copy,sys
from pathlib import Path
src=Path(sys.argv[1]);out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
data=src.read_bytes();size=struct.unpack_from('<I',data,12)[0];s=json.loads(data[20:20+size]);binary=data[28+size:];assignment=json.loads(Path(sys.argv[2]).read_text());manifest={'modules':{},'textures':{}}
def rawview(i):
 v=s['bufferViews'][i];return binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
imagepaths={}
for i,img in enumerate(s['images']):
 raw=rawview(img['bufferView']);suffix={'image/png':'png','image/jpeg':'jpg','image/webp':'webp'}[img['mimeType']];name='texture-'+hashlib.sha256(raw).hexdigest()[:16]+'.'+suffix;(out/name).write_bytes(raw);imagepaths[i]=name;manifest['textures'][name]=len(raw)
for key in sorted(set(assignment.values())):
 d={'asset':copy.deepcopy(s['asset']),'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'materials':[],'textures':[],'images':[],'samplers':[],'accessors':[],'bufferViews':[],'buffers':[{'byteLength':0}]};blob=bytearray();maps={k:{} for k in ['meshes','materials','textures','images','samplers','accessors','bufferViews']}
 def cp(kind,i):
  if i in maps[kind]:return maps[kind][i]
  obj=copy.deepcopy(s[kind][i]);idx=len(d[kind]);maps[kind][i]=idx;d[kind].append(obj)
  if kind=='bufferViews':
   blob.extend(b'\0'*(-len(blob)%4));obj['byteOffset']=len(blob);obj['buffer']=0;blob.extend(rawview(i))
  elif kind=='accessors':
   assert 'sparse' not in obj
   if 'bufferView' in obj:obj['bufferView']=cp('bufferViews',obj['bufferView'])
  elif kind=='images':
   obj.pop('bufferView',None);obj['uri']=imagepaths[i]
  elif kind=='textures':
   if 'source' in obj:obj['source']=cp('images',obj['source'])
   if 'sampler' in obj:obj['sampler']=cp('samplers',obj['sampler'])
   for e in obj.get('extensions',{}).values():
    if 'source' in e:e['source']=cp('images',e['source'])
  elif kind=='materials':
   def walk(o):
    if isinstance(o,dict):
     for k,v in o.items():
      if ('texture' in k.lower()) and isinstance(v,dict) and 'index' in v:v['index']=cp('textures',v['index'])
      else:walk(v)
    elif isinstance(o,list):
     for v in o:walk(v)
   walk(obj)
  elif kind=='meshes':
   for p in obj['primitives']:
    assert 'targets' not in p
    p['attributes']={k:cp('accessors',v) for k,v in p['attributes'].items()}
    if 'indices' in p:p['indices']=cp('accessors',p['indices'])
    if 'material' in p:p['material']=cp('materials',p['material'])
    for en,e in p.get('extensions',{}).items():
     assert en=='KHR_draco_mesh_compression';e['bufferView']=cp('bufferViews',e['bufferView'])
  return idx
 if key=='base':
  d['nodes']=copy.deepcopy(s['nodes']);d['scenes']=copy.deepcopy(s['scenes']);d['scene']=s.get('scene',0)
  for i,n in enumerate(d['nodes']):
   n.setdefault('extras',{})['moduleNode']=i
   if 'mesh' in n:
    if assignment[n['name']]==key:n['mesh']=cp('meshes',n['mesh'])
    else:n.pop('mesh')
 else:
  for i,n in enumerate(s['nodes']):
   if 'mesh' in n and assignment[n['name']]==key:d['scenes'][0]['nodes'].append(len(d['nodes']));d['nodes'].append({'name':n['name'],'mesh':cp('meshes',n['mesh']),'extras':{'attachTo':i}})
 for k in ['extensionsUsed','extensionsRequired']:
  if k in s:d[k]=s[k]
 d['buffers'][0]['byteLength']=len(blob);blob.extend(b'\0'*(-len(blob)%4));j=json.dumps(d,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*(-len(j)%4);raw=struct.pack('<III',0x46546c67,2,28+len(j)+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob;name=key+'-'+hashlib.sha256(raw).hexdigest()[:12]+'.glb';(out/name).write_bytes(raw);manifest['modules'][key]={'file':name,'bytes':len(raw),'textures':sorted({x['uri'] for x in d['images']}),'nodes':len(d['nodes']) if key!='base' else sum('mesh'in n for n in d['nodes'])}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v['bytes'] for k,v in manifest['modules'].items()},indent=2));print('Total',sum(p.stat().st_size for p in out.iterdir()))
