// Reconstruct exact decoded runtime geometry for offline baking; never ship this scratch GLB.
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {copyToDocument,dedup,unpartition} from '@gltf-transform/functions';
import D from 'draco3dgltf';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const input=process.argv[2]||'public/assets/modules',output=process.argv[3];if(!output)throw Error('Supply module directory and output GLB');
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await D.createDecoderModule()});
const manifest=JSON.parse(await fs.readFile(input+'/manifest.json')),doc=await io.read(input+'/'+manifest.modules.base.file),targets=new Map(doc.getRoot().listNodes().map(n=>[n.getExtras().moduleNode,n]));
for(const[key,entry]of Object.entries(manifest.modules))if(key!=='base'){
 const part=await io.read(input+'/'+entry.file),meshes=part.getRoot().listMeshes(),map=copyToDocument(doc,part,meshes);
 for(const n of part.getRoot().listNodes())if(n.getMesh()){const parent=targets.get(n.getExtras().attachTo);assert(parent&&!parent.getMesh());assert.deepEqual(n.getMatrix(),[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);parent.setMesh(map.get(n.getMesh()))}
}
doc.getRoot().listExtensionsUsed().find(e=>e.extensionName==='KHR_draco_mesh_compression')?.dispose();
await doc.transform(dedup(),unpartition());await io.write(output,doc);console.log('Assembled',doc.getRoot().listNodes().filter(n=>n.getMesh()).length,'mesh nodes into',output);
