// Plan world-projected irradiance charts without changing any runtime geometry or UVs.
import {NodeIO} from '@gltf-transform/core';import {ALL_EXTENSIONS} from '@gltf-transform/extensions';import{getBounds}from'@gltf-transform/functions';import * as T from'three';import fs from'node:fs/promises';import crypto from'node:crypto';
const input=process.argv[2],output=process.argv[3];const io=new NodeIO().registerExtensions(ALL_EXTENSIONS),doc=await io.read(input);const receivers=[],floors=[];
for(const n of doc.getRoot().listNodes()){
 if(!n.getMesh())continue;let visible=true;for(let p=n;p;p=p.getParentNode())if(p.getExtras().source_visible===false)visible=false;if(!visible)continue;
 const ps=n.getMesh().listPrimitives();if(ps.some(p=>p.getMaterial()?.getAlphaMode()==='BLEND'||p.getMaterial()?.getExtension('KHR_materials_transmission')?.getTransmissionFactor()>0))continue;
 let meta={};try{meta=JSON.parse(n.getExtras().metadata??'{}')}catch{}
 const box=getBounds(n),size=box.max.map((v,i)=>v-box.min[i]);
 if(/^F0[1-9]$/.test(meta.id??'')){floors.push({name:n.getName(),moduleNode:n.getExtras().moduleNode,...box});continue}
 if(Math.max(...size)<.28||Math.min(...size.filter(v=>v>.005))<.012||/^(树木|Cloth cover|Warm page)/.test(n.getName()))continue;
 const matrix=new T.Matrix4().fromArray(n.getWorldMatrix()),v=new T.Vector3(),points=[];let axial=true,totalArea=0,axialArea=0;
 for(const p of ps){const pos=p.getAttribute('POSITION'),idx=p.getIndices()?.getArray();if(pos.getCount()>5000){axial=false;break}for(let i=0;i<pos.getCount();i++)points[i]=v.fromArray(pos.getArray(),i*3).applyMatrix4(matrix).clone();for(let i=0;i<(idx?.length??pos.getCount());i+=3){const a=points[idx?idx[i]:i],b=points[idx?idx[i+1]:i+1],c=points[idx?idx[i+2]:i+2];const norm=b.clone().sub(a).cross(c.clone().sub(a));const area=norm.length();totalArea+=area;norm.normalize();if(Math.max(...norm.toArray().map(Math.abs))>=.999)axialArea+=area;}if(!axial)break}
 if(axial&&totalArea>0&&axialArea/totalArea>.95)receivers.push({name:n.getName(),moduleNode:n.getExtras().moduleNode,...box});
}
const width=2048;let x=4,y=4,row=0;
for(const r of receivers){r.rects=[];const size=r.max.map((v,i)=>v-r.min[i]);for(let face=0;face<6;face++){const axes=face<2?[2,1]:face<4?[0,2]:[0,1];const w=Math.max(4,Math.min(256,Math.ceil(size[axes[0]]*32))),h=Math.max(4,Math.min(256,Math.ceil(size[axes[1]]*32)));if(x+w+4>width){x=4;y+=row+8;row=0}r.rects.push([x,y,w,h]);x+=w+8;row=Math.max(row,h)}}
const height=2**Math.ceil(Math.log2(y+row+4));for(const r of receivers)r.rects=r.rects.map(([x,y,w,h])=>[x/width,y/height,w/width,h/height]);
const result={version:1,sourceSha256:crypto.createHash('sha256').update(await fs.readFile(input)).digest('hex'),sourceModules:Object.values(JSON.parse(await fs.readFile('public/assets/modules/manifest.json')).modules).map(m=>m.file).sort(),wall:{width,height,receivers},floor:{width:1024,height:512,bounds:[0,0,14.2,7.12],receivers:floors}};
await fs.writeFile(output,JSON.stringify(result,null,2));console.log({receivers:receivers.length,floors:floors.length,atlas:[width,height]});
