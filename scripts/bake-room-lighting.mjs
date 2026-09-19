// Offline contact occlusion from the exact authored meshes. No model simplification.
// Usage: node scripts/bake-floor-contact.mjs source.glb
import fs from 'node:fs';
import crypto from 'node:crypto';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import D from 'draco3dgltf';
import {getBounds} from '@gltf-transform/functions';
import * as T from 'three';
import {MeshBVH} from 'three-mesh-bvh';
import sharp from 'sharp';
const sourceModules=Object.values(JSON.parse(fs.readFileSync('public/assets/modules/manifest.json')).modules).map(m=>m.file).sort();
const path=process.argv[2];if(!path)throw Error('Provide the lossless full source GLB');
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await D.createDecoderModule()});
const doc=await io.read(path),parts=[[],[]],receivers=[];let counts=[0,0];
for(const n of doc.getRoot().listNodes()){
 if(!n.getMesh())continue;
 let visible=true,dynamic=false,exclude=false;
 for(let p=n;p;p=p.getParentNode()){
  const e=p.getExtras();if(e.source_visible===false)visible=false;
  for(const key of Object.keys(e).filter(k=>k.startsWith('interaction_'))){
   if(['interaction_furniture','interaction_piano','interaction_dining-stored'].includes(key))dynamic=true;
   else if(key!=='interaction_effect-floor')exclude=true;
  }
 }
 if(!visible||exclude)continue;
 const matrix=new T.Matrix4().fromArray(n.getWorldMatrix()),point=new T.Vector3();
 for(const primitive of n.getMesh().listPrimitives()){
  const m=primitive.getMaterial();if(m?.getAlphaMode()==='BLEND')continue;
  const p=primitive.getAttribute('POSITION'),idx=primitive.getIndices()?.getArray();
  const xyz=new Float32Array(p.getCount()*3);
  for(let i=0;i<p.getCount();i++){point.fromArray(p.getArray(),i*3).applyMatrix4(matrix);point.toArray(xyz,i*3)}
  // Box-shaped opaque white architectural receivers use six world-space charts.
  const box=new T.Box3().setFromArray(xyz),size=box.getSize(new T.Vector3());
  const color=m?.getBaseColorFactor()||[0,0,0];
  let axial=true;
  for(let i=0;i<(idx?.length||p.getCount());i+=3){
   const a=new T.Vector3().fromArray(xyz,(idx?idx[i]:i)*3),b=new T.Vector3().fromArray(xyz,(idx?idx[i+1]:i+1)*3),c=new T.Vector3().fromArray(xyz,(idx?idx[i+2]:i+2)*3);
   const normal=b.sub(a).cross(c.sub(a)).normalize();if(Math.max(Math.abs(normal.x),Math.abs(normal.y),Math.abs(normal.z))<.999)axial=false;
  }
  if(!dynamic&&axial&&!m?.getBaseColorTexture()&&Math.min(...color.slice(0,3))>.55&&m.getMetallicFactor()<.05&&size.y>.2&&Math.min(size.x,size.y,size.z)>.008)
   receivers.push({name:n.getName(),min:box.min.toArray(),max:box.max.toArray()});
  const out=parts[dynamic?1:0];
  for(let i=0;i<(idx?.length||p.getCount());i+=3){
   const ids=[idx?idx[i]:i,idx?idx[i+1]:i+1,idx?idx[i+2]:i+2];
   const ys=ids.map(v=>xyz[v*3+1]);
   // Ignore floors below the launch surface and elevated geometry beyond the bake radius.
   if(dynamic&&(Math.max(...ys)<.032||Math.min(...ys)>1.2))continue;
   for(const v of ids)out.push(xyz[v*3],xyz[v*3+1],xyz[v*3+2]);
   counts[dynamic?1:0]++;
  }
 }
}
const bvhs=parts.map(p=>{const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(p,3));return new MeshBVH(g,{maxLeafSize:8})});

