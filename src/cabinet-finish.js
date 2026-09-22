import * as THREE from 'three';
// One lacquer response across adjoining cabinet panels and curved edge pieces.
// Projected bake charts do not follow those curves continuously; retain a small
// amount of baked contact shade, while the shared PBR lighting defines the finish.
const names=/^(圆弧包覆实体层|壁龛背部|壁龛靠沙发端|洗衣隐藏门板|书架沙发侧60圆角收口|入门柜门套侧圆角收口|南侧书架|南侧整柜书架齐平收口|南侧通高柜2035(?!门后)|通高柜内退踢脚|玄关左侧圆弧包覆|玄关前拱框|玄关层板_700)/;
const entryCabinet=/^入户侧高柜(实体|门板|顶封板)/;
const bedroomCabinet=/^主卧衣柜2630(实体|门板|顶封板)/;
const entryJoinery=new Set(['玄关餐桌连接侧体','玄关后方结构柱','玄关共用背墙']);
const softLivingWood=new Set(['Warm walnut - real oak scan tinted.005','Warm walnut - real oak scan tinted.004'].flatMap(n=>[n,THREE.PropertyBinding.sanitizeNodeName(n)]));
const seen=new WeakSet();
export function prepareCabinetFinish(group){group.traverse(o=>{
 const livingWood=softLivingWood.has(o.name),name=o.userData.source_name||o.name,bedroom=bedroomCabinet.test(name),printedArt=/^(展示画框画芯|画芯线条示意)/.test(name),recessBacking=name==='南侧通高柜2035门后暗缝底';
 if(!o.isMesh||seen.has(o)||(!names.test(name)&&!entryCabinet.test(name)&&!bedroom&&!entryJoinery.has(name)&&!printedArt&&!recessBacking&&!livingWood))return;seen.add(o);
 const multi=Array.isArray(o.material);const materials=(multi?o.material:[o.material]).map(original=>{
  if(!printedArt&&!recessBacking&&original.userData.source_material_id!==(livingWood?370:bedroom?8:38))return original;
  const m=original.clone(),previous=original.onBeforeCompile,key=original.customProgramCacheKey();
  const diningFlat=/^(南侧书架|南侧通高柜2035门板|南侧整柜书架齐平收口)/.test(name);
  m.userData.continuousCabinet=true;
  m.onBeforeCompile=(shader,...args)=>{
   previous.call(m,shader,...args);
   if(recessBacking){
    shader.vertexShader='varying float cabinetBackingHeight;\n'+shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\ncabinetBackingHeight=(modelMatrix*vec4(transformed,1.0)).y;');
    shader.fragmentShader='varying float cabinetBackingHeight;\n'+shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\nfloat cabinetBackingMask=1.0-step(0.08,cabinetBackingHeight);diffuseColor.rgb=mix(diffuseColor.rgb,vec3(0.8713671,0.8631572,0.8307699),cabinetBackingMask);');
   }
   shader.fragmentShader=shader.fragmentShader.replace('#include <aomap_fragment>',`vec3 cabinetContinuousDiffuse=reflectedLight.directDiffuse+reflectedLight.indirectDiffuse;\n#include <aomap_fragment>`)
    .replace('vec3 totalSpecular =',`totalDiffuse=mix(totalDiffuse,mix(cabinetContinuousDiffuse,totalDiffuse,${printedArt?'0.0':livingWood?'0.40':bedroom?'0.25':diningFlat?'0.55':'0.16'}),${recessBacking?'cabinetBackingMask':'1.0'});\nvec3 totalSpecular =`);
  };
  m.customProgramCacheKey=()=>key+'|continuous-cabinet-lacquer-v5'+(livingWood?'|soft-living-oak':'')+(bedroom?'|bedroom-ivory':'')+(diningFlat?'|dining-flat':'')+(printedArt?'|printed-paper':recessBacking?'|ivory-lower-backing':'');return m;
 });o.material=multi?materials:materials[0];
})}
