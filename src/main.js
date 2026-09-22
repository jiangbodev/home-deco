import './style.css';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';
import {createAppearance} from './appearance.js';
import {createMirrors} from './mirrors.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const $=s=>document.querySelector(s), canvas=$('#scene');
const coarse=matchMedia('(pointer:coarse)').matches;
import {rooms} from './rooms.js';
import {createModules} from './modules.js';
import {createLoadingProgress} from './loading-progress.js';
let appearance,mirrors;
let modules,visitSequence=0,lastRoom=-1;
let frameLoop,contextLost=false;
let renderer, model, ready=false, quality='auto', yaw=0,pitch=0, mapOpen=false;
let stateEntries=[], frameAverage=16, adaptiveScale=1.35;
const scene=new THREE.Scene();scene.background=new THREE.Color('#edf1f5');
const camera=new THREE.PerspectiveCamera(65,1,.035,90);camera.rotation.order='YXZ';
const pendingWalkRooms=new Set();
const initialTransforms=new Map(), keys=new Set(), joystick={x:0,y:0};
const C=new THREE.Matrix4().makeRotationX(-Math.PI/2), Ci=C.clone().invert();
const stateNames={'bath-partition':'打开主卫内部隔断','doors':'打开房门','privacy-curtain':'合上隐私帘','kitchen-window-open':'打开厨房窗','laundry-doors':'展开洗衣区隐藏门'};
let toastTimer;
function toast(text){$('#toast').textContent=text;$('#toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('show'),2400)}
function metadata(o){try{return JSON.parse(o.userData.metadata||'{}')}catch{return {}}}
function resize(redraw=true){if(!renderer||contextLost)return;const w=canvas.clientWidth,h=canvas.clientHeight;if(!w||!h)return;camera.aspect=w/h;camera.updateProjectionMatrix();const max=quality==='high'?2:quality==='low'?1:Math.min(adaptiveScale,Math.sqrt(2400000/(w*h))),ratio=Math.min(devicePixelRatio,max);const size=renderer.getSize(new THREE.Vector2());if(renderer.getPixelRatio()===ratio&&size.x===w&&size.y===h)return;renderer.setPixelRatio(ratio);renderer.setSize(w,h,false);if(ready&&redraw)renderer.render(scene,camera)}
window.addEventListener('resize',()=>resize());window.visualViewport?.addEventListener('resize',()=>resize());
function markRoom(i){if($('#room-nav').dataset.activeRoom===String(i))return;$('#room-label').textContent=rooms[i].name;document.querySelectorAll('[data-room]').forEach(b=>b.setAttribute('aria-current',String(Number(b.dataset.room)===i)));const nav=$('#room-nav'),button=nav.querySelector(`[data-room="${i}"]`);if(nav.dataset.activeRoom!==String(i)){nav.dataset.activeRoom=String(i);if(button){const left=button.offsetLeft-nav.offsetLeft;if(left<nav.scrollLeft)nav.scrollLeft=left;else if(left+button.offsetWidth>nav.scrollLeft+nav.clientWidth)nav.scrollLeft=left+button.offsetWidth-nav.clientWidth}}}
async function visit(i){const request=++visitSequence;if(ready&&modules){try{await modules.room(i)}catch{toast('房间暂未加载，请再次选择重试');return}if(request!==visitSequence)return}const r=rooms[i].entry??rooms[i];camera.position.set(r.x,1.4,r.z);yaw=Math.atan2(r.x-r.look[0],r.z-r.look[1]);pitch=-.04;camera.rotation.set(pitch,yaw,0,'YXZ');markRoom(i);updateMap();keys.clear();joystick.x=joystick.y=0;if(ready)canvas.focus({preventScroll:true})}
function roomButton(i){const b=document.createElement('button');b.textContent=rooms[i].name;b.dataset.room=i;b.onclick=()=>{closeDialogs();visit(i)};return b}
rooms.forEach((_,i)=>{$('#all-rooms').append(roomButton(i));if(rooms[i].shortcut!==false)$('#room-nav').append(roomButton(i))});
function openDialog(id,button){endInput();const d=$(id);d.showModal();button?.setAttribute('aria-expanded','true');mapOpen=id==='#map-panel';updateMap()}
function closeDialogs(){document.querySelectorAll('dialog[open]').forEach(d=>d.close());mapOpen=false;document.querySelectorAll('[aria-expanded=true]').forEach(b=>b.setAttribute('aria-expanded','false'))}
$('#map-button').onclick=()=>openDialog('#map-panel',$('#map-button'));
$('#settings-button').onclick=()=>openDialog('#settings-panel',$('#settings-button'));
$('#help-button').onclick=()=>openDialog('#help-panel');
document.querySelectorAll('dialog').forEach(d=>{d.querySelector('.close').onclick=()=>d.close();d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close()}});d.addEventListener('close',()=>{mapOpen=false;document.querySelectorAll('[aria-expanded=true]').forEach(b=>b.setAttribute('aria-expanded','false'))})});
$('#quality').onchange=e=>{quality=e.target.value;resize()};
$('#retry').onclick=()=>location.reload();
$('#reset').onclick=()=>{for(const[o,t]of initialTransforms){o.matrix.copy(t.matrix);o.matrix.decompose(o.position,o.quaternion,o.scale);o.visible=t.visible}model.updateMatrixWorld(true);refreshAppearance();syncStateControls();quality='auto';$('#quality').value='auto';resize();closeDialogs();visit(0);toast('已恢复初始空间')};

