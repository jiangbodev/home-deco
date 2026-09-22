import * as THREE from 'three';
// Millimetre-scale midrib and lateral veins on the seven authored indoor leaves.
// Coordinates follow each leaf's existing stem direction; no new texture request.
export function prepareLeafFinish(group){
 group.traverse(o=>{
  if(!o.isMesh||Array.isArray(o.material)||o.material.userData.source_material_id!==341||o.material.userData.leafFinish)return;
  const g=o.geometry,p=g.getAttribute('position');g.computeBoundingBox();const b=g.boundingBox,c=b.getCenter(new THREE.Vector3());
  const across=new THREE.Vector2(-c.y,c.x).normalize();let width=0;
  for(let i=0;i<p.count;i++)width=Math.max(width,Math.abs((p.getX(i)-c.x)*across.x+(p.getY(i)-c.y)*across.y));
  const uv=new Float32Array(p.count*2);
  for(let i=0;i<p.count;i++){uv[i*2]=((p.getX(i)-c.x)*across.x+(p.getY(i)-c.y)*across.y)/width;uv[i*2+1]=(b.max.z-p.getZ(i))/(b.max.z-b.min.z);}
  g.setAttribute('leafCoord',new THREE.BufferAttribute(uv,2));
  const original=o.material,m=original.clone(),compile=original.onBeforeCompile,key=original.customProgramCacheKey();m.userData.leafFinish=true;
  m.onBeforeCompile=shader=>{
   compile.call(original,shader);
   shader.vertexShader='attribute vec2 leafCoord; varying vec2 leafSurface;\n'+shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nleafSurface=leafCoord;');
   shader.fragmentShader='varying vec2 leafSurface;\n'+shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
    float leafX=abs(leafSurface.x),leafY=leafSurface.y;
    float mid=1.0-smoothstep(.014,.035+fwidth(leafSurface.x),leafX);
    float ribs=abs(fract((leafY-leafX*.17)*11.0)-.5);
    float lateral=(1.0-smoothstep(.018,.06+fwidth(leafY)*11.0,ribs))*(1.0-smoothstep(.65,.98,leafX));
    float vein=max(mid,lateral*.40)*smoothstep(.03,.12,leafY)*(1.0-smoothstep(.88,1.0,leafY));
    diffuseColor.rgb*=mix(vec3(.91,.96,.91),vec3(1.20,1.12,.94),vein);
    diffuseColor.rgb*=1.0-.055*leafX+.025*sin(leafY*18.0+leafX*5.0);
   `);
  };m.customProgramCacheKey=()=>key+'-leaf-veins-v1';o.material=m;
 });
}
