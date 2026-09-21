# Blender editable scene

`home-deco-bedding.blend` is a local editable reconstruction from the runtime modules at commit `8fcd1e1`, not the original author's missing Blender file. It includes packed imported textures and six non-destructive bedding Decimate modifiers. The rest of the imported house remains intact. Original Blender construction history and the web application's custom lighting shaders cannot be recovered from a GLB.

Blender 4.5.14 LTS was used. Binary `.blend` files remain ignored by the repository's existing policy.

To reconstruct from the original module directory:

```sh
node scripts/assemble-modules.mjs /path/to/original/modules qa/original-source.glb
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/blender-simplify-bedding.py -- qa/original-source.glb source/home-deco-bedding.blend qa/blender-bedding.glb review/blender-bedding.json
node scripts/import-blender-bedding.mjs /path/to/original/modules public/assets/modules qa/blender-bedding.glb
node scripts/assemble-modules.mjs public/assets/modules qa/optimized-source.glb
node scripts/bake-floor-contact.mjs qa/optimized-source.glb
node scripts/bake-room-lighting.mjs qa/optimized-source.glb
node scripts/bake-object-contact.mjs qa/optimized-source.glb
node scripts/verify-modules.mjs qa/optimized-source.glb
npm run build
node scripts/check-model-budget.mjs
```

Import only the six edited meshes back into their existing modules. Keep the original material/texture references and attachment indices. Rebuild from original inputs, never repeatedly decimate the simplified outputs.
