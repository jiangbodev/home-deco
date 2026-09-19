import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS, KHRMaterialsUnlit} from '@gltf-transform/extensions';
import {dedup, draco, textureCompress, weld} from '@gltf-transform/functions';
import draco3d from 'draco3dgltf';
import sharp from 'sharp';
import {mkdir,stat,writeFile} from 'node:fs/promises';
const input=process.argv[2];
if(!input) throw new Error('Usage: npm run optimize -- /path/to/original.glb');
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.encoder':await draco3d.createEncoderModule(),'draco3d.decoder':await draco3d.createDecoderModule()});
const doc=await io.read(input);
const before={nodes:doc.getRoot().listNodes().length,meshes:doc.getRoot().listMeshes().length,images:doc.getRoot().listTextures().length,bytes:(await stat(input)).size};
// The source exporter placed RGBA contact shadows in emissiveTexture, losing alpha.
// Correct the GLB material itself, rather than rebuilding shadows in frontend JS.
const unlit=doc.createExtension(KHRMaterialsUnlit);
let shadowMaterialsFixed=0;
for(const node of doc.getRoot().listNodes()) if(node.getName().startsWith('Blender实际网格接触阴影_')) {
  for(const prim of node.getMesh()?.listPrimitives()??[]) {
    const mat=prim.getMaterial(), tex=mat?.getEmissiveTexture();
    if(!tex)continue;
    mat.setBaseColorTexture(tex).setBaseColorFactor([1,1,1,1]).setAlphaMode('BLEND').setEmissiveTexture(null).setEmissiveFactor([0,0,0]).setExtension('KHR_materials_unlit',unlit.createUnlit());
    shadowMaterialsFixed++;
  }
}
// No simplification, joining, flattening or pruning: keep authored nodes and states.
await doc.transform(weld(),dedup(),textureCompress({encoder:sharp,targetFormat:'webp',resize:[1024,1024],slots:/baseColorTexture|emissiveTexture/,quality:88}),textureCompress({encoder:sharp,targetFormat:'webp',resize:[384,384],slots:/normalTexture/,lossless:true}),textureCompress({encoder:sharp,targetFormat:'webp',resize:[512,512],slots:/occlusionTexture|metallicRoughnessTexture/,quality:88}),draco({quantizePosition:14,quantizeNormal:10,quantizeTexcoord:12,encodeSpeed:0,decodeSpeed:0}));
await mkdir('public/assets',{recursive:true});
await io.write('public/assets/home.glb',doc);
const bytes=(await stat('public/assets/home.glb')).size;
const report={before,after:{nodes:doc.getRoot().listNodes().length,meshes:doc.getRoot().listMeshes().length,images:doc.getRoot().listTextures().length,bytes},below20MB:bytes<20000000,geometrySimplified:false,shadowMaterialsFixed};
await writeFile('compression-report.json',JSON.stringify(report,null,2)+'\n');
console.log(report);
if(bytes>=20000000)process.exitCode=1;
