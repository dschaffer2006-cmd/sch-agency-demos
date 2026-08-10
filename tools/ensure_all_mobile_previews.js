const fs = require('fs');
const path = require('path');
const cp = require('child_process');
const { chromium } = require('playwright');

const ROOT = process.cwd();
const BASE = 'http://127.0.0.1:8765';
const EXCLUDE = new Set(['.github','tools','node_modules','runs','artifacts','sch-agency-website']);

function validSlug(s) {
  return s && !EXCLUDE.has(s) && !s.startsWith('.') && !s.includes('/');
}
function historicalSlugs() {
  const slugs = new Set();
  let log = '';
  try {
    log = cp.execFileSync('git',['log','--all','--name-only','--pretty=format:','--','*/index.html'],{encoding:'utf8'});
  } catch (_) {}
  for (const raw of log.split(/\r?\n/)) {
    const parts = raw.trim().split('/');
    if (parts.length === 2 && parts[1] === 'index.html' && validSlug(parts[0])) slugs.add(parts[0]);
  }
  for (const entry of fs.readdirSync(ROOT,{withFileTypes:true})) {
    if (entry.isDirectory() && validSlug(entry.name) && fs.existsSync(path.join(ROOT,entry.name,'index.html'))) slugs.add(entry.name);
  }
  const expected = path.join(ROOT,'expected-pages-routes.txt');
  if (fs.existsSync(expected)) {
    for (const raw of fs.readFileSync(expected,'utf8').split(/\r?\n/)) {
      const s = raw.trim().replace(/^\/+|\/+$/g,'');
      if (s && !s.startsWith('#') && validSlug(s)) slugs.add(s);
    }
  }
  return [...slugs].sort();
}

(async () => {
  const slugs = historicalSlugs();
  const missing = slugs.filter(s => fs.existsSync(path.join(ROOT,s,'index.html')) && !fs.existsSync(path.join(ROOT,s,'preview-mobile.png')));
  const report = { total_routes: slugs.length, missing_before: missing.length, generated: [], failed: [] };
  if (!missing.length) {
    fs.writeFileSync('all-preview-generation-report.json', JSON.stringify(report,null,2));
    console.log('All routes already have preview-mobile.png');
    return;
  }
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
  page.setDefaultTimeout(15000);
  for (const slug of missing) {
    const url = `${BASE}/${slug}/`;
    try {
      const response = await page.goto(url,{waitUntil:'domcontentloaded',timeout:20000});
      const status = response ? response.status() : 0;
      if (status < 200 || status >= 300) throw new Error(`HTTP ${status}`);
      await page.waitForTimeout(450);
      const out = path.join(ROOT,slug,'preview-mobile.png');
      await page.screenshot({path:out,fullPage:false,type:'png'});
      report.generated.push({slug,url,path:`${slug}/preview-mobile.png`,status});
      console.log(`PREVIEW PASS ${slug}`);
    } catch (err) {
      report.failed.push({slug,url,error:String(err)});
      console.error(`PREVIEW FAIL ${slug}: ${err}`);
    }
  }
  await browser.close();
  fs.writeFileSync('all-preview-generation-report.json', JSON.stringify(report,null,2));
  if (report.failed.length) process.exitCode = 2;
})();
