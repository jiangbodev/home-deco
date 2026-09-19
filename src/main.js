import './style.css';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const $=s=>document.querySelector(s), canvas=$('#scene');
const coarse=matchMedia('(pointer:coarse)').matches;
import {rooms} from './rooms.js';
import {createModules} from './modules.js';
let modules,visitSequence=0,lastRoom=-1;
let renderer, model, ready=false, quality='auto', yaw=0,pitch=0, mapOpen=false;
let stateEntries=[], wallMeshes=[], floorMeshes=[], frameAverage=16, adaptiveScale=coarse?1.35:1.7;
const scene=new THREE.Scene();scene.background=new THREE.Color('#e9ede5');
const camera=new THREE.PerspectiveCamera(65,1,.035,90);camera.rotation.order='YXZ';
const initialTransforms=new Map(), keys=new Set(), joystick={x:0,y:0};
const ray=new THREE.Raycaster(), down=new THREE.Vector3(0,-1,0), direction=new THREE.Vector3();
const C=new THREE.Matrix4().makeRotationX(-Math.PI/2), Ci=C.clone().invert();
const stateNames={'doors':'打开房门','privacy-curtain':'合上隐私帘','kitchen-window-open':'打开厨房窗','laundry-doors':'展开洗衣区隐藏门','ceiling':'显示吊顶','effect-floor':'效果图连续木地板','furniture':'显示家具','piano':'显示钢琴','dining-stored':'收纳餐椅与条凳'};
let toastTimer;
function toast(text){$('#toast').textContent=text;$('#toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('show'),2400)}
function metadata(o){try{return JSON.parse(o.userData.metadata||'{}')}catch{return {}}}
function effectiveVisible(o){for(let p=o;p;p=p.parent)if(!p.visible)return false;return true}
function resize(){if(!renderer)return;const w=canvas.clientWidth,h=canvas.clientHeight;camera.aspect=w/h;camera.updateProjectionMatrix();const max=quality==='high'?2:quality==='low'?1:adaptiveScale;renderer.setPixelRatio(Math.min(devicePixelRatio,max));renderer.setSize(w,h,false)}
window.addEventListener('resize',resize);window.visualViewport?.addEventListener('resize',resize);
function markRoom(i){$('#room-label').textContent=rooms[i].name;document.querySelectorAll('[data-room]').forEach(b=>b.setAttribute('aria-current',String(Number(b.dataset.room)===i)))}
async function visit(i){const request=++visitSequence;if(ready&&modules){try{await modules.room(i)}catch{toast('房间暂未加载，请再次选择重试');return}if(request!==visitSequence)return}const r=rooms[i];camera.position.set(r.x,1.5,r.z);yaw=Math.atan2(r.x-r.look[0],r.z-r.look[1]);pitch=-.04;camera.rotation.set(pitch,yaw,0,'YXZ');markRoom(i);updateMap();keys.clear();joystick.x=joystick.y=0;if(ready)canvas.focus({preventScroll:true})}
function roomButton(i){const b=document.createElement('button');b.textContent=rooms[i].name;b.dataset.room=i;b.onclick=()=>{closeDialogs();visit(i)};return b}
rooms.forEach((_,i)=>{$('#all-rooms').append(roomButton(i));if(i<6)$('#room-nav').append(roomButton(i))});
function openDialog(id,button){keys.clear();joystick.x=joystick.y=0;const d=$(id);d.showModal();button?.setAttribute('aria-expanded','true');mapOpen=id==='#map-panel';updateMap()}
function closeDialogs(){document.querySelectorAll('dialog[open]').forEach(d=>d.close());mapOpen=false;document.querySelectorAll('[aria-expanded=true]').forEach(b=>b.setAttribute('aria-expanded','false'))}
$('#map-button').onclick=()=>openDialog('#map-panel',$('#map-button'));
$('#settings-button').onclick=()=>openDialog('#settings-panel',$('#settings-button'));
$('#help-button').onclick=()=>openDialog('#help-panel');
document.querySelectorAll('dialog').forEach(d=>{d.querySelector('.close').onclick=()=>d.close();d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close()}});d.addEventListener('close',()=>{mapOpen=false;document.querySelectorAll('[aria-expanded=true]').forEach(b=>b.setAttribute('aria-expanded','false'))})});
$('#quality').onchange=e=>{quality=e.target.value;resize()};
$('#retry').onclick=()=>location.reload();
$('#reset').onclick=()=>{for(const[o,t]of initialTransforms){o.matrix.copy(t.matrix);o.matrix.decompose(o.position,o.quaternion,o.scale);o.visible=t.visible}model.updateMatrixWorld(true);syncStateControls();quality='auto';$('#quality').value='auto';resize();closeDialogs();visit(0);toast('已恢复初始空间')};

