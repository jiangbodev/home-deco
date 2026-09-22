import * as THREE from 'three';
// Explicit source materials; do not infer finishes from brightness or object names.
const plaster=new Set([2,3,4]);
const lacquer=new Set([8,24,37,38,54,56,62,64,67,85,87]);
const timber=new Set([9,15,17,25,32,35,41,45,50,52,65,69,72,75]);
const livingWood=new Set(['Warm walnut - real oak scan tinted.005','Warm walnut - real oak scan tinted.004'].flatMap(n=>[n,THREE.PropertyBinding.sanitizeNodeName(n)]));
const profiles={
 rug:{rough:.98,amplitude:'.00032',colorNoise:'.085',roughNoise:'.04',uv:'vec2(3.0)',edge:0},
 cloth:{rough:.91,amplitude:'.00009',colorNoise:'.055',roughNoise:'.035',uv:'vec2(110.0)',edge:0},
 paper:{rough:.94,amplitude:'.000012',colorNoise:'.025',roughNoise:'.025',uv:'vec2(70.0)',edge:0},
 plaster:{rough:.92,amplitude:'.00016',colorNoise:'.025',roughNoise:'.16',uv:'vec2(4.0)',edge:0},
 lacquer:{rough:.32,amplitude:'.000025',colorNoise:'.008',roughNoise:'.045',uv:'vec2(4.0)',edge:.0012},
 timber:{rough:.78,amplitude:'.00005',colorNoise:'.015',roughNoise:'.12',uv:'vec2(4.0)',edge:.0018},
 counter:{rough:.32,amplitude:'.000035',colorNoise:'.085',roughNoise:'.16',uv:'vec2(12.0)',edge:.0015},
 steel:{rough:.29,amplitude:'.000004',colorNoise:'.012',roughNoise:'.17',uv:'vec2(2.0,80.0)',edge:0},
};
// Only shade easing on sharp, axis-aligned box parts. Curves retain authored normals.
function boxEasing(geometry){
 const p=geometry.attributes.position,n=geometry.attributes.normal;
 if(!p||!n||p.count>80)return false;
 for(let i=0;i<n.count;i++)if(Math.max(Math.abs(n.getX(i)),Math.abs(n.getY(i)),Math.abs(n.getZ(i)))<.999)return false;
 if(!geometry.boundingBox)geometry.computeBoundingBox();
 return Math.min(...geometry.boundingBox.getSize(new THREE.Vector3()).toArray())>.006;
}
export function createSurfaceFinishes(renderer){
 const neutral=new THREE.DataTexture(new Uint8Array([128,128,128,255]),1,1);neutral.needsUpdate=true;
 const grain={value:neutral},seen=new WeakSet();
 async function load(){try{
  const t=await new THREE.TextureLoader().loadAsync(import.meta.env.BASE_URL+'assets/surfaces/paint-grain-v1.png');
  t.colorSpace=THREE.NoColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;
  t.anisotropy=Math.min(4,renderer.capabilities.getMaxAnisotropy());renderer.initTexture(t);grain.value=t;
 }catch(e){console.warn('Optional finish texture unavailable',e)}}
 function prepare(group){group.traverse(o=>{
  if(!o.isMesh||seen.has(o))return;seen.add(o);
  const multiple=Array.isArray(o.material),materials=multiple?o.material:[o.material];
  const result=materials.map(original=>{
   const id=original.userData.source_material_id;
   const bookPaper=id===121||(id===307&&/搁板薄书|玄关书籍/.test(o.userData.source_name||o.name));
   const bookCloth=/^Cloth cover|^搁板薄书|^玄关书籍/.test(o.userData.source_name||o.name)&&!bookPaper;
   const kind=bookPaper?'paper':(id===321||id===100||bookCloth)?'cloth':plaster.has(id)?'plaster':lacquer.has(id)?'lacquer':(timber.has(id)||id===320||id===370)?'timber':id===51?'rug':id===19?'counter':[80,360,361].includes(id)?'steel':null;
   if(!kind)return original;
   const softenLivingWood=id===370&&livingWood.has(o.name);
   const profile=[360,361].includes(id)?{...profiles.steel,rough:id===360?.255:.20,roughNoise:'.08',amplitude:'.0000015',uv:'vec2(220.0,3.0)'}:softenLivingWood?{...profiles.timber,rough:.72,roughNoise:'.05'}:[25,32,35,41,45,320,370].includes(id)?{...profiles.timber,rough:[25,32,35,320,370].includes(id)?.48:.55}:profiles[kind],edge=profile.edge&&boxEasing(o.geometry)?profile.edge:0;
   // Keep each receiver's existing baked-light callback; Material.clone does not copy it.
   const m=original.clone(),previous=original.onBeforeCompile,previousKey=original.customProgramCacheKey();
   m.userData.surfaceFinish=kind;m.userData.edgeEasing=edge;
   if(kind==='plaster')m.color.setRGB(.68,.66,.63);
   // Preserve authored warm ivory cabinet color; avoid flattening it to wall-like grey.
   if(kind==='counter')m.color.setRGB(.72,.71,.66);
   // TV console only: deepen the washed-out oak without darkening other cabinetry.
   if(id===370&&o.name===THREE.PropertyBinding.sanitizeNodeName('Warm walnut - real oak scan tinted.005'))m.color.multiply(new THREE.Color().setRGB(.50,.43,.35));
   if(kind==='steel')m.metalness=.96;
   if(kind==='rug'&&m.normalMap)m.normalScale.multiplyScalar(.45);
   if(kind==='timber'&&m.normalMap)m.normalScale.multiplyScalar(.35);
   if(kind==='lacquer'&&m.normalMap)m.normalScale.multiplyScalar(.12);
   m.roughness=profile.rough;
   m.onBeforeCompile=(shader,...args)=>{
    previous.call(m,shader,...args);shader.uniforms.finishGrain=grain;
    const declarations='varying vec3 finishPosition;\nvarying vec3 finishNormal;\n'+(kind==='paper'?'varying float pageStack;\n':'')+(edge?'varying vec3 finishLocal;\nvarying vec3 finishScale;\n':'');
    if(edge){shader.uniforms.finishMin={value:o.geometry.boundingBox.min};shader.uniforms.finishMax={value:o.geometry.boundingBox.max}}
    shader.vertexShader=declarations+shader.vertexShader.replace('#include <worldpos_vertex>',`#include <worldpos_vertex>
     finishPosition=(modelMatrix*vec4(transformed,1.0)).xyz;finishNormal=inverseTransformDirection(transformedNormal,viewMatrix);
     ${kind==='paper'?`pageStack=${id===121?'uv.x':'finishPosition.y'};`:''}
     ${edge?'finishLocal=transformed;finishScale=vec3(length(modelMatrix[0].xyz),length(modelMatrix[1].xyz),length(modelMatrix[2].xyz));':''}
    `);
    shader.fragmentShader=declarations+'uniform sampler2D finishGrain;\n'+(edge?'uniform vec3 finishMin;\nuniform vec3 finishMax;\n':'')+shader.fragmentShader
     .replace('#include <color_fragment>',`#include <color_fragment>
      vec3 fn=abs(normalize(finishNormal));
      vec2 finishUV=fn.x>fn.y&&fn.x>fn.z?finishPosition.zy:(fn.y>fn.z?finishPosition.xz:finishPosition.xy);
      vec3 finishData=texture2D(finishGrain,finishUV*${profile.uv}).rgb;
      diffuseColor.rgb*=1.0+(finishData.${kind==='counter'?'g':'r'}-.5)*${profile.colorNoise};
      ${softenLivingWood?'float cabinetWoodLuma=dot(diffuseColor.rgb,vec3(.2126,.7152,.0722));diffuseColor.rgb=mix(vec3(cabinetWoodLuma),diffuseColor.rgb,.68)*1.12+vec3(.032,.029,.022);':''}
      ${kind==='rug'?`vec2 yarnUV=finishPosition.xz*240.0;
       vec2 yarnCell=fract(yarnUV),yarnIndex=floor(yarnUV);
       float seed=fract(sin(dot(yarnIndex,vec2(127.1,311.7)))*43758.5453);
       float yarnAA=1.0-smoothstep(.28,.85,max(fwidth(yarnUV.x),fwidth(yarnUV.y)));
       float tuft=sin(yarnCell.x*3.14159265)*sin(yarnCell.y*3.14159265);
       float yarnRelief=(tuft-.40)*yarnAA*(.65+seed*.35);
       float nap=texture2D(finishGrain,finishPosition.xz*vec2(.55,3.4)).r-.5;
       diffuseColor.rgb*=vec3(.98,.955,.885)*(1.0+yarnRelief*.23+nap*.09);`:''}
      ${kind==='paper'?`float pageCoord=pageStack*1400.0;
       float pageAA=1.0-smoothstep(.3,.9,fwidth(pageCoord));
       float pageLine=pow(.5+.5*cos(pageCoord*6.2831853),10.0)*pageAA;
       diffuseColor.rgb*=1.0-pageLine*.17;`:''}
      ${kind==='timber'?'float woodTone=dot(diffuseColor.rgb,vec3(.2126,.7152,.0722));diffuseColor.rgb=mix(vec3(woodTone),diffuseColor.rgb,.9);':''}
     `)
     .replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>
      roughnessFactor=clamp(roughnessFactor+(finishData.b-.5)*${profile.roughNoise},.2,1.0);
      ${kind==='timber'&&m.map?'roughnessFactor=clamp(roughnessFactor+(dot(sampledDiffuseColor.rgb,vec3(.2126,.7152,.0722))-.3)*.1,'+([320,370].includes(id)?'.36':[25,32,35,41,45].includes(id)?'.42':'.52')+',.9);':''}
     `)
     .replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
      vec3 sx=dFdx(-vViewPosition),sy=dFdy(-vViewPosition);
      vec3 rx=cross(sy,normal),ry=cross(normal,sx);
      float det=dot(sx,rx)*faceDirection;
      float height=finishData.g*${profile.amplitude};
      ${kind==='rug'?'height+=yarnRelief*.00065;':''}
      ${edge?`vec3 edgeDistances=max(vec3(0.0),min(finishLocal-finishMin,finishMax-finishLocal)*finishScale);
       float clearance=max(min(edgeDistances.x,edgeDistances.y),min(max(edgeDistances.x,edgeDistances.y),edgeDistances.z));
       height+=${edge.toFixed(4)}*.35*smoothstep(0.0,${edge.toFixed(4)},clearance);`:''}
      vec3 grad=sign(det)*(dFdx(height)*rx+dFdy(height)*ry);
      normal=normalize(max(abs(det),1e-10)*normal-grad);
     `);
   };
   m.customProgramCacheKey=()=>previousKey+'|finish-v9-'+kind+(softenLivingWood?'-living-soft-oak':'')+([25,32,35,41,45,320,370].includes(id)?'-satin-'+id:'')+([360,361].includes(id)?'-appliance-'+id:'')+(edge?'-edge':'');return m;
  });o.material=multiple?result:result[0];
 })}
 return {load,prepare};
}
