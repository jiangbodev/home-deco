// One lacquer response across adjoining cabinet panels and curved edge pieces.
// Projected bake charts do not follow those curves continuously; retain a small
// amount of baked contact shade, while the shared PBR lighting defines the finish.
const names=/^(圆弧包覆实体层|壁龛背部|壁龛靠沙发端|洗衣隐藏门板|南侧书架|南侧整柜书架齐平收口|南侧通高柜2035(?!门后)|通高柜内退踢脚|玄关左侧圆弧包覆|玄关前拱框|玄关层板_700)/;
const entryJoinery=new Set(['玄关餐桌连接侧体','玄关后方结构柱','玄关共用背墙']);
const seen=new WeakSet();
export function prepareCabinetFinish(group){group.traverse(o=>{
 const name=o.userData.source_name||o.name,printedArt=/^(展示画框画芯|画芯线条示意)/.test(name),recessBacking=name==='南侧通高柜2035门后暗缝底';
 if(!o.isMesh||seen.has(o)||(!names.test(name)&&!entryJoinery.has(name)&&!printedArt&&!recessBacking))return;seen.add(o);
 const multi=Array.isArray(o.material);const materials=(multi?o.material:[o.material]).map(original=>{
  if(!printedArt&&!recessBacking&&original.userData.source_material_id!==38)return original;
  const m=original.clone(),previous=original.onBeforeCompile,key=original.customProgramCacheKey();
  m.userData.continuousCabinet=true;
  m.onBeforeCompile=(shader,...args)=>{
   previous.call(m,shader,...args);
   if(recessBacking){
    shader.vertexShader='varying float cabinetBackingHeight;\n'+shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\ncabinetBackingHeight=(modelMatrix*vec4(transformed,1.0)).y;');
    shader.fragmentShader='varying float cabinetBackingHeight;\n'+shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\nfloat cabinetBackingMask=1.0-step(0.08,cabinetBackingHeight);diffuseColor.rgb=mix(diffuseColor.rgb,vec3(0.8713671,0.8631572,0.8307699),cabinetBackingMask);');
   }
   shader.fragmentShader=shader.fragmentShader.replace('#include <aomap_fragment>',`vec3 cabinetContinuousDiffuse=reflectedLight.directDiffuse+reflectedLight.indirectDiffuse;\n#include <aomap_fragment>`)
    .replace('vec3 totalSpecular =',`totalDiffuse=mix(totalDiffuse,mix(cabinetContinuousDiffuse,totalDiffuse,${printedArt?'0.0':'0.16'}),${recessBacking?'cabinetBackingMask':'1.0'});\nvec3 totalSpecular =`);
  };
  m.customProgramCacheKey=()=>key+'|continuous-cabinet-lacquer-v1'+(printedArt?'|printed-paper':recessBacking?'|ivory-lower-backing':'');return m;
 });o.material=multi?materials:materials[0];
})}
