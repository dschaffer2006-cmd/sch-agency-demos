const fs=require('fs'),path=require('path'),{chromium}=require('playwright');
const slugs=["the-eden-hair-salon-pecs","ani-fodraszszalon-pecs","clarity-hajstudio-pecs","hair-and-nails-club-pecs","nowa-salon-pecs","hair-by-flora-onodi-pecs","pacek-barbershop-pecs","hajnalfeny-szepsegkozpont-pecs","lefti-hajstudio-dunaujvaros","wellness-hajstudio-zellei-erzsebet-dunaujvaros","lk-royal-barber-dunaujvaros","masculine-barber-shop-dunaujvaros","gurubi-szalon-dunaujvaros","farosz-szepsegszalon-dunaujvaros","gentlemens-barbershop-dunaujvaros","hajlabor-dunaujvaros","beke-barbershop-dunaujvaros","mens-room-dunaujvaros","barbi-hair-clinic-tatabanya","bella-signora-tatabanya"];
const forbidden=['lorem ipsum','todo','image here','photo here','placeholder'];
async function act(page,effect){
 const e=page.locator(`[data-effect="${effect}"]`).first(); if(!await e.count())return;
 await e.scrollIntoViewIfNeeded(); await page.waitForTimeout(180);
 if(effect==='drag-pan'){const b=await e.boundingBox();if(b){await page.mouse.move(b.x+b.width*.6,b.y+b.height*.5);await page.mouse.down();await page.mouse.move(b.x+b.width*.25,b.y+b.height*.3,{steps:4});await page.mouse.up()}}
 else if(effect==='accordion') await e.locator('button').nth(1).click();
 else if(['flip-card','particle-button','dynamic-island','morph'].includes(effect)) await e.click();
 else if(['spotlight','glitch','cursor-reactive','image-trail','magnetic-grid','dock-nav'].includes(effect)){const b=await e.boundingBox();if(b)await page.mouse.move(b.x+b.width*.55,b.y+b.height*.45);if(effect==='glitch')await e.focus()}
 else if(effect==='coverflow'){await e.evaluate(el=>el.scrollIntoView({block:'center'}));await page.waitForTimeout(120);await e.locator('.next').click({timeout:5000})}
 else if(effect==='cursor-reveal') await e.locator('input').evaluate(el=>{el.value='70';el.dispatchEvent(new Event('input',{bubbles:true}))});
 else if(['sticky-cards','sticky-story'].includes(effect)){await e.evaluate(el=>window.scrollTo(0,el.offsetTop+320));await page.waitForTimeout(160)}
 await page.waitForTimeout(['typewriter','text-scramble','odometer'].includes(effect)?650:180);
}
(async()=>{
 const browser=await chromium.launch({headless:true}),report=[];
 for(const slug of slugs){
  const row={slug,critical:[],effects:[]};
  for(const vp of [{n:'desktop',w:1440,h:900},{n:'mobile',w:390,h:844}]){
   const page=await browser.newPage({viewport:{width:vp.w,height:vp.h}}),ce=[],pe=[],rf=[];
   page.on('console',m=>{if(m.type()==='error')ce.push(m.text())});page.on('pageerror',e=>pe.push(String(e)));page.on('requestfailed',r=>rf.push(r.url()));
   let res;try{res=await page.goto(`http://127.0.0.1:8765/${slug}/`,{waitUntil:'networkidle',timeout:30000})}catch(e){row.critical.push(`${vp.n}: nav ${e.message}`)}
   const m=await page.evaluate(forbidden=>{const h=document.querySelector('h1')?.getBoundingClientRect(),hd=document.querySelector('header')?.getBoundingClientRect(),text=document.body.innerText.toLowerCase();return{sw:document.documentElement.scrollWidth,iw:innerWidth,h:h&&[h.left,h.right],hh:hd?.height||0,viewport:!!document.querySelector('meta[name="viewport"]'),sections:[...document.querySelectorAll('main section')].map(x=>{const r=x.getBoundingClientRect();return[r.width,r.height]}),bad:forbidden.filter(x=>text.includes(x)),effects:[...document.querySelectorAll('[data-effect]')].map(x=>[x.dataset.effect,x.dataset.state]),cta:[...document.querySelectorAll('a.pill')].map(a=>a.getAttribute('href'))}},forbidden);
   if(!res||res.status()<200||res.status()>299)row.critical.push(`${vp.n}: HTTP ${res?.status()||'none'}`);
   if(ce.length)row.critical.push(`${vp.n}: console ${ce.join('|')}`);if(pe.length)row.critical.push(`${vp.n}: pageerror ${pe.join('|')}`);if(rf.length)row.critical.push(`${vp.n}: failed ${rf.join('|')}`);
   if(!m.viewport)row.critical.push(`${vp.n}: viewport missing`);if(m.sw>m.iw+1)row.critical.push(`${vp.n}: overflow ${m.sw}>${m.iw}`);if(!m.h||m.h[0]<0||m.h[1]>m.iw+1)row.critical.push(`${vp.n}: h1 outside`);
   if(m.sections.some(x=>x[0]<=0||x[1]<=0))row.critical.push(`${vp.n}: zero section`);if(m.bad.length)row.critical.push(`${vp.n}: forbidden ${m.bad.join(',')}`);if(m.effects.length!==3)row.critical.push(`${vp.n}: effects ${m.effects.length}`);if(!m.cta.length||m.cta.some(x=>!x||x==='#'))row.critical.push(`${vp.n}: bad CTA`);
   for(const id of ['szolg','motion','kapcsolat']){await page.evaluate(id=>document.getElementById(id).scrollIntoView({block:'start',behavior:'instant'}),id);await page.waitForTimeout(50);const top=await page.locator('#'+id).evaluate(el=>el.getBoundingClientRect().top);if(top<m.hh-4)row.critical.push(`${vp.n}: header overlap ${id}`)}
   if(vp.n==='mobile'){await page.evaluate(()=>scrollTo(0,0));const menu=page.locator('#menu'),nav=page.locator('#nav');await menu.click();if(!await nav.evaluate(el=>el.classList.contains('open')&&getComputedStyle(el).display!=='none'))row.critical.push('mobile: menu open');await nav.locator('a').first().click();if(await nav.evaluate(el=>el.classList.contains('open')))row.critical.push('mobile: menu close')}
   const before=new Map(m.effects);for(const [ef]of m.effects)await act(page,ef);const after=await page.evaluate(()=>[...document.querySelectorAll('[data-effect]')].map(x=>[x.dataset.effect,x.dataset.state]));
   if(vp.n==='desktop'){row.effects=after;for(const [ef,st]of after)if(st===before.get(ef))row.critical.push(`effect no change ${ef}:${st}`)}
   await page.goto(`http://127.0.0.1:8765/${slug}/`,{waitUntil:'domcontentloaded'});await page.screenshot({path:path.join(slug,`preview-${vp.n}.png`),fullPage:false});await page.screenshot({path:path.join(slug,`${vp.n}-full.png`),fullPage:true});await page.close();
  }
  const rp=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});await rp.goto(`http://127.0.0.1:8765/${slug}/`);const rm=await rp.evaluate(()=>({sw:document.documentElement.scrollWidth,iw:innerWidth,hidden:[...document.querySelectorAll('main section')].filter(x=>{const r=x.getBoundingClientRect(),s=getComputedStyle(x);return r.width<=0||r.height<=0||s.display==='none'||s.visibility==='hidden'}).length}));if(rm.sw>rm.iw+1)row.critical.push('reduced: overflow');if(rm.hidden)row.critical.push('reduced: hidden content');await rp.close();
  row.result=row.critical.length?'FAIL':'PASS';report.push(row);console.log(`W5QA ${slug} ${row.result}${row.critical.length?' :: '+row.critical.join(' || '):''}`);
 }
 await browser.close();fs.writeFileSync('worker5-191-210-qa-report.json',JSON.stringify(report,null,2));const bad=report.filter(x=>x.result==='FAIL');console.log(`W5SUMMARY total=${report.length} pass=${report.length-bad.length} fail=${bad.length}`);if(bad.length)process.exitCode=1;
})();
