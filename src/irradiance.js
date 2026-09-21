import * as THREE from 'three';
// Optional Cycles diffuse lightmaps. Geometry/UVs stay unchanged; no runtime bake or shadow pass.
export function createIrradiance(renderer){
 const neutral=new THREE.DataTexture(new Uint8Array([0,0,0,255]),1,1);neutral.needsUpdate=true;
 const maps={wall:{value:neutral},floor:{value:neutral}},weight={value:0},receivers=new Map(),seen=new WeakSet();let manifest,available=false,target=0;
 const base=import.meta.env.BASE_URL+'assets/lighting/';
 async function init(){try{const r=await fetch(base+'irradiance.json',{cache:'no-cache',signal:AbortSignal.timeout(4000)});if(!r.ok)return;manifest=await r.json();for(const kind of ['floor','wall'])for(const receiver of manifest[kind].receivers)receivers.set(receiver.moduleNode,{...receiver,kind})}catch(e){console.warn('Optional traced lighting metadata unavailable',e)}}
 async function load(){if(!manifest)return;try{await Promise.all(['floor','wall'].map(async kind=>{const texture=await new THREE.TextureLoader().loadAsync(base+manifest[kind].file);texture.flipY=false;texture.colorSpace=THREE.NoColorSpace;texture.minFilter=THREE.LinearFilter;texture.magFilter=THREE.LinearFilter;texture.generateMipmaps=false;renderer.initTexture(texture);maps[kind].value=texture}));available=true}catch(e){console.warn('Optional traced lighting unavailable',e)}}
 function prepare(group){group.traverse(o=>{
  if(!o.isMesh||seen.has(o))return;seen.add(o);const r=receivers.get(o.userData.attachTo??o.userData.moduleNode);if(!r)return;
  // Box-projected charts switch abruptly around curved niche fascias. These
  // three shells use continuous PBR lighting; the flat niche lining stays baked.
  if(/^圆弧包覆实体层(?:0|900|1230)$/.test(o.userData.source_name||o.name))return;
  const multi=Array.isArray(o.material);const materials=(multi?o.material:[o.material]).map(original=>{
   const m=original.clone(),previous=original.onBeforeCompile,key=original.customProgramCacheKey();m.userData.tracedLighting=r.kind;
   m.onBeforeCompile=(shader,...args)=>{
    previous.call(m,shader,...args);Object.assign(shader.uniforms,{tracedMap:maps[r.kind],tracedWeight:weight});
    if(r.kind==='wall'){shader.uniforms.tracedMin={value:new THREE.Vector3(...r.min)};shader.uniforms.tracedSize={value:new THREE.Vector3(...r.max).sub(shader.uniforms.tracedMin.value).max(new THREE.Vector3(.000001,.000001,.000001))};shader.uniforms.tracedRects={value:r.rects.map(v=>new THREE.Vector4(...v))}}
    else {const b=manifest.floor.bounds;shader.uniforms.tracedBounds={value:new THREE.Vector4(b[0],b[1],b[2]-b[0],b[3]-b[1])}}
    const varyings='varying vec3 tracedPosition; varying vec3 tracedNormal;\n';
    shader.vertexShader=varyings+shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\ntracedPosition=(modelMatrix*vec4(transformed,1.0)).xyz;tracedNormal=inverseTransformDirection(transformedNormal,viewMatrix);');
    shader.fragmentShader=varyings+'uniform sampler2D tracedMap; uniform float tracedWeight;\n'+(r.kind==='wall'?'uniform vec3 tracedMin;uniform vec3 tracedSize;uniform vec4 tracedRects[6];\n':'uniform vec4 tracedBounds;\n')+shader.fragmentShader;
    const uv=r.kind==='floor'?'vec2 tracedUV=(tracedPosition.xz-tracedBounds.xy)/tracedBounds.zw;':`vec3 tn=normalize(tracedNormal);
#ifdef DOUBLE_SIDED
tn*=faceDirection;
#endif
vec3 ta=abs(tn),tp=clamp((tracedPosition-tracedMin)/tracedSize,0.0,1.0);int tf;vec2 tu;
     if(ta.x>ta.y&&ta.x>ta.z){tf=tn.x>0.0?0:1;tu=tp.zy;}else if(ta.y>ta.z){tf=tn.y>0.0?2:3;tu=tp.xz;}else{tf=tn.z>0.0?4:5;tu=tp.xy;}
     vec4 tr=tracedRects[tf];vec2 tracedUV=tr.xy+tu*tr.zw;`;
    shader.fragmentShader=shader.fragmentShader.replace('vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;',`${uv}
     vec4 tracedSample=texture2D(tracedMap,tracedUV);vec3 tracedIrradiance=exp2(tracedSample.rgb*4.0)-1.0;
     vec3 totalDiffuse=mix(reflectedLight.directDiffuse+reflectedLight.indirectDiffuse,diffuseColor.rgb*(tracedIrradiance*1.65+vec3(0.08)),tracedWeight*tracedSample.a*${r.kind==='wall'?'0.72':'1.0'});`);
   };m.customProgramCacheKey=()=>key+'|cycles-diffuse-v2-'+r.kind;return m;
  });o.material=multi?materials:materials[0];
 })}
 function update(model,initialTransforms,loaded,assetFiles){let unchanged=true;model.traverse(o=>{if(!Object.keys(o.userData).some(k=>k.startsWith('interaction_')))return;const initial=initialTransforms.get(o);if(!initial||initial.visible!==o.visible||o.matrix.elements.some((v,i)=>Math.abs(v-initial.matrix.elements[i])>1e-5))unchanged=false});target=available&&unchanged&&loaded?.length===assetFiles?.length&&JSON.stringify(manifest?.sourceModules)===JSON.stringify(assetFiles)?1:0;if(!target)weight.value=0}
 function tick(dt){weight.value+=(target-weight.value)*(1-Math.exp(-dt*4))}
 return {init,load,prepare,update,tick};
}
