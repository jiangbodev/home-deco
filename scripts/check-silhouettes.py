"""Geometry-only orthographic checks, not material or browser screenshots."""
import json,struct,sys,numpy as np
from PIL import Image,ImageDraw
def load(p):
 f=open(p,'rb');f.seek(12);l,_=struct.unpack('<II',f.read(8));d=json.loads(f.read(l));f.read(8);return d,f.read()
def array(d,b,i):
 a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];w=3 if a['type']=='VEC3' else 1
 return np.ndarray((a['count'],w),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*w),np.dtype(dt).itemsize))
def triangles(d,b,name):
 n=next(n for n in d['nodes']if n.get('name')==name);out=[]
 for p in d['meshes'][n['mesh']]['primitives']:
  v=array(d,b,p['attributes']['POSITION']);indices=array(d,b,p['indices']).reshape(-1,3);out.append(v[indices])
 return np.concatenate(out)
a,ab=load(sys.argv[1]);d,db=load(sys.argv[2]);names=['Natural cane insert','fabric 1','White Fabric','树木_leaves'];labels=['Cane panel','Upholstery A','Upholstery B','Tree foliage'];sheet=Image.new('RGB',(1024,4*294),'#f9f9f6');draw=ImageDraw.Draw(sheet);report=[]
for row,(name,label)in enumerate(zip(names,labels)):
 x,y=triangles(a,ab,name),triangles(d,db,name);lo=x.min((0,1));hi=x.max((0,1));axes=np.argsort(hi-lo)[-2:];p,q=x[:,:,axes],y[:,:,axes];low=p.min((0,1));size=p.max((0,1))-low;scale=min(460/size[0],240/size[1]);masks=[]
 for j,t in enumerate([p,q]):
  mask=Image.new('1',(500,260));md=ImageDraw.Draw(mask);pts=(t-low)*scale;pts[:,:,0]+=(500-size[0]*scale)/2;pts[:,:,1]=250-pts[:,:,1]
  for tri in pts:md.polygon([tuple(v)for v in tri],fill=1)
  masks.append(np.array(mask));im=Image.new('RGB',mask.size,'#f9f9f6');im.paste('#395643',mask=mask);sheet.paste(im,(12+j*512,row*294+24));draw.text((18+j*512,row*294+5),label+(' / baseline'if j==0 else' / candidate'),fill='#263c33')
 union=np.logical_or(*masks).sum();diff=np.logical_xor(*masks).sum();report.append({'node':name,'projectionAxes':axes.tolist(),'silhouetteChangedFraction':float(diff/union)})
sheet.save(sys.argv[3]);open(sys.argv[3]+'.json','w').write(json.dumps(report,indent=2));print(report)
