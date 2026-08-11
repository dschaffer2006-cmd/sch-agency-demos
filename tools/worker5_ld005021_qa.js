const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const slug='outreach/LD-005-021-unique-salon-barbershop';
const base='http://127.0.0.1:8765/'+slug+'/';
const report={lead_id:'LD-005-021',checks:[],errors:[],result:'FAIL'};
const add=(name,pass,detail='')=>report.checks.push({name,pass,detail});

(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  for(const vp of [{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844}]){
   const context=await browser.newContext({viewport:{width:vp.width,height:vp.height}});
   const page=await context.newPage();
   const consoleErrors=[]; const pageErrors=[]; const failed=[];
   page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())});
   page.on('pageerror',e=>pageErrors.push(String(e)));
   page.on('requestfailed',r=>failed.push(`${r.url()} :: ${r.failure()?.errorText||'failed'}`));
   const res=await page.goto(base,{waitUntil:'networkidle'});
   add(`${vp.name}.http2xx`,!!res&&res.status()>=200&&res.status()<300,String(res?.status()));
   add(`${vp.name}.console_errors`,consoleErrors.length===0,consoleErrors.join(' | '));
   add(`${vp.name}.page_errors`,pageErrors.length===0,pageErrors.join(' | '));
   add(`${vp.name}.failed_requests`,failed.length===0,failed.join(' | '));
   add(`${vp.name}.viewport_meta`,await page.locator('meta[name="viewport"]').count()===1);
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
   add(`${vp.name}.no_horizontal_overflow`,overflow,await page.evaluate(()=>`${document.documentElement.scrollWidth}/${innerWidth}`));
   const bad=await page.evaluate(()=>/lorem ipsum|\bTODO\b|PLACEHOLDER/i.test(document.body.innerText));
   add(`${vp.name}.no_placeholders`,!bad);
   const hiddenMain=await page.evaluate(()=>[...document.querySelectorAll('main section')].some(s=>{const r=s.getBoundingClientRect();return r.width<2||r.height<2}));
   add(`${vp.name}.main_sections_visible`,!hiddenMain);
   const booking=page.locator('a[href="https://unique-salon-and-barbershop.reservio.com/"]');
   add(`${vp.name}.booking_cta_present`,await booking.count()>=2,String(await booking.count()));
   if(vp.name==='mobile'){
    const menu=page.locator('.menu'); await menu.click();
    add('mobile.menu_opens',await page.locator('.navlinks').evaluate(el=>el.classList.contains('open')));
    await page.locator('.navlinks a[href="#szolgaltatasok"]').click();
    add('mobile.menu_closes_after_link',!(await page.locator('.navlinks').evaluate(el=>el.classList.contains('open'))));
   }
   await page.screenshot({path:`${slug}/${vp.name}-full.png`,fullPage:true});
   await page.goto(base,{waitUntil:'networkidle'});
   await page.screenshot({path:`${slug}/preview-${vp.name}.png`,fullPage:false});
   await context.close();
  }
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'}); const page=await context.newPage(); await page.goto(base,{waitUntil:'networkidle'});
  const hidden=await page.evaluate(()=>[...document.querySelectorAll('[data-reveal]')].some(x=>getComputedStyle(x).opacity==='0'));
  add('reduced_motion.content_visible',!hidden); await context.close();
  report.result=report.checks.every(x=>x.pass)?'PASS':'FAIL';
 }catch(e){report.errors.push(String(e));}
 finally{await browser.close();fs.writeFileSync('worker5-ld005021-qa-report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));if(report.result!=='PASS')process.exit(1);}
})();