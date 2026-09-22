import * as THREE from 'three';
const C=new THREE.Matrix4().makeRotationX(-Math.PI/2),Ci=C.clone().invert();
const nameOf=o=>o.userData.source_name||o.name;
const byName=(model,name)=>model.getObjectByName(THREE.PropertyBinding.sanitizeNodeName(name))||model.getObjectByName(name);
const localState=s=>C.clone().multiply(new THREE.Matrix4().fromArray(s.matrix)).multiply(Ci);
const distance=(a,b)=>a.elements.reduce((s,x,i)=>s+Math.abs(x-b.elements[i]),0);
const visible=o=>{for(;o;o=o.parent)if(!o.visible)return false;return true};
export function buildDoorMechanisms(model){
 model.updateMatrixWorld(true);
 // Shower leaves have no authored opening state. Rotate only glass, its seal and
 // leaf hardware about the existing right-hand hinge; perimeter frames stay fixed.
 for(const[prefix,x,z]of [['主卫',9.4159,1.12075],['次卫',5.1761,1.03743]]){
  const pivot=new THREE.Vector3(x,0,z),swing=new THREE.Matrix4().makeTranslation(...pivot.toArray()).multiply(new THREE.Matrix4().makeRotationY(Math.PI/2)).multiply(new THREE.Matrix4().makeTranslation(...pivot.clone().negate().toArray()));
  for(const suffix of ['淋浴透明玻璃','淋浴透明玻璃嵌玻密封条','淋浴单扇门铰链及拉手']){
   const o=byName(model,prefix+suffix);if(!o)continue;
   const off=o.matrix.clone(),on=o.parent.matrixWorld.clone().invert().multiply(swing).multiply(o.matrixWorld);
   o.userData['interaction_shower-'+prefix]=JSON.stringify(Object.fromEntries([['off',off],['on',on]].map(([k,m])=>[k,{visible:true,matrix:Ci.clone().multiply(m).multiply(C).toArray()}])));
  }
 }
 const doors=[],groups=new Map();
 model.traverse(o=>{for(const[key,value]of Object.entries(o.userData)){
  if(key!=='interaction_doors'&&key!=='interaction_bath-partition'&&!key.startsWith('interaction_shower-'))continue;
  const group=key==='interaction_doors'?o.uuid:key;
  if(!groups.has(group)){const door={id:group,name:key==='interaction_bath-partition'?'主卫内部隔断':key.startsWith('interaction_shower-')?key.slice(19)+'淋浴门':nameOf(o).replace(/门扇$/,'').replace('_',' '),key:key.slice(12),entries:[],handles:[],animation:null};groups.set(group,door);doors.push(door)}
  const pair=JSON.parse(value);groups.get(group).entries.push({o,pair,off:localState(pair.off),on:localState(pair.on)});
 }});
 const addHandle=(door,o,world)=>{if(!o)return;const point=world||new THREE.Box3().setFromObject(o).getCenter(new THREE.Vector3());door.handles.push({o,local:o.worldToLocal(point.clone()),door})};
 for(const door of doors){
  if(door.key==='doors'){
   door.entries[0].o.traverse(o=>{if(/执手|指拉槽/.test(o.name))addHandle(door,o)});
   if(nameOf(door.entries[0].o)==='次卧儿童房连通移门_1门扇')byName(model,'次卧儿童房连通移门_2门扇')?.traverse(o=>{if(/指拉槽/.test(o.name))addHandle(door,o)});
  }else if(door.key==='bath-partition'){
   const o=byName(model,'主卫内部压纹隔断竖框.001');if(o){const p=new THREE.Box3().setFromObject(o).getCenter(new THREE.Vector3());p.y=1.12;addHandle(door,o,p)}
  }else{
   const prefix=door.key.slice(7),o=byName(model,prefix+'淋浴单扇门铰链及拉手');for(const offset of [-.025,.049])addHandle(door,o,new THREE.Vector3(prefix==='主卫'?8.6794:4.3398,1.15,(prefix==='主卫'?1.12075:1.03743)+offset));
  }
 }
 return doors;
}
export function doorIsOpen(door){const e=door.entries[0];return distance(e.o.matrix,e.on)<distance(e.o.matrix,e.off)}
export function beginDoorMotion(door,open=!(door.animation?.open??doorIsOpen(door))){
 door.animation={open,elapsed:0,tracks:door.entries.map(e=>{const to=open?e.on:e.off;const p=new THREE.Vector3(),q=new THREE.Quaternion(),s=new THREE.Vector3();to.decompose(p,q,s);return{e,p,q,s,startP:e.o.position.clone(),startQ:e.o.quaternion.clone(),startS:e.o.scale.clone()}})};
}
export function stepDoorMotion(door,dt){const a=door.animation;if(!a)return false;a.elapsed+=dt;const t=Math.min(1,a.elapsed/.45),ease=t*t*(3-2*t);for(const r of a.tracks){const o=r.e.o;o.position.lerpVectors(r.startP,r.p,ease);o.quaternion.slerpQuaternions(r.startQ,r.q,ease);o.scale.lerpVectors(r.startS,r.s,ease);o.updateMatrix();if(t===1){o.matrix.copy(a.open?r.e.on:r.e.off);o.matrix.decompose(o.position,o.quaternion,o.scale);o.visible=r.e.pair[a.open?'on':'off'].visible}}if(t===1)door.animation=null;return true;}
export function installDoorControls({model,camera,canvas,doors,onChange}){
 const handles=doors.flatMap(d=>d.handles),ray=new THREE.Raycaster(),world=new THREE.Vector3(),projected=new THREE.Vector3();let down=null,hover=null,lastHover=0;
 const hint=document.createElement('button');hint.className='door-action';hint.hidden=true;hint.type='button';hint.onclick=()=>{if(hover)toggle(hover.door)};document.body.append(hint);
 const meshes=[];model.traverse(o=>{if(o.isMesh)meshes.push(o)});
 function pick(x,y){model.updateMatrixWorld(true);const r=canvas.getBoundingClientRect();let best=null,score=Infinity;
  for(const h of handles){if(!visible(h.o))continue;h.o.localToWorld(world.copy(h.local));if(world.distanceTo(camera.position)>3.1)continue;projected.copy(world).project(camera);if(projected.z>1||projected.z< -1)continue;const px=r.left+(projected.x+1)*r.width/2,py=r.top+(1-projected.y)*r.height/2,d=Math.hypot(x-px,y-py);if(d>28||d>=score)continue;
   const dist=world.distanceTo(camera.position);ray.set(camera.position,world.clone().sub(camera.position).normalize());ray.far=Math.max(0,dist-.12);const blocked=ray.intersectObjects(meshes.filter(visible),false);if(blocked.length)continue;best={...h,px,py};score=d;
  }return best;
 }
 function show(hit){hover=hit;canvas.style.cursor=hit?'pointer':'';hint.hidden=!hit;if(hit){hint.textContent=(hit.door.animation?.open??doorIsOpen(hit.door))?'关闭 · '+hit.door.name:'打开 · '+hit.door.name;hint.style.left=Math.max(85,Math.min(innerWidth-85,hit.px))+'px';hint.style.top=Math.max(65,hit.py-38)+'px'}}
 function toggle(door){beginDoorMotion(door);show(null)}
 canvas.addEventListener('pointerdown',e=>{if(e.button!==0)return;down={id:e.pointerId,x:e.clientX,y:e.clientY,time:performance.now(),moved:false}});
 canvas.addEventListener('pointermove',e=>{if(down&&e.pointerId===down.id){if(Math.hypot(e.clientX-down.x,e.clientY-down.y)>6)down.moved=true;show(null);return}if(performance.now()-lastHover<80)return;lastHover=performance.now();show(pick(e.clientX,e.clientY))});
 canvas.addEventListener('pointerup',e=>{if(!down||e.pointerId!==down.id)return;const press=down;down=null;if(press.moved||performance.now()-press.time>700)return;const hit=pick(e.clientX,e.clientY);if(hit)toggle(hit.door)});
 const cancel=()=>{down=null;show(null)};canvas.addEventListener('pointercancel',cancel);canvas.addEventListener('lostpointercapture',()=>{down=null});window.addEventListener('blur',cancel);
 canvas.addEventListener('keydown',e=>{if(!['KeyE','Enter'].includes(e.code)||e.repeat)return;const r=canvas.getBoundingClientRect(),hit=hover||pick(r.left+r.width/2,r.top+r.height/2);if(hit){e.preventDefault();toggle(hit.door)}});
 return{doors,cancel(key){cancel();for(const d of doors)if(!key||d.key===key)d.animation=null},tick(dt){let changed=false,finished=false;for(const d of doors){const active=!!d.animation;if(stepDoorMotion(d,dt)){changed=true;if(active&&!d.animation)finished=true;else if(d.animation&&!d.animation.invalidated){d.animation.invalidated=true;onChange(false)}}}if(changed){model.updateMatrixWorld(true);if(finished)onChange(true)}if(hover&&(performance.now()-lastHover>1000))show(null)}};
}
