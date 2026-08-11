import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
const slug='LD-001-022-lauras-beauty-bar';
const booking='https://bwnet.hu/partner/cziszerlaura';
const browser=await chromium.launch({headless:true});
const result={slug,pass:true,viewports:{}};
for(const [label,viewport] of [['desktop',{width:1440,height:900}],['mobile',{width:390,height:844}]]){
 const page=await browser.newPage({viewport});
 const consoleErrors=[],pageErrors=[],failedRequests=[];
 page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())});
 page.on('pageerror',e=>pageErrors.push(String(e)));
 page.on('requestfailed',r=>failedRequests.push(r.url()));
 const resp=await page.goto(`http://127.0.0.1:8768/outreach/${slug}/`,{waitUntil:'networkidle',timeout:30000});
 const metrics=await page.evaluate(()=>{
  const body=document.body.innerText;
  const heads=[...document.querySelectorAll('h1,h2,h3')].map(e=>{const r=e.getBoundingClientRect();return {text:e.textContent?.trim(),left:r.left,right:r.right}}).filter(x=>x.left<-1||x.right>innerWidth+1);
  const zero=[...document.querySelectorAll('main > section')].map(e=>{const r=e.getBoundingClientRect();return {id:e.id,w:r.width,h:r.height}}).filter(x=>x.w<1||x.h<1);
  return {viewportMeta:!!document.querySelector('meta[name="viewport"]'),overflow:document.documentElement.scrollWidth>innerWidth+1,badText:/lorem ipsum|\bTODO\b|PLACEHOLDER/i.test(body),headingOverflow:heads,zeroSections:zero,demoMarker:/Koncepciódemó|bemutató célból/i.test(body)};
 });
 let menuOk=true;
 if(label==='mobile'){
  const menu=page.locator('[data-menu]'),nav=page.locator('[data-nav]');await menu.click();const opened=await nav.evaluate(e=>e.classList.contains('open'));await nav.locator('a').first().click();const closed=!(await nav.evaluate(e=>e.classList.contains('open')));menuOk=opened&&closed;
 }
 const links=page.locator('[data-booking-link]');
 const linkCount=await links.count(); let bookingLinksOk=linkCount>=2;
 for(let i=0;i<linkCount;i++){if(await links.nth(i).getAttribute('href')!==booking)bookingLinksOk=false}
 await page.evaluate(()=>scrollTo(0,0));await page.waitForTimeout(150);
 const dir=path.join('qa','worker1',slug);fs.mkdirSync(dir,{recursive:true});
 await page.screenshot({path:path.join(dir,`${label}-viewport.png`),fullPage:false});await page.screenshot({path:path.join(dir,`${label}-full.png`),fullPage:true});
 fs.copyFileSync(path.join(dir,`${label}-viewport.png`),path.join('outreach',slug,`preview-${label}.png`));
 const pass=(resp?.status()??0)>=200&&(resp?.status()??0)<300&&metrics.viewportMeta&&!metrics.overflow&&!metrics.badText&&!metrics.headingOverflow.length&&!metrics.zeroSections.length&&metrics.demoMarker&&!consoleErrors.length&&!pageErrors.length&&!failedRequests.length&&menuOk&&bookingLinksOk;
 result.viewports[label]={status:resp?.status()??0,...metrics,consoleErrors,pageErrors,failedRequests,menuOk,bookingLinksOk,bookingLinkCount:linkCount,pass};if(!pass)result.pass=false;await page.close();
}
await browser.close();fs.writeFileSync('worker1-laura-qa.json',JSON.stringify({generated_at:new Date().toISOString(),worker:'MUNKÁS_1',result},null,2));console.log(JSON.stringify(result,null,2));if(!result.pass)process.exit(1);
