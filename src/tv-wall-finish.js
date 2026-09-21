// The dining TV backdrop spans separate meshes and separate baked charts.
// Give only its coplanar room-facing surface one ivory finish and continuous PBR
// illumination. Keep the underside, arch reveal and other rooms' baked lighting.
const receivers=new Set(['玄关前拱框','玄关共用背墙','玄关餐桌连接侧体','过道玄关连续低顶']);
const patched=new WeakSet();
export function prepareTVWall(group){
 group.traverse(o=>{
  if(!o.isMesh||patched.has(o)||!receivers.has(o.userData.source_name||o.name))return;
  patched.add(o);
  const multi=Array.isArray(o.material);
  o.material=(multi?o.material:[o.material]).map(original=>{
   const m=original.clone(),previous=original.onBeforeCompile,key=original.customProgramCacheKey();
   m.onBeforeCompile=(shader,...args)=>{
    previous.call(m,shader,...args);
    const varyings='varying vec3 tvWallPosition;\n';
    shader.vertexShader=varyings+shader.vertexShader.replace('#include <worldpos_vertex>',`#include <worldpos_vertex>
     tvWallPosition=(modelMatrix*vec4(transformed,1.0)).xyz;
`);
    shader.fragmentShader=varyings+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
     float tvWallFace=step(0.999,abs(normalize(cross(dFdx(tvWallPosition),dFdy(tvWallPosition))).x))*step(5.53,tvWallPosition.x)*step(tvWallPosition.x,5.55)*step(4.27,tvWallPosition.z)*step(tvWallPosition.z,5.21);
     diffuseColor.rgb=mix(diffuseColor.rgb,vec3(0.84,0.825,0.79),tvWallFace);`);
    shader.fragmentShader=shader.fragmentShader.replace('#include <lights_physical_fragment>',`normal=normalize(mix(normal,mat3(viewMatrix)*vec3(1.0,0.0,0.0),tvWallFace));\n     #include <lights_physical_fragment>`);
    // Save the physically lit diffuse before the contact/lightmap additions.
    shader.fragmentShader=shader.fragmentShader.replace('#include <aomap_fragment>',`vec3 tvWallDiffuse=reflectedLight.directDiffuse+reflectedLight.indirectDiffuse;
     #include <aomap_fragment>`);
    shader.fragmentShader=shader.fragmentShader.replace('vec3 totalSpecular =',`totalDiffuse=mix(totalDiffuse,tvWallDiffuse,tvWallFace);
     vec3 totalSpecular =`);
   };
   m.customProgramCacheKey=()=>key+'|continuous-tv-ivory-v1';return m;
  });if(!multi)o.material=o.material[0];
 });
}
