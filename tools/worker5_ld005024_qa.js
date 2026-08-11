const { chromium } = require('playwright');
const fs = require('fs');

const slug = 'outreach/LD-005-024-anita-szepsegszalon-zuglo';
const base = `http://127.0.0.1:8765/${slug}/`;
const report = { lead_id: 'LD-005-024', checks: [], errors: [], result: 'FAIL' };
const add = (name, pass, detail = '') => report.checks.push({ name, pass, detail });

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    for (const vp of [
      { name: 'desktop', width: 1440, height: 900 },
      { name: 'mobile', width: 390, height: 844 },
    ]) {
      const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
      const page = await context.newPage();
      const consoleErrors = [];
      const pageErrors = [];
      const failedRequests = [];
      page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
      page.on('pageerror', e => pageErrors.push(String(e)));
      page.on('requestfailed', r => failedRequests.push(r.url()));

      const res = await page.goto(base, { waitUntil: 'networkidle' });
      add(`${vp.name}.http2xx`, !!res && res.status() >= 200 && res.status() < 300, String(res?.status()));
      add(`${vp.name}.console`, consoleErrors.length === 0, consoleErrors.join('|'));
      add(`${vp.name}.pageerror`, pageErrors.length === 0, pageErrors.join('|'));
      add(`${vp.name}.requests`, failedRequests.length === 0, failedRequests.join('|'));
      add(`${vp.name}.viewport`, await page.locator('meta[name="viewport"]').count() === 1);
      add(`${vp.name}.overflow`, await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), await page.evaluate(() => `${document.documentElement.scrollWidth}/${innerWidth}`));
      add(`${vp.name}.placeholders`, !(await page.evaluate(() => /lorem ipsum|\bTODO\b|PLACEHOLDER/i.test(document.body.innerText))));

      if (vp.name === 'mobile') {
        await page.locator('.menu').click();
        add('mobile.menu_open', await page.locator('.links').evaluate(el => el.classList.contains('open')));
        await page.locator('.links a[href="#szolgaltatasok"]').click();
        add('mobile.menu_close', !(await page.locator('.links').evaluate(el => el.classList.contains('open'))));
      }

      await page.locator('.hero a[href="#foglalas"]').click();
      await page.locator('.step[data-step="1"] .next').click();
      add(`${vp.name}.booking_validation`, await page.locator('#e1').evaluate(el => el.classList.contains('show')));
      await page.locator('.choice').first().click();
      await page.locator('.step[data-step="1"] .next').click();
      await page.locator('.date').first().click();
      await page.locator('.slot').first().click();
      await page.locator('.step[data-step="2"] .next').click();
      await page.fill('#name', 'Teszt Anna');
      await page.fill('#email', 'anna@example.com');
      await page.locator('.step[data-step="3"] .next').click();
      add(`${vp.name}.booking_summary`, await page.locator('.step[data-step="4"]').evaluate(el => el.classList.contains('active')));
      await page.locator('#finish').click();
      add(`${vp.name}.booking_success`, await page.locator('.step[data-step="5"]').evaluate(el => el.classList.contains('active')));

      await page.goto(base, { waitUntil: 'networkidle' });
      await page.screenshot({ path: `${slug}/${vp.name}-full.png`, fullPage: true });
      await page.screenshot({ path: `${slug}/preview-${vp.name}.png`, fullPage: false });
      await context.close();
    }

    const reducedContext = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    const reducedPage = await reducedContext.newPage();
    await reducedPage.goto(base, { waitUntil: 'networkidle' });
    const hidden = await reducedPage.evaluate(() => [...document.querySelectorAll('[data-reveal]')].some(x => getComputedStyle(x).opacity === '0'));
    add('reduced_motion', !hidden);
    await reducedContext.close();

    report.result = report.checks.every(x => x.pass) ? 'PASS' : 'FAIL';
  } catch (e) {
    report.errors.push(String(e));
  } finally {
    await browser.close();
    fs.writeFileSync('worker5-ld005024-qa-report.json', JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
    if (report.result !== 'PASS') process.exit(1);
  }
})();
