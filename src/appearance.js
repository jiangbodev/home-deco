import * as THREE from 'three';
import {createSurfaceFinishes} from './surface-finishes.js';

// Offline-baked contact maps; no shadow render passes while walking.
export function createAppearance(renderer){
 const finishes=createSurfaceFinishes(renderer);
 const white=new THREE.DataTexture(new Uint8Array([0,0,0,255]),1,1);white.needsUpdate=true;
 const contact={value:white},bounds={value:new THREE.Vector4(-.5,-.5,15,10)};
 const fixed={value:0},furniture={value:0};
 const wallContact={value:white},wallStrength={value:0};
 const tuned=new WeakSet(),patched=new WeakSet(),wallReceivers=new Map();let available=false,wallAvailable=false,wallManifest,floorManifest;
 async function init(){
  try{const r=await fetch(import.meta.env.BASE_URL+'assets/lighting/walls.json',{signal:AbortSignal.timeout(4000)});if(!r.ok)throw Error('Wall manifest unavailable');wallManifest=await r.json();for(const receiver of wallManifest.receivers)wallReceivers.set(receiver.name,receiver)}catch(error){console.warn('Optional wall shading unavailable',error)}
 }
 async function load(){
  void finishes.load();
  try{
   const base=import.meta.env.BASE_URL+'assets/lighting/';
   const response=await fetch(base+'contact.json');if(!response.ok)throw Error('Contact manifest unavailable');
   const manifest=await response.json();floorManifest=manifest;
   const texture=await new THREE.TextureLoader().loadAsync(base+manifest.file);
   texture.flipY=false;texture.colorSpace=THREE.NoColorSpace;
   texture.minFilter=THREE.LinearFilter;texture.magFilter=THREE.LinearFilter;texture.generateMipmaps=false;
   renderer.initTexture(texture);contact.value=texture;
   const b=manifest.bounds;bounds.value.set(b[0],b[1],b[2]-b[0],b[3]-b[1]);available=true;
   if(wallManifest){const wall=await new THREE.TextureLoader().loadAsync(base+wallManifest.file);wall.flipY=false;wall.colorSpace=THREE.NoColorSpace;wall.minFilter=THREE.LinearFilter;wall.magFilter=THREE.LinearFilter;wall.generateMipmaps=false;renderer.initTexture(wall);wallContact.value=wall;wallAvailable=true}
  }catch(error){console.warn('Optional contact shading unavailable',error)}
 }
 function prepare(group){
  group.traverse(o=>{
   if(!o.isMesh)return;
   for(const m of Array.isArray(o.material)?o.material:[o.material]){
    if(tuned.has(m))continue;tuned.add(m);
    // Retain authored maps and UV scale; only calibrate their surface response.
    if(!m.map&&!m.transparent&&m.metalness<.05&&m.roughness>.45&&Math.min(m.color.r,m.color.g,m.color.b)>.55)m.color.multiplyScalar(.86);
    if(m.name.startsWith('Warm walnut - real oak scan tinted')){
     m.roughness=.9;if(m.normalMap)m.normalScale.multiplyScalar(1.5);
    }
    if([190,191,192,193,194,195].includes(m.userData.source_material_id)&&m.normalMap)m.normalScale.multiplyScalar(1.35);
   }
   let meta={};try{meta=JSON.parse(o.userData.metadata||'{}')}catch{}
   // Deferred nodes retain source metadata on their original parent.
   if(!meta.id&&o.parent)try{meta=JSON.parse(o.parent.userData.metadata||'{}')}catch{}
   const floor=/^F0[1-9]$/.test(meta.id||'')||/玄关六角砖/.test(o.name);
   const receiver=wallReceivers.get(o.userData.source_name||o.name)||wallReceivers.get(o.parent?.userData.source_name);
   if(!floor&&!receiver)return;
   const multiple=Array.isArray(o.material);
   const materials=multiple?o.material:[o.material];
   o.material=materials.map(original=>{
    if(patched.has(original))return original;
    const m=original.clone();patched.add(m);
    if(receiver&&!floor){
     m.onBeforeCompile=shader=>{
      Object.assign(shader.uniforms,{wallContact,wallStrength,wallMin:{value:new THREE.Vector3().fromArray(receiver.min)},wallSize:{value:new THREE.Vector3().fromArray(receiver.max).sub(new THREE.Vector3().fromArray(receiver.min))},wallRects:{value:receiver.rects.map(r=>new THREE.Vector4().fromArray(r))}});
      shader.vertexShader='varying vec3 contactPosition;\nvarying vec3 contactNormal;\n'+shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\ncontactPosition=(modelMatrix*vec4(transformed,1.0)).xyz;contactNormal=inverseTransformDirection(transformedNormal,viewMatrix);');
      shader.fragmentShader='varying vec3 contactPosition;\nvarying vec3 contactNormal;\nuniform sampler2D wallContact;\nuniform float wallStrength;\nuniform vec3 wallMin;\nuniform vec3 wallSize;\nuniform vec4 wallRects[6];\n'+shader.fragmentShader.replace('#include <aomap_fragment>',`#include <aomap_fragment>
       vec3 wn=normalize(contactNormal),an=abs(wn),wp=clamp((contactPosition-wallMin)/wallSize,0.0,1.0);
       int face;vec2 faceUV;
       if(an.x>an.y&&an.x>an.z){face=wn.x>0.0?0:1;faceUV=wp.zy;}
       else if(an.y>an.z){face=wn.y>0.0?2:3;faceUV=wp.xz;}
       else{face=wn.z>0.0?4:5;faceUV=wp.xy;}
       vec4 rect=wallRects[face];float shade=1.0-texture2D(wallContact,rect.xy+faceUV*rect.zw).r*wallStrength;
       reflectedLight.indirectDiffuse*=shade;reflectedLight.directDiffuse*=shade;
      `);
     };m.customProgramCacheKey=()=> 'wall-contact-v1';return m;
    }
    m.onBeforeCompile=shader=>{
     Object.assign(shader.uniforms,{floorContact:contact,contactBounds:bounds,contactFixed:fixed,contactFurniture:furniture});
     shader.vertexShader='varying vec3 contactPosition;\n'+shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\ncontactPosition = (modelMatrix * vec4(transformed, 1.0)).xyz;');
     shader.fragmentShader='varying vec3 contactPosition;\nuniform sampler2D floorContact;\nuniform vec4 contactBounds;\nuniform float contactFixed;\nuniform float contactFurniture;\n'+shader.fragmentShader.replace('#include <aomap_fragment>',`#include <aomap_fragment>
      vec2 contactUV=(contactPosition.xz-contactBounds.xy)/contactBounds.zw;
      vec2 contactAO=texture2D(floorContact,contactUV).rg;
      float contactInside=step(0.0,contactUV.x)*step(contactUV.x,1.0)*step(0.0,contactUV.y)*step(contactUV.y,1.0);
      float contactShade=1.0-contactInside*clamp(contactAO.r*contactFixed+contactAO.g*contactFurniture,0.0,0.65);
      reflectedLight.indirectDiffuse*=contactShade;
      reflectedLight.directDiffuse*=contactShade;
     `);
    };
    m.customProgramCacheKey=()=> 'floor-contact-v1';return m;
   });if(!multiple)o.material=o.material[0];
  });
  finishes.prepare(group);
 }
 function update(model,initialTransforms,loaded,assetFiles){
  const matches=manifest=>JSON.stringify(manifest?.sourceModules)===JSON.stringify(assetFiles);
  fixed.value=available&&matches(floorManifest)&&loaded?.length===assetFiles?.length ? .55 : 0;
  wallStrength.value=wallAvailable&&matches(wallManifest)&&loaded?.length===assetFiles?.length ? .48 : 0;
  let unchanged=true;
  model.traverse(o=>{
   if(!['interaction_furniture','interaction_piano','interaction_dining-stored'].some(k=>k in o.userData))return;
   const initial=initialTransforms.get(o);
   if(!initial||o.visible!==initial.visible||o.matrix.elements.some((v,i)=>Math.abs(v-initial.matrix.elements[i])>1e-5))unchanged=false;
  });furniture.value=unchanged?fixed.value:0;
 }
 return {init,load,prepare,update};
}