function readStates(){
 const grouped=new Map();
 model.traverse(o=>{
   o.visible=o.userData.source_visible!==false;
   initialTransforms.set(o,{matrix:o.matrix.clone(),visible:o.visible});
   for(const[k,v]of Object.entries(o.userData))if(k.startsWith('interaction_')){
     try{const pair=JSON.parse(v),key=k.slice(12);if(!grouped.has(key))grouped.set(key,[]);grouped.get(key).push({o,pair})}catch{console.warn('Invalid interaction metadata',o.name,k)}
   }
 });
 // Expose everyday controls only; other authored states retain their defaults.
 for(const[key,entries]of grouped){
   if(!Object.hasOwn(stateNames,key))continue;
   const label=document.createElement('label');label.className='setting-row';label.append(document.createTextNode(stateNames[key]||key));const input=document.createElement('input');input.type='checkbox';input.setAttribute('role','switch');label.append(input);$('#state-controls').append(label);
   input.onchange=()=>{entries.forEach(({o,pair})=>{const s=pair[(key==='laundry-doors'?!input.checked:input.checked)?'on':'off'];if(!s)return;o.visible=s.visible;const m=C.clone().multiply(new THREE.Matrix4().fromArray(s.matrix)).multiply(Ci);m.decompose(o.position,o.quaternion,o.scale);o.updateMatrix()});model.updateMatrixWorld(true);refreshAppearance()};
   stateEntries.push({key,entries,input});
 }
 syncStateControls();
}
function syncStateControls(){for(const{key,entries,input}of stateEntries){let on=0,off=0;for(const{o,pair}of entries){for(const[k,s]of Object.entries(pair)){const m=C.clone().multiply(new THREE.Matrix4().fromArray(s.matrix)).multiply(Ci);const err=m.elements.reduce((t,v,i)=>t+Math.abs(v-o.matrix.elements[i]),0)+(o.visible===s.visible?0:100);if(k==='on')on+=err;else off+=err}}input.checked=key==='laundry-doors'?off<on:on<off}}

function refreshAppearance(){
 if(!model)return;model.updateMatrixWorld(true);appearance?.update(model,initialTransforms,modules?.loaded,modules?.assetFiles);
}

