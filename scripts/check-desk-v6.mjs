import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {getBounds} from '@gltf-transform/functions';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS),before=await io.read('qa/desk-v6/before.glb'),after=await io.read('qa/desk-v6/source.glb');
const old=new Map(before.getRoot().listNodes().map(n=>[n.getName(),n])),spec=JSON.parse(await fs.readFile('review/desk-v6/blender.json')),added=new Set(spec.added.map(x=>x.name));let unchanged=0,triangles=0;
for(const n of after.getRoot().listNodes()){
 if(!added.has(n.getName())){const o=old.get(n.getName());assert(o,n.getName());assert.deepEqual(n.getMatrix(),o.getMatrix());assert.deepEqual(n.getExtras(),o.getExtras());if(n.getMesh()){assert.deepEqual(getBounds(n),getBounds(o));unchanged++}}
 for(const p of n.getMesh()?.listPrimitives()??[]){triangles+=p.getIndices().getCount()/3;for(const a of p.listAttributes())assert([...a.getArray()].every(Number.isFinite));}
 if(!added.has(n.getName()))continue;
 const b=getBounds(n);assert(b.min[0]>=13.3488&&b.max[0]<=13.9492&&b.min[2]>=.7392&&b.max[2]<=2.4896);assert(b.min[1]>=.7499&&b.min[1]<.755);
 if(n.getName().includes('显示器')){assert(b.min[2]>.96);assert(b.max[1]<1.26)}
}
for(const x of spec.measurements)assert(Math.abs(Math.hypot(x.activeWidthM,x.activeHeightM)/.0254-27)<1e-10);
for(const name of ['主卧层板书册1','主卧层板书册2','主卧层板陶碗1','主卧层板陶碗2'])assert.equal(after.getRoot().listNodes().find(n=>n.getName()===name).getExtras().source_visible,false);
const result={unchangedMeshBounds:unchanged,addedMeshNodes:added.size,triangles,addedTriangles:triangles-652882,measurements:spec.measurements};await fs.writeFile('review/desk-v6/validation.json',JSON.stringify(result,null,2));console.log(result);