const root='public/assets/lighting/',floorMeta=JSON.parse(fs.readFileSync(root+'contact.json')),wallMeta=JSON.parse(fs.readFileSync(root+'walls.json'));
const windows=[],tracks=[];
for(const n of doc.getRoot().listNodes()){
 if(!n.getMesh())continue;const mat=n.getMesh().listPrimitives()[0].getMaterial();
 if(mat?.getName()==='外窗清玻璃'){
  const b=getBounds(n),dx=b.max[0]-b.min[0],dz=b.max[2]-b.min[2],axis=dx<dz?0:2,span=axis===0?2:0;
  const normal=new T.Vector3(axis===0?(b.min[0]>7?-1:1):0,0,axis===2?1:0),area=(b.max[1]-b.min[1])*(b.max[span]-b.min[span]);
  for(const u of [.2,.5,.8])for(const v of [.25,.75]){const p=b.min.map((x,i)=>(x+b.max[i])/2);p[span]=b.min[span]+u*(b.max[span]-b.min[span]);p[1]=b.min[1]+v*(b.max[1]-b.min[1]);windows.push({position:new T.Vector3(...p).addScaledVector(normal,.025),normal,area:area/6})}
 }
 if(/^客餐厅轨道射灯透镜/.test(n.getName())){const b=getBounds(n);tracks.push({position:new T.Vector3((b.min[0]+b.max[0])/2,b.min[1]-.008,(b.min[2]+b.max[2])/2),axis:new T.Vector3(0,-1,.38).normalize()})}
}
const ray=new T.Ray(),to=new T.Vector3();
function irradiance(point,normal){
 ray.origin.copy(point);let day=0,warm=0;
 for(const l of windows){to.copy(l.position).sub(point);const d=to.length();if(d>7)continue;to.divideScalar(d);const cosine=normal.dot(to),emit=-l.normal.dot(to);if(cosine<=0||emit<=0)continue;ray.direction.copy(to);if(!bvhs[0].raycastFirst(ray,T.DoubleSide,.008,d-.04))day+=3.5*l.area*cosine*emit/(d*d+.25)}
 for(const l of tracks){to.copy(l.position).sub(point);const d=to.length();if(d>4)continue;to.divideScalar(d);const cosine=normal.dot(to),cone=T.MathUtils.smoothstep(-l.axis.dot(to),.62,.92);if(cosine<=0||cone===0)continue;ray.direction.copy(to);if(!bvhs[0].raycastFirst(ray,T.DoubleSide,.008,d-.04))warm+=4*cosine*cone/(d*d+.2)}
 return [Math.min(1,day/4),Math.min(1,warm/4)];
}
const oldFloor=await sharp(root+floorMeta.file).removeAlpha().raw().toBuffer(),floor=Buffer.alloc(floorMeta.width*floorMeta.height*4),point=new T.Vector3(),normal=new T.Vector3(0,1,0);
for(let y=0;y<floorMeta.height;y++){for(let x=0;x<floorMeta.width;x++){
 const i=y*floorMeta.width+x,b=floorMeta.bounds;point.set(b[0]+(x+.5)/floorMeta.width*(b[2]-b[0]),.035,b[1]+(y+.5)/floorMeta.height*(b[3]-b[1]));const [day,warm]=irradiance(point,normal);
 floor[i*4]=oldFloor[i*3];floor[i*4+1]=oldFloor[i*3+1];floor[i*4+2]=Math.round(day*255);floor[i*4+3]=Math.round(128+warm*127);
 }if(y%128===0)console.log('Daylight floor',y)}
// Keep channels independent: alpha stores lamp energy, never coverage.
const floorImage=await sharp(floor,{raw:{width:floorMeta.width,height:floorMeta.height,channels:4}}).png().toBuffer();
const floorName='floor-light-'+crypto.createHash('sha256').update(floorImage).digest('hex').slice(0,12)+'.png';fs.writeFileSync(root+floorName,floorImage);
floorMeta.file=floorName;floorMeta.bytes=floorImage.length;floorMeta.channels={r:'fixed occlusion',g:'default furniture occlusion',b:'daylight / 4',a:'128 + 127 * warm track lighting / 4'};
const wallOld=await sharp(root+wallMeta.file).removeAlpha().raw().toBuffer({resolveWithObject:true}),wall=Buffer.alloc(wallMeta.width*wallMeta.height*3);
for(let i=0;i<wallMeta.width*wallMeta.height;i++)wall[i*3]=wallOld.data[i*wallOld.info.channels];
let count=0;
for(const r of wallMeta.receivers){for(let face=0;face<6;face++){
 const axis=Math.floor(face/2),sign=face%2===0?1:-1,axes=face<2?[2,1]:face<4?[0,2]:[0,1];
 const rect=r.rects[face],sx=Math.round(rect[0]*wallMeta.width),sy=Math.round(rect[1]*wallMeta.height),w=Math.round(rect[2]*wallMeta.width),h=Math.round(rect[3]*wallMeta.height);
 normal.set(0,0,0).setComponent(axis,sign);
 for(let y=-1;y<=h;y++)for(let x=-1;x<=w;x++){
  point.fromArray(r.min);point.setComponent(axis,(sign>0?r.max:r.min)[axis]+sign*.006);
  for(const [j,t,len] of [[0,x,w],[1,y,h]])point.setComponent(axes[j],r.min[axes[j]]+T.MathUtils.clamp((t+.5)/len,.001,.999)*(r.max[axes[j]]-r.min[axes[j]]));
  const [day,warm]=irradiance(point,normal),i=((sy+y)*wallMeta.width+sx+x)*3;wall[i+1]=Math.round(day*255);wall[i+2]=Math.round(warm*255);
 }
 }if(++count%20===0)console.log('Daylight wall',count)}
const wallImage=await sharp(wall,{raw:{width:wallMeta.width,height:wallMeta.height,channels:3}}).png().toBuffer();
const wallName='wall-light-'+crypto.createHash('sha256').update(wallImage).digest('hex').slice(0,12)+'.png';fs.writeFileSync(root+wallName,wallImage);wallMeta.file=wallName;wallMeta.bytes=wallImage.length;wallMeta.channels={r:'fixed occlusion',g:'daylight / 4',b:'warm track lighting / 4'};
const lighting={version:1,energyScale:4,windows:windows.map(l=>({position:l.position.toArray(),normal:l.normal.toArray(),area:l.area})),tracks:tracks.map(l=>({position:l.position.toArray(),axis:l.axis.toArray()})),pendants:[[6.0092,1.64,4.7304],[6.8492,1.64,4.7304]],dayColor:[1,1,.96],warmColor:[1,.73,.42]};
fs.writeFileSync(root+'fixtures.json',JSON.stringify(lighting));
floorMeta.lightingVersion=wallMeta.lightingVersion=1;
fs.writeFileSync(root+'contact.json',JSON.stringify(floorMeta));fs.writeFileSync(root+'walls.json',JSON.stringify(wallMeta));console.log('Baked',floorName,floorImage.length,wallName,wallImage.length);
