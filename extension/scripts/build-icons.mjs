// CELIKOM C mark: repo-native vector geometry, rasterized for Chrome's setIcon.
import { deflateSync } from 'node:zlib';
import { mkdir, writeFile } from 'node:fs/promises';
const root = new URL('../assets/icons/', import.meta.url);
const palettes = {gray:['#858b8e','#edf0f1'],green:['#66e0bf','#0b1013']};
function crc(bytes) {let value=0xffffffff;for(const byte of bytes){value^=byte;for(let j=0;j<8;j++)value=(value>>>1)^((value&1)?0xedb88320:0);}return (value^0xffffffff)>>>0;}
function chunk(type,data) {const tag=Buffer.from(type),size=Buffer.alloc(4),checksum=Buffer.alloc(4);size.writeUInt32BE(data.length);checksum.writeUInt32BE(crc(Buffer.concat([tag,data])));return Buffer.concat([size,tag,data,checksum]);}
const rgb = hex => [1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));
function png(size,bg,fg) {
  const rows=Buffer.alloc(size*(size*4+1)),background=rgb(bg),foreground=rgb(fg);
  for(let y=0;y<size;y++)for(let x=0;x<size;x++) {
    const sum=[0,0,0,0];
    for(let sy=0;sy<4;sy++)for(let sx=0;sx<4;sx++) {
      const px=(x+(sx+0.5)/4)*128/size,py=(y+(sy+0.5)/4)*128/size;
      const qx=Math.max(Math.abs(px-64)-40,0),qy=Math.max(Math.abs(py-64)-40,0);
      if(qx*qx+qy*qy>24*24)continue;
      const dx=px-64,dy=py-64,r=Math.hypot(dx,dy),angle=Math.abs(Math.atan2(dy,dx));
      const capX=64+29.5*Math.cos(0.65),capY=29.5*Math.sin(0.65);
      const cap=Math.min(Math.hypot(px-capX,py-64-capY),Math.hypot(px-capX,py-64+capY))<=5.5;
      const color=((r>=24&&r<=35&&angle>=0.65)||cap)?foreground:background;
      for(let c=0;c<3;c++)sum[c]+=color[c];sum[3]++;
    }
    const at=y*(size*4+1)+1+x*4;
    for(let c=0;c<3;c++)rows[at+c]=sum[3]?Math.round(sum[c]/sum[3]):0;
    rows[at+3]=Math.round(sum[3]*255/16);
  }
  const ihdr=Buffer.alloc(13);ihdr.writeUInt32BE(size,0);ihdr.writeUInt32BE(size,4);ihdr[8]=8;ihdr[9]=6;
  return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',ihdr),chunk('IDAT',deflateSync(rows)),chunk('IEND',Buffer.alloc(0))]);
}
export async function buildIcons() {
  await mkdir(root,{recursive:true});
  for(const [name,[bg,fg]] of Object.entries(palettes)) {
    await writeFile(new URL(`${name}-source.svg`,root),`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect width="128" height="128" rx="24" fill="${bg}"/><path d="M87.48 46.15 A29.5 29.5 0 1 0 87.48 81.85" fill="none" stroke="${fg}" stroke-width="11" stroke-linecap="round"/></svg>\n`);
    for(const size of [16,32,48,128])await writeFile(new URL(`${name}-${size}.png`,root),png(size,bg,fg));
  }
}
