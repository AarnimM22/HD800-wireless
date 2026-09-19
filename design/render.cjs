const fs=require('fs');
const path=require('path');
const sharp=require('C:/Users/aarni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
(async()=>{for(const f of fs.readdirSync(path.join(__dirname,'svg')).filter(x=>x.endsWith('.svg'))){
 await sharp(path.join(__dirname,'svg',f),{density:120,limitInputPixels:false}).flatten({background:'#fff'}).resize({width:2400}).png().toFile(path.join(__dirname,f.replace('.svg','.png')));
}console.log('Rendered 7 sheets');})();
