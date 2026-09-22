// Development-only, reproducible review camera and movement sample. Never loaded in production.
export function installDiningReview({camera,renderer,setAngles}) {
  if(new URLSearchParams(location.search).get('study')!=='dining')return;
  const origin=[8.65,1.4,5.18],yaw=Math.atan2(8.65-5.7,5.18-4.73),pitch=-.025;
  const restore=()=>{camera.position.set(...origin);setAngles(yaw,pitch)};
  restore();
  const readyMs=Math.round(performance.now());
  const box=document.createElement('aside');box.id='dining-review';box.style='position:fixed;top:70px;left:20px;z-index:100;background:#fff;padding:8px;color:#222;font:12px monospace';
  const reset=document.createElement('button');reset.textContent='餐厅对比机位';reset.onclick=restore;
  const sample=document.createElement('button');sample.textContent='测量餐厅移动';
  const reverse=document.createElement('button');reverse.textContent='柜面与桌椅';reverse.onclick=()=>{camera.position.set(7.65,1.4,3.75);setAngles(Math.atan2(7.65-6.4,3.75-6.1),-.18)};
  const detail=document.createElement('button');detail.textContent='椅背与支撑';detail.onclick=()=>{camera.position.set(7.85,1.05,3.98);setAngles(Math.atan2(7.85-6.4,3.98-4.45),-.3)};
  const output=document.createElement('output');output.id='dining-review-result';const load=document.createElement('output');load.id='dining-load-result';load.textContent=JSON.stringify({localReadyMs:readyMs});load.style.display='block';box.append(reset,reverse,detail,sample,output,load);document.body.append(box);
  sample.onclick=()=>{restore();sample.disabled=true;let last=0,start=0;const times=[];
    function tick(t){if(!start)start=t;const s=(t-start)/1000;if(last&&s>.5)times.push(t-last);last=t;
      camera.position.x=origin[0]-.28*Math.sin(s*.8);camera.position.z=origin[2]+.12*Math.sin(s);setAngles(yaw+.14*Math.sin(s*.9),pitch);
      if(s<6)requestAnimationFrame(tick);else{times.sort((a,b)=>a-b);output.textContent=JSON.stringify({frames:times.length,medianMs:times[Math.floor(times.length*.5)],p95Ms:times[Math.floor(times.length*.95)],drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,width:renderer.domElement.width,height:renderer.domElement.height});restore();sample.disabled=false;}
    }requestAnimationFrame(tick);
  };
}
