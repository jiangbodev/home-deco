// Bake optional contact shading from exact source geometry; never change meshes.
import fs from 'node:fs';import crypto from 'node:crypto';import{gzipSync}from'node:zlib';
import{NodeIO}from'@gltf-transform/core';import{ALL_EXTENSIONS}from'@gltf-transform/extensions';import D from'draco3dgltf';import * as T from'three';import{MeshBVH}from'three-mesh-bvh';
const source=process.argv[2];if(!source)throw Error('Supply exact source GLB');
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await D.createDecoderModule()});
const doc=await io.read(source),receivers=[],triangles=[];
const walls=new Set(JSON.parse(fs.readFileSync('public/assets/lighting/walls.json')).receivers.map(r=>r.name));const point=new T.Vector3(),normal=new T.Vector3();
for(const n of doc.getRoot().listNodes()){
 if(!n.getMesh()||/^树木/.test(n.getName()))continue;
 let visible=true,exclude=false;
 for(let p=n;p;p=p.getParentNode()){const e=p.getExtras();if(e.source_visible===false)visible=false;for(const k of Object.keys(e).filter(k=>k.startsWith('interaction_')))if(!['interaction_furniture','interaction_piano','interaction_dining-stored','interaction_effect-floor'].includes(k))exclude=true;}
 if(!visible||exclude)continue;
 const matrix=new T.Matrix4().fromArray(n.getWorldMatrix()),nm=new T.Matrix3().getNormalMatrix(matrix);
 for(const p of n.getMesh().listPrimitives()){
  const m=p.getMaterial();if(m.getAlphaMode()==='BLEND')continue;
  const a=p.getAttribute('POSITION'),ns=p.getAttribute('NORMAL'),indices=p.getIndices()?.getArray(),xyz=new Float32Array(a.getCount()*3);
  for(let i=0;i<a.getCount();i++)point.fromArray(a.getArray(),i*3).applyMatrix4(matrix).toArray(xyz,i*3);
  for(let i=0;i<(indices?.length||a.getCount());i++){const k=(indices?indices[i]:i)*3;triangles.push(xyz[k],xyz[k+1],xyz[k+2])}
  let metadata={};try{metadata=JSON.parse(n.getExtras().metadata||'{}')}catch{}
  if(!ns||walls.has(n.getName())||/^F0[1-9]$/.test(metadata.id||'')||/玄关六角砖/.test(n.getName())||m.getMetallicFactor()>.5)continue;
  const size=new T.Box3().setFromArray(xyz).getSize(new T.Vector3()),area=2*(size.x*size.y+size.x*size.z+size.y*size.z);
  if(a.getCount()<96||a.getCount()/Math.max(area,.01)<300)continue;
  const normals=new Float32Array(xyz.length);for(let i=0;i<a.getCount();i++)normal.fromArray(ns.getArray(),i*3).applyNormalMatrix(nm).toArray(normals,i*3);
  let hash=2166136261;for(const b of new Uint8Array(a.getArray().buffer,a.getArray().byteOffset,a.getArray().byteLength))hash=Math.imul(hash^b,16777619)>>>0;
  receivers.push({name:n.getName(),xyz,normals,hash,count:a.getCount()});
 }
}
const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.Float32BufferAttribute(triangles,3));const bvh=new MeshBVH(geometry,{maxLeafSize:8});
const samples=32,radius=.6,dirs=Array.from({length:samples},(_,i)=>{const r=Math.sqrt((i+.5)/samples),phi=i*2.39996323;return new T.Vector3(r*Math.cos(phi),Math.sqrt(1-r*r),r*Math.sin(phi))});
const ray=new T.Ray(),tangent=new T.Vector3(),bitangent=new T.Vector3(),up=new T.Vector3();const data=Buffer.alloc(receivers.reduce((s,r)=>s+r.count,0)),entries=[];let offset=0;
for(const [j,r] of receivers.entries()){
 for(let i=0;i<r.count;i++){
  point.fromArray(r.xyz,i*3);normal.fromArray(r.normals,i*3).normalize();up.set(0,Math.abs(normal.y)<.9?1:0,Math.abs(normal.y)<.9?0:1);tangent.crossVectors(up,normal).normalize();bitangent.crossVectors(normal,tangent);
  ray.origin.copy(point).addScaledVector(normal,.0025);let sum=0;
  for(const d of dirs){ray.direction.copy(tangent).multiplyScalar(d.x).addScaledVector(normal,d.y).addScaledVector(bitangent,d.z);const hit=bvh.raycastFirst(ray,T.DoubleSide,.002,radius);if(hit)sum+=Math.pow(1-hit.distance/radius,1.2)}
  data[offset+i]=Math.round(255*sum/samples);
  if(i&&i%40000===0)console.log('Baking',r.name,i,'/',r.count);
 }
 entries.push({name:r.name,count:r.count,hash:r.hash,offset});offset+=r.count;if(j%30===0)console.log('Objects',j,'/',receivers.length,'vertices',offset);
}
const packed=gzipSync(data,{level:9,mtime:0}),file='object-contact-'+crypto.createHash('sha256').update(packed).digest('hex').slice(0,12)+'.bin.gz',root='public/assets/lighting/';fs.writeFileSync(root+file,packed);
const sourceModules=Object.values(JSON.parse(fs.readFileSync('public/assets/modules/manifest.json')).modules).map(m=>m.file).sort();fs.writeFileSync(root+'objects.json',JSON.stringify({file,bytes:packed.length,rawBytes:data.length,sourceModules,sourceSha256:crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),samples,radius,entries}));console.log('Wrote',file,packed.length,data.length,entries.length);
