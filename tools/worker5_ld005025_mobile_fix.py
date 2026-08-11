from pathlib import Path
p=Path('outreach/LD-005-025-re-szepseg-egeszseg/index.html')
s=p.read_text(encoding='utf-8')
needle='@media(max-width:820px){.menu{display:block}'
replacement='@media(max-width:820px){html,body{max-width:100%;overflow-x:hidden}.story>*,.book-grid>*{min-width:0}.fact{grid-template-columns:1fr}.fact strong,.contact-card p,.contact-card strong{min-width:0;overflow-wrap:anywhere;word-break:break-word}.menu{display:block}'
if needle not in s:
    raise SystemExit('target CSS marker not found')
s=s.replace(needle,replacement,1)
p.write_text(s,encoding='utf-8')
print('LD-005-025 targeted mobile overflow fix applied')
