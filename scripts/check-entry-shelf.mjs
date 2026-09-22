import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {getBounds} from '@gltf-transform/functions';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const doc=await new NodeIO().registerExtensions(ALL_EXTENSIONS).read(process.argv[2]||'qa/entry-shelf-source.glb');
const nodes=new Map(doc.getRoot().listNodes().map(n=>[n.getName(),n]));
const bounds=name=>getBounds(nodes.get(name));
for(const name of ['玄关餐桌连接侧体','玄关后方结构柱','玄关共用背墙','玄关前拱框','玄关左侧圆弧包覆'])assert(nodes.get(name).getMesh().listPrimitives().every(p=>p.getMaterial().getExtras().source_material_id===38),name+' must use the same ivory lacquer');
const projector=bounds('超短焦投影机_产品外形示意'),ceiling=bounds('原顶_高度待核'),bulkhead=bounds('客厅南顶面边带');
assert(projector.min[1]>2.3,'Projector must clear standing head height');
assert(Math.abs(projector.max[1]-ceiling.min[1])<.001,'Ceiling plate must meet the actual ceiling');
assert(projector.max[2]<bulkhead.min[2]-.04,'Keep housing and mount in front of AC soffit/grille');
assert(Math.abs((projector.min[0]+projector.max[0])/2-11.0306)<.002,'Projector and screen horizontal axes');
const shelf=bounds('沙发上方浅色层板');let support=shelf.max[1];
for(let i=0;i<3;i++){const b=bounds('搁板薄书示意'+i);assert(Math.abs(b.min[1]-support)<.001,'Stacked books must rest on support');assert(b.min[0]>=shelf.min[0]&&b.max[0]<=shelf.max[0]&&b.min[2]>=shelf.min[2]&&b.max[2]<=shelf.max[2],'Book overhang');support=b.max[1];}
const cabinet=bounds('主卧北窗转角地柜'),counter=bounds('主卧转角连续台面');assert(Math.abs(cabinet.max[1]-counter.min[1])<.001,'Cabinet must support return countertop');assert(cabinet.min[0]>=counter.min[0]-.001&&cabinet.max[0]<=counter.max[0]+.001,'Cabinet width');assert(cabinet.min[1]>=-.001,'Cabinet floor');
const report={entryLacquerUnified:true,projector,ceilingClearanceAndConnection:true,booksSupported:true,bedroomCabinet: cabinet};await fs.writeFile('review/entry-shelf-checks.json',JSON.stringify(report,null,2)+'\n');console.log(report);
