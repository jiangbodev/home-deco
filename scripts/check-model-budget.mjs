import fs from 'node:fs';import path from 'node:path';
const root=process.argv[2]||'dist/assets/modules';const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));const files=new Set(['manifest.json',...Object.values(manifest.modules).map(m=>m.file),...Object.keys(manifest.textures)]);let bytes=0;
for(const file of files){if(path.basename(file)!==file)throw Error('Invalid asset path');const size=fs.statSync(path.join(root,file)).size;bytes+=size;const expected=manifest.textures[file]??Object.values(manifest.modules).find(m=>m.file===file)?.bytes;if(expected!==undefined&&size!==expected)throw Error('Asset size mismatch: '+file)}
for(const m of Object.values(manifest.modules))for(const texture of m.textures)if(!files.has(texture))throw Error('Missing shared texture');
if(!manifest.modules.base||bytes>=20_000_000)throw Error('Model budget exceeded or base missing');console.log(`${files.size} model resources: ${bytes} bytes / 20000000`);
