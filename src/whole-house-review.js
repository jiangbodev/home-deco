// Local-only audit cameras and bounded movement sample; excluded by Vite's DEV guard.
export function installWholeHouseReview({camera,renderer,setAngles}){
 if(new URLSearchParams(location.search).get('study')!=='whole-house')return;
 const views=[['客厅全景',8.0,1.4,5.4,12.0,1.1,5.25],['电视柜',12.6,1.4,5.15,10.5,.65,3.8],['玄关木柜',4.6,1.4,6.78,4.95,1.05,5.15],['厨房',5.65,1.4,2.65,6.2,1.05,1.3],['主卧木作',13.5,1.4,3.7,13.0,1.1,1.2],['次卧木柜',1.35,1.4,3.25,2.7,1.25,1.91],['主卫木柜',10.1,1.4,2.5,8.2,1.1,2.25],['次卫百叶',4.9,1.4,2.69,4.75,1.45,.1],['儿童房',3.05,1.4,5.05,1.3,1.4,5.75],['客厅天花',10.8,1.4,5.1,10.8,2.7,5.09],['天花东向',9.5,1.4,5.4,12.6,2.6,5.3],['天花西向',12.6,1.4,5.4,8.7,2.6,5.3]];
 let current=views[0];const go=v=>{current=v;const [label,x,y,z,tx,ty,tz]=v;camera.position.set(x,y,z);setAngles(Math.atan2(x-tx,z-tz),Math.atan2(ty-y,Math.hypot(x-tx,z-tz)))};
 const box=document.createElement('aside');box.id='whole-house-review';box.style='position:fixed;top:65px;left:12px;max-width:550px;z-index:100;background:#ffffffe8;color:#222;padding:6px;font:12px monospace';
 for(const v of views){const b=document.createElement('button');b.textContent=v[0];b.onclick=()=>go(v);box.append(b);}
 const sample=document.createElement('button');sample.textContent='采样当前房间';const output=document.createElement('output');output.style.display='block';output.id='whole-house-result';
 sample.onclick=()=>{sample.disabled=true;output.textContent='';const v=current;const [name,x,y,z,tx,ty,tz]=v,originYaw=Math.atan2(x-tx,z-tz),pitch=Math.atan2(ty-y,Math.hypot(x-tx,z-tz));let last=0,start=0;const times=[];
 function tick(t){if(!start)start=t;const s=(t-start)/1000;if(last&&s>.5)times.push(t-last);last=t;camera.position.x=x+.12*Math.sin(s);camera.position.z=z+.12*Math.sin(s*.8);setAngles(originYaw+.15*Math.sin(s),pitch);if(s<6)requestAnimationFrame(tick);else{times.sort((a,b)=>a-b);output.textContent=JSON.stringify({name,frames:times.length,medianMs:times[Math.floor(times.length*.5)],p95Ms:times[Math.floor(times.length*.95)],drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,width:renderer.domElement.width,height:renderer.domElement.height});go(v);sample.disabled=false;}}requestAnimationFrame(tick);
 };box.append(sample,output);document.body.append(box);go(current);
}
