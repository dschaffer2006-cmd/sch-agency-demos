const fs = require('fs');
const { chromium } = require('playwright');

const groups = [
  ['Friseur-Seminare', 'https://www.facebook.com/groups/485677074886353/'],
  ['Herczeg Gyongyi Curly', 'https://www.facebook.com/groups/709221493099190/'],
  ['Professional Barbers', 'https://www.facebook.com/groups/ProfessionalBarbers/'],
  ['Hairdressing Advice Tips Education', 'https://www.facebook.com/groups/883708115725466/'],
  ['Barberiu Bendruomene', 'https://www.facebook.com/groups/2854621111360631/'],
  ['Curly Hair Hungary', 'https://www.facebook.com/groups/715444302524194/'],
  ['Hair Style Dye HELP DIY', 'https://www.facebook.com/groups/496078433895888/']
];

function uniq(arr){return [...new Set(arr.filter(Boolean))]}
async function clickTexts(page, texts) {
  for (const t of texts) {
    const loc = page.getByText(t, {exact:false});
    const n = await loc.count().catch(()=>0);
    for (let i=0;i<Math.min(n,3);i++) {
      try { await loc.nth(i).click({timeout:800, force:true}); await page.waitForTimeout(150); } catch {}
    }
  }
}

(async()=>{
  const browser = await chromium.launch({headless:true});
  const out=[];
  fs.mkdirSync('facebook-probe', {recursive:true});
  for (const [name,url] of groups) {
    const ctx = await browser.newContext({viewport:{width:1440,height:1000}, locale:'en-US'});
    const page = await ctx.newPage();
    const row={name,url,finalUrl:null,title:null,publicMarkers:[],privateMarkers:[],articles:0,articleSamples:[],commentMarkers:0,loginMarkers:0,bodySample:null,error:null};
    try {
      await page.goto(url,{waitUntil:'domcontentloaded',timeout:45000});
      await page.waitForTimeout(2500);
      await clickTexts(page,['Allow all cookies','Only allow essential cookies','Decline optional cookies','Not Now','Close','Maybe later']);
      for(let s=0;s<18;s++){
        await clickTexts(page,['See more','View more comments','View previous comments','more comments','previous comments']);
        await page.mouse.wheel(0,2600);
        await page.waitForTimeout(350);
      }
      const data=await page.evaluate(()=>{
        const text=document.body?.innerText||'';
        const arts=[...document.querySelectorAll('[role="article"]')].map(x=>x.innerText.trim()).filter(x=>x.length>20);
        const pub=['Public group','Public','Nyilvános csoport','Nyilvános','Öffentliche Gruppe'].filter(x=>text.includes(x));
        const priv=['Private group','Private','Zárt csoport','Privát csoport','Geschlossene Gruppe','Private Gruppe'].filter(x=>text.includes(x));
        const commentHits=(text.match(/comment|comments|hozzászólás|komment/gi)||[]).length;
        const loginHits=(text.match(/log in|login|bejelentkez|create new account|sign up/gi)||[]).length;
        return {text,arts,pub,priv,commentHits,loginHits,title:document.title};
      });
      row.finalUrl=page.url(); row.title=data.title; row.publicMarkers=data.pub; row.privateMarkers=data.priv;
      row.articles=data.arts.length; row.articleSamples=uniq(data.arts).slice(0,20); row.commentMarkers=data.commentHits; row.loginMarkers=data.loginHits; row.bodySample=data.text.slice(0,12000);
      await page.screenshot({path:`facebook-probe/${name.replace(/[^a-z0-9]+/gi,'-').toLowerCase()}.png`,fullPage:false});
    } catch(e){row.error=String(e); try{await page.screenshot({path:`facebook-probe/${name.replace(/[^a-z0-9]+/gi,'-').toLowerCase()}-error.png`})}catch{}}
    out.push(row); await ctx.close();
  }
  await browser.close();
  fs.writeFileSync('facebook-probe/results.json', JSON.stringify(out,null,2));
  for(const r of out) console.log('FBPROBE',r.name,'articles='+r.articles,'pub='+r.publicMarkers.join('|'),'priv='+r.privateMarkers.join('|'),'comments='+r.commentMarkers,'login='+r.loginMarkers,'final='+r.finalUrl,'err='+(r.error||''));
})();
