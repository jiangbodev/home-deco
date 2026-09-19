import * as THREE from 'three';
// Explicit source material IDs: exclude stone, fabric, books, glass and fixtures.
const plaster=new Set([2,3,4]);
const lacquer=new Set([8,24,37,38,54,56,62,64,67,85,87]);
export function createSurfaceFinishes(renderer){
 const neutral=new THREE.DataTexture(new Uint8Array([128,128,128,255]),1,1);neutral.needsUpdate=true;
 const grain={value:neutral},seen=new WeakSet();
 async function load(){try{
  const t=await new THREE.TextureLoader().loadAsync(import.meta.env.BASE_URL+'assets/surfaces/paint-grain-v1.png');
  t.colorSpace=THREE.NoColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;
  t.anisotropy=Math.min(4,renderer.capabilities.getMaxAnisotropy());renderer.initTexture(t);grain.value=t;
 }catch(e){console.warn('Optional finish texture unavailable',e)}}
 function prepare(group){group.traverse(o=>{if(!o.isMesh)return;
  for(const m of Array.isArray(o.material)?o.material:[o.material]){
   const id=m.userData.source_material_id,wall=plaster.has(id);
   if((!wall&&!lacquer.has(id))||seen.has(m))continue;seen.add(m);
   // Linear reflectance: warm white plaster and slightly deeper ivory cabinetry.
   m.color.setRGB(...(wall?[.62,.60,.56]:[.64,.605,.535]));
   m.roughness=wall?.9:.43;
   // Existing lacquer normal maps remain; grain adds fine-scale relief only.
   const previous=m.onBeforeCompile,previousKey=m.customProgramCacheKey();
   m.onBeforeCompile=(shader,...args)=>{
    previous.call(m,shader,...args);
    shader.uniforms.finishGrain=grain;
    shader.vertexShader='varying vec3 finishPosition;\nvarying vec3 finishNormal;\n'+shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nfinishPosition=(modelMatrix*vec4(transformed,1.0)).xyz;finishNormal=inverseTransformDirection(transformedNormal,viewMatrix);');
    shader.fragmentShader='varying vec3 finishPosition;\nvarying vec3 finishNormal;\nuniform sampler2D finishGrain;\n'+shader.fragmentShader
     .replace('#include <color_fragment>',`#include <color_fragment>
      vec3 fn=abs(normalize(finishNormal));
      vec2 finishUV=fn.x>fn.y&&fn.x>fn.z?finishPosition.zy:(fn.y>fn.z?finishPosition.xz:finishPosition.xy);
      vec3 finishData=texture2D(finishGrain,finishUV*4.0).rgb;
      diffuseColor.rgb*=1.0+(finishData.r-.5)*${wall?'.055':'.025'};
     `)
     .replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>
      roughnessFactor=clamp(roughnessFactor+(finishData.b-.5)*${wall?'.16':'.2'},.28,1.0);
     `)
     .replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
      // Screen derivatives plus mip filtering fade subpixel pores without shimmer.
      vec3 sx=dFdx(-vViewPosition),sy=dFdy(-vViewPosition);
      vec3 rx=cross(sy,normal),ry=cross(normal,sx);
      float det=dot(sx,rx)*faceDirection;
      float height=finishData.g*${wall?'.00032':'.00012'};
      vec3 grad=sign(det)*(dFdx(height)*rx+dFdy(height)*ry);
      normal=normalize(max(abs(det),1e-10)*normal-grad);
     `);
   };
   m.customProgramCacheKey=()=>previousKey+(wall?'|plaster-v1':'|lacquer-v1');
  }
 })}
 return {load,prepare};
}
