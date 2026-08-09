from pathlib import Path

# Revision 3: Template 06 desktop asymmetry must collapse cleanly on 390px mobile.
mobile_fix = '''<style>
@media(max-width:760px){
  body[data-template="6"] .services{grid-template-columns:1fr!important}
  body[data-template="6"] .service{min-width:0!important;width:100%}
  body[data-template="6"] .service:first-child{grid-row:auto!important;min-height:300px}
  body[data-template="6"] .hero-art{clip-path:none}
}
</style>'''

for slug in ['hair-by-flora-onodi-pecs', 'hajlabor-dunaujvaros']:
    p = Path(slug) / 'index.html'
    html = p.read_text(encoding='utf-8').replace('</head>', mobile_fix + '</head>', 1)
    p.write_text(html, encoding='utf-8')

print('worker5 revision 3 mobile fix applied')
