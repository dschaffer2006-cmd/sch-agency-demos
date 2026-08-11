import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const leads = [
  ['LD-001-020-hazuga-alexandra-fodrasz','Hazuga Alexandra Fodrász'],
  ['LD-003-018-pedikur-manikur-szepsegszalon','Pedikűr – Manikűr Szépségszalon'],
  ['LD-004-016-szalai-bettina-kozmetika-sminktetovalas','Szalai Bettina']
];
const base = 'http://127.0.0.1:8765/outreach/';
const liveBase = 'https://dschaffer2006-cmd.github.io/sch-agency-demos/outreach/';
const foreignNames = ['Baranyai Szalon','Dorin Kozmetika','Ditke Szépségpatika','ROA Beauty','Kolibri Szépségszalon'];
const browser = await chromium.launch({headless:true});
const results=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

for (const [slug,name] of leads) {
  const lead={slug,name,viewports:{},live:{},pass:true};
  const qaDir=path.join('qa','worker2',slug); fs.mkdirSync(qaDir,{recursive:true});
  for (const [label,viewport] of [['desktop',{width:1440,height:900}],['mobile',{width:390,height:844}]]) {
    const page=await browser.newPage({viewport});
    const consoleErrors=[],pageErrors=[],failedRequests=[];
    page.on('console',m=>{if(m.type()==='error') consoleErrors.push(m.text())});
    page.on('pageerror',e=>pageErrors.push(String(e)));
    page.on('requestfailed',r=>failedRequests.push(r.url()));
    const resp=await page.goto(base+slug+'/',{waitUntil:'networkidle',timeout:30000});
    const status=resp?.status() ?? 0;
    const metrics=await page.evaluate(({foreignNames})=>{
      const body=document.body.innerText;
      const heads=[...document.querySelectorAll('h1,h2,h3')].map(e=>{const r=e.getBoundingClientRect();return {text:e.textContent.trim(),left:r.left,right:r.right}}).filter(x=>x.left<-1||x.right>innerWidth+1);
      const zero=[...document.querySelectorAll('main > section')].map(e=>{const r=e.getBoundingClientRect();return {id:e.id,w:r.width,h:r.height}}).filter(x=>x.w<1||x.h<1);
      return {viewportMeta:!!document.querySelector('meta[name="viewport"]'),overflow:document.documentElement.scrollWidth>innerWidth+1,badText:/lorem ipsum|\bTODO\b|PLACEHOLDER/i.test(body),foreign:foreignNames.filter(n=>body.includes(n)),headingOverflow:heads,zeroSections:zero};
    },{foreignNames});
    let menuOk=true;
    if(label==='mobile'){
      await page.locator('.menu').click();
      const opened=await page.locator('.links').evaluate(e=>e.classList.contains('open'));
      await page.locator('.links a').first().click();
      const closed=!(await page.locator('.links').evaluate(e=>e.classList.contains('open')));
      menuOk=opened&&closed;
    }
    await page.locator('[data-book]:visible').first().click();
    const dialogOpen=await page.locator('#bookDemo').evaluate(e=>e.open);
    await page.locator('.bp.on .opt').first().click();
    await page.locator('.bp.on .opt').first().click();
    await page.locator('.bp.on .opt').first().click();
    await page.locator('#nm').fill('QA Teszt');
    await page.locator('#ct').fill('qa@example.hu');
    await page.locator('[data-contact]').click();
    const bookingSuccess=(await page.locator('.bp.on .success').count())===1;
    await page.locator('[data-close]:visible').last().click();
    for (const y of [0,600,1200,1800,2400,3200,4200,5200]) { await page.evaluate(y=>scrollTo(0,y),y); await page.waitForTimeout(60); }
    await page.evaluate(()=>scrollTo(0,0)); await page.waitForTimeout(120);
    await page.screenshot({path:path.join(qaDir,`${label}-viewport.png`),fullPage:false});
    await page.screenshot({path:path.join(qaDir,`${label}-full.png`),fullPage:true});
    if(label==='mobile') fs.copyFileSync(path.join(qaDir,'mobile-viewport.png'),path.join('outreach',slug,'preview-mobile.png'));
    const pass=status>=200&&status<300&&metrics.viewportMeta&&!metrics.overflow&&!metrics.badText&&!metrics.foreign.length&&!metrics.headingOverflow.length&&!metrics.zeroSections.length&&!consoleErrors.length&&!pageErrors.length&&!failedRequests.length&&menuOk&&dialogOpen&&bookingSuccess;
    lead.viewports[label]={status,...metrics,consoleErrors,pageErrors,failedRequests,menuOk,dialogOpen,bookingSuccess,pass};
    if(!pass) lead.pass=false;
    await page.close();
  }

  const livePage=await browser.newPage({viewport:{width:390,height:844}});
  let liveStatus=0, liveTitle='', liveName=false, liveError='';
  for(let attempt=1;attempt<=6;attempt++){
    try{
      const r=await livePage.goto(liveBase+slug+'/',{waitUntil:'networkidle',timeout:30000});
      liveStatus=r?.status()??0;
      liveTitle=await livePage.title();
      liveName=(await livePage.locator('body').innerText()).toLocaleLowerCase('hu-HU').includes(name.toLocaleLowerCase('hu-HU').split(' – ')[0].split(' — ')[0]);
      if(liveStatus>=200&&liveStatus<300&&liveName) break;
    }catch(e){liveError=String(e)}
    await sleep(5000);
  }
  lead.live={url:liveBase+slug+'/',status:liveStatus,title:liveTitle,namePresent:liveName,error:liveError,pass:liveStatus>=200&&liveStatus<300&&liveName};
  if(!lead.live.pass) lead.pass=false;
  await livePage.close();
  results.push(lead);
}
await browser.close();
const report={generated_at:new Date().toISOString(),worker:'MUNKÁS_2',passed:results.filter(x=>x.pass).length,failed:results.filter(x=>!x.pass).length,results};
fs.writeFileSync('worker2-outreach-demo-qa.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
if(report.failed) process.exit(1);
