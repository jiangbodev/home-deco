// Keep loaded rooms resident; geometry and shared texture URLs are content-addressed.
export const initialModules=['base','room-0','room-1','room-2'];
export function createModules({loader,root,prepare,onStatus,onAttach=()=>{},onManifest=()=>{},onProgress=()=>{}}){
 const base=import.meta.env.BASE_URL+'assets/modules/';let manifest,started=false;const loaded=new Map(),pending=new Map(),targets=new Map(),queue=[];let failed=false;
 const forRoom=i=>[`room-${i}`,...(i===4?['bedding-main']:i===5?['bedding-second']:[])];
 const neighbors=[[2,1,3,5],[2,4,0],[0,1,3],[2,0,8],[1,7],[0,6,8],[5,0],[4,3],[5,3]];
 const status=()=>onStatus({loaded:loaded.size,total:Object.keys(manifest.modules).length,failed});
 async function load(key){
  if(!manifest.modules[key]||loaded.has(key))return;
  if(pending.has(key))return pending.get(key);
  const task=(async()=>{const g=await loader.loadAsync(base+manifest.modules[key].file,event=>onProgress(manifest.modules[key].file,event.loaded));await prepare(g.scene);
   if(key==='base'){root.add(g.scene);g.scene.traverse(o=>{if(Number.isInteger(o.userData.moduleNode))targets.set(o.userData.moduleNode,o)})}
   else for(const o of [...g.scene.children]){const parent=targets.get(o.userData.attachTo);if(!parent)throw Error('Missing model attachment');parent.add(o)}
   root.updateMatrixWorld(true);onAttach();loaded.set(key,true);status();
  })().catch(e=>{failed=true;status();throw e}).finally(()=>pending.delete(key));pending.set(key,task);return task;
 }
 async function drain(){if(started)return;started=true;while(queue.length){const key=queue.shift();try{await load(key)}catch(e){console.warn('Room module failed',key,e)}}started=false;status()}
 function prioritize(i){const first=[...forRoom(i),...(neighbors[i]||[]).flatMap(forRoom)];for(const key of first.reverse()){const p=queue.indexOf(key);if(p>=0)queue.splice(p,1);if(manifest.modules[key]&&!loaded.has(key))queue.unshift(key)}void drain()}
 return {
  async init({wholeHome=false}={}){const r=await fetch(base+'manifest.json',{cache:'no-cache'});if(!r.ok)throw Error('Model manifest unavailable');manifest=await r.json();const keys=wholeHome?Object.keys(manifest.modules):initialModules;onManifest(manifest,keys);await load('base');await Promise.all(initialModules.filter(key=>key!=='base').map(load));if(wholeHome)for(const key of keys)await load(key)},
  async room(i){await Promise.all(forRoom(i).map(load));prioritize(i)},
  prioritize,
  isRoomLoaded(i){return forRoom(i).every(key=>!manifest.modules[key]||loaded.has(key))},
  background(){failed=false;for(const key of Object.keys(manifest.modules))if(!loaded.has(key)&&!queue.includes(key))queue.push(key);prioritize(0)},
  get assetFiles(){return manifest?Object.values(manifest.modules).map(m=>m.file).sort():[]},
  get loaded(){return [...loaded.keys()]},
 };
}
