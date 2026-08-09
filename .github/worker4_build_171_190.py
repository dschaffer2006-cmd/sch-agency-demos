import csv, html, io, json, pathlib, re, unicodedata, urllib.request

SHEET_CSV='https://docs.google.com/spreadsheets/d/10h3Wz2S_2lsnoVtsT8lJy7bFlWas8eV43yM5cugeYKs/export?format=csv&gid=255039092'
PAGES_BASE='https://dschaffer2006-cmd.github.io/sch-agency-demos/'

TEMPLATES=[
 ('clean-minimal','Clean Minimal',['Text Mask Reveal','Scroll SVG Draw','Circular Text Path'],'#f7f5ef','#11110f','#38705b','sans'),
 ('soft-luxury','Soft Luxury',['Curtain Reveal','Mesh Gradient Background','Gradient Stroke Text'],'#f4eee9','#362929','#ae806c','serif'),
 ('editorial-serif','Editorial Serif',['Horizontal Scroll','Kinetic Marquee','Drag-to-Pan Grid'],'#f6f1e8','#171717','#b13f2d','serif'),
 ('nordic-calm','Nordic Calm',['Accordion Image Slider','Scroll Color Shift','Typewriter Effect'],'#f2f4ef','#26332d','#708b78','sans'),
 ('monochrome-chic','Monochrome Chic',['3D Flip Cards','Spotlight Border Cards','Glitch Effect'],'#111111','#f7f7f4','#d9d9d4','sans'),
 ('bold-conversion','Bold Conversion',['Dynamic Island Nav','View Transition Morphing','Magnetic Repel Grid'],'#fff3dd','#1d1a17','#ef6f2e','sans'),
 ('split-business','Split Business',['Split Screen Scroll','Layered Zoom Parallax','Cursor-Reactive Environment'],'#eee9df','#17263a','#b96a4c','sans'),
 ('modern-grid','Modern Grid',['Hover Image Trail','Magnetic Repel Grid','View Transition Morphing'],'#eaf0f4','#12222d','#4a8099','sans'),
 ('card-stack','Card Stack',['Sticky Card Stack','3D Coverflow Carousel','macOS Dock Navigation'],'#ede8f5','#1e1830','#755aa3','sans'),
 ('sticky-story','Sticky Story',['Sticky Stack Narrative','Text Scramble Decode','Cursor Image Reveal'],'#171614','#f2eadb','#c38d58','serif'),
]

def norm(s):
    s=unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower().strip()
    return ' '.join(s.split())

def slugify(s):
    s=unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower()
    s=re.sub(r'[^a-z0-9]+','-',s).strip('-')
    return s[:54].strip('-') or 'vallalkozas'

def esc(s): return html.escape(s or '', quote=True)

def fetch_rows():
    raw=urllib.request.urlopen(SHEET_CSV,timeout=30).read().decode('utf-8-sig')
    rows=list(csv.reader(io.StringIO(raw)))
    headers=rows[0]
    hmap={norm(h):i for i,h in enumerate(headers)}
    def pick(row,*labels):
        for label in labels:
            k=norm(label)
            if k in hmap and hmap[k] < len(row):
                v=row[hmap[k]].strip()
                if v: return v
        return ''
    out=[]
    for sheet_row in range(172,192):
        row=rows[sheet_row-1]
        worker=pick(row,'melyik chatgtp nézi át?')
        if worker!='Munkás 4': continue
        item={
            'sheet_row':sheet_row,
            'number':pick(row,'szám','szam'),
            'place':pick(row,'hely'),
            'profession':pick(row,'szakma'),
            'status':pick(row,'státus','status'),
            'phone':pick(row,'telefon','tel'),
            'website':pick(row,'weboldal'),
            'email':pick(row,'email','e-mail'),
            'name':pick(row,'vállalkozás neve','vallalkozas neve'),
            'maps':pick(row,'Google Maps link','google maps link'),
            'facebook':pick(row,'Facebook'),
            'instagram':pick(row,'Instagram'),
            'booking':pick(row,'booking link','foglalás','foglalas'),
            'worker':worker,
        }
        if not item['name']:
            item['name']=item['profession'] or f"Lead {item['number']}"
        out.append(item)
    if len(out)!=20:
        raise SystemExit(f'Expected 20 Munkás 4 leads in rows 172-191, got {len(out)}')
    return out

