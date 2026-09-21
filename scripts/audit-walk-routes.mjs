// Install Playwright outside production dependencies; set PLAYWRIGHT_MODULE if needed.
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'/tmp/home-deco-browser/node_modules/playwright/index.mjs');import fs from'node:fs/promises';import sharp from'sharp';
const output=process.argv[2]||'qa/walk-routes-draft';await fs.mkdir(output,{recursive:true});
const routes=[
{name:'玄关',points:[[4.65,6.55],[4.65,5.9],[5.05,5.65],[5.9,5.3]],targets:[[4.8,5],[4.3,4.85],[5.5,4.75],[5.5,4.75]]},
{name:'客厅',points:[[9.7,5.1],[10.6,5.25],[11.7,5.1],[12.5,5.8]],targets:[[7.9,6.6],[11,6.4],[13,6.3],[11.1,6.5]]},
{name:'餐厅',points:[[9.4,5],[8,5.4],[6.1,5.5],[6.1,4.6]],targets:[[6.5,4.8],[5.55,4.7],[5.55,4.7],[5.4,5.1]]},
{name:'厨房',points:[[6.2,2.65],[6.2,2.2],[6.15,1.6],[6.1,1.2]],targets:[[6.1,.6],[6.65,1.8],[5.65,1.3],[6.1,.5]]},
{name:'主卧',points:[[13.2,4.5],[13.2,3.8],[12.45,2.7],[12.7,1.25]],targets:[[12.1,2.8],[11.4,2.5],[11.2,1.5],[13.7,1.6]]},
{name:'次卧',points:[[3.05,3.7],[2.65,3],[2.55,2.3],[2.4,2.8]],targets:[[1.1,2.4],[1.1,2.4],[1,1.7],[2.1,3.5]]},
{name:'儿童房',points:[[3.1,5.4],[2.25,5.75],[1.2,5.8],[1.1,6.3]],targets:[[1,5.2],[1,5.2],[3.4,5.5],[1.2,4.7]]},
{name:'主卫',points:[[9.6,2.5],[8.95,2.3],[8.9,1.65],[8.2,1.9]],targets:[[8.3,1.1],[8.2,2.65],[8.8,.7],[7.4,1.6]]},
{name:'次卫',points:[[4.75,2],[4.75,1.6],[4.8,1],[4.7,.8]],targets:[[4.9,.6],[4.9,.6],[3.9,.8],[4.8,2.1]]}];
const b=await chromium.launch({executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true}),p=await b.newPage({viewport:{width:960,height:720},deviceScaleFactor:1}),errors=[];p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});await p.route('**/src/main.js*',async r=>{const s=await r.fetch();await r.fulfill({response:s,body:await s.text()+'\nwindow.audit={get ready(){return ready},get model(){return model},get renderer(){return renderer},get modules(){return modules},scene,camera,visit};'})});await p.goto(process.env.AUDIT_URL||'http://127.0.0.1:5173');await p.waitForFunction(()=>window.audit?.ready&&audit.modules.loaded.length===12);await p.waitForTimeout(4500);await p.evaluate(()=>audit.renderer.setAnimationLoop(null));const report=[];
for(const [ri,route]of routes.entries()){
 const panels=[],captures=[];let frames=[];
 for(let i=0;i<route.points.length;i++){
  const pos=route.points[i],target=route.targets[i],prev=route.points[Math.max(0,i-1)],oldTarget=route.targets[Math.max(0,i-1)];
  const r=await p.evaluate(async({pos,target,prev,oldTarget})=>{const times=[];let last=performance.now();for(let k=0;k<45;k++){await new Promise(requestAnimationFrame);let now=performance.now();times.push(now-last);last=now;const t=(k+1)/45;audit.camera.position.set(prev[0]+(pos[0]-prev[0])*t,1.4,prev[1]+(pos[1]-prev[1])*t);audit.camera.lookAt(oldTarget[0]+(target[0]-oldTarget[0])*t,1.3,oldTarget[1]+(target[1]-oldTarget[1])*t);audit.renderer.render(audit.scene,audit.camera)}return{image:document.querySelector('canvas').toDataURL(),times,render:{...audit.renderer.info.render}}},{pos,target,prev,oldTarget});
  frames.push(...r.times);const buf=Buffer.from(r.image.split(',')[1],'base64'),file=`${ri}-${i}.png`;await fs.writeFile(output+'/'+file,buf);panels.push({input:await sharp(buf).resize(480,360).toBuffer(),left:i%2*480,top:Math.floor(i/2)*360});captures.push({file,pos:[pos[0],1.4,pos[1]],target,...r.render});
 }
 frames.sort((a,b)=>a-b);report.push({room:route.name,frames:frames.length,p50:frames[90],p95:frames[171],max:frames.at(-1),captures});await sharp({create:{width:960,height:720,channels:3,background:'#222'}}).composite(panels).jpeg({quality:90}).toFile(output+`/room-${ri}.jpg`);console.log(route.name,report.at(-1).p95);
}
await fs.writeFile(output+'/report.json',JSON.stringify({errors,routes:report},null,2));await b.close();
