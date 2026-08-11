import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
const slug='LD-001-023-lux-barber-shop', booking='https://lux-barber-shop.salonic.hu/';
const browser=await chromium.launch({headless:true});const result={slug,pass:true,viewports:{}};
for(const [label,viewport] of [['desktop',{width:1440,height:900}],['mobile',{width:390,height:844}]]){
 const page=await browser.newPage({viewport});const ce=[],pe=[],fr=[];page.on('console',m=>{if(m.type()==='error')ce.push(m.text())});page.on('pageerror',e=>pe.push(String(e)));page.on('requestfailed',r=>fr.push(r.url()));
 const resp=await page.goto(`http://127.0.0.1:8769/outreach/${slug}/`,{waitUntil:'networkidle',timeout:30000});
 const metrics=await page.evaluate(()=>{const body=document.body.innerText;const hs=[...document.querySelectorAll('h1,h2,h3')].map(e=>{const r=e.getBoundingClientRect();return {t:e.textContent?.trim(),l:r.left,r:r.right}}).filter(x=>x.l<-1||x.r>innerWidth+1);return {viewportMeta:!!document.querySelector('meta[name="viewport"]'),overflow:document.documentElement.scrollWidth>innerWidth+1,badText:/lorem ipsum|\bTODO\b|PLACEHOLDER/i.test(body),headingOverflow:hs,demoMarker:/Koncepciódemó|bemutató célból/i.test(body)}});
 let menuOk=true;if(label==='mobile'){const m=page.locator('[data-menu]'),n=page.locator('[data-nav]');await m.click();const o=await n.evaluate(e=>e.classList.contains('open'));await n.locator('a').first().click();const c=!(await n.evaluate(e=>e.classList.contains('open')));menuOk=o&&c}
 const links=page.locator('[data-booking-link]');const count=await links.count();let bookingLinksOk=count>=3;for(let i=0;i<count;i++){if(await links.nth(i).getAttribute('href')!==booking)bookingLinksOk=false}
 await page.evaluate(()=>scrollTo(0,0));await page.waitForTimeout(120);const dir=path.join('qa','worker1',slug);fs.mkdirSync(dir,{recursive:true});await page.screenshot({path:path.join(dir,`${label}-viewport.png`),fullPage:false});await page.screenshot({path:path.join(dir,`${label}-full.png`),fullPage:true});fs.copyFileSync(path.join(dir,`${label}-viewport.png`),path.join('outreach',slug,`preview-${label}.png`));
 const pass=(resp?.status()??0)>=200&&(resp?.status()??0)<300&&metrics.viewportMeta&&!metrics.overflow&&!metrics.badText&&!metrics.headingOverflow.length&&metrics.demoMarker&&!ce.length&&!pe.length&&!fr.length&&menuOk&&bookingLinksOk;result.viewports[label]={status:resp?.status()??0,...metrics,consoleErrors:ce,pageErrors:pe,failedRequests:fr,menuOk,bookingLinksOk,bookingLinkCount:count,pass};if(!pass)result.pass=false;await page.close();
}
await browser.close();fs.writeFileSync('worker1-lux-qa.json',JSON.stringify({generated_at:new Date().toISOString(),worker:'MUNKÁS_1',result},null,2));console.log(JSON.stringify(result,null,2));if(!result.pass)process.exit(1);
