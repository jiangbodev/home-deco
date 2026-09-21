// The denominator is fixed by the initial manifest, not a growing request count.
// Model streams report bytes; shared images count once when Three finishes loading them.
export function createLoadingProgress(onChange){
 const expected=new Map(),received=new Map(),failed=new Set();
 let phase='manifest',total=0;
 function emit(){const loaded=[...received.values()].reduce((sum,n)=>sum+n,0);onChange({phase,loaded,total,percent:total?Math.floor(100*loaded/total):0})}
 function name(url){return new URL(url,'https://loading.invalid/').pathname.split('/').pop()}
 function record(url,bytes){
  if(phase!=='download')return;
  const file=name(url),size=expected.get(file);if(size===undefined||failed.has(file))return;
  received.set(file,Math.max(received.get(file)||0,Math.min(size,Math.max(0,bytes))));emit();
 }
 return {
  plan(manifest,keys){
   expected.clear();received.clear();failed.clear();
   for(const key of keys){const module=manifest.modules[key];if(!module)continue;expected.set(module.file,module.bytes);for(const file of module.textures)expected.set(file,manifest.textures[file])}
   total=[...expected.values()].reduce((sum,n)=>sum+n,0);phase='download';emit();
  },
  bytes:record,
  resourceDone(url){const size=expected.get(name(url));if(size!==undefined)record(url,size)},
  resourceFailed(url){failed.add(name(url))},
  preparing(){phase='prepare';emit()},
  complete(){phase='ready';emit()},
 };
}
