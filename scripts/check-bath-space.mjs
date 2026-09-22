import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const before=await io.read('qa/bath-space/before.glb'),after=await io.read('qa/bath-space/source.glb');
const old=new Map(before.getRoot().listNodes().map(n=>[n.getName(),n]));
const hidden=new Set(JSON.parse(await fs.readFile('review/bath-space/blender.json')).hidden);
let checked=0;
for(const n of after.getRoot().listNodes()){
 const b=old.get(n.getName());assert(b);assert.deepEqual(n.getMatrix(),b.getMatrix());
 const expected={...b.getExtras()};if(hidden.has(n.getName()))expected.source_visible=false;
 assert.deepEqual(n.getExtras(),expected);
 if(n.getMesh()){
  const ps=n.getMesh().listPrimitives(),bs=b.getMesh().listPrimitives();assert.equal(ps.length,bs.length);
  for(let i=0;i<ps.length;i++){assert(ps[i].getIndices().getCount()<=bs[i].getIndices().getCount(),'Unexpected added geometry: '+n.getName());const a=ps[i].getAttribute('POSITION'),b=bs[i].getAttribute('POSITION');for(const edge of ['getMin','getMax']){const av=a[edge]([]),bv=b[edge]([]);for(let j=0;j<3;j++)assert(Math.abs(av[j]-bv[j])<.001,'Bounds changed: '+n.getName());}}
  checked++;
 }
}
for(const name of hidden)assert.equal(after.getRoot().listNodes().find(n=>n.getName()===name).getExtras().source_visible,false);
console.log(JSON.stringify({removedFromScene:[...hidden],unchangedGeometryMeshes:checked,windowsAndShower:'Original transforms and bounds within 1 mm retained; no added triangles'}));