function buildNavigation(){
 refreshAppearance();
 const svgNS='http://www.w3.org/2000/svg';const svg=document.createElementNS(svgNS,'svg');svg.setAttribute('viewBox','-.4 -.4 15 8');svg.setAttribute('aria-label','户型导航');
 const wallGroup=document.createElementNS(svgNS,'g');wallGroup.setAttribute('fill','#b6c0ae');svg.append(wallGroup);
 model.updateMatrixWorld(true);
 model.traverse(o=>{
   const m=metadata(o);
   if(o.isMesh){
     if(['wall','column'].includes(m.kind)){
       const b=new THREE.Box3().setFromObject(o);if(b.min.y<1.4&&b.max.y>.5){const r=document.createElementNS(svgNS,'rect');r.setAttribute('x',b.min.x);r.setAttribute('y',b.min.z);r.setAttribute('width',Math.max(.06,b.max.x-b.min.x));r.setAttribute('height',Math.max(.06,b.max.z-b.min.z));wallGroup.append(r)}
     }
   }
 });
 rooms.forEach((r,i)=>{const g=document.createElementNS(svgNS,'g');g.setAttribute('role','button');g.setAttribute('tabindex','0');g.setAttribute('aria-label','前往'+r.name);g.classList.add('map-room');const c=document.createElementNS(svgNS,'circle');c.setAttribute('cx',r.x);c.setAttribute('cy',r.z);c.setAttribute('r','.3');c.setAttribute('opacity','.4');const t=document.createElementNS(svgNS,'text');t.setAttribute('x',r.x);t.setAttribute('y',r.z+.62);t.setAttribute('text-anchor','middle');t.textContent=r.name;g.append(c,t);const go=()=>{closeDialogs();visit(i)};g.onclick=go;g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}};svg.append(g)});
 const marker=document.createElementNS(svgNS,'path');marker.id='map-marker';marker.setAttribute('d','M0 -.28 .18 .2 0 .1 -.18 .2Z');marker.setAttribute('fill','#234f39');marker.setAttribute('stroke','#fff');marker.setAttribute('stroke-width','.05');svg.append(marker);$('#map').append(svg);
}
function updateMap(){const m=$('#map-marker');if(m)m.setAttribute('transform',`translate(${camera.position.x} ${camera.position.z}) rotate(${-yaw*180/Math.PI})`)}

function move(dt){let x=joystick.x+(keys.has('KeyD')||keys.has('ArrowRight')?1:0)-(keys.has('KeyA')||keys.has('ArrowLeft')?1:0),z=joystick.y+(keys.has('KeyS')||keys.has('ArrowDown')?1:0)-(keys.has('KeyW')||keys.has('ArrowUp')?1:0);const len=Math.hypot(x,z);if(len<.04)return;if(len>1){x/=len;z/=len}const speed=1.35*dt;const dx=(Math.cos(yaw)*x+Math.sin(yaw)*z)*speed,dz=(-Math.sin(yaw)*x+Math.cos(yaw)*z)*speed;const p=camera.position;let targetRoom=0,targetDistance=Infinity;rooms.forEach((r,i)=>{const d=Math.hypot(r.x-p.x-dx,r.z-p.z-dz);if(d<targetDistance){targetDistance=d;targetRoom=i}});if(modules&&!modules.isRoomLoaded(targetRoom)){if(!pendingWalkRooms.has(targetRoom)){pendingWalkRooms.add(targetRoom);modules.room(targetRoom).catch(()=>toast('房间尚未就绪，请稍后重试')).finally(()=>pendingWalkRooms.delete(targetRoom))}return}
 // Free walkthrough: walls and furniture never block movement.
 p.x+=dx;p.z+=dz;p.y=1.4;let nearest=0,dist=Infinity;rooms.forEach((r,i)=>{const d=Math.hypot(r.x-p.x,r.z-p.z);if(d<dist){nearest=i;dist=d}});markRoom(nearest);if(nearest!==lastRoom){lastRoom=nearest;modules?.prioritize(nearest)}if(mapOpen)updateMap()}
function endInput(){keys.clear();joystick.x=joystick.y=0;$('#stick').style.transform='';lookPointer=null;stickPointer=null}
window.addEventListener('blur',endInput);document.addEventListener('visibilitychange',()=>{if(document.hidden)endInput()});
window.addEventListener('keydown',e=>{if(document.querySelector('dialog[open]')||/INPUT|SELECT|BUTTON/.test(e.target.tagName))return;if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code)){keys.add(e.code);e.preventDefault();$('#hint').style.opacity=0}});window.addEventListener('keyup',e=>keys.delete(e.code));
let lookPointer=null, lastX=0,lastY=0,stickPointer=null;
canvas.addEventListener('pointerdown',e=>{if(!ready||lookPointer!==null)return;lookPointer=e.pointerId;lastX=e.clientX;lastY=e.clientY;canvas.setPointerCapture(e.pointerId);canvas.focus({preventScroll:true});$('#hint').style.opacity=0});
canvas.addEventListener('pointermove',e=>{if(e.pointerId!==lookPointer)return;yaw-=(e.clientX-lastX)*.003;pitch=THREE.MathUtils.clamp(pitch-(e.clientY-lastY)*.003,-1.05,1.05);lastX=e.clientX;lastY=e.clientY;camera.rotation.set(pitch,yaw,0,'YXZ')});
for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,e=>{if(e.pointerId===lookPointer)lookPointer=null});
const stick=$('#joystick');
function setStick(e){const r=stick.getBoundingClientRect(),x=e.clientX-r.left-r.width/2,y=e.clientY-r.top-r.height/2;const len=Math.hypot(x,y),travel=Math.max(18,(r.width-34)/2-6),scale=len>travel?travel/len:1;joystick.x=x*scale/travel;joystick.y=y*scale/travel;$('#stick').style.transform=`translate(${x*scale}px,${y*scale}px)`}
stick.onpointerdown=e=>{if(stickPointer!==null)return;stickPointer=e.pointerId;stick.setPointerCapture(e.pointerId);setStick(e);$('#hint').style.opacity=0};stick.onpointermove=e=>{if(e.pointerId===stickPointer)setStick(e)};
for(const event of ['pointerup','pointercancel','lostpointercapture'])stick.addEventListener(event,e=>{if(e.pointerId===stickPointer){stickPointer=null;joystick.x=joystick.y=0;$('#stick').style.transform=''}});

