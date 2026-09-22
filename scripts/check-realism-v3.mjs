import{NodeIO}from'@gltf-transform/core';import{ALL_EXTENSIONS}from'@gltf-transform/extensions';import{getBounds}from'@gltf-transform/functions';import fs from'node:fs/promises';import assert from'node:assert/strict';
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS),a=await io.read('qa/realism-v3/before.glb'),b=await io.read('qa/realism-v3/source.glb');
const spec=JSON.parse(await fs.readFile('review/realism-v3/blender.json')),changed=new Set(spec.changed),hidden=new Set(spec.hidden),old=new Map(a.getRoot().listNodes().map(n=>[n.getName(),n])),nodes=new Map(b.getRoot().listNodes().map(n=>[n.getName(),n]));let preserved=0,triangles=0;
for(const n of b.getRoot().listNodes()){
 const p=old.get(n.getName());if(p){assert.deepEqual(n.getMatrix(),p.getMatrix(),n.getName());const extras={...p.getExtras()};if(hidden.has(n.getName()))extras.source_visible=false;assert.deepEqual(n.getExtras(),extras);if(n.getMesh()&&!changed.has(n.getName())){const x=getBounds(n),y=getBounds(p);for(const k of ['min','max'])for(let i=0;i<3;i++)assert(Math.abs(x[k][i]-y[k][i])<.001,n.getName());preserved++;}}else assert(spec.added.some(v=>v.name===n.getName()));
 for(const p of n.getMesh()?.listPrimitives()??[])triangles+=p.getIndices().getCount()/3;
}
const bounds=name=>getBounds(nodes.get(name));
const desk=bounds('主卧书桌_600x1750台面');for(const name of ['主卧书桌支架','主卧书桌支架.001']){const leg=bounds(name);assert(leg.max[1]>=desk.min[1]-.0003&&leg.max[1]<=desk.min[1]+.002);}
for(const h of [1200,1540,1920]){const box=bounds('主卧转角开放层板_'+h);assert(Math.abs(box.max[0]-box.min[0]-.3)<.0003);assert(Math.abs(box.max[2]-box.min[2]-.74)<.0003);assert(Math.abs(box.max[1]-box.min[1]-.04)<.0003);}
for(let i=1;i<=2;i++){const books=bounds('主卧层板书册'+i),shelf=bounds('主卧转角开放层板_'+[1200,1540][i-1]),bowl=bounds('主卧层板陶碗'+i);assert(Math.abs(books.min[1]-shelf.max[1])<.0003);assert(Math.abs(bowl.min[1]-books.max[1])<.0003);assert(books.min[0]>shelf.min[0]&&books.max[0]<shelf.max[0]);}
const head=bounds('主卧床头软包靠板');assert(Math.abs(head.min[2]-.219388)<.0003);assert(head.max[0]<11.899&&head.min[0]>10.098);assert(head.min[1]>.498);
const chair=bounds('Warm grey upholstered study chair.001'),legs=bounds('Warm walnut - real oak scan tinted.007');assert(chair.max[0]<desk.min[0]-.008);assert(Math.abs(legs.min[1])<.0003);assert(legs.max[1]>=chair.min[1]);
for(const name of ['浴缸侧裙','浴缸前裙','浴缸外包1275x840','浴缸深内腔'])assert(nodes.get(name).getMesh().listPrimitives().every(p=>p.getMaterial().getExtras().source_material_id===302));
for(const name of ['次卫中央空调外机机壳','次卫中央空调外机保温管','次卫外机朝外排风导流罩'])assert.equal(nodes.get(name).getExtras().source_visible,false);
const result={triangles,preservedMeshBounds:preserved,originalTransformsPreserved:true,deskSupport:'contact within 2 mm',shelves:'740 x 300 x 40 mm',booksAndBowls:'supported',headboard:'at wall, within bed width',chair:'floor support and desktop clearance',bath:'porcelain, not grey countertop'};await fs.writeFile('review/realism-v3/validation.json',JSON.stringify(result,null,2));console.log(result);
