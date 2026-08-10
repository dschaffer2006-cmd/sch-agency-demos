import json,pathlib,re,sys
from playwright.sync_api import sync_playwright
root=pathlib.Path('.')
manifest=json.load(open(root/'worker4-batch-manifest.json'))
report=[]
forbidden=['lorem ipsum','todo','image here','photo here','placeholder text']
def num(css):
    m=re.search(r'-?\d+(?:\.\d+)?',str(css)); return float(m.group()) if m else 0.0
def fits(page,w):
    b=page.locator('h1').first.bounding_box(); return bool(b and b['width']>0 and b['height']>0 and b['x']>=-2 and b['x']+b['width']<=w+2)
def effects(page,t):
    fx={}
    if t=='clean-minimal':
        page.wait_for_timeout(1400); fx['text_mask']=page.locator('body').evaluate("e=>e.classList.contains('ready')") and page.locator('h1').evaluate("e=>getComputedStyle(e).backgroundPositionX")!='100%'; fx['svg_draw']=num(page.locator('.svgdraw path').evaluate("e=>getComputedStyle(e).strokeDashoffset"))<5; fx['circular_text']=page.locator('.circlebadge').evaluate("e=>getComputedStyle(e).animationName")=='spin'
    elif t=='soft-luxury':
        page.wait_for_timeout(1200); fx['curtain']=page.locator('body').evaluate("e=>e.classList.contains('ready')") and page.locator('.visual').evaluate("e=>getComputedStyle(e,'::after').transform")!='none'; fx['mesh']=page.locator('.meshfx').evaluate("e=>getComputedStyle(e).animationName")=='meshmove'; fx['gradient_stroke']=num(page.locator('h1 em').evaluate("e=>getComputedStyle(e).webkitTextStrokeWidth"))>0
    elif t=='editorial-serif':
        g=page.locator('#serviceGrid'); a=g.evaluate('e=>e.scrollLeft'); g.evaluate('e=>e.scrollLeft=160'); page.wait_for_timeout(80); b=g.evaluate('e=>e.scrollLeft'); fx['horizontal_scroll']=b>a; m=page.locator('.marquee-track'); a=m.evaluate('e=>getComputedStyle(e).transform'); page.wait_for_timeout(180); b=m.evaluate('e=>getComputedStyle(e).transform'); fx['kinetic_marquee']=a!=b; d=page.locator('#dragCanvas'); bb=d.bounding_box(); page.mouse.move(bb['x']+100,bb['y']+100); page.mouse.down(); page.mouse.move(bb['x']+20,bb['y']+100); page.mouse.up(); fx['drag_pan']=page.locator('#dragPlane').evaluate("e=>e.style.transform") not in ('','translateX(0px)')
    elif t=='nordic-calm':
        c=page.locator('.service-card').first; c.click(); fx['accordion']=c.evaluate("e=>e.classList.contains('open')"); page.locator('#services').scroll_into_view_if_needed(); page.wait_for_timeout(180); fx['color_shift']=page.locator('body').evaluate("e=>e.classList.contains('color-shifted')"); e=page.locator('#eyebrow'); a=e.inner_text(); page.wait_for_timeout(220); b=e.inner_text(); fx['typewriter']=len(b)>=len(a) and len(b)>3
    elif t=='monochrome-chic':
        c=page.locator('.service-card').first; c.click(); fx['flip']=c.evaluate("e=>e.classList.contains('flipped')"); c.hover(position={'x':40,'y':30}); fx['spotlight']=bool(c.evaluate("e=>e.style.getPropertyValue('--mx')")); h=page.locator('h1'); h.hover(); fx['glitch']=h.evaluate("e=>getComputedStyle(e,'::after').content") not in ('none','normal','')
    elif t=='bold-conversion':
        page.locator('#odo').scroll_into_view_if_needed(); page.wait_for_timeout(650); fx['odometer']=page.locator('#odo').inner_text()=='03'; page.locator('#island').click(); fx['dynamic_island']=page.locator('#island').evaluate("e=>e.classList.contains('expanded')"); page.locator('#burst').click(position={'x':20,'y':15}); page.wait_for_timeout(30); fx['particle_button']=page.locator('.particle').count()>0
    elif t=='split-business':
        page.evaluate('scrollTo(0,700)'); page.wait_for_timeout(180); fx['split_scroll']=page.locator('.hero .copy').evaluate("e=>getComputedStyle(e).transform")!='none'; fx['parallax']=page.locator('.orb').first.evaluate("e=>getComputedStyle(e).transform")!='none'; v=page.locator('#visual'); v.hover(position={'x':100,'y':100}); fx['cursor_reactive']=v.evaluate("e=>getComputedStyle(e).transform")!='none'
    elif t=='modern-grid':
        v=page.locator('#visual'); bb=v.bounding_box(); page.mouse.move(bb['x']+40,bb['y']+40); page.mouse.move(bb['x']+120,bb['y']+120); page.wait_for_timeout(30); fx['image_trail']=page.locator('.trail-dot').count()>0; mg=page.locator('#magGrid'); bb=mg.bounding_box(); page.mouse.move(bb['x']+20,bb['y']+20); page.wait_for_timeout(50); fx['magnetic_grid']=mg.locator('i').first.evaluate("e=>getComputedStyle(e).transform")!='none'; mg.click(position={'x':20,'y':20}); fx['morph']=page.locator('#morph').evaluate("e=>e.classList.contains('open')"); page.locator('#morphClose').click()
    elif t=='card-stack':
        fx['sticky_stack']=page.locator('.service-card').first.evaluate("e=>getComputedStyle(e).position")=='sticky'; c=page.locator('.service-card').first; c.click(); fx['coverflow']=c.evaluate("e=>e.classList.contains('active')"); page.locator('.dock a').first.click(); fx['dock']=page.locator('.dock').evaluate("e=>e.dataset.clicked==='1'")
    elif t=='sticky-story':
        fx['sticky_story']=page.locator('.story-panel').evaluate("e=>getComputedStyle(e).position")=='sticky'; r=page.locator('#range'); r.evaluate("e=>{e.value=75;e.dispatchEvent(new Event('input',{bubbles:true}))}"); fx['before_after']=page.locator('#shade').evaluate("e=>e.style.right")=='25%'; page.evaluate('scrollTo(0,650)'); page.wait_for_timeout(120); fx['scramble_scroll']=page.locator('#scrambleChip').evaluate("e=>e.classList.contains('active')")
    return fx
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    for lead in manifest:
        slug=lead['slug']; url=f'http://127.0.0.1:8765/{slug}/'; out=root/slug; probs=[]; fx={}
        page=browser.new_page(viewport={'width':1440,'height':900}); ce=[]; pe=[]; rf=[]; page.on('console',lambda m,a=ce:a.append(m.text) if m.type=='error' else None); page.on('pageerror',lambda e,a=pe:a.append(str(e))); page.on('requestfailed',lambda r,a=rf:a.append(r.url))
        try:
            resp=page.goto(url,wait_until='networkidle',timeout=30000)
            if not resp or not 200<=resp.status<300: probs.append('desktop.http')
            if ce: probs.append('desktop.console')
            if pe: probs.append('desktop.pageerror')
            if rf: probs.append('desktop.requestfailed')
            if page.locator('meta[name="viewport"]').count()!=1: probs.append('viewport.meta')
            if not page.evaluate('document.documentElement.scrollWidth <= innerWidth'): probs.append('desktop.overflow')
            if not fits(page,1440): probs.append('desktop.headline')
            if not page.evaluate("[...document.querySelectorAll('main section')].every(s=>{let r=s.getBoundingClientRect();return r.width>0&&r.height>0})"): probs.append('desktop.zero-section')
            if any(x in page.locator('body').inner_text().lower() for x in forbidden): probs.append('placeholder')
            fx=effects(page,lead['template'])
            if len(fx)!=3 or not all(fx.values()): probs.append('effects:'+json.dumps(fx))
            page.goto(url,wait_until='networkidle'); page.screenshot(path=str(out/'desktop-viewport.png')); page.screenshot(path=str(out/'desktop-full.png'),full_page=True); page.locator('#contact').scroll_into_view_if_needed(); page.screenshot(path=str(out/'desktop-contact.png'))
        except Exception as e: probs.append('desktop.exception:'+repr(e))
        page.close()
        mp=browser.new_page(viewport={'width':390,'height':844}); ce=[]; pe=[]; rf=[]; mp.on('console',lambda m,a=ce:a.append(m.text) if m.type=='error' else None); mp.on('pageerror',lambda e,a=pe:a.append(str(e))); mp.on('requestfailed',lambda r,a=rf:a.append(r.url))
        try:
            r=mp.goto(url,wait_until='networkidle',timeout=30000)
            if not r or not 200<=r.status<300: probs.append('mobile.http')
            if ce: probs.append('mobile.console')
            if pe: probs.append('mobile.pageerror')
            if rf: probs.append('mobile.requestfailed')
            if not mp.evaluate('document.documentElement.scrollWidth <= innerWidth'): probs.append('mobile.overflow')
            if not fits(mp,390): probs.append('mobile.headline')
            mp.locator('#menu').click();
            if not mp.locator('#nav').evaluate("e=>e.classList.contains('open')"): probs.append('mobile.menu-open')
            mp.screenshot(path=str(out/'mobile-menu-open.png')); mp.locator('#nav a[href="#services"]').click();
            if mp.locator('#nav').evaluate("e=>e.classList.contains('open')"): probs.append('mobile.menu-close')
            mp.goto(url,wait_until='networkidle'); mp.screenshot(path=str(out/'preview-mobile.png')); mp.screenshot(path=str(out/'mobile-full.png'),full_page=True); mp.locator('#contact').scroll_into_view_if_needed(); mp.screenshot(path=str(out/'mobile-contact.png'))
        except Exception as e: probs.append('mobile.exception:'+repr(e))
        mp.close(); rm=browser.new_page(viewport={'width':390,'height':844},reduced_motion='reduce')
        try:
            rm.goto(url,wait_until='networkidle'); readable=rm.evaluate("[...document.querySelectorAll('main h1,main h2,main p,.service-card')].every(e=>{let s=getComputedStyle(e),r=e.getBoundingClientRect();return s.visibility!='hidden'&&Number(s.opacity)>0&&r.height>0})")
            if not readable: probs.append('reduced-motion.readability')
            if not rm.evaluate('document.documentElement.scrollWidth <= innerWidth'): probs.append('reduced-motion.overflow')
        except Exception as e: probs.append('reduced.exception:'+repr(e))
        rm.close(); result='PASS' if not probs else 'FAIL'; report.append({'id':lead['id'],'name':lead['name'],'slug':slug,'template':lead['template'],'effects':fx,'problems':probs,'result':result}); print(lead['id'],result,probs,fx,flush=True)
    browser.close()
(root/'worker4-171-190-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('SUMMARY',len(report),sum(r['result']=='PASS' for r in report),sum(r['result']=='FAIL' for r in report)); sys.exit(1 if any(r['result']=='FAIL' for r in report) else 0)
