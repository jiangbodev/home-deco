import * as THREE from 'three';
import {RGBELoader} from 'three/addons/loaders/RGBELoader.js';
// Two offline Cycles captures: local window reflections without per-frame cube renders.
export function createReflections(renderer){
 const base=import.meta.env.BASE_URL+'assets/lighting/';
 const materials=new Map(),maps=new Map();let manifest,available=false,active=false;
 async function init(){try{const r=await fetch(base+'reflections.json',{cache:'no-cache',signal:AbortSignal.timeout(4000)});if(r.ok)manifest=await r.json()}catch(e){console.warn('Optional reflection metadata unavailable',e)}}
 async function load(){if(!manifest)return;const pmrem=new THREE.PMREMGenerator(renderer);try{
  pmrem.compileEquirectangularShader();
  for(const probe of manifest.probes){const texture=await new RGBELoader().loadAsync(base+probe.file);const target=pmrem.fromEquirectangular(texture);texture.dispose();maps.set(probe.name,target.texture)}
  available=true;
 }catch(e){console.warn('Optional local reflections unavailable',e)}finally{pmrem.dispose()}}
 function prepare(group){group.traverse(o=>{if(!o.isMesh)return;const probe=manifest?.receivers[o.userData.attachTo??o.userData.moduleNode];if(!probe)return;
  for(const m of Array.isArray(o.material)?o.material:[o.material])if(['lacquer','timber','counter','steel'].includes(m.userData.surfaceFinish))materials.set(m,{probe,original:m.envMap,intensity:m.envMapIntensity});
 })}
 function update(model,initialTransforms,loaded,files){let unchanged=true;model.traverse(o=>{if(!Object.keys(o.userData).some(k=>k.startsWith('interaction_')))return;const initial=initialTransforms.get(o);if(!initial||initial.visible!==o.visible||o.matrix.elements.some((v,i)=>Math.abs(v-initial.matrix.elements[i])>1e-5))unchanged=false});
 const next=available&&unchanged&&loaded?.length===files?.length&&JSON.stringify(manifest?.sourceModules)===JSON.stringify(files);if(next===active)return;active=next;
 for(const[m,r]of materials){m.envMap=active?maps.get(r.probe):r.original;m.envMapIntensity=active ? .65 : r.intensity;m.needsUpdate=true}
 }
 return{init,load,prepare,update};
}
