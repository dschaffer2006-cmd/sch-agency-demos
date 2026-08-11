import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const leads=[
 ['LD-001-006-haj-lak-fodraszat','Haj-Lak Fodrászat'],
 ['LD-001-011-baranyai-szalon','Baranyai Szalon'],
 ['LD-001-016-nagy-szilvia-fodrasz','Nagy Szilvia Fodrász'],
 ['LD-001-017-skin-line-kozmetika','Skin Line Kozmetika Veszprém']
];
const browser=await chromium.launch({headless:true});
const results=[];
for(const [slug,name] of leads){
 const item={slug,name,pass:true,viewports:{}};
 for(const [label,viewport] of [['desktop',{width:1440,height:900}],['mobile',{width:390,height:844}]]){
  const page=await browser.newPage({viewport});
  const errors=[],pageErrors=[],failed=[];
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
  page.on('pageerror',e=>pageErrors.push(String(e)));
  page.on('requestfailed',r=>failed.push(r.url()));
  const resp=await page.goto(`http://127.0.0.1:8766/outreach/${slug}/`,{waitUntil:'networkidle',timeout:30000});
  const metrics=await page.evaluate(()=>({
    viewportMeta:!!document.querySelector('meta[name="viewport"]'),
    overflow:document.documentElement.scrollWidth>innerWidth+1,
    demoMarker:/koncepciódemó|bemutató célból/i.test(document.body.innerText),
    badText:/lorem ipsum|\bTODO\b|PLACEHOLDER/i.test(document.body.innerText)
  }));
  let menuOk=true;
  if(label==='mobile'){
    const menu=page.locator('[data-menu],#menu').first();
    if(await menu.count()){
      await menu.click();
      menuOk=true;
      await page.keyboard.press('Escape').catch(()=>{});
    }
  }
  await page.evaluate(()=>scrollTo(0,0)); await page.waitForTimeout(150);
  const preview=path.join('outreach',slug,`preview-${label}.png`);
  await page.screenshot({path:preview,fullPage:false});
  const pass=(resp?.status()??0)>=200&&(resp?.status()??0)<300&&metrics.viewportMeta&&!metrics.overflow&&metrics.demoMarker&&!metrics.badText&&!errors.length&&!pageErrors.length&&!failed.length&&menuOk;
  item.viewports[label]={status:resp?.status()??0,...metrics,consoleErrors:errors,pageErrors,failedRequests:failed,menuOk,pass};
  if(!pass)item.pass=false;
  await page.close();
 }
 results.push(item);
}
await browser.close();
const report={generated_at:new Date().toISOString(),worker:'MUNKÁS_1',passed:results.filter(x=>x.pass).length,failed:results.filter(x=>!x.pass).length,results};
fs.writeFileSync('worker1-old4-preview-qa.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
if(report.failed)process.exit(1);
