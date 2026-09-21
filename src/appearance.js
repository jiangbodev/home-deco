import * as THREE from 'three';
import {RectAreaLightUniformsLib} from 'three/addons/lights/RectAreaLightUniformsLib.js';
import {createObjectContact} from './object-contact.js';
import {createReflections} from './reflections.js';
import {createIrradiance} from './irradiance.js';
import {createSurfaceFinishes} from './surface-finishes.js';

// Offline-baked contact maps; no shadow render passes while walking.
export function createAppearance(renderer){
 const finishes=createSurfaceFinishes(renderer),objectContact=createObjectContact(),irradiance=createIrradiance(renderer),reflections=createReflections(renderer);
 const white=new THREE.DataTexture(new Uint8Array([0,0,0,255]),1,1);white.needsUpdate=true;
 const contact={value:white},bounds={value:new THREE.Vector4(-.5,-.5,15,10)};
 const fixed={value:0},furniture={value:0};
 const wallContact={value:white},wallStrength={value:0},bakedLight={value:0};
 const tuned=new WeakSet(),patched=new WeakSet(),wallReceivers=new Map();let available=false,wallAvailable=false,wallManifest,floorManifest;
 const dayColor={value:new THREE.Color(1,1,.96)},warmColor={value:new THREE.Color(1,.73,.42)},pendants=[];
 let fixtureConfig,bakedTarget=0;
 async function init(){
  const base=import.meta.env.BASE_URL+'assets/lighting/';
  await Promise.allSettled([
   objectContact.init(),irradiance.init(),reflections.init(),
   (async()=>{const r=await fetch(base+'fixtures.json',{cache:'no-cache',signal:AbortSignal.timeout(4000)});if(r.ok)fixtureConfig=await r.json()})(),
   (async()=>{const r=await fetch(base+'walls.json',{cache:'no-cache',signal:AbortSignal.timeout(4000)});if(!r.ok)throw Error('Wall manifest unavailable');wallManifest=await r.json();for(const receiver of wallManifest.receivers)wallReceivers.set(receiver.name,receiver)})()
  ]);
 }
 async function load(){
  void finishes.load();const tracedLoading=Promise.all([irradiance.load(),reflections.load()]);
  try{
   const base=import.meta.env.BASE_URL+'assets/lighting/';
   const response=await fetch(base+'contact.json',{cache:'no-cache'});if(!response.ok)throw Error('Contact manifest unavailable');
   const manifest=await response.json();floorManifest=manifest;
   const texture=await new THREE.TextureLoader().loadAsync(base+manifest.file);
   texture.flipY=false;texture.colorSpace=THREE.NoColorSpace;
   texture.minFilter=THREE.LinearFilter;texture.magFilter=THREE.LinearFilter;texture.generateMipmaps=false;
   renderer.initTexture(texture);contact.value=texture;
   const b=manifest.bounds;bounds.value.set(b[0],b[1],b[2]-b[0],b[3]-b[1]);available=true;
   if(wallManifest){const wall=await new THREE.TextureLoader().loadAsync(base+wallManifest.file);wall.flipY=false;wall.colorSpace=THREE.NoColorSpace;wall.minFilter=THREE.LinearFilter;wall.magFilter=THREE.LinearFilter;wall.generateMipmaps=false;renderer.initTexture(wall);wallContact.value=wall;wallAvailable=true}
  }catch(error){console.warn('Optional contact shading unavailable',error)}
  await tracedLoading;
 }
 function prepare(group){
  group.traverse(o=>{
   if(!o.isMesh)return;
   if(/^(餐桌灯泡|客餐厅轨道射灯透镜)(?:\.?\d+)?$/.test(o.userData.source_name||o.name)&&!Array.isArray(o.material)){
    o.material=o.material.clone();o.material.emissive.set(0xffd3a0);o.material.emissiveIntensity=1.1;
   }
   for(const m of Array.isArray(o.material)?o.material:[o.material]){
    if(tuned.has(m))continue;tuned.add(m);
    // Retain authored maps and UV scale; only calibrate their surface response.
    if(m.name==='室内水波玻璃'){m.roughness=.22;if(m.normalMap)m.normalScale.multiplyScalar(.6)}
    if(![8,24,37,38,54,56,62,64,67,85,87].includes(m.userData.source_material_id)&&!m.map&&!m.transparent&&m.metalness<.05&&m.roughness>.45&&Math.min(m.color.r,m.color.g,m.color.b)>.55)m.color.multiplyScalar(.86);
    if(m.name.startsWith('Warm walnut - real oak scan tinted')){
     m.roughness=.9;if(m.normalMap)m.normalScale.multiplyScalar(.65);
    }
    if([190,191,192,193,194,195].includes(m.userData.source_material_id)&&m.normalMap)m.normalScale.multiplyScalar(.8);
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
      Object.assign(shader.uniforms,{wallContact,wallStrength,bakedLight,dayColor,warmColor,wallMin:{value:new THREE.Vector3().fromArray(receiver.min)},wallSize:{value:new THREE.Vector3().fromArray(receiver.max).sub(new THREE.Vector3().fromArray(receiver.min))},wallRects:{value:receiver.rects.map(r=>new THREE.Vector4().fromArray(r))}});
      shader.vertexShader='varying vec3 contactPosition;\nvarying vec3 contactNormal;\n'+shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\ncontactPosition=(modelMatrix*vec4(transformed,1.0)).xyz;contactNormal=inverseTransformDirection(transformedNormal,viewMatrix);');
      shader.fragmentShader='varying vec3 contactPosition;\nvarying vec3 contactNormal;\nuniform sampler2D wallContact;\nuniform float bakedLight;\nuniform vec3 dayColor;\nuniform vec3 warmColor;\nuniform float wallStrength;\nuniform vec3 wallMin;\nuniform vec3 wallSize;\nuniform vec4 wallRects[6];\n'+shader.fragmentShader.replace('#include <aomap_fragment>',`#include <aomap_fragment>
       vec3 wn=normalize(contactNormal),an=abs(wn),wp=clamp((contactPosition-wallMin)/wallSize,0.0,1.0);
       int face;vec2 faceUV;
       if(an.x>an.y&&an.x>an.z){face=wn.x>0.0?0:1;faceUV=wp.zy;}
       else if(an.y>an.z){face=wn.y>0.0?2:3;faceUV=wp.xz;}
       else{face=wn.z>0.0?4:5;faceUV=wp.xy;}
       vec4 rect=wallRects[face];vec3 baked=texture2D(wallContact,rect.xy+faceUV*rect.zw).rgb;float shade=1.0-baked.r*wallStrength;
       reflectedLight.indirectDiffuse*=shade;reflectedLight.directDiffuse*=shade;
       reflectedLight.indirectDiffuse+=diffuseColor.rgb*(baked.g*dayColor+baked.b*warmColor)*bakedLight;
      `);
     };m.customProgramCacheKey=()=> 'wall-light-v2';return m;
    }
    m.onBeforeCompile=shader=>{
     Object.assign(shader.uniforms,{floorContact:contact,contactBounds:bounds,contactFixed:fixed,contactFurniture:furniture,bakedLight,dayColor,warmColor});
     shader.vertexShader='varying vec3 contactPosition;\n'+shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\ncontactPosition = (modelMatrix * vec4(transformed, 1.0)).xyz;');
     shader.fragmentShader='varying vec3 contactPosition;\nuniform sampler2D floorContact;\nuniform float bakedLight;\nuniform vec3 dayColor;\nuniform vec3 warmColor;\nuniform vec4 contactBounds;\nuniform float contactFixed;\nuniform float contactFurniture;\n'+shader.fragmentShader.replace('#include <aomap_fragment>',`#include <aomap_fragment>
      vec2 contactUV=(contactPosition.xz-contactBounds.xy)/contactBounds.zw;
      vec4 contactData=texture2D(floorContact,contactUV);vec2 contactAO=contactData.rg;
      float contactInside=step(0.0,contactUV.x)*step(contactUV.x,1.0)*step(0.0,contactUV.y)*step(contactUV.y,1.0);
      float contactShade=1.0-contactInside*clamp(contactAO.r*contactFixed+contactAO.g*contactFurniture,0.0,0.65);
      reflectedLight.indirectDiffuse*=contactShade;
      reflectedLight.directDiffuse*=contactShade;
      reflectedLight.indirectDiffuse+=diffuseColor.rgb*(contactData.b*dayColor+max(0.0,(contactData.a*255.0-128.0)/127.0)*warmColor)*bakedLight*contactInside;
     `);
    };
    m.customProgramCacheKey=()=> 'floor-light-v2';return m;
   });if(!multiple)o.material=o.material[0];
  });
  finishes.prepare(group);objectContact.prepare(group);irradiance.prepare(group);reflections.prepare(group);
 }
 function update(model,initialTransforms,loaded,assetFiles){
  irradiance.update(model,initialTransforms,loaded,assetFiles);reflections.update(model,initialTransforms,loaded,assetFiles);
  const matches=manifest=>JSON.stringify(manifest?.sourceModules)===JSON.stringify(assetFiles);
  fixed.value=available&&matches(floorManifest)&&loaded?.length===assetFiles?.length ? .55 : 0;
  wallStrength.value=wallAvailable&&matches(wallManifest)&&loaded?.length===assetFiles?.length ? .48 : 0;
  bakedTarget=fixed.value>0&&wallStrength.value>0&&floorManifest.lightingVersion===1&&wallManifest.lightingVersion===1 ? 1.8 : 0;
  const visible=name=>{let o=model.getObjectByName(THREE.PropertyBinding.sanitizeNodeName(name));if(!o)return false;for(;o;o=o.parent)if(!o.visible)return false;return true};
  pendants.forEach((light,i)=>{light.intensity=visible(i?'餐桌灯泡.001':'餐桌灯泡')?35:0});
  if(fixtureConfig)warmColor.value.fromArray(fixtureConfig.warmColor).multiplyScalar(visible('客餐厅轨道射灯透镜')?1:0);
  let unchanged=true;
  model.traverse(o=>{
   if(!['interaction_furniture','interaction_piano','interaction_dining-stored'].some(k=>k in o.userData))return;
   const initial=initialTransforms.get(o);
   if(!initial||o.visible!==initial.visible||o.matrix.elements.some((v,i)=>Math.abs(v-initial.matrix.elements[i])>1e-5))unchanged=false;
  });furniture.value=unchanged?fixed.value:0;objectContact.update(loaded,assetFiles,unchanged);
 }
 function addFixtures(scene){
  if(!fixtureConfig)return;
  dayColor.value.fromArray(fixtureConfig.dayColor);warmColor.value.fromArray(fixtureConfig.warmColor);
  RectAreaLightUniformsLib.init();
  for(const p of fixtureConfig.pendants){const light=new THREE.RectAreaLight(0xffd4a0,35,.25,.25);light.position.fromArray(p);light.lookAt(p[0],p[1]-1,p[2]);scene.add(light);pendants.push(light)}
 }
 function tick(dt){irradiance.tick(dt);objectContact.tick(dt);bakedLight.value+=(bakedTarget-bakedLight.value)*(1-Math.exp(-dt*6))}
 return {init,load,prepare,update,addFixtures,tick};
}
