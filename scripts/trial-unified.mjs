// Offline GLB candidate only. This does not add geometry generation to the frontend.
import {NodeIO,PropertyType} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {compactPrimitive,dedup,draco,weld,prune} from '@gltf-transform/functions';
import {MeshoptSimplifier as S} from 'meshoptimizer';
import D from 'draco3dgltf';
import {mkdir,writeFile,stat} from 'node:fs/promises';
await S.ready;
const input=process.argv[2]||'public/assets/home.glb';
const out=process.argv[3]||'qa/unified-trial';await mkdir(out,{recursive:true});
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await D.createDecoderModule(),'draco3d.encoder':await D.createEncoderModule()});
const doc=await io.read(input);doc.getRoot().listExtensionsUsed().find(e=>e.extensionName==='KHR_draco_mesh_compression')?.dispose();
const protectedKinds=new Set(['wall','column','solid','opening-infill','glass','fixed-window','sliding-window','sill','wood-sill','door','sliding-door','folding-door','sliding-track','cove','hvac','casework-return','window-junction','finish']);
const meta=n=>{try{return JSON.parse(n.getExtras().metadata||'{}')}catch{return {}}};
const usage=new Map();for(const n of doc.getRoot().listNodes())if(n.getMesh()){let refs=usage.get(n.getMesh());if(!refs)usage.set(n.getMesh(),refs=[]);refs.push(n)}
const count=m=>m.listPrimitives().reduce((s,p)=>s+(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3,0);
const stats=[],before=doc.getRoot().listNodes().reduce((s,n)=>s+(n.getMesh()?count(n.getMesh()):0),0);
await doc.transform(weld());
for(const [mesh,nodes]of usage){
 const names=nodes.map(n=>n.getName()).join('|'),n0=nodes[0],t0=count(mesh);
 const protectedMesh=nodes.some(n=>protectedKinds.has(meta(n).kind)||/墙|顶面|地板|地砖|地面|六角砖|门扇|窗框|接触阴影/.test(n.getName()));
 let group='furniture',ratio=.35,errorMetres=.002;
 if(protectedMesh||t0<500){group='protected';ratio=1}
 else if(/树木_|窗外/.test(names)){group='exterior-tree';ratio=.10;errorMetres=.010}
 else if(/cane|藤|woven/i.test(names)){group='cane';ratio=.40;errorMetres=.001}
 else if(/fabric|fur_|pillow|cushion|布|被子|毯|窗帘/i.test(names)){group='textile';ratio=.18;errorMetres=.0025}
 let maxError=0;
 if(ratio<1)for(const p of mesh.listPrimitives()){
   if(p.getMode()!==4||!p.getIndices())continue;
   const pos=p.getAttribute('POSITION'),N=pos.getCount(),positions=pos.getArray();
   const indices=new Uint32Array(p.getIndices().getArray());
   const fields=['NORMAL','TEXCOORD_0','COLOR_0'].map(k=>[k,p.getAttribute(k)]).filter(([,a])=>a);
   const stride=fields.reduce((s,[,a])=>s+a.getElementSize(),0),attrs=new Float32Array(N*stride),weights=[];
   let offset=0;for(const[k,a]of fields){const ar=a.getArray(),sz=a.getElementSize();for(let i=0;i<N;i++)for(let j=0;j<sz;j++)attrs[i*stride+offset+j]=ar[i*sz+j];for(let j=0;j<sz;j++)weights.push(k==='NORMAL'?.05:k==='TEXCOORD_0'?.1:.1);offset+=sz}
   const wm=n0.getWorldMatrix(),worldScale=Math.max(Math.hypot(...wm.slice(0,3)),Math.hypot(...wm.slice(4,7)),Math.hypot(...wm.slice(8,11)));
   const scale=S.getScale(positions,3),relativeError=errorMetres/(worldScale*scale||1);
   const target=Math.max(120,Math.floor(indices.length*ratio/3)*3);
   const [reduced,error]=S.simplifyWithAttributes(indices,positions,3,attrs,stride,weights,null,target,relativeError,['Permissive']);
   if(reduced.length===0)throw Error('Empty mesh '+names);
   p.setIndices(doc.createAccessor().setType('SCALAR').setArray(reduced).setBuffer(pos.getBuffer()));compactPrimitive(p);maxError=Math.max(maxError,error*scale*worldScale);
 }
 stats.push({names:nodes.map(n=>n.getName()),uses:nodes.length,group,before:t0,after:count(mesh),maxAlgorithmErrorMetres:maxError});
}
// Discard orphan vertex/index streams created by simplification, never scene nodes.
await doc.transform(dedup(),prune({propertyTypes:[PropertyType.ACCESSOR]}));
const after=doc.getRoot().listNodes().reduce((s,n)=>s+(n.getMesh()?count(n.getMesh()):0),0);
await doc.transform(draco({quantizePosition:16,quantizeNormal:10,quantizeTexcoord:12,encodeSpeed:0,decodeSpeed:0}));
await io.write(out+'/home-unified-candidate.glb',doc);
const report={input,output:out+'/home-unified-candidate.glb',status:'candidate-not-visually-approved',method:'Offline attribute-aware meshoptimizer; no Blender baking performed',before,after,bytes:(await stat(out+'/home-unified-candidate.glb')).size,nodes:doc.getRoot().listNodes().length,stats};
await writeFile(out+'/trial-report.json',JSON.stringify(report,null,2)+'\n');
console.log({before,after,bytes:report.bytes,nodes:report.nodes,groups:stats.reduce((o,r)=>{o[r.group]??={before:0,after:0};o[r.group].before+=r.before*r.uses;o[r.group].after+=r.after*r.uses;return o},{})});
