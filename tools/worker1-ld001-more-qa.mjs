import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const leads = [
  ['LD-001-010-szereto-martina-fodrasz','Szerető Martina Fodrász'],
  ['LD-001-013-szabo-adrienn-rose','Szabó Adrienn Fodrász'],
  ['LD-001-015-marcos-barbershop',"Marco's Barbershop"],
  ['LD-001-019-pipacs-szepsegsziget','Pipacs Szépségsziget'],
  ['LD-001-020-hazuga-alexandra-fodrasz','Hazuga Alexandra Fodrász']
];
const base='http://127.0.0.1:8765/outreach/';
const browser=await chromium.launch({headless:true});
const results=[];

for (const [slug,name] of leads) {
  const lead={slug,name,pass:true,viewports:{}};
  const qaDir=path.join('qa','worker1',slug); fs.mkdirSync(qaDir,{recursive:true});
  for (const [label,viewport] of [['desktop',{width:1440,height:900}],['mobile',{width:390,height:844}]]) {
    const page=await browser.newPage({viewport});
    const consoleErrors=[],pageErrors=[],failedRequests=[];
    page.on('console',m=>{if(m.type()==='error') consoleErrors.push(m.text())});
    page.on('pageerror',e=>pageErrors.push(String(e)));
    page.on('requestfailed',r=>failedRequests.push(r.url()));
    const resp=await page.goto(base+slug+'/',{waitUntil:'networkidle',timeout:30000});
    const status=resp?.status()??0;
    const metrics=await page.evaluate(()=>{
      const body=document.body.innerText;
      const heads=[...document.querySelectorAll('h1,h2,h3')].map(e=>{const r=e.getBoundingClientRect();return {text:e.textContent?.trim(),left:r.left,right:r.right}}).filter(x=>x.left<-1||x.right>innerWidth+1);
      const zero=[...document.querySelectorAll('main > section')].map(e=>{const r=e.getBoundingClientRect();return {id:e.id,w:r.width,h:r.height}}).filter(x=>x.w<1||x.h<1);
      return {viewportMeta:!!document.querySelector('meta[name="viewport"]'),overflow:document.documentElement.scrollWidth>innerWidth+1,badText:/lorem ipsum|\bTODO\b|PLACEHOLDER/i.test(body),headingOverflow:heads,zeroSections:zero,demoMarker:/koncepciódemó|bemutató célból/i.test(body)};
    });
    let menuOk=true;
    if(label==='mobile'){
      const menu=page.locator('[data-menu]');
      const nav=page.locator('[data-nav]');
      if(await menu.count()){
        await menu.click();
        const opened=await nav.evaluate(e=>e.classList.contains('open'));
        const first=nav.locator('a').first();
        if(await first.count()) await first.click();
        const closed=!(await nav.evaluate(e=>e.classList.contains('open')));
        menuOk=opened&&closed;
      }
    }
    let formOk=true, emptyErrorOk=true, successOk=true;
    const form=page.locator('[data-demo-form]');
    if(await form.count()){
      await form.locator('button[type="submit"]').click();
      emptyErrorOk=await form.locator('[data-error]').isVisible();
      const req=form.locator('[required]');
      for(let i=0;i<await req.count();i++){
        const el=req.nth(i); const tag=await el.evaluate(e=>e.tagName.toLowerCase()); const type=await el.getAttribute('type');
        if(tag==='select') await el.selectOption({index:1});
        else if(type==='date') await el.fill('2026-08-20');
        else await el.fill(i%2===0?'QA Teszt':'qa@example.hu');
      }
      await form.locator('button[type="submit"]').click();
      successOk=await form.locator('[data-success]').isVisible();
      formOk=emptyErrorOk&&successOk;
    }
    await page.evaluate(()=>scrollTo(0,0)); await page.waitForTimeout(120);
    await page.screenshot({path:path.join(qaDir,`${label}-viewport.png`),fullPage:false});
    await page.screenshot({path:path.join(qaDir,`${label}-full.png`),fullPage:true});
    fs.copyFileSync(path.join(qaDir,`${label}-viewport.png`),path.join('outreach',slug,`preview-${label}.png`));
    const pass=status>=200&&status<300&&metrics.viewportMeta&&!metrics.overflow&&!metrics.badText&&!metrics.headingOverflow.length&&!metrics.zeroSections.length&&metrics.demoMarker&&!consoleErrors.length&&!pageErrors.length&&!failedRequests.length&&menuOk&&formOk;
    lead.viewports[label]={status,...metrics,consoleErrors,pageErrors,failedRequests,menuOk,emptyErrorOk,successOk,pass};
    if(!pass) lead.pass=false;
    await page.close();
  }
  results.push(lead);
}
await browser.close();
const report={generated_at:new Date().toISOString(),worker:'MUNKÁS_1',passed:results.filter(x=>x.pass).length,failed:results.filter(x=>!x.pass).length,results};
fs.writeFileSync('worker1-ld001-more-qa.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
if(report.failed) process.exit(1);
