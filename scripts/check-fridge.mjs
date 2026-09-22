import{NodeIO}from'@gltf-transform/core';import{ALL_EXTENSIONS}from'@gltf-transform/extensions';import{getBounds}from'@gltf-transform/functions';import fs from'node:fs/promises';import assert from'node:assert/strict';
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS),before=await io.read('qa/fridge-before.glb'),after=await io.read('qa/fridge-wide-source.glb'),originals=new Map(before.getRoot().listNodes().map(n=>[n.getName(),n]));
const hidden=new Set(['冰箱外包拉手','冰箱外包门后暗缝底']),changed=new Set(JSON.parse(await fs.readFile('review/fridge/blender-wide.json')).changed);let preserved=0,triangles=0;
for(const n of after.getRoot().listNodes()){
 const b=originals.get(n.getName());assert(b);assert.deepEqual(n.getMatrix(),b.getMatrix());assert.deepEqual(n.getExtras(),hidden.has(n.getName())?{...b.getExtras(),source_visible:false}:b.getExtras());
 if(!n.getMesh())continue;
 triangles+=n.getMesh().listPrimitives().reduce((s,p)=>s+p.getIndices().getCount()/3,0);
 if(!changed.has(n.getName())){const a=getBounds(n),bb=getBounds(b);assert(a.min.every((v,i)=>Math.abs(v-bb.min[i])<.0002)&&a.max.every((v,i)=>Math.abs(v-bb.max[i])<.0002));preserved++;}
}
const fridge=after.getRoot().listNodes().find(n=>n.getName()==='冰箱外包门板1'),b=getBounds(fridge);assert(b.min[0]>3.482&&b.max[0]<4.151);assert(b.min[1]>.025&&b.max[1]<1.78);assert(b.min[2]>2.457&&b.max[2]<3.322);
const mids=fridge.getMesh().listPrimitives().map(p=>p.getMaterial().getExtras().source_material_id);for(const id of[360,361,362,363])assert(mids.includes(id));
const report={triangles,unrelatedMeshBoundsPreserved:preserved,transformsAndInteractionMetadataPreserved:true,retiredKnobAndBacking:true,fridgeBounds:b,materials:mids,applianceFitsResizedNiche:true,nominalNicheWidth:.9,adjacentStorageWidth:.45};await fs.writeFile('review/fridge/validation-wide.json',JSON.stringify(report,null,2));console.log(report);