function readStates(){
 const grouped=new Map();
 model.traverse(o=>{
   o.visible=o.userData.source_visible!==false;
   initialTransforms.set(o,{matrix:o.matrix.clone(),visible:o.visible});
   for(const[k,v]of Object.entries(o.userData))if(k.startsWith('interaction_')){
     try{const pair=JSON.parse(v),key=k.slice(12);if(!grouped.has(key))grouped.set(key,[]);grouped.get(key).push({o,pair})}catch{console.warn('Invalid interaction metadata',o.name,k)}
   }
 });
 for(const[key,entries]of grouped){
   const label=document.createElement('label');label.className='setting-row';label.append(document.createTextNode(stateNames[key]||key));const input=document.createElement('input');input.type='checkbox';input.setAttribute('role','switch');label.append(input);$('#state-controls').append(label);
   input.onchange=()=>{entries.forEach(({o,pair})=>{const s=pair[input.checked?'on':'off'];if(!s)return;o.visible=s.visible;const m=C.clone().multiply(new THREE.Matrix4().fromArray(s.matrix)).multiply(Ci);m.decompose(o.position,o.quaternion,o.scale);o.updateMatrix()});model.updateMatrixWorld(true)};
   stateEntries.push({key,entries,input});
 }
 syncStateControls();
}
function syncStateControls(){for(const{entries,input}of stateEntries){let on=0,off=0;for(const{o,pair}of entries){for(const[k,s]of Object.entries(pair)){const m=C.clone().multiply(new THREE.Matrix4().fromArray(s.matrix)).multiply(Ci);const err=m.elements.reduce((t,v,i)=>t+Math.abs(v-o.matrix.elements[i]),0)+(o.visible===s.visible?0:100);if(k==='on')on+=err;else off+=err}}input.checked=on<off}}

