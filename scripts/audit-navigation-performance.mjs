// CPU/geometry diagnostic only: does not measure browser GPU frame rate.
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import draco from 'draco3dgltf';
import * as THREE from 'three';
import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {MeshBVH,acceleratedRaycast} from 'three-mesh-bvh';
import {rooms} from '../src/rooms.js';
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await draco.createDecoderModule()});
const manifest=JSON.parse(await fs.readFile('public/assets/modules/manifest.json'));
const root=new THREE.Group(),targets=new Map(),stats=[];
for(const [key,entry] of Object.entries(manifest.modules).sort(([a],[b])=>a==='base'?-1:b==='base'?1:0)){
 const doc=await io.read('public/assets/modules/'+entry.file),objects=new Map();let triangles=0,meshes=0;
 for(const n of doc.getRoot().listNodes()){
  const o=new THREE.Group();o.name=n.getName();o.userData=n.getExtras();o.visible=o.userData.source_visible!==false;o.matrix.fromArray(n.getMatrix());o.matrix.decompose(o.position,o.quaternion,o.scale);objects.set(n,o);
  for(const p of n.getMesh()?.listPrimitives()??[]){
   const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(p.getAttribute('POSITION').getArray(),3));if(p.getIndices())g.setIndex(new THREE.BufferAttribute(p.getIndices().getArray(),1));
   const mesh=new THREE.Mesh(g,new THREE.MeshBasicMaterial({side:p.getMaterial()?.getDoubleSided()?THREE.DoubleSide:THREE.FrontSide}));mesh.name=n.getName();mesh.userData={...o.userData,auditModule:key};o.add(mesh);triangles+=(g.index?.count??g.attributes.position.count)/3;meshes++;
  }
 }
 for(const[n,o]of objects)for(const c of n.listChildren())o.add(objects.get(c));
 const group=new THREE.Group();for(const n of doc.getRoot().listScenes()[0].listChildren())group.add(objects.get(n));
 if(key==='base'){root.add(group);group.traverse(o=>{if(Number.isInteger(o.userData.moduleNode))targets.set(o.userData.moduleNode,o)})}
 else for(const o of [...group.children]){const parent=targets.get(o.userData.attachTo);if(!parent)throw Error('Missing attachment');parent.add(o)}
 stats.push({module:key,meshes,triangles});
}
root.updateMatrixWorld(true);
const obstacleBounds=new Map(),floorMeshes=[];
function effectiveVisible(o){for(let p=o;p;p=p.parent)if(!p.visible)return false;return true}
root.traverse(o=>{if(!o.isMesh)return;o.geometry.computeBoundingBox();o.geometry.computeBoundingSphere();obstacleBounds.set(o,o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld));let m={};try{m=JSON.parse(o.userData.metadata||'{}')}catch{}if(/^F0[1-9]$/.test(m.id||''))floorMeshes.push(o)});
const camera=new THREE.PerspectiveCamera(65,16/9,.035,90),ray=new THREE.Raycaster(),direction=new THREE.Vector3(),down=new THREE.Vector3(0,-1,0);
const src=execFileSync('git',['show','8fcd1e1:src/main.js'],{encoding:'utf8'}); // Historical collision implementation for comparison.
// Run the actual production collision function, with reconstructed decoded meshes.
const allowedStep=new Function('THREE','camera','direction','obstacleBounds','effectiveVisible','ray','floorMeshes','down',src.slice(src.indexOf('function allowedStep('),src.indexOf('\nfunction move('))+';return allowedStep')(THREE,camera,direction,obstacleBounds,effectiveVisible,ray,floorMeshes,down);
const samples=[];
for(let z=2.7;z<=5.11;z+=.15)for(let x=10.8;x<=12.76;x+=.15){
 camera.position.set(x,1.5,z);const times=[];let exits=0;
 for(let run=0;run<5;run++){const t=performance.now();exits=0;for(const[dx,dz]of [[.0225,0],[-.0225,0],[0,.0225],[0,-.0225]])exits+=allowedStep(x+dx,z+dz)?1:0;times.push(performance.now()-t)}
 times.sort((a,b)=>a-b);if(!exits)continue;
 const nearby=[...obstacleBounds].filter(([o,b])=>effectiveVisible(o)&&b.max.x>=x-.203&&b.min.x<=x+.203&&b.max.z>=z-.203&&b.min.z<=z+.203&&b.max.y>=.35&&b.min.y<=1.5).map(([o])=>({name:o.name,module:o.userData.auditModule,triangles:(o.geometry.index?.count??o.geometry.attributes.position.count)/3})).sort((a,b)=>b.triangles-a.triangles);
 samples.push({x:+x.toFixed(2),z:+z.toFixed(2),fourDirectionsMs:+times[2].toFixed(3),exits,nearby:nearby.slice(0,5)});
}
const views=rooms.filter((_,i)=>[1,4].includes(i)).map(r=>{camera.position.set(r.x,1.5,r.z);camera.lookAt(r.look[0],1.46,r.look[1]);camera.updateMatrixWorld(true);const f=new THREE.Frustum().setFromProjectionMatrix(new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse));let meshes=0,triangles=0;const modules={};root.traverse(o=>{if(o.isMesh&&effectiveVisible(o)&&f.intersectsObject(o)){meshes++;const n=(o.geometry.index?.count??o.geometry.attributes.position.count)/3;triangles+=n;const key=o.userData.auditModule;modules[key]??={meshes:0,triangles:0};modules[key].meshes++;modules[key].triangles+=n}});return {room:r.name,meshes,triangles,modules}});
samples.sort((a,b)=>b.fourDirectionsMs-a.fourDirectionsMs);
const collisionComparison=[];
const probes=[{x:11.7,z:3.45},{x:10.95,z:3.9},{x:12.45,z:2.7},{x:11.7,z:5.1}];
function measure(){return probes.map(p=>{camera.position.set(p.x,1.5,p.z);const directions=[];for(const[dx,dz]of [[.0225,0],[-.0225,0],[0,.0225],[0,-.0225]]){const times=[];let allowed;for(let i=0;i<35;i++){const t=performance.now();allowed=allowedStep(p.x+dx,p.z+dz);times.push(performance.now()-t)}times.sort((a,b)=>a-b);directions.push({dx,dz,allowed,medianMs:+times[17].toFixed(4)})}return {...p,directions}})}
const before=measure();
// Prototype only; indirect BVHs leave source indices untouched.
const buildStart=performance.now();let acceleratedMeshes=0;
root.traverse(o=>{if(o.isMesh&&(o.geometry.index?.count??o.geometry.attributes.position.count)>3000){o.geometry.boundsTree=new MeshBVH(o.geometry,{indirect:true});o.raycast=acceleratedRaycast;acceleratedMeshes++}});
const buildMs=performance.now()-buildStart;ray.firstHitOnly=true;
const after=measure();
let mismatches=0;
// Recheck all sampled positions and directions with and without acceleration.
for(const p of samples){camera.position.set(p.x,1.5,p.z);for(const[dx,dz]of [[.0225,0],[-.0225,0],[0,.0225],[0,-.0225]]){const fast=allowedStep(p.x+dx,p.z+dz);root.traverse(o=>{if(o.isMesh&&o.geometry.boundsTree)o.raycast=THREE.Mesh.prototype.raycast});const slow=allowedStep(p.x+dx,p.z+dz);root.traverse(o=>{if(o.isMesh&&o.geometry.boundsTree)o.raycast=acceleratedRaycast});if(fast!==slow)mismatches++}}
collisionComparison.push({before,after,acceleratedMeshes,buildMs:+buildMs.toFixed(2),checks:samples.length*4,mismatches});
const report={collisionComparison,note:'Node CPU diagnostic; four independent directional collision checks per sample, median of five runs. Frustum counts are estimates, not measured draw calls. No GPU/FPS claim.',stats,views,collision:{samples:samples.length,worst:samples.slice(0,12),medianFourDirectionsMs:samples[Math.floor(samples.length/2)]?.fourDirectionsMs}};
await fs.mkdir('review',{recursive:true});await fs.writeFile('review/navigation-performance.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