async function start(){
 try{
   renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,powerPreference:coarse?'default':'high-performance'});renderer.transmissionResolutionScale=.35;renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
   resize();const pmrem=new THREE.PMREMGenerator(renderer), env=new RoomEnvironment();scene.environment=pmrem.fromScene(env,.04).texture;env.dispose();pmrem.dispose();scene.environmentIntensity=.45;
   scene.add(new THREE.HemisphereLight(0xf3f6ff,0xb0a394,.6));const sun=new THREE.DirectionalLight(0xfff6ea,.7);sun.position.set(12,8,6);scene.add(sun);
   appearance=createAppearance(renderer);const appearanceReady=appearance.init();
   const lightingReady=appearanceReady.then(()=>appearance.load());
   const progress=$('#progress'),label=$('#load-label');
   const startup=createLoadingProgress(({phase,loaded,total,percent})=>{
     $('#load-value').textContent=phase==='download'?`${percent}%`:phase==='ready'?'100%':'···';
     if(phase==='download'){
       progress.value=percent;
       label.textContent=percent===100?'空间资源已下载，正在准备光照…':`正在下载空间资源 ${percent}% · ${(loaded/1e6).toFixed(2)} / ${(total/1e6).toFixed(2)} MB`;
     }else if(phase==='prepare'){progress.removeAttribute('value');label.textContent='正在准备光照与室内画面…'}
     else if(phase==='ready')progress.value=100;
   });
   const manager=new THREE.LoadingManager();manager.onProgress=url=>startup.resourceDone(url);manager.onError=url=>startup.resourceFailed(url);
   const loader=new GLTFLoader(manager), draco=new DRACOLoader(manager);draco.setDecoderPath(import.meta.env.BASE_URL+'draco/');draco.setWorkerLimit(coarse?2:4);loader.setDRACOLoader(draco);
   $('#load-label').textContent='正在读取空间资源清单…';
   THREE.Cache.enabled=true;
   model=new THREE.Group();scene.add(model);
   const anisotropy=Math.min(renderer.capabilities.getMaxAnisotropy(),coarse?4:8);
   const uploadedTextures=new WeakSet(),texturePool=new WeakMap();let preparation=Promise.resolve();
   const shareTexture=texture=>{
     const image=texture.source?.data;if(!image||typeof image!=='object')return texture;
     let variants=texturePool.get(image);if(!variants)texturePool.set(image,variants=new Map());
     const key=JSON.stringify([...['mapping','channel','wrapS','wrapT','magFilter','minFilter','anisotropy','format','internalFormat','type','colorSpace','flipY','generateMipmaps','premultiplyAlpha','unpackAlignment','rotation','matrixAutoUpdate'].map(k=>texture[k]),texture.offset.toArray(),texture.repeat.toArray(),texture.center.toArray(),texture.matrix.toArray()]);
     if(!variants.has(key))variants.set(key,texture);return variants.get(key);
   };
   const nextFrame=()=>new Promise(resolve=>requestAnimationFrame(resolve));
   const prepare=group=>{
     // Serialize GPU preparation even when room navigation requests several downloads.
     const task=preparation.then(async()=>{
       await appearanceReady;appearance.prepare(group);
       const textures=new Set();group.traverse(o=>{if(o.isMesh){o.frustumCulled=true;for(const m of Array.isArray(o.material)?o.material:[o.material]){for(const k of ['map','normalMap','roughnessMap','metalnessMap','aoMap'])if(m[k])m[k].anisotropy=anisotropy;for(const [key,value]of Object.entries(m))if(value?.isTexture){m[key]=shareTexture(value);textures.add(m[key])}if(m.transparent)m.depthWrite=false}}});
       if(!ready)return; // The initial scene is prepared together before it is revealed.
       for(const texture of textures)if(!uploadedTextures.has(texture)){await nextFrame();if(contextLost)throw Error('Graphics context interrupted');renderer.initTexture(texture);uploadedTextures.add(texture)}
       await nextFrame();if(contextLost)throw Error('Graphics context interrupted');
       await renderer.compileAsync(group,camera,scene);
     });preparation=task.catch(()=>{});return task;
   };
   const status=document.createElement('button');status.className='module-status';status.hidden=true;status.onclick=()=>modules.background();$('#ui').append(status);
   modules=createModules({loader,root:model,prepare,onManifest:startup.plan,onProgress:startup.bytes,onAttach:()=>{if(ready)refreshAppearance()},onStatus:s=>{appearance.update(model,initialTransforms,modules?.loaded,modules?.assetFiles);status.hidden=s.loaded===s.total;status.textContent=s.failed?'部分房间加载失败 · 点击重试':'正在补齐其他房间…';status.disabled=!s.failed}});
   await modules.init({wholeHome:true});startup.preparing();await lightingReady;appearance.addFixtures(scene);readStates();buildNavigation();await visit(0);appearance.settle();mirrors=createMirrors(scene,model,camera,{coarse});await mirrors.warm(renderer);mirrors.update(quality);
   await renderer.compileAsync(scene,camera);renderer.render(scene,camera);startup.complete();ready=true;$('#loading').hidden=true;$('#ui').hidden=false;
   if(coarse)$('#hint').textContent='拖动画面环顾';
   let last=performance.now(),count=0;
   frameLoop=now=>{if(contextLost||document.hidden){last=now;return}const ms=now-last;last=now;const dt=Math.min(ms/1000,.05);appearance.tick(dt);if(!document.querySelector('dialog[open]'))move(dt);frameAverage=.94*frameAverage+.06*Math.min(ms,80);count++;if(quality==='auto'&&count%60===0&&frameAverage>20&&adaptiveScale>.7){adaptiveScale=Math.max(.7,adaptiveScale-.1);resize(false)}else if(quality==='auto'&&count%240===0&&frameAverage<16.9&&adaptiveScale<1.35){adaptiveScale=Math.min(1.35,adaptiveScale+.05);resize(false)}mirrors?.update(quality);renderer.render(scene,camera)};
   renderer.setAnimationLoop(frameLoop);
   if(import.meta.env.DEV) import('./dining-review.js').then(({installDiningReview})=>installDiningReview({camera,renderer,setAngles:(y,p)=>{yaw=y;pitch=p;camera.rotation.set(pitch,yaw,0,'YXZ')}}));
   if(import.meta.env.DEV) import('./whole-house-review.js').then(({installWholeHouseReview})=>installWholeHouseReview({camera,renderer,setAngles:(y,p)=>{yaw=y;pitch=p;camera.rotation.set(pitch,yaw,0,'YXZ')}}));
   if(import.meta.env.DEV) import('./fridge-review.js').then(({installFridgeReview})=>installFridgeReview({camera,renderer,setAngles:(y,p)=>{yaw=y;pitch=p;camera.rotation.set(pitch,yaw,0,'YXZ')}}));
   canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();contextLost=true;endInput();renderer.setAnimationLoop(null);$('#loading').hidden=false;$('#load-label').textContent='正在恢复三维画面…';progress.hidden=false;progress.removeAttribute('value');$('#retry').hidden=false});
   canvas.addEventListener('webglcontextrestored',async()=>{try{contextLost=false;resize(false);await renderer.compileAsync(scene,camera);renderer.render(scene,camera);last=performance.now();renderer.setAnimationLoop(frameLoop);$('#loading').hidden=true;$('#retry').hidden=true;modules.background()}catch(error){console.error(error);$('#load-label').textContent='画面恢复失败，请重新加载';$('#retry').hidden=false}});

 }catch(error){console.error(error);$('#load-label').textContent=renderer?'空间加载失败，请检查网络后重试。':'浏览器暂时无法启用三维画面，请检查硬件加速或换浏览器打开。';$('#retry').hidden=false;$('#progress').hidden=true}
}
start();