def tel_href(phone):
    p=re.sub(r'[^0-9+]','',phone or '')
    return 'tel:'+p if p else ''

def mail_href(email): return 'mailto:'+email if email else ''

def choose_cta(x):
    if x['booking']: return ('Időpont / foglalás',x['booking'])
    if x['phone']: return ('Hívás',tel_href(x['phone']))
    if x['email']: return ('E-mail',mail_href(x['email']))
    if x['website']: return ('Jelenlegi oldal',x['website'])
    if x['maps']: return ('Megnyitás térképen',x['maps'])
    return ('Kapcsolat','#kapcsolat')

def social_links(x):
    links=[]
    for label,key in [('Instagram','instagram'),('Facebook','facebook'),('Jelenlegi oldal','website'),('Térkép','maps')]:
        if x.get(key): links.append(f'<a href="{esc(x[key])}" target="_blank" rel="noopener">{label} ↗</a>')
    return ''.join(links)

def template_specific(tid):
    # Each variation changes actual section geometry and its cinematic signature, not only colors.
    if tid==0:
        return ('hero hero-clean','facts rows','proof proof-line','contact contact-clean')
    if tid==1:
        return ('hero hero-luxury','facts arches','proof proof-orbit','contact contact-luxury')
    if tid==2:
        return ('hero hero-editorial','facts editorial-list','proof proof-horizontal','contact contact-editorial')
    if tid==3:
        return ('hero hero-nordic','facts accordion','proof proof-nordic','contact contact-nordic')
    if tid==4:
        return ('hero hero-mono','facts flip-grid','proof proof-checker','contact contact-mono')
    if tid==5:
        return ('hero hero-bold','facts conversion-grid','proof proof-morph','contact contact-bold')
    if tid==6:
        return ('hero hero-split','facts split-list','proof proof-parallax','contact contact-split')
    if tid==7:
        return ('hero hero-grid','facts bento','proof proof-magnetic','contact contact-grid')
    if tid==8:
        return ('hero hero-stack','facts sticky-cards','proof proof-coverflow','contact contact-stack')
    return ('hero hero-story','facts story-steps','proof proof-reveal','contact contact-story')

