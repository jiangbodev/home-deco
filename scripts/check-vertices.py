"""Compare rendered vertices; discard zero-area source faces, not visible geometry.
Usage: python check-vertices.py original.glb decoded.glb
Requires numpy and scipy; not part of the web build.
"""
import sys,json,struct,numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
def load(path):
    with open(path,'rb') as f:
        f.seek(12);length,_=struct.unpack('<II',f.read(8));data=json.loads(f.read(length));f.read(8);return data,f.read()
def array(data,buffer,index):
    a=data['accessors'][index];v=data['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];width=3 if a['type']=='VEC3' else 1
    return np.ndarray((a['count'],width),dtype=dt,buffer=buffer,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*width),np.dtype(dt).itemsize))
def visible_positions(data,buffer,primitive):
    v=array(data,buffer,primitive['attributes']['POSITION']).astype('float64');i=array(data,buffer,primitive['indices']).reshape(-1,3);t=v[i];area=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1);keep=area>1e-18
    return v[np.unique(i[keep])],int((~keep).sum())
a,ab=load(sys.argv[1]);d,db=load(sys.argv[2]);old={n['name']:i for i,n in enumerate(a['nodes'])};parents={c:i for i,n in enumerate(a['nodes']) for c in n.get('children',[])};cache={}
def world(i):
    if i in cache:return cache[i]
    n=a['nodes'][i];m=np.eye(4)
    if 'matrix' in n:m=np.array(n['matrix']).reshape(4,4,order='F')
    else:
        m[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
    if i in parents:m=world(parents[i])@m
    cache[i]=m;return m
maxerr=0.;largest='';checked=0;degBefore=0;degAfter=0
for node in d['nodes']:
    if 'mesh' not in node:continue
    i=old[node['name']];on=a['nodes'][i];m=world(i)
    for p,q in zip(a['meshes'][on['mesh']]['primitives'],d['meshes'][node['mesh']]['primitives']):
        x,da=visible_positions(a,ab,p);y,dd=visible_positions(d,db,q);degBefore+=da;degAfter+=dd
        if not len(x) or not len(y):
            if bool(len(x))!=bool(len(y)):raise ValueError('Lost surface: '+node['name'])
            continue
        x=x@m[:3,:3].T+m[:3,3];y=y@m[:3,:3].T+m[:3,3]
        err=max(cKDTree(x).query(y)[0].max(),cKDTree(y).query(x)[0].max());checked+=len(x)
        if err>maxerr:maxerr=float(err);largest=node['name']
report={'comparison':'bidirectional nearest-vertex distance for nonzero-area faces in world metres; every mesh node','maxVertexDistanceMetres':maxerr,'largestErrorNode':largest,'verticesChecked':checked,'zeroAreaFacesBefore':degBefore,'zeroAreaFacesAfter':degAfter}
open('vertex-report.json','w').write(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
if maxerr>.001:sys.exit(1)