function buildNavigation(){
 const svgNS='http://www.w3.org/2000/svg';const svg=document.createElementNS(svgNS,'svg');svg.setAttribute('viewBox','-.4 -.4 15 8');svg.setAttribute('aria-label','户型导航');
 const wallGroup=document.createElementNS(svgNS,'g');wallGroup.setAttribute('fill','#b6c0ae');svg.append(wallGroup);
 model.updateMatrixWorld(true);
 model.traverse(o=>{
   const m=metadata(o);
   if(o.isMesh){
     // Authored architectural surfaces only; keep thin textile leaves out of collision tests.
     let door=false;for(let p=o;p&&p!==model;p=p.parent){if(['door','sliding-door','folding-door'].includes(metadata(p).kind)){door=true;break}}
     if(['wall','column','glass','opening-infill','fixed-window','sliding-window'].includes(m.kind)||door)wallMeshes.push(o);
     if(/^F0[1-9]$/.test(m.id||''))floorMeshes.push(o);
     if(['wall','column'].includes(m.kind)){
       const b=new THREE.Box3().setFromObject(o);if(b.min.y<1.4&&b.max.y>.5){const r=document.createElementNS(svgNS,'rect');r.setAttribute('x',b.min.x);r.setAttribute('y',b.min.z);r.setAttribute('width',Math.max(.06,b.max.x-b.min.x));r.setAttribute('height',Math.max(.06,b.max.z-b.min.z));wallGroup.append(r)}
     }
   }
 });
 rooms.forEach((r,i)=>{const g=document.createElementNS(svgNS,'g');g.setAttribute('role','button');g.setAttribute('tabindex','0');g.setAttribute('aria-label','前往'+r.name);g.classList.add('map-room');const c=document.createElementNS(svgNS,'circle');c.setAttribute('cx',r.x);c.setAttribute('cy',r.z);c.setAttribute('r','.3');c.setAttribute('opacity','.4');const t=document.createElementNS(svgNS,'text');t.setAttribute('x',r.x);t.setAttribute('y',r.z+.62);t.setAttribute('text-anchor','middle');t.textContent=r.name;g.append(c,t);const go=()=>{closeDialogs();visit(i)};g.onclick=go;g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}};svg.append(g)});
 const marker=document.createElementNS(svgNS,'path');marker.id='map-marker';marker.setAttribute('d','M0 -.28 .18 .2 0 .1 -.18 .2Z');marker.setAttribute('fill','#234f39');marker.setAttribute('stroke','#fff');marker.setAttribute('stroke-width','.05');svg.append(marker);$('#map').append(svg);
}
function updateMap(){const m=$('#map-marker');if(m)m.setAttribute('transform',`translate(${camera.position.x} ${camera.position.z}) rotate(${-yaw*180/Math.PI})`)}
function allowedStep(x,z){
 if(x<.15||x>14.03||z<.15||z>6.94)return false;
 const pos=camera.position;direction.set(x-pos.x,0,z-pos.z);const dist=direction.length();if(!dist)return true;direction.normalize();
 for(const h of [.7,1.5]){ray.set(new THREE.Vector3(pos.x,h,pos.z),direction);ray.far=dist+.2;if(ray.intersectObjects(wallMeshes,false).some(h=>effectiveVisible(h.object)))return false}
 ray.set(new THREE.Vector3(x,.35,z),down);ray.far=.55;
 return ray.intersectObjects(floorMeshes,false).some(h=>effectiveVisible(h.object));
}
function move(dt){let x=joystick.x+(keys.has('KeyD')||keys.has('ArrowRight')?1:0)-(keys.has('KeyA')||keys.has('ArrowLeft')?1:0),z=joystick.y+(keys.has('KeyS')||keys.has('ArrowDown')?1:0)-(keys.has('KeyW')||keys.has('ArrowUp')?1:0);const len=Math.hypot(x,z);if(len<.04)return;if(len>1){x/=len;z/=len}const speed=1.35*dt;const dx=(Math.cos(yaw)*x+Math.sin(yaw)*z)*speed,dz=(-Math.sin(yaw)*x+Math.cos(yaw)*z)*speed;const p=camera.position;if(allowedStep(p.x+dx,p.z))p.x+=dx;if(allowedStep(p.x,p.z+dz))p.z+=dz;p.y=1.5;let nearest=0,dist=Infinity;rooms.forEach((r,i)=>{const d=Math.hypot(r.x-p.x,r.z-p.z);if(d<dist){nearest=i;dist=d}});markRoom(nearest);if(nearest!==lastRoom){lastRoom=nearest;modules?.prioritize(nearest)}if(mapOpen)updateMap()}
function endInput(){keys.clear();joystick.x=joystick.y=0;$('#stick').style.transform='';lookPointer=null;stickPointer=null}
window.addEventListener('blur',endInput);document.addEventListener('visibilitychange',()=>{if(document.hidden)endInput()});
window.addEventListener('keydown',e=>{if(document.querySelector('dialog[open]')||/INPUT|SELECT|BUTTON/.test(e.target.tagName))return;if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code)){keys.add(e.code);e.preventDefault();$('#hint').style.opacity=0}});window.addEventListener('keyup',e=>keys.delete(e.code));
let lookPointer=null, lastX=0,lastY=0,stickPointer=null;
canvas.addEventListener('pointerdown',e=>{if(!ready||lookPointer!==null)return;lookPointer=e.pointerId;lastX=e.clientX;lastY=e.clientY;canvas.setPointerCapture(e.pointerId);canvas.focus({preventScroll:true});$('#hint').style.opacity=0});
canvas.addEventListener('pointermove',e=>{if(e.pointerId!==lookPointer)return;yaw-=(e.clientX-lastX)*.003;pitch=THREE.MathUtils.clamp(pitch-(e.clientY-lastY)*.003,-1.05,1.05);lastX=e.clientX;lastY=e.clientY;camera.rotation.set(pitch,yaw,0,'YXZ')});
for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,e=>{if(e.pointerId===lookPointer)lookPointer=null});
const stick=$('#joystick');
function setStick(e){const r=stick.getBoundingClientRect(),x=e.clientX-r.left-r.width/2,y=e.clientY-r.top-r.height/2;const len=Math.hypot(x,y),scale=len>28?28/len:1;joystick.x=x*scale/28;joystick.y=y*scale/28;$('#stick').style.transform=`translate(${x*scale}px,${y*scale}px)`}
stick.onpointerdown=e=>{if(stickPointer!==null)return;stickPointer=e.pointerId;stick.setPointerCapture(e.pointerId);setStick(e);$('#hint').style.opacity=0};stick.onpointermove=e=>{if(e.pointerId===stickPointer)setStick(e)};
for(const event of ['pointerup','pointercancel','lostpointercapture'])stick.addEventListener(event,e=>{if(e.pointerId===stickPointer){stickPointer=null;joystick.x=joystick.y=0;$('#stick').style.transform=''}});

