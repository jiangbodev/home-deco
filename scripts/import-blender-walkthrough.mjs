// Integrate Blender-authored living-area geometry; preserve original module hierarchy, materials and textures.
import {NodeIO,PropertyType} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {copyToDocument,prune,draco,unpartition} from '@gltf-transform/functions';
import * as THREE from 'three';
import D from 'draco3dgltf';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';

const input=process.argv[2],output=process.argv[3],blenderFile=process.argv[4];
if(!input||!output||!blenderFile||input===output)throw Error('Usage: node scripts/import-blender-living.mjs ORIGINAL_MODULE_DIR OUTPUT_MODULE_DIR BLENDER_EXPORT.glb');
await fs.mkdir(output,{recursive:true});
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await D.createDecoderModule(),'draco3d.encoder':await D.createEncoderModule()});
const edited=await io.read(blenderFile),editedNodes=new Map(edited.getRoot().listNodes().map(n=>[n.getName(),n]));
const removed=new Set();
const manifest=JSON.parse(await fs.readFile(input+'/manifest.json')),report=[];
const base=await io.read(input+'/'+manifest.modules.base.file),parents=new Map(base.getRoot().listNodes().map(n=>[n.getExtras().moduleNode,n]));
for(const key of Object.keys(manifest.modules)){
 const entry=manifest.modules[key],doc=await io.read(input+'/'+entry.file);
 if(!doc.getRoot().listNodes().some(n=>n.getMesh()&&(editedNodes.has(n.getName())||removed.has(n.getName()))))continue;
 doc.getRoot().listExtensionsUsed().find(e=>e.extensionName==='KHR_draco_mesh_compression')?.dispose();
 const treeInstances=new Map();
 for(const n of doc.getRoot().listNodes()){
  if(!n.getMesh())continue;
  if(removed.has(n.getName())){n.setMesh(null);continue;}
  const originalMesh=n.getMesh();if(n.getName().startsWith('树木_')&&treeInstances.has(originalMesh)){n.setMesh(treeInstances.get(originalMesh));continue;}
  const editedNode=editedNodes.get(n.getName());if(!editedNode?.getMesh())continue;
  const unique=n.getMesh().clone();for(const p of unique.listPrimitives()){unique.removePrimitive(p);unique.addPrimitive(p.clone())}n.setMesh(unique);if(n.getName().startsWith('树木_'))treeInstances.set(originalMesh,unique);
  const oldPrimitives=n.getMesh().listPrimitives(),newPrimitives=editedNode.getMesh().listPrimitives();assert.equal(oldPrimitives.length,newPrimitives.length);
  const targetWorld=new THREE.Matrix4().fromArray((key==='base'?n:parents.get(n.getExtras().attachTo)).getWorldMatrix());
  const sourceWorld=new THREE.Matrix4().fromArray(editedNode.getWorldMatrix());
  const transform=targetWorld.clone().invert().multiply(sourceWorld),normalMatrix=new THREE.Matrix3().getNormalMatrix(transform);
  for(let i=0;i<oldPrimitives.length;i++){
   const p=oldPrimitives[i],editedPrimitive=newPrimitives[i],before=p.getIndices().getCount()/3;
   const bounds=a=>{const box=new THREE.Box3().setFromArray(a);return [...box.min.toArray(),...box.max.toArray()]};const oldBounds=bounds(p.getAttribute('POSITION').getArray());
   const properties=[...editedPrimitive.listAttributes(),editedPrimitive.getIndices()],map=copyToDocument(doc,edited,properties);
   for(const semantic of p.listSemantics())p.setAttribute(semantic,null);
   for(const semantic of editedPrimitive.listSemantics())p.setAttribute(semantic,map.get(editedPrimitive.getAttribute(semantic)));
   p.setIndices(map.get(editedPrimitive.getIndices()));
   if(n.getName().startsWith('Cloth cover'))p.getMaterial().setBaseColorFactor([1,1,1,1]);
   if(n.getName().startsWith('Curved pointed leaf'))p.getMaterial().setDoubleSided(true);
   for(const semantic of ['POSITION','NORMAL','TANGENT']){
    const attr=p.getAttribute(semantic);if(!attr)continue;const data=attr.getArray(),stride=attr.getElementSize(),v=new THREE.Vector3();
    for(let j=0;j<attr.getCount();j++){v.fromArray(data,j*stride);if(semantic==='POSITION')v.applyMatrix4(transform);else v.applyMatrix3(normalMatrix).normalize();v.toArray(data,j*stride)}
   }
   const after=p.getIndices().getCount()/3,newBounds=bounds(p.getAttribute('POSITION').getArray());
   assert(after>0,'Empty edited geometry');
   report.push({module:key,name:n.getName(),before,after,oldBounds,newBounds,method:'Blender walkthrough repair; original module hierarchy/materials preserved'});
  }
 }
 await doc.transform(prune({propertyTypes:[PropertyType.MESH,PropertyType.PRIMITIVE,PropertyType.ACCESSOR]}),unpartition(),draco({quantizePosition:16,quantizeNormal:10,quantizeTexcoord:12,encodeSpeed:0,decodeSpeed:0}));
 // GLTF JSON export leaves the existing content-addressed textures external.
 const {json,resources}=await io.writeJSON(doc,{format:'GLTF'});assert.equal(json.buffers.length,1);
 const binary=Buffer.from(resources[json.buffers[0].uri]);delete json.buffers[0].uri;
 for(const image of json.images??[]){assert(entry.textures.includes(image.uri));assert.deepEqual(Buffer.from(resources[image.uri]),await fs.readFile(input+'/'+image.uri))}
 const str=Buffer.from(JSON.stringify(json)),j=Buffer.alloc(Math.ceil(str.length/4)*4,32);str.copy(j);const b=Buffer.alloc(Math.ceil(binary.length/4)*4);binary.copy(b);
 const header=Buffer.alloc(20);header.writeUInt32LE(0x46546c67,0);header.writeUInt32LE(2,4);header.writeUInt32LE(28+j.length+b.length,8);header.writeUInt32LE(j.length,12);header.writeUInt32LE(0x4e4f534a,16);
 const bh=Buffer.alloc(8);bh.writeUInt32LE(b.length,0);bh.writeUInt32LE(0x004e4942,4);const raw=Buffer.concat([header,j,bh,b]);
 const file=key+'-'+crypto.createHash('sha256').update(raw).digest('hex').slice(0,12)+'.glb';await fs.writeFile(output+'/'+file,raw);manifest.modules[key]={...entry,file,bytes:raw.length};
}
await fs.writeFile(output+'/manifest.json',JSON.stringify(manifest,null,2)+'\n');await fs.writeFile('review/walkthrough-integration.json',JSON.stringify(report,null,2)+'\n');console.log(report);
