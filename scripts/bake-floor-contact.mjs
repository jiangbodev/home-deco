// Offline contact occlusion from the exact authored meshes. No model simplification.
// Usage: node scripts/bake-floor-contact.mjs source.glb
import fs from 'node:fs';
import crypto from 'node:crypto';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import D from 'draco3dgltf';
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
const width=768,height=512,bounds=[-.5,-.5,14.5,9.5],samples=48,radius=.85;
const dirs=Array.from({length:samples},(_,i)=>{const r=Math.sqrt((i+.5)/samples),phi=i*2.399963229728653;return new T.Vector3(r*Math.cos(phi),Math.sqrt(1-r*r),r*Math.sin(phi))});
const pixels=Buffer.alloc(width*height*3),ray=new T.Ray();
for(let y=0;y<height;y++){
 for(let x=0;x<width;x++){
  ray.origin.set(bounds[0]+(x+.5)/width*(bounds[2]-bounds[0]),.035,bounds[1]+(y+.5)/height*(bounds[3]-bounds[1]));
  for(let b=0;b<2;b++){
   let sum=0;for(const d of dirs){ray.direction.copy(d);const hit=bvhs[b].raycastFirst(ray,T.DoubleSide,.003,radius);if(hit)sum+=Math.pow(1-hit.distance/radius,.65)}
   pixels[(y*width+x)*3+b]=Math.round(255*sum/samples);
  }
 }
 if(y%128===0)console.log('Bake row',y,'/',height);
}
const output=await sharp(pixels,{raw:{width,height,channels:3}}).blur(.7).png().toBuffer();
const name='floor-contact-'+crypto.createHash('sha256').update(output).digest('hex').slice(0,12)+'.png';
fs.writeFileSync('public/assets/lighting/'+name,output);
fs.writeFileSync('public/assets/lighting/contact.json',JSON.stringify({file:name,sourceModules,bytes:output.length,width,height,bounds,samples,radius,sourceSha256:crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex'),triangles:counts,channels:{r:'fixed geometry',g:'default visible furniture',b:'unused'},excludes:'all doors, movable windows, curtains, ceiling, transparent surfaces'},null,2)+'\n');
console.log(name,output.length,counts);

// Static wall/cabinet corner occlusion; never includes openable or movable objects.
const atlasWidth=1024,charts=[];let cursorX=2,cursorY=2,rowHeight=0;
for(const r of receivers){r.rects=[];const size=r.max.map((v,i)=>v-r.min[i]);for(let face=0;face<6;face++){
 const axes=face<2?[2,1]:face<4?[0,2]:[0,1];
 const w=Math.max(3,Math.min(256,Math.ceil(size[axes[0]]*32))),h=Math.max(3,Math.min(128,Math.ceil(size[axes[1]]*32)));
 if(cursorX+w+2>atlasWidth){cursorX=2;cursorY+=rowHeight+4;rowHeight=0}
 const rect=[cursorX,cursorY,w,h];r.rects.push(rect);charts.push({r,face,axes,rect});cursorX+=w+4;rowHeight=Math.max(rowHeight,h);
}}
const atlasHeight=2**Math.ceil(Math.log2(cursorY+rowHeight+2)),atlas=Buffer.alloc(atlasWidth*atlasHeight,0),normal=new T.Vector3(),tangent=new T.Vector3(),bitangent=new T.Vector3();
console.log('Wall bake',receivers.length,'receivers',atlasWidth,atlasHeight);
for(let ci=0;ci<charts.length;ci++){
 const {r,face,axes,rect:[sx,sy,w,h]}=charts[ci],axis=Math.floor(face/2),sign=face%2===0?1:-1;
 normal.set(0,0,0).setComponent(axis,sign);tangent.set(0,0,0).setComponent(axes[0],1);bitangent.crossVectors(normal,tangent);
 for(let y=-1;y<=h;y++)for(let x=-1;x<=w;x++){
  const origin=r.min.slice();origin[axis]=(sign>0?r.max:r.min)[axis]+sign*.006;
  origin[axes[0]]=r.min[axes[0]]+Math.min(.999,Math.max(.001,(x+.5)/w))*(r.max[axes[0]]-r.min[axes[0]]);
  origin[axes[1]]=r.min[axes[1]]+Math.min(.999,Math.max(.001,(y+.5)/h))*(r.max[axes[1]]-r.min[axes[1]]);
  ray.origin.fromArray(origin);let sum=0;
  for(const d of dirs){ray.direction.copy(tangent).multiplyScalar(d.x).addScaledVector(normal,d.y).addScaledVector(bitangent,d.z);const hit=bvhs[0].raycastFirst(ray,T.DoubleSide,.003,.5);if(hit)sum+=Math.pow(1-hit.distance/.5,.65)}
  atlas[(sy+y)*atlasWidth+sx+x]=Math.round(255*sum/samples);
 }
 if(ci%120===0)console.log('Wall chart',ci,'/',charts.length);
}
const wallData=await sharp(atlas,{raw:{width:atlasWidth,height:atlasHeight,channels:1}}).png().toBuffer();
const wallName='wall-contact-'+crypto.createHash('sha256').update(wallData).digest('hex').slice(0,12)+'.png';fs.writeFileSync('public/assets/lighting/'+wallName,wallData);
for(const r of receivers)r.rects=r.rects.map(([x,y,w,h])=>[x/atlasWidth,y/atlasHeight,w/atlasWidth,h/atlasHeight]);
fs.writeFileSync('public/assets/lighting/walls.json',JSON.stringify({file:wallName,sourceModules,bytes:wallData.length,width:atlasWidth,height:atlasHeight,receivers})+'\n');console.log('Wall output',wallName,wallData.length);
