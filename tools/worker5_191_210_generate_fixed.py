from pathlib import Path
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
for slug, (old, new) in category_fixes.items():
    p = Path(slug) / 'index.html'
    html = p.read_text(encoding='utf-8').replace(old, new)
    p.write_text(html, encoding='utf-8')

# Targeted revision for Template 09: non-interactive sticky cards must not block the interactive coverflow below.
card_stack_fix = '''<style>
.sticky-cards article{pointer-events:none}
.coverflow{position:relative;z-index:8;background:var(--bg);padding:20px 0;scroll-margin-top:110px}
</style>'''
for slug in ['lefti-hajstudio-dunaujvaros', 'barbi-hair-clinic-tatabanya']:
    p = Path(slug) / 'index.html'
    html = p.read_text(encoding='utf-8').replace('</head>', card_stack_fix + '</head>')
    p.write_text(html, encoding='utf-8')

print('worker5 targeted fixes applied')
