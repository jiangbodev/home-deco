import assert from 'node:assert/strict';
import * as THREE from 'three';
import {createMirrors} from '../src/mirrors.js';
const scene=new THREE.Scene(),model=new THREE.Group();scene.add(model);
const main=new THREE.Mesh(new THREE.PlaneGeometry(.84,1.05),new THREE.MeshStandardMaterial());main.name='主卫镜面示意';main.position.set(8.178,1.81,2.535);main.rotation.y=Math.PI/2;model.add(main);
const outer=new THREE.Mesh(new THREE.CircleGeometry(.45,24),new THREE.MeshStandardMaterial());outer.name='外置台盆镜面示意';outer.position.set(4.54,1.73,4.7575);outer.rotation.y=Math.PI;model.add(outer);
const camera=new THREE.PerspectiveCamera(65,1.2,.035,90);const mirrors=createMirrors(scene,model,camera);
function look(pos,target,quality='high'){camera.position.set(...pos);camera.lookAt(...target);mirrors.update(quality);return scene.children.filter(o=>o.isReflector&&o.visible)}
assert.equal(look([10.1,1.4,2.5],[8.178,1.8,2.535]).length,1);assert.equal(main.visible,false);assert.equal(outer.visible,true);
assert.equal(look([10.1,1.4,2.5],[8.178,1.8,2.535],'low').length,0);assert.equal(main.visible,true);
assert.equal(look([10.1,1.4,2.5],[8.178,1.8,2.535],'auto').length,0,'Automatic prioritizes frame rate');
assert.equal(look([4.54,1.4,3.8],[4.54,1.73,4.7575]).length,1);assert.equal(outer.visible,false);assert.equal(main.visible,true);
assert.equal(look([10.1,1.4,2.5],[8.178,1.8,2.535],'auto').length,0,'Automatic prioritizes frame rate');
assert.equal(look([4.54,1.4,5.4],[4.54,1.73,4.7575]).length,0,'Back of mirror must not render');
assert.equal(look([14,1.4,2.5],[8.178,1.8,2.535]).length,0,'Distant mirror uses fallback');
model.visible=false;assert.equal(look([10.1,1.4,2.5],[8.178,1.8,2.535]).length,0);model.visible=true;
for(const source of [main,outer]){const mirror=scene.children.find(o=>o.name==='Planar '+source.name);scene.updateMatrixWorld(true);const a=new THREE.Box3().setFromObject(source),b=new THREE.Box3().setFromObject(mirror);assert(a.min.distanceTo(b.min)<1e-5&&a.max.distanceTo(b.max)<1e-5,'Mirror outline changed');}
const mobileScene=new THREE.Scene();const lightweight=createMirrors(mobileScene,model,camera,{coarse:true});lightweight.update();assert.equal(mobileScene.children.length,0,'Touch fallback must not allocate reflection targets');
console.log('Mirror visibility, near/front selection, low/touch fallback and outline preservation passed.');
