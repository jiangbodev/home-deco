import * as THREE from 'three';
import {Reflector} from 'three/addons/objects/Reflector.js';

// Only the nearest visible bathroom mirror receives one reduced-resolution pass.
// Automatic/low quality and touch devices keep the static environment fallback.
export function createMirrors(scene, model, camera, {coarse=false}={}) {
 if(coarse)return {update(){},async warm(){}};
 const glazing=[];model.traverse(o=>{if(o.isMesh&&(Array.isArray(o.material)?o.material:[o.material]).some(m=>m.transmission>0))glazing.push(o)});
 const entries=[],frustum=new THREE.Frustum(),viewProjection=new THREE.Matrix4();
 const definitions=new Map([['主卫镜面示意',new THREE.Vector3(1,0,0)],['外置台盆镜面示意',new THREE.Vector3(0,0,-1)]]);
 model.updateMatrixWorld(true);
 model.traverse(source=>{
  const normal=definitions.get(source.userData.source_name||source.name);
  if(!source.isMesh||!normal||!source.visible)return;
  const box=new THREE.Box3().setFromObject(source),center=box.getCenter(new THREE.Vector3());
  const rotation=new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,0,1),normal);
  const pose=new THREE.Matrix4().compose(center,rotation,new THREE.Vector3(1,1,1));
  const geometry=source.geometry.clone().applyMatrix4(pose.clone().invert().multiply(source.matrixWorld));
  const mirror=new Reflector(geometry,{textureWidth:768,textureHeight:768,multisample:2,color:new THREE.Color(.48,.48,.48),clipBias:.0002});
  const capture=mirror.onBeforeRender;
  mirror.onBeforeRender=(renderer,scene,viewCamera)=>{
   // Three.js also draws opaque mirrors into its glass-transmission target.
   // That auxiliary draw must reuse the texture, not capture the scene again.
   if(viewCamera!==camera||renderer.getRenderTarget()!==null)return;
   // Avoid a second refractive scene render inside the reflected scene.
   // Window/door profiles remain; their clear panes are optically omitted here.
   const visibility=glazing.map(o=>o.visible);
   glazing.forEach(o=>{o.visible=false});
   try{capture.call(mirror,renderer,scene,viewCamera)}finally{glazing.forEach((o,i)=>{o.visible=visibility[i]})}
  };
  mirror.name='Planar '+source.name;mirror.position.copy(center);mirror.quaternion.copy(rotation);mirror.visible=false;
  scene.add(mirror);entries.push({source,mirror,box,center,normal});
 });
 function update(quality='auto') {
  camera.updateMatrixWorld();viewProjection.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);frustum.setFromProjectionMatrix(viewProjection);
  let nearest=null,distance=Infinity;
  if(!coarse&&quality==='high')for(const e of entries){
   let visible=true;for(let p=e.source.parent;p;p=p.parent)if(!p.visible)visible=false;
   const v=camera.position.clone().sub(e.center),d=v.length();
   if(visible&&d<4.5&&d<distance&&v.dot(e.normal)>.025&&frustum.intersectsBox(e.box)){nearest=e;distance=d;}
  }
  for(const e of entries){e.source.visible=e!==nearest;e.mirror.visible=e===nearest;}
 }
 async function warm(renderer){
  for(const e of entries)e.mirror.visible=true;
  try{await renderer.compileAsync(scene,camera)}finally{update()}
 }
 return {update,warm};
}
