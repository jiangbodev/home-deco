// Start baseline Vite on 5174 and candidate Vite on 5173. Playwright is a diagnostic-only dependency.
const {chromium}=await import(process.env.HOME_DECO_PLAYWRIGHT||'playwright');
import fs from 'node:fs/promises';
const browser=await chromium.launch({executablePath:process.env.HOME_DECO_CHROME||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
const report=[];
for(const [label,port]of [['before',5174],['after',5173]]){
 const page=await browser.newPage({viewport:{width:1100,height:760},deviceScaleFactor:1});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.route('**/src/main.js*',async route=>{const r=await route.fetch();let body=await r.text();body+='\nwindow.audit={get ready(){return ready},get renderer(){return renderer},get model(){return model},get modules(){return modules},camera,scene,visit,move,keys,get appearance(){return appearance},setYaw(v){yaw=v;camera.rotation.set(0,v,0,"YXZ")}};';await route.fulfill({response:r,body})});
 await page.goto('http://127.0.0.1:'+port,{waitUntil:'domcontentloaded'});
 try{await page.waitForFunction(()=>window.audit?.ready&&window.audit.modules.loaded.length===12,{},{timeout:60000})}catch(e){console.error(label,errors,await page.evaluate(()=>({ready:window.audit?.ready,loaded:window.audit?.modules?.loaded,label:document.querySelector('#load-label')?.textContent,status:document.querySelector('.module-status')?.textContent})));await browser.close();throw e}
 await page.waitForTimeout(1500);
 const gpu=await page.evaluate(()=>{const gl=audit.renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)});
 console.log('Loaded',label);const result={label,gpu,errors,views:[]};
 result.hotspot=await page.evaluate(()=>{
  const moves=[];audit.renderer.setAnimationLoop(null);audit.setYaw(0);audit.keys.add('KeyW');
  for(let i=0;i<150;i++){audit.camera.position.set(11.7,1.5,3.45);const t=performance.now();audit.move(1/60);moves.push(performance.now()-t)}audit.keys.clear();
  const a=moves.slice(30).sort((a,b)=>a-b);return {moveMs:{median:a[60],p95:a[114]},note:'Synchronous CPU-only hotspot probe; not FPS'};
 });
 for(const room of [4,5]){
  const data=await page.evaluate(async room=>{await audit.visit(room);audit.renderer.setAnimationLoop(null);audit.renderer.render(audit.scene,audit.camera);const meshes=[];audit.model.traverse(o=>{if(o.isMesh&&/^(fabric 1|Fur_black|White Fabric)/.test(o.name)){const b=o.geometry.boundingBox;meshes.push({name:o.name,position:o.getWorldPosition(o.position.clone()).toArray(),bounds:b?{min:b.min.toArray(),max:b.max.toArray()}:null})}});return {image:document.querySelector('canvas').toDataURL('image/png'),render:{...audit.renderer.info.render},meshes}},room);
  await fs.writeFile(`qa/${label}-room-${room}.png`,Buffer.from(data.image.split(',')[1],'base64'));delete data.image;result.views.push({room,...data});
 }
 if(label==='after')result.movement=await page.evaluate(()=>{audit.camera.position.set(11.7,1.5,4);audit.setYaw(0);audit.keys.add('KeyW');const start=performance.now();for(let i=0;i<120;i++)audit.move(1/60);audit.keys.clear();return {from:[11.7,1.5,4],to:audit.camera.position.toArray(),msFor120Steps:performance.now()-start}});
 report.push(result);await page.close();
}
await browser.close();await fs.writeFile('qa/browser-report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
