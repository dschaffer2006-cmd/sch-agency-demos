#!/usr/bin/env python3
from pathlib import Path
import concurrent.futures, json, subprocess, time, urllib.error, urllib.request

BASE='https://dschaffer2006-cmd.github.io/sch-agency-demos'
EXCLUDE={'.github','tools','node_modules','runs','artifacts','sch-agency-website'}
EXPECTED=Path('expected-pages-routes.txt')
REPORT=Path('all-pages-and-previews-audit.json')

def git(*args):
    return subprocess.run(['git',*args],text=True,capture_output=True).stdout

def valid(s):
    return bool(s) and s not in EXCLUDE and not s.startswith('.') and '/' not in s

def slugs():
    out=set()
    for raw in git('log','--all','--name-only','--pretty=format:','--','*/index.html').splitlines():
        p=raw.strip().split('/')
        if len(p)==2 and p[1]=='index.html' and valid(p[0]): out.add(p[0])
    for p in Path('.').glob('*/index.html'):
        if valid(p.parent.name): out.add(p.parent.name)
    if EXPECTED.exists():
        for raw in EXPECTED.read_text(encoding='utf-8').splitlines():
            s=raw.strip().strip('/')
            if s and not s.startswith('#') and valid(s): out.add(s)
    return sorted(out)

def get(url, timeout=20):
    req=urllib.request.Request(url,headers={'User-Agent':'SCH-Strict-Pages-Audit/1.0','Cache-Control':'no-cache'})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            body=r.read(32768).decode('utf-8','ignore').lower()
            status=int(getattr(r,'status',r.getcode()))
            gh404='file not found' in body and 'github pages' in body
            return {'status':status,'content_type':r.headers.get('content-type',''),'github_pages_404':gh404,'error':''}
    except urllib.error.HTTPError as e:
        body=e.read(32768).decode('utf-8','ignore').lower()
        return {'status':int(e.code),'content_type':e.headers.get('content-type','') if e.headers else '','github_pages_404':'file not found' in body and 'github pages' in body,'error':str(e)}
    except Exception as e:
        return {'status':None,'content_type':'','github_pages_404':False,'error':repr(e)}

def check(slug):
    page_url=f'{BASE}/{slug}/'
    preview_url=f'{BASE}/{slug}/preview-mobile.png'
    page=get(page_url); preview=get(preview_url)
    page_ok=bool(page['status'] and 200<=page['status']<300 and not page['github_pages_404'])
    preview_ok=bool(preview['status'] and 200<=preview['status']<300 and not preview['github_pages_404'] and preview['content_type'].lower().startswith('image/'))
    return {'slug':slug,'page_url':page_url,'preview_url':preview_url,'page_ok':page_ok,'preview_ok':preview_ok,'ok':page_ok and preview_ok,'page':page,'preview':preview}

def main():
    names=slugs(); pending=set(names); rows={}
    for attempt in range(1,7):
        if not pending: break
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            batch=list(ex.map(check,sorted(pending)))
        for r in batch: r['attempt']=attempt; rows[r['slug']]=r
        pending={r['slug'] for r in batch if not r['ok']}
        if pending and attempt<6:
            print(f'Attempt {attempt}: {len(pending)} routes/previews still failing; waiting...',flush=True)
            time.sleep(20)
    items=[rows[s] for s in names]
    failed=[r for r in items if not r['ok']]
    report={'base_url':BASE,'total_routes':len(items),'passed':len(items)-len(failed),'failed':len(failed),'all_ok':not failed,'failed_routes':failed,'items':items}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('total_routes','passed','failed','all_ok')},ensure_ascii=False))
    return 0 if not failed else 2

if __name__=='__main__': raise SystemExit(main())
