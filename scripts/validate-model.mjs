import{NodeIO}from'@gltf-transform/core';
import{ALL_EXTENSIONS}from'@gltf-transform/extensions';
import{getBounds}from'@gltf-transform/functions';
import draco from'draco3dgltf';
import validator from'gltf-validator';
import{readFile,writeFile}from'node:fs/promises';
import{createHash}from'node:crypto';
const input=process.argv[2];if(!input)throw Error('Pass the original GLB path');
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await draco.createDecoderModule()});
const src=await io.read(input),dst=await io.read('public/assets/home.glb');
const original=new Map(src.getRoot().listNodes().map(n=>[n.getName(),n]));
let maxTransformError=0,maxBoundsError=0,trianglesBefore=0,trianglesAfter=0,metadataMismatches=[];
for(const n of dst.getRoot().listNodes()){
 const old=original.get(n.getName());if(!old)throw Error('Unexpected node '+n.getName());
 for(const[key,value]of Object.entries(old.getExtras()))if(JSON.stringify(value)!==JSON.stringify(n.getExtras()[key]))metadataMismatches.push(n.getName()+':'+key);
 const a=old.getWorldMatrix(),b=n.getWorldMatrix();maxTransformError=Math.max(maxTransformError,...a.map((v,i)=>Math.abs(v-b[i])));
 if(n.getMesh()){
  const x=getBounds(old),y=getBounds(n);for(const key of ['min','max'])maxBoundsError=Math.max(maxBoundsError,...x[key].map((v,i)=>Math.abs(v-y[key][i])));
  for(const p of old.getMesh().listPrimitives())trianglesBefore+=(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3;
  for(const p of n.getMesh().listPrimitives())trianglesAfter+=(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3;
 }
}
const data=await readFile('public/assets/home.glb');
const result=await validator.validateBytes(new Uint8Array(data),{maxIssues:10000,ignoredIssues:['UNUSED_OBJECT']});
dst.getRoot().listExtensionsUsed().find(e=>e.extensionName==='KHR_draco_mesh_compression')?.dispose();
const decoded=await io.writeBinary(dst);
const decodedResult=await validator.validateBytes(decoded,{maxIssues:10000,ignoredIssues:['UNUSED_OBJECT']});
const summarize=r=>({errors:r.issues.numErrors,warnings:r.issues.numWarnings,codes:[...new Set(r.issues.messages.map(m=>m.code))],truncated:r.issues.truncated});
const report={bytes:data.length,sha256:createHash('sha256').update(data).digest('hex'),nodesBefore:original.size,nodesAfter:dst.getRoot().listNodes().length,trianglesBefore,trianglesAfter,triangleReductionFraction:(trianglesBefore-trianglesAfter)/trianglesBefore,maxTransformError,maxBoundsErrorMetres:maxBoundsError,metadataMismatches,validator:summarize(result),decodedValidator:summarize(decodedResult),note:'No simplification transform. Draco removes degenerate faces; run check-vertices.py for nonzero surface vertex tolerance.'};
await writeFile('validation-report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
if(process.argv[3])await writeFile(process.argv[3],decoded);
if(data.length>=20000000||maxTransformError>1e-6||maxBoundsError>.001||metadataMismatches.length||result.issues.numErrors||decodedResult.issues.numErrors||(trianglesBefore-trianglesAfter)/trianglesBefore>.003)process.exitCode=1;