async function start(){
 try{
   renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,powerPreference:coarse?'default':'high-performance'});renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
   resize();const pmrem=new THREE.PMREMGenerator(renderer), env=new RoomEnvironment();scene.environment=pmrem.fromScene(env,.04).texture;env.dispose();pmrem.dispose();scene.environmentIntensity=.8;
   scene.add(new THREE.HemisphereLight(0xfffcf1,0x9aa08e,1.6));const sun=new THREE.DirectionalLight(0xfff4df,2.2);sun.position.set(2,8,-4);scene.add(sun);
   const loader=new GLTFLoader(), draco=new DRACOLoader();draco.setDecoderPath(import.meta.env.BASE_URL+'draco/');draco.setWorkerLimit(coarse?2:4);loader.setDRACOLoader(draco);
   $('#load-label').textContent='正在加载入口空间…';
   THREE.Cache.enabled=true;
   model=new THREE.Group();scene.add(model);
   const anisotropy=Math.min(renderer.capabilities.getMaxAnisotropy(),coarse?4:8);
   const prepare=group=>group.traverse(o=>{if(o.isMesh){o.frustumCulled=true;for(const m of Array.isArray(o.material)?o.material:[o.material]){for(const k of ['map','normalMap','roughnessMap','metalnessMap','aoMap'])if(m[k])m[k].anisotropy=anisotropy;if(m.transparent)m.depthWrite=false}}});
   const status=document.createElement('button');status.className='module-status';status.hidden=true;status.onclick=()=>modules.background();$('#ui').append(status);
   modules=createModules({loader,root:model,prepare,onStatus:s=>{status.hidden=s.loaded===s.total;status.textContent=s.failed?'部分房间加载失败 · 点击重试':'正在补齐其他房间…';status.disabled=!s.failed}});
   await modules.init();readStates();buildNavigation();await visit(0);
   await renderer.compileAsync(scene,camera);renderer.render(scene,camera);ready=true;$('#loading').hidden=true;$('#ui').hidden=false;
   // Yield the first visible frame before fetching the rest of the home.
   requestAnimationFrame(()=>requestAnimationFrame(()=>modules.background()));
   if(coarse)$('#hint').textContent='左手移动 · 拖动画面环顾';
   let last=performance.now(),count=0;
   renderer.setAnimationLoop(now=>{const ms=now-last;last=now;if(document.hidden)return;const dt=Math.min(ms/1000,.05);if(!document.querySelector('dialog[open]'))move(dt);renderer.render(scene,camera);frameAverage=.98*frameAverage+.02*ms;if(++count%180===0&&quality==='auto'&&frameAverage>30&&adaptiveScale>1){adaptiveScale=Math.max(1,adaptiveScale-.15);resize()}});
   canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();endInput();renderer.setAnimationLoop(null);$('#loading').hidden=false;$('#load-label').textContent='图形资源已释放，请重新加载';$('#retry').hidden=false});
 }catch(error){console.error(error);$('#load-label').textContent=renderer?'空间加载失败，请检查网络后重试。':'浏览器暂时无法启用三维画面，请检查硬件加速或换浏览器打开。';$('#retry').hidden=false;$('#progress').hidden=true}
}
start();
