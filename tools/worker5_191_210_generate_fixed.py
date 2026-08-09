from pathlib import Path
from html import unescape
import re
import runpy

# Generate from the validated batch generator first.
runpy.run_path('tools/worker5_191_210_generate.py', run_name='__main__')

# Source-sheet category corrections: use the exact source category instead of a name-based inference.
category_fixes = {
    'masculine-barber-shop-dunaujvaros': ('Borbély · Soft Luxury', 'Fodrászszalon · Soft Luxury'),
    'farosz-szepsegszalon-dunaujvaros': ('Szépségszalon · Nordic Calm', 'Fodrászszalon · Nordic Calm'),
    'gentlemens-barbershop-dunaujvaros': ('Borbély · Monochrome Chic', 'Fodrászszalon · Monochrome Chic'),
    'beke-barbershop-dunaujvaros': ('Borbély · Split Business', 'Fodrászszalon · Split Business'),
}

# Visual revision 2: make each template visibly structural, not a palette swap.
diversity_css = '''<style>
.hero-copy{position:relative;z-index:2}
.long-title h1{font-size:clamp(2.7rem,4.7vw,5.2rem);line-height:.94}
.gallery-band{padding-top:36px}
.abstract-gallery{display:grid;grid-template-columns:1.35fr .8fr .8fr;gap:14px;margin-top:36px}
.abstract-gallery figure{margin:0;min-height:330px;border-radius:28px;position:relative;overflow:hidden;border:1px solid color-mix(in srgb,var(--ink) 14%,transparent);background:linear-gradient(145deg,var(--accent),color-mix(in srgb,var(--ink) 85%,#000))}
.abstract-gallery figure:nth-child(2){background:linear-gradient(155deg,color-mix(in srgb,var(--accent) 25%,var(--bg)),var(--surface))}
.abstract-gallery figure:nth-child(3){background:var(--ink)}
.abstract-gallery figure:before,.abstract-gallery figure:after{content:"";position:absolute;border:1px solid rgba(255,255,255,.42);border-radius:50%;width:65%;aspect-ratio:1;left:-15%;top:12%}
.abstract-gallery figure:after{left:48%;top:48%;width:48%}
.abstract-gallery figcaption{position:absolute;left:18px;bottom:16px;padding:7px 10px;border-radius:999px;background:color-mix(in srgb,var(--bg) 82%,transparent);color:var(--ink);font-size:.7rem;letter-spacing:.08em;text-transform:uppercase}
body[data-template="1"] .hero{grid-template-columns:1.35fr .65fr}
body[data-template="1"] .hero-art{min-height:390px;border-radius:8px}
body[data-template="1"] .services{grid-template-columns:1fr}
body[data-template="1"] .service{min-height:120px;border-radius:0;border-inline:0;background:transparent;display:grid;grid-template-columns:90px 1fr 1fr;align-items:center}
body[data-template="1"] .abstract-gallery{grid-template-columns:2fr 1fr}
body[data-template="1"] .abstract-gallery figure:nth-child(3){display:none}
body[data-template="2"] .hero{grid-template-columns:.86fr 1.14fr}
body[data-template="2"] .hero-art{border-radius:48% 48% 28px 28px;min-height:570px}
body[data-template="2"] .service{border-radius:90px 26px 90px 26px;padding:34px}
body[data-template="2"] .contact-card{border-radius:90px 30px 90px 30px}
body[data-template="2"] .abstract-gallery figure:first-child{border-radius:46% 46% 26px 26px}
body[data-template="3"] .hero{grid-template-columns:1fr;padding-bottom:28px}
body[data-template="3"] .hero-copy{max-width:920px}
body[data-template="3"] .hero-art{min-height:300px;border-radius:0}
body[data-template="3"] .services{grid-template-columns:1fr 1fr 1fr}
body[data-template="3"] .service{background:transparent;border-radius:0;border-inline:0;min-height:180px}
body[data-template="3"] .abstract-gallery{grid-template-columns:2fr 1fr 1fr}
body[data-template="3"] .abstract-gallery figure{border-radius:0;min-height:390px}
body[data-template="4"] .hero{grid-template-columns:.78fr 1.22fr}
body[data-template="4"] .hero-art{border-radius:120px 28px 120px 28px}
body[data-template="4"] .services{grid-template-columns:repeat(3,1fr)}
body[data-template="4"] .service{border-radius:18px;min-height:250px}
body[data-template="4"] .abstract-gallery{grid-template-columns:1fr 1fr}
body[data-template="4"] .abstract-gallery figure:nth-child(3){grid-column:1/-1;min-height:210px}
body[data-template="5"] .hero{grid-template-columns:1fr;position:relative;isolation:isolate}
body[data-template="5"] .hero-art{position:absolute;inset:24px;z-index:0;opacity:.32;min-height:0}
body[data-template="5"] .hero-copy{max-width:850px}
body[data-template="5"] .services{grid-template-columns:repeat(3,1fr)}
body[data-template="5"] .service{min-height:300px;display:flex;flex-direction:column;justify-content:space-between}
body[data-template="5"] .abstract-gallery{grid-template-columns:1fr 1fr 1fr}
body[data-template="5"] .abstract-gallery figure{border-radius:0}
body[data-template="6"] .hero{grid-template-columns:1.2fr .8fr}
body[data-template="6"] .hero-art{clip-path:polygon(8% 0,100% 0,100% 92%,0 100%);border-radius:18px}
body[data-template="6"] .services{grid-template-columns:1.35fr .65fr}
body[data-template="6"] .service:first-child{grid-row:span 2;min-height:435px;background:var(--accent);color:white}
body[data-template="6"] .contact-card{border-radius:18px}
body[data-template="6"] .abstract-gallery figure:first-child{grid-column:span 2}
body[data-template="7"] .hero{padding-inline:0;gap:0;grid-template-columns:1fr 1fr}
body[data-template="7"] .hero-copy{padding-left:max(18px,calc((100vw - 1160px)/2));padding-right:55px}
body[data-template="7"] .hero-art{border-radius:0;min-height:calc(100svh - 72px)}
body[data-template="7"] .services{grid-template-columns:1fr}
body[data-template="7"] .service:nth-child(even){margin-left:18%;background:var(--ink);color:var(--bg)}
body[data-template="7"] .abstract-gallery{grid-template-columns:1fr 1fr}
body[data-template="7"] .abstract-gallery figure:first-child{grid-row:span 2;min-height:680px}
body[data-template="8"] .hero{grid-template-columns:.72fr 1.28fr}
body[data-template="8"] .hero-art{clip-path:polygon(0 9%,68% 0,100% 24%,90% 100%,18% 92%);border-radius:18px}
body[data-template="8"] .services{grid-template-columns:1.1fr .9fr}
body[data-template="8"] .service:first-child{grid-row:span 2;min-height:430px}
body[data-template="8"] .service:nth-child(2){min-height:180px}
body[data-template="8"] .abstract-gallery{grid-template-columns:1fr 1fr 1fr 1fr}
body[data-template="8"] .abstract-gallery figure:first-child{grid-column:span 2}
body[data-template="9"] .hero{grid-template-columns:.8fr 1.2fr}
body[data-template="9"] .hero-art{border-radius:48px;transform:rotate(1.5deg);box-shadow:0 35px 80px rgba(0,0,0,.22)}
body[data-template="9"] .services{grid-template-columns:1fr}
body[data-template="9"] .service{margin-bottom:-20px;min-height:180px;box-shadow:0 18px 50px rgba(0,0,0,.12)}
body[data-template="9"] .service:nth-child(2){margin-left:6%}body[data-template="9"] .service:nth-child(3){margin-left:12%}
body[data-template="9"] .abstract-gallery figure{border-radius:42px}
body[data-template="10"] .hero{grid-template-columns:1fr;position:relative;isolation:isolate;min-height:calc(100svh - 72px);align-items:end}
body[data-template="10"] .hero-art{position:absolute;inset:22px;z-index:0;opacity:.42;min-height:0;border-radius:42px}
body[data-template="10"] .hero-copy{max-width:900px;padding-bottom:7vh}
body[data-template="10"] .services{grid-template-columns:1fr 1fr 1fr}
body[data-template="10"] .service{min-height:270px;background:transparent;border-radius:0;border-top:1px solid color-mix(in srgb,var(--ink) 25%,transparent);border-inline:0;border-bottom:0}
body[data-template="10"] .abstract-gallery{grid-template-columns:1fr 1fr}
body[data-template="10"] .abstract-gallery figure{min-height:500px;border-radius:40px}
body[data-template="10"] .abstract-gallery figure:nth-child(3){grid-column:1/-1;min-height:220px}
.sticky-cards article{pointer-events:none}
.coverflow{position:relative;z-index:8;background:var(--bg);padding:20px 0;scroll-margin-top:110px}
@media(max-width:760px){
 .long-title h1{font-size:clamp(2.15rem,9.6vw,3.7rem);line-height:.98}
 .abstract-gallery{grid-template-columns:1fr 1fr!important}.abstract-gallery figure{min-height:220px!important;border-radius:22px!important}.abstract-gallery figure:first-child{grid-column:1/-1!important;grid-row:auto!important;min-height:330px!important}.abstract-gallery figure:nth-child(3){display:block!important;grid-column:auto!important}
 body[data-template="1"] .service{grid-template-columns:55px 1fr;padding:20px}.service p{grid-column:2}
 body[data-template="3"] .services,body[data-template="4"] .services,body[data-template="5"] .services,body[data-template="10"] .services{grid-template-columns:1fr}
 body[data-template="5"] .hero-art,body[data-template="10"] .hero-art{position:relative;inset:auto;opacity:1;z-index:auto;min-height:320px}
 body[data-template="5"] .hero,body[data-template="10"] .hero{display:grid;grid-template-columns:1fr;align-items:center}
 body[data-template="7"] .hero{padding:58px 18px;gap:32px}body[data-template="7"] .hero-copy{padding:0}body[data-template="7"] .hero-art{min-height:340px}
 body[data-template="7"] .service:nth-child(even){margin-left:0}
 body[data-template="8"] .services{grid-template-columns:1fr}body[data-template="8"] .service:first-child{grid-row:auto;min-height:260px}
 body[data-template="9"] .service:nth-child(n){margin-left:0;margin-bottom:10px}
}
</style>'''