def build_page(x,idx):
    tid=idx%10
    key,tname,effects,bg,ink,accent,font=TEMPLATES[tid]
    num=x['number'] or str(171+idx)
    slug=f"w4-{num}-{slugify(x['name'])}"
    cta_label,cta_href=choose_cta(x)
    city=(x['place'].split(',')[0].strip() if x['place'] else '')
    hero_cls,facts_cls,proof_cls,contact_cls=template_specific(tid)
    contact_bits=[]
    if x['phone']: contact_bits.append(f'<a class="contact-line" href="{esc(tel_href(x["phone"]))}">{esc(x["phone"])}</a>')
    if x['email']: contact_bits.append(f'<a class="contact-line" href="{esc(mail_href(x["email"]))}">{esc(x["email"])}</a>')
    if x['place']: contact_bits.append(f'<p>{esc(x["place"])}</p>')
    if not contact_bits: contact_bits.append('<p>Kapcsolat az elérhető hivatalos online csatornán keresztül.</p>')
    online=[]
    if x['website']: online.append('Weboldal')
    if x['booking']: online.append('Foglalási oldal')
    if x['instagram']: online.append('Instagram')
    if x['facebook']: online.append('Facebook')
    online_text=' · '.join(online) if online else 'Kapcsolati csatorna a térképes adatlapon'
    dark = tid in (4,9)
    css=f'''
:root{{--bg:{bg};--ink:{ink};--accent:{accent};--paper:{'#191919' if dark else '#ffffff'};--radius:26px;--max:1180px}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 Inter,Arial,sans-serif;overflow-x:hidden}}body.serif h1,body.serif h2,body.serif .display{{font-family:Georgia,'Times New Roman',serif;font-weight:400}}a{{color:inherit}}.wrap{{width:min(var(--max),calc(100% - 36px));margin:auto}}header{{position:fixed;z-index:50;top:0;left:0;right:0;border-bottom:1px solid color-mix(in srgb,var(--ink) 14%,transparent);background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(16px)}}nav{{height:72px;display:flex;align-items:center;justify-content:space-between;gap:20px}}.brand{{font-weight:850;letter-spacing:-.04em;text-decoration:none;max-width:48%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.navlinks{{display:flex;gap:18px;align-items:center}}.navlinks a{{text-decoration:none}}.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:0 19px;border-radius:999px;background:var(--accent);color:{'#111' if dark else '#fff'};font-weight:800;text-decoration:none;border:0;cursor:pointer}}.ghost{{background:transparent;color:var(--ink);border:1px solid color-mix(in srgb,var(--ink) 28%,transparent)}}.menu{{display:none;width:44px;height:44px;border-radius:50%;background:none;border:1px solid currentColor;color:inherit}}main{{padding-top:72px}}section{{padding:90px 0}}section[id]{{scroll-margin-top:90px}}.eyebrow{{font-size:.73rem;text-transform:uppercase;letter-spacing:.16em;font-weight:800;color:var(--accent)}}h1,h2,h3,p{{margin-top:0}}h1{{font-size:clamp(3.3rem,8vw,7.8rem);line-height:.88;letter-spacing:-.065em;margin:20px 0 28px;overflow-wrap:anywhere}}h2{{font-size:clamp(2.5rem,5vw,5.2rem);line-height:.94;letter-spacing:-.05em}}.lead{{font-size:clamp(1rem,1.8vw,1.28rem);max-width:690px;opacity:.76}}.actions{{display:flex;gap:10px;flex-wrap:wrap;margin-top:28px}}.hero{{min-height:calc(100svh - 72px);display:grid;align-items:center;gap:34px;position:relative;overflow:hidden}}.hero .wrap{{display:grid;grid-template-columns:1.12fr .88fr;align-items:center;gap:48px}}.visual{{min-height:470px;position:relative;border-radius:32px;overflow:hidden;background:linear-gradient(145deg,var(--accent),color-mix(in srgb,var(--ink) 75%,#000));isolation:isolate}}.visual:before,.visual:after{{content:'';position:absolute;border:1px solid rgba(255,255,255,.5);border-radius:50%;inset:10% 25% 25% -15%;transform:rotate(18deg)}}.visual:after{{inset:35% -12% -15% 28%;transform:rotate(-12deg)}}.orb{{position:absolute;width:38%;aspect-ratio:1;border-radius:50%;right:8%;top:10%;background:color-mix(in srgb,#fff 20%,transparent);backdrop-filter:blur(8px)}}.demo-note{{display:inline-block;margin-top:17px;font-size:.72rem;opacity:.55}}.section-head{{display:grid;grid-template-columns:.55fr 1.45fr;gap:30px;margin-bottom:46px}}.facts{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.fact{{min-height:230px;padding:28px;border:1px solid color-mix(in srgb,var(--ink) 15%,transparent);border-radius:24px;background:color-mix(in srgb,var(--bg) 80%,#fff);position:relative;overflow:hidden}}.fact strong{{font-size:1.5rem;letter-spacing:-.04em}}.fact p{{opacity:.68;margin:12px 0 0}}.proof{{padding-top:40px}}.proof-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:stretch}}.proof-panel{{min-height:440px;border-radius:30px;padding:34px;border:1px solid color-mix(in srgb,var(--ink) 14%,transparent);position:relative;overflow:hidden}}.proof-panel.dark{{background:var(--ink);color:var(--bg)}}.proof-panel .big{{font-size:clamp(2.3rem,5vw,5rem);line-height:.92;letter-spacing:-.055em}}.concept{{position:absolute;inset:auto 24px 24px 24px;font-size:.72rem;opacity:.6}}.contact{{padding-top:52px}}.contact-box{{padding:clamp(30px,6vw,68px);border-radius:36px;background:var(--accent);color:{'#111' if dark else '#fff'};display:grid;grid-template-columns:1.15fr .85fr;gap:40px}}.contact-lines{{display:flex;flex-direction:column;gap:10px;justify-content:flex-end}}.contact-line{{font-weight:850;font-size:clamp(1.15rem,2.7vw,2rem);text-decoration:none;overflow-wrap:anywhere}}.socials{{display:flex;gap:12px;flex-wrap:wrap;margin-top:15px}}.socials a{{font-size:.86rem}}footer{{padding:28px 0 44px;font-size:.75rem;opacity:.55}}.foot{{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}}
/* 01 clean */.hero-clean{{background:linear-gradient(90deg,transparent 0 71%,color-mix(in srgb,var(--accent) 7%,transparent) 71%)}}.hero-clean .visual{{border-radius:0;min-height:560px}}.rows{{grid-template-columns:1fr}}.rows .fact{{min-height:130px;border-radius:0;border-width:1px 0 0;display:grid;grid-template-columns:120px 1fr;align-items:center}}.proof-line .proof-panel:first-child{{border-radius:0}}
/* 02 luxury */.hero-luxury .visual{{border-radius:50% 50% 22% 22% / 30% 30% 15% 15%}}.arches .fact{{border-radius:44px 44px 120px 44px}}.proof-orbit .proof-panel{{border-radius:50px}}
/* 03 editorial */.hero-editorial .wrap{{grid-template-columns:.72fr 1.28fr}}.hero-editorial .visual{{border-radius:0;transform:rotate(2deg)}}.editorial-list{{grid-template-columns:1fr}}.editorial-list .fact{{display:grid;grid-template-columns:80px 1fr;min-height:auto;border-radius:0;border-width:1px 0 0;background:none}}.proof-horizontal{{overflow:hidden}}.proof-horizontal .proof-grid{{grid-template-columns:1.35fr .65fr}}
/* 04 nordic */.hero-nordic .visual{{border-radius:160px 26px 26px 26px}}.accordion{{grid-template-columns:1fr}}.accordion .fact{{min-height:88px;transition:.35s}}.accordion .fact.active{{min-height:200px;background:color-mix(in srgb,var(--accent) 16%,var(--bg))}}
/* 05 mono */.hero-mono{{background:#111;color:#f7f7f4}}.hero-mono .visual{{background:#f7f7f4;border-radius:0}}.hero-mono .visual:before,.hero-mono .visual:after{{border-color:#111}}.flip-grid .fact{{background:#171717;perspective:900px;transition:transform .55s}}.flip-grid .fact.flipped{{transform:rotateY(180deg)}}.proof-checker .proof-grid{{gap:0}}.proof-checker .proof-panel{{border-radius:0}}
/* 06 bold */.hero-bold .visual{{border-radius:22px;box-shadow:18px 18px 0 var(--ink)}}.conversion-grid .fact:nth-child(2){{transform:translateY(25px)}}.proof-morph .proof-panel{{transition:.45s}}.proof-morph .proof-panel.morphed{{border-radius:90px;transform:scale(.97)}}
/* 07 split */.hero-split .wrap{{width:100%;max-width:none;grid-template-columns:1fr 1fr;gap:0}}.hero-split .copy{{padding:70px max(26px,calc((100vw - var(--max))/2))}}.hero-split .visual{{border-radius:0;min-height:calc(100svh - 72px)}}.split-list{{grid-template-columns:1fr 1fr}}.split-list .fact:nth-child(3){{grid-column:1/-1}}.proof-parallax .proof-panel:first-child{{transform:translateY(var(--py,0px))}}
/* 08 grid */.hero-grid .wrap{{grid-template-columns:.85fr 1.15fr}}.hero-grid .visual{{border-radius:22px;clip-path:polygon(0 0,100% 0,100% 72%,72% 72%,72% 100%,0 100%)}}.bento{{grid-template-columns:1.2fr .8fr}}.bento .fact:first-child{{grid-row:span 2;min-height:474px}}.proof-magnetic .proof-panel{{background-image:radial-gradient(circle at var(--mx,50%) var(--my,50%),color-mix(in srgb,var(--accent) 22%,transparent),transparent 35%)}}
/* 09 stack */.hero-stack .visual{{border-radius:32px;transform:perspective(900px) rotateY(-8deg)}}.sticky-cards{{display:block}}.sticky-cards .fact{{position:sticky;top:96px;margin-bottom:24px;background:var(--bg);box-shadow:0 16px 50px color-mix(in srgb,var(--ink) 10%,transparent)}}.sticky-cards .fact:nth-child(2){{top:116px}}.sticky-cards .fact:nth-child(3){{top:136px}}.proof-coverflow .proof-panel:first-child{{transform:perspective(900px) rotateY(var(--cover,-8deg));transition:.35s}}
/* 10 story */.hero-story{{background:#171614;color:#f2eadb}}.hero-story .visual{{border-radius:0;background:linear-gradient(145deg,#6b4930,#171614)}}.story-steps{{display:block}}.story-steps .fact{{margin-left:42%;min-height:230px;border-radius:0;background:none;border-width:0 0 1px}}.proof-reveal .proof-panel:first-child{{position:sticky;top:96px}}
.effect-bar{{height:2px;background:var(--accent);transform-origin:left;transform:scaleX(var(--progress,.08));position:fixed;z-index:80;top:71px;left:0;right:0}}.island{{position:fixed;z-index:70;left:50%;bottom:18px;transform:translateX(-50%);padding:9px 14px;background:var(--ink);color:var(--bg);border-radius:999px;font-size:.72rem;transition:.3s;max-width:92vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.island.open{{padding:14px 24px}}.circular{{position:absolute;right:24px;bottom:24px;width:92px;height:92px;border:1px solid rgba(255,255,255,.45);border-radius:50%;display:grid;place-items:center;font-size:.63rem;text-transform:uppercase;letter-spacing:.12em;transition:transform .3s}}.trail-dot{{position:fixed;width:18px;height:18px;border-radius:50%;pointer-events:none;background:var(--accent);mix-blend-mode:difference;z-index:90;opacity:0}}.dock{{position:fixed;z-index:65;left:50%;bottom:18px;transform:translateX(-50%);display:flex;gap:6px;padding:7px;background:color-mix(in srgb,var(--bg) 82%,transparent);border:1px solid color-mix(in srgb,var(--ink) 15%,transparent);border-radius:18px;backdrop-filter:blur(16px)}}.dock a{{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;text-decoration:none;background:color-mix(in srgb,var(--accent) 18%,var(--bg));transition:.2s}}
@media(max-width:760px){{nav{{height:66px}}main{{padding-top:66px}}.navlinks{{position:fixed;display:none;top:76px;left:12px;right:12px;padding:16px;flex-direction:column;align-items:stretch;background:var(--bg);border:1px solid color-mix(in srgb,var(--ink) 18%,transparent);border-radius:20px}}.navlinks.open{{display:flex}}.menu{{display:block}}.hero{{min-height:auto}}.hero .wrap,.hero-split .wrap,.hero-editorial .wrap,.hero-grid .wrap{{grid-template-columns:1fr}}.hero-split .copy{{padding:58px 18px}}.hero-split .visual{{min-height:360px}}.hero .wrap{{padding:58px 0}}.visual{{min-height:330px}}h1{{font-size:clamp(3rem,15vw,5rem)}}section{{padding:68px 0}}.section-head,.proof-grid,.contact-box{{grid-template-columns:1fr}}.facts,.split-list,.bento{{grid-template-columns:1fr}}.bento .fact:first-child{{grid-row:auto;min-height:260px}}.rows .fact,.editorial-list .fact{{grid-template-columns:1fr}}.story-steps .fact{{margin-left:0}}.sticky-cards .fact{{position:relative;top:auto!important}}.proof-reveal .proof-panel:first-child{{position:relative;top:auto}}.proof-parallax .proof-panel:first-child{{transform:none!important}}.conversion-grid .fact:nth-child(2){{transform:none}}.circular{{width:72px;height:72px}}.dock{{display:none}}.island{{bottom:10px}}}}
@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}*,*:before,*:after{{animation:none!important;transition-duration:.01ms!important;scroll-behavior:auto!important}}.proof-parallax .proof-panel:first-child{{transform:none!important}}.effect-bar{{display:none}}}}
'''
    # Markup intentionally keeps factual claims limited to Sheet-backed fields.
    page=f'''<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{esc(x['name'])} — weboldal demo</title><meta name="description" content="{esc(x['name'])} személyre szabott, mobilbarát bemutatkozó weboldal-koncepció."><style>{css}</style></head><body class="{'serif' if font=='serif' else 'sans'} template-{key}"><div class="effect-bar" id="effectBar"></div><header><nav class="wrap"><a class="brand" href="#top">{esc(x['name'])}</a><div class="navlinks" id="nav"><a href="#informacio">Információ</a><a href="#online">Online</a><a href="#kapcsolat">Kapcsolat</a><a class="btn" href="{esc(cta_href)}">{esc(cta_label)}</a></div><button class="menu" id="menu" aria-label="Menü" aria-controls="nav" aria-expanded="false">☰</button></nav></header><main id="top"><section class="{hero_cls}"><div class="wrap"><div class="copy"><div class="eyebrow">{esc(x['profession'])}{' · '+esc(city) if city else ''}</div><h1>{esc(x['name'])}</h1><p class="lead">Személyre szabott weboldal-koncepció, amely a legfontosabb elérhetőségeket és online csatornákat egy letisztult felületen rendezi.</p><div class="actions"><a class="btn" href="{esc(cta_href)}">{esc(cta_label)}</a><a class="btn ghost" href="#informacio">Részletek</a></div><span class="demo-note">Demo koncepció • SCH Agency Website Factory • Lead {esc(num)}</span></div><div class="visual" id="pointerZone" data-effect="{esc(effects[2])}"><span class="orb"></span><span class="circular" id="circular">{esc(tname)} · {esc(num)}</span></div></div></section><section id="informacio"><div class="wrap"><div class="section-head"><div class="eyebrow">01 · Alapinformáció</div><h2>A lényeg gyorsan elérhető.</h2></div><div class="{facts_cls}" id="facts"><article class="fact" tabindex="0"><strong>Helyszín</strong><p>{esc(x['place']) if x['place'] else 'A helyszínhez a hivatalos térképes adatlap használható.'}</p></article><article class="fact" tabindex="0"><strong>Kapcsolat</strong><p>{esc(x['phone']) if x['phone'] else (esc(x['email']) if x['email'] else 'Kapcsolat az elérhető hivatalos online csatornán.')}</p></article><article class="fact" tabindex="0"><strong>Online jelenlét</strong><p>{esc(online_text)}</p></article></div></div></section><section class="proof" id="online"><div class="wrap"><div class="section-head"><div class="eyebrow">02 · Vizuális irány</div><h2>{esc(tname)} karakter, a vállalkozáshoz igazítva.</h2></div><div class="{proof_cls}"><div class="proof-grid"><article class="proof-panel dark" id="scrollPanel"><div class="eyebrow" style="color:var(--accent)">{esc(effects[0])}</div><p class="big">Kevesebb keresés. Gyorsabb kapcsolat.</p><span class="concept">Ez a blokk design-koncepció; nem állít ügyfélreferenciát vagy nem igazolt üzleti eredményt.</span></article><article class="proof-panel" id="clickPanel" tabindex="0"><div class="eyebrow">{esc(effects[1])}</div><h3 style="font-size:2rem">Interaktív, mégis használható.</h3><p>A mozgás a hierarchiát segíti; mobilon és reduced-motion módban egyszerűsödik.</p><button class="btn ghost" type="button" id="effectAction">Interakció kipróbálása</button></article></div></div></div></section><section class="{contact_cls}" id="kapcsolat"><div class="wrap"><div class="contact-box"><div><div class="eyebrow" style="color:inherit;opacity:.7">03 · Kapcsolat</div><h2>Innen egy lépés a kapcsolatfelvétel.</h2><div class="socials">{social_links(x)}</div></div><div class="contact-lines">{''.join(contact_bits)}<a class="btn ghost" href="{esc(cta_href)}">{esc(cta_label)}</a></div></div></div></section></main><footer><div class="wrap foot"><span>{esc(x['name'])} — demo weboldal</span><span>{esc(tname)} · {esc(' · '.join(effects))}</span></div></footer><div class="island" id="island">{esc(x['name'])} · demo</div><div class="trail-dot" id="trail"></div><script>
const state={{scroll:0,click:0,pointer:0}};window.__qaEffects=state;
const bar=document.getElementById('effectBar'),circ=document.getElementById('circular'),scrollPanel=document.getElementById('scrollPanel');
function onScroll(){{const max=Math.max(1,document.documentElement.scrollHeight-innerHeight);const p=Math.min(1,scrollY/max);state.scroll=Math.round(p*100);bar.style.setProperty('--progress',Math.max(.06,p));circ.style.transform=`rotate(${{p*180}}deg)`;if(document.body.classList.contains('template-split-business')) scrollPanel.style.setProperty('--py',`${{Math.min(60,p*80)}}px`);if(document.body.classList.contains('template-card-stack')) scrollPanel.style.setProperty('--cover',`${{-8+p*18}}deg`);}}
addEventListener('scroll',onScroll,{{passive:true}});onScroll();
const action=document.getElementById('effectAction'),island=document.getElementById('island');action.addEventListener('click',()=>{{state.click++;action.dataset.state=String(state.click);island.classList.toggle('open');document.getElementById('clickPanel').classList.toggle('morphed');const facts=[...document.querySelectorAll('.fact')];if(facts.length){{facts[state.click%facts.length].classList.toggle('active');facts[state.click%facts.length].classList.toggle('flipped')}}}});
const zone=document.getElementById('pointerZone'),trail=document.getElementById('trail');zone.addEventListener('pointermove',e=>{{state.pointer++;zone.dataset.state=String(state.pointer);const r=zone.getBoundingClientRect(),x=((e.clientX-r.left)/r.width*100).toFixed(1),y=((e.clientY-r.top)/r.height*100).toFixed(1);document.documentElement.style.setProperty('--mx',x+'%');document.documentElement.style.setProperty('--my',y+'%');trail.style.opacity='.6';trail.style.left=(e.clientX-9)+'px';trail.style.top=(e.clientY-9)+'px';}});zone.addEventListener('pointerleave',()=>trail.style.opacity='0');
const menu=document.getElementById('menu'),nav=document.getElementById('nav');menu.addEventListener('click',()=>{{const o=nav.classList.toggle('open');menu.setAttribute('aria-expanded',o)}});nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{{nav.classList.remove('open');menu.setAttribute('aria-expanded','false')}}));
if(document.body.classList.contains('template-editorial-serif')){{const p=document.getElementById('clickPanel');let down=false,sx=0; p.addEventListener('pointerdown',e=>{{down=true;sx=e.clientX;p.setPointerCapture(e.pointerId)}});p.addEventListener('pointermove',e=>{{if(down) p.style.transform=`translateX(${{Math.max(-30,Math.min(30,(e.clientX-sx)/3))}}px)`}});p.addEventListener('pointerup',()=>{{down=false;p.style.transform=''}})}}
if(document.body.classList.contains('template-sticky-story')){{let original=action.textContent;action.addEventListener('click',()=>{{const target='KAPCSOLAT';let i=0;const timer=setInterval(()=>{{action.textContent=target.slice(0,++i)+(i<target.length?'_':'');if(i>=target.length)clearInterval(timer)}},45)}})}}
</script></body></html>'''
    return slug,page

def main():
    rows=fetch_rows()
    manifest=[]
    for idx,x in enumerate(rows):
        slug,page=build_page(x,idx)
        d=pathlib.Path(slug);d.mkdir(exist_ok=True)
        (d/'index.html').write_text(page,encoding='utf-8')
        manifest.append({**x,'slug':slug,'demo_url':PAGES_BASE+slug+'/','preview_url':PAGES_BASE+slug+'/preview-mobile.png','template':TEMPLATES[idx%10][1],'effects':TEMPLATES[idx%10][2]})
    pathlib.Path('worker4-171-190-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Generated',len(manifest),'Worker 4 sites')
    for m in manifest: print(m['number'],m['name'],m['slug'],m['template'])

if __name__=='__main__': main()
