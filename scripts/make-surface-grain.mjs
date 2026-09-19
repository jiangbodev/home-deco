// Deterministic material data, not a photograph: R=low-frequency variation,
// G=microscopic height, B=roughness variation. Tileable at every octave.
import sharp from 'sharp';import fs from 'node:fs';
const size=256,buf=Buffer.alloc(size*size*3);
function hash(x,y,n){let h=Math.imul(x+17,374761393)^Math.imul(y+31,668265263)^Math.imul(n,1274126177);h=Math.imul(h^(h>>>13),1274126177);return((h^(h>>>16))>>>0)/4294967295}
function noise(x,y,n){const ix=Math.floor(x),iy=Math.floor(y),f=x-ix,g=y-iy,u=f*f*(3-2*f),v=g*g*(3-2*g),a=hash(ix%n,iy%n,n),b=hash((ix+1)%n,iy%n,n),c=hash(ix%n,(iy+1)%n,n),d=hash((ix+1)%n,(iy+1)%n,n);return (a+(b-a)*u)*(1-v)+(c+(d-c)*u)*v}
for(let y=0;y<size;y++)for(let x=0;x<size;x++){
 const n=k=>noise(x/size*k,y/size*k,k),i=(y*size+x)*3;
 buf[i]=Math.round(255*(.55*n(4)+.3*n(8)+.15*n(16)));
 buf[i+1]=Math.round(255*(.5*n(64)+.3*n(128)+.2*n(32)));
 buf[i+2]=Math.round(255*(.65*n(16)+.35*n(64)));
}
fs.mkdirSync('public/assets/surfaces',{recursive:true});await sharp(buf,{raw:{width:size,height:size,channels:3}}).png().toFile('public/assets/surfaces/paint-grain-v1.png');
