from pathlib import Path
from html import unescape
import re

# Revision 3: fix the two Template 06 mobile overflows and the visual-supervisor
# typography issue where long Hungarian words were being split mid-word.
revision3_css = '''<style>
h1{overflow-wrap:normal!important;word-break:normal!important;hyphens:none!important}
body[data-template="1"] h1{font-size:clamp(3rem,5vw,5.3rem)}
body[data-template="2"] h1{font-size:clamp(2.8rem,3.8vw,4.2rem)}
body[data-template="3"] h1{font-size:clamp(3.2rem,5.2vw,5.7rem)}
body[data-template="4"] h1{font-size:clamp(2.7rem,3.5vw,3.8rem)}
body[data-template="5"] h1{font-size:clamp(3rem,5vw,5.4rem)}
body[data-template="6"] h1{font-size:clamp(2.9rem,4.6vw,5rem)}
body[data-template="7"] h1{font-size:clamp(2.7rem,3.6vw,4rem)}
body[data-template="8"] h1{font-size:clamp(2.55rem,3.2vw,3.55rem)}
body[data-template="9"] h1{font-size:clamp(2.6rem,3.4vw,3.8rem)}
body[data-template="10"] h1{font-size:clamp(3rem,4.5vw,5rem)}
body.fit-title h1{font-size:clamp(2.45rem,3.15vw,3.75rem)!important;line-height:.98}
@media(max-width:760px){
  h1{font-size:clamp(2.35rem,10vw,3.45rem)!important;line-height:.98}
  body.fit-title h1{font-size:clamp(2.05rem,8.6vw,2.95rem)!important;line-height:1}
  body[data-template="6"] .services{grid-template-columns:1fr!important}
  body[data-template="6"] .service{min-width:0!important;width:100%}
  body[data-template="6"] .service:first-child{grid-row:auto!important;min-height:300px}
  body[data-template="6"] .hero-art{clip-path:none}
}
</style>'''

slugs = [
 'the-eden-hair-salon-pecs','ani-fodraszszalon-pecs','clarity-hajstudio-pecs','hair-and-nails-club-pecs','nowa-salon-pecs','hair-by-flora-onodi-pecs','pacek-barbershop-pecs','hajnalfeny-szepsegkozpont-pecs','lefti-hajstudio-dunaujvaros','wellness-hajstudio-zellei-erzsebet-dunaujvaros','lk-royal-barber-dunaujvaros','masculine-barber-shop-dunaujvaros','gurubi-szalon-dunaujvaros','farosz-szepsegszalon-dunaujvaros','gentlemens-barbershop-dunaujvaros','hajlabor-dunaujvaros','beke-barbershop-dunaujvaros','mens-room-dunaujvaros','barbi-hair-clinic-tatabanya','bella-signora-tatabanya'
]

for slug in slugs:
    p = Path(slug) / 'index.html'
    html = p.read_text(encoding='utf-8')
    m = re.search(r'<h1>(.*?)</h1>', html, flags=re.S)
    title = unescape(re.sub(r'<[^>]+>', '', m.group(1))) if m else ''
    words = re.findall(r'[^\s]+', title)
    needs_fit = len(title) > 20 or any(len(w) > 12 for w in words)
    if needs_fit and 'fit-title' not in html.split('>',1)[0]:
        if '<body class="long-title" data-template=' in html:
            html = html.replace('<body class="long-title" data-template=', '<body class="long-title fit-title" data-template=', 1)
        elif '<body data-template=' in html:
            html = html.replace('<body data-template=', '<body class="fit-title" data-template=', 1)
    html = html.replace('</head>', revision3_css + '</head>', 1)
    p.write_text(html, encoding='utf-8')

print('worker5 revision 3 mobile + typography fixes applied')