gallery = '''<section class="gallery-band"><div class="wrap"><div class="section-head"><div class="eyebrow">Vizuális rendszer</div><h2>Absztrakt, arculathoz igazítható galéria.</h2></div><div class="abstract-gallery" aria-label="Absztrakt vizuális galéria"><figure><figcaption>01 · Atmoszféra</figcaption></figure><figure><figcaption>02 · Részlet</figcaption></figure><figure><figcaption>03 · Ritmus</figcaption></figure></div></div></section>'''

for slug_dir in [p for p in Path('.').iterdir() if p.is_dir() and (p / 'index.html').exists()]:
    slug = slug_dir.name
    # Scope post-processing to this Worker 5 batch only.
    if slug not in {
        'the-eden-hair-salon-pecs','ani-fodraszszalon-pecs','clarity-hajstudio-pecs','hair-and-nails-club-pecs','nowa-salon-pecs','hair-by-flora-onodi-pecs','pacek-barbershop-pecs','hajnalfeny-szepsegkozpont-pecs','lefti-hajstudio-dunaujvaros','wellness-hajstudio-zellei-erzsebet-dunaujvaros','lk-royal-barber-dunaujvaros','masculine-barber-shop-dunaujvaros','gurubi-szalon-dunaujvaros','farosz-szepsegszalon-dunaujvaros','gentlemens-barbershop-dunaujvaros','hajlabor-dunaujvaros','beke-barbershop-dunaujvaros','mens-room-dunaujvaros','barbi-hair-clinic-tatabanya','bella-signora-tatabanya'
    }:
        continue
    p = slug_dir / 'index.html'
    html = p.read_text(encoding='utf-8')
    if slug in category_fixes:
        old, new = category_fixes[slug]
        html = html.replace(old, new)
    m = re.search(r'<h1>(.*?)</h1>', html, flags=re.S)
    if m and len(unescape(re.sub('<[^>]+>', '', m.group(1)))) > 28:
        html = html.replace('<body data-template=', '<body class="long-title" data-template=', 1)
    html = html.replace('</head>', diversity_css + '</head>', 1)
    html = html.replace('<section id="kapcsolat">', gallery + '<section id="kapcsolat">', 1)
    p.write_text(html, encoding='utf-8')

print('worker5 visual revision 2 applied')
