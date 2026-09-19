import fs from 'node:fs';import path from 'node:path';
const root=process.argv[2]||'dist/assets/modules';const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));const files=new Set(['manifest.json',...Object.values(manifest.modules).map(m=>m.file),...Object.keys(manifest.textures)]);let bytes=0;
for(const file of files){if(path.basename(file)!==file)throw Error('Invalid asset path');const size=fs.statSync(path.join(root,file)).size;bytes+=size;const expected=manifest.textures[file]??Object.values(manifest.modules).find(m=>m.file===file)?.bytes;if(expected!==undefined&&size!==expected)throw Error('Asset size mismatch: '+file)}
for(const m of Object.values(manifest.modules))for(const texture of m.textures)if(!files.has(texture))throw Error('Missing shared texture');
if(!manifest.modules.base||bytes>=20_000_000)throw Error('Model budget exceeded or base missing');console.log(`${files.size} model resources: ${bytes} bytes / 20000000`);
const lighting=path.resolve(root,'../lighting');
if(fs.existsSync(lighting)){
 const files=new Set(),sources=Object.values(manifest.modules).map(m=>m.file).sort();
 for(const name of ['contact.json','walls.json']){
  const m=JSON.parse(fs.readFileSync(path.join(lighting,name)));
  if(JSON.stringify(m.sourceModules)!==JSON.stringify(sources))throw Error('Rebake lighting after model updates');
  if(path.basename(m.file)!==m.file||fs.statSync(path.join(lighting,m.file)).size!==m.bytes)throw Error('Lighting asset mismatch');
  files.add(name);files.add(m.file);
 }
 for(const file of files)bytes+=fs.statSync(path.join(lighting,file)).size;
 if(bytes>=20_000_000)throw Error('Model and lighting budget exceeded');
 console.log(`Including baked contact lighting: ${bytes} bytes / 20000000`);
}

const grain=path.resolve(root,'../surfaces/paint-grain-v1.png');
if(fs.existsSync(grain)){bytes+=fs.statSync(grain).size;if(bytes>=20_000_000)throw Error('Surface textures exceed total budget');console.log(`Including surface finishes: ${bytes} bytes / 20000000`)}
