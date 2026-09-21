import * as THREE from 'three';
// Optional vertex occlusion; no new render passes or changes to source meshes.
export function createObjectContact(){
 const strength={value:0},entries=new Map(),seen=new WeakSet();let manifest,data,target=0;
 async function init(){try{
  const base=import.meta.env.BASE_URL+'assets/lighting/',signal=AbortSignal.timeout(4000);
  const r=await fetch(base+'objects.json',{cache:'no-cache',signal});if(!r.ok)return;
  const m=await r.json();if(!/^object-contact-[a-f0-9]+\.bin\.gz$/.test(m.file))return;
  const b=await fetch(base+m.file,{signal});if(!b.ok)return;
  const packed=await b.arrayBuffer();let bytes;
  // fetch already decodes hosts serving Content-Encoding: gzip.
  if(packed.byteLength===m.rawBytes&&b.headers.get('content-encoding')?.includes('gzip'))bytes=new Uint8Array(packed);
  else{if(packed.byteLength!==m.bytes||typeof DecompressionStream==='undefined')return;bytes=new Uint8Array(await new Response(new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());}
  if(bytes.length!==m.rawBytes)return;
  for(const e of m.entries){if(e.offset<0||e.count<1||e.offset+e.count>bytes.length)throw Error('Invalid contact data');entries.set(THREE.PropertyBinding.sanitizeNodeName(e.name),e)}manifest=m;data=bytes;
 }catch(e){console.warn('Optional object contact unavailable',e)}}
 function prepare(group){if(!data)return;group.traverse(o=>{
  if(!o.isMesh||seen.has(o))return;seen.add(o);
  const e=entries.get(THREE.PropertyBinding.sanitizeNodeName(o.userData.source_name||o.name)),p=o.geometry.attributes.position;
  if(!e||!p||p.isInterleavedBufferAttribute||p.count!==e.count)return;
  let hash=2166136261;for(const b of new Uint8Array(p.array.buffer,p.array.byteOffset,p.array.byteLength))hash=Math.imul(hash^b,16777619)>>>0;if(hash!==e.hash)return;
  const source=o.geometry,g=new THREE.BufferGeometry();for(const [name,attribute] of Object.entries(source.attributes))g.setAttribute(name,attribute);g.setIndex(source.index);g.groups=source.groups.map(group=>({...group}));g.drawRange={...source.drawRange};g.boundingBox=source.boundingBox;g.boundingSphere=source.boundingSphere;
  g.setAttribute('objectOcclusion',new THREE.Uint8BufferAttribute(data.slice(e.offset,e.offset+e.count),1,true));o.geometry=g;
  const multiple=Array.isArray(o.material),mats=(multiple?o.material:[o.material]).map(original=>{
   if(original.userData.source_material_id===20)return original;
   const m=original.clone(),previous=original.onBeforeCompile,key=original.customProgramCacheKey();m.userData.objectContact=true;
   m.onBeforeCompile=(shader,...args)=>{
    previous.call(m,shader,...args);shader.uniforms.objectContactStrength=strength;
    shader.vertexShader='attribute float objectOcclusion;\nvarying float vObjectOcclusion;\n'+shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvObjectOcclusion=objectOcclusion;');
    shader.fragmentShader='varying float vObjectOcclusion;\nuniform float objectContactStrength;\n'+shader.fragmentShader.replace('#include <aomap_fragment>',`#include <aomap_fragment>
     float objectShade=clamp(vObjectOcclusion*objectContactStrength,0.0,.72);
     reflectedLight.indirectDiffuse*=1.0-objectShade;
     reflectedLight.directDiffuse*=1.0-objectShade*.55;
     reflectedLight.indirectSpecular*=1.0-objectShade*.65;
    `);
   };m.customProgramCacheKey=()=>key+'|object-contact-v1';return m;
  });o.material=multiple?mats:mats[0];
 })}
 function update(loaded,files,unchanged){target=manifest&&JSON.stringify(manifest.sourceModules)===JSON.stringify(files)&&loaded?.length===files?.length&&unchanged ? .9 : 0;if(!target)strength.value=0;}
 function tick(dt){strength.value+=(target-strength.value)*(1-Math.exp(-6*dt))}
 return {init,prepare,update,tick};
}
