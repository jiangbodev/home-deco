export function installFridgeReview({camera,renderer,setAngles}){
 if(new URLSearchParams(location.search).get('study')!=='fridge')return;
 const box=document.createElement('aside');box.style='position:fixed;top:70px;left:20px;background:white;color:black;padding:8px;z-index:100';
 for(const[label,x,y,z,tx,ty,tz]of [['冰箱正面',5.15,1.4,2.98,4.07,1.05,2.98],['冰箱侧面',5.20,1.4,4.25,4.07,1.02,2.98]]){
  const b=document.createElement('button');b.textContent=label;b.onclick=()=>{camera.position.set(x,y,z);setAngles(Math.atan2(x-tx,z-tz),Math.atan2(ty-y,Math.hypot(x-tx,z-tz)))};box.append(b);
 }
 document.body.append(box);box.firstChild.click();
}
