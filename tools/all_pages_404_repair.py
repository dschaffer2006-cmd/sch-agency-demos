#!/usr/bin/env python3
from pathlib import Path
import concurrent.futures
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = "https://dschaffer2006-cmd.github.io/sch-agency-demos"
REPORT_RESTORE = Path("all-pages-404-restore-report.json")
REPORT_AUDIT = Path("all-pages-404-audit.json")
EXPECTED = Path("expected-pages-routes.txt")
EXCLUDE = {".github", "tools", "node_modules", "runs", "artifacts", "sch-agency-website"}


def git(*args, check=True):
    p = subprocess.run(["git", *args], text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def valid_slug(slug):
    return bool(slug) and slug not in EXCLUDE and not slug.startswith(".") and "/" not in slug


def historical_slugs():
    # Any top-level directory that has ever contained index.html counts as a generated demo route.
    out = git("log", "--all", "--name-only", "--pretty=format:", "--", "*/index.html")
    slugs = set()
    for raw in out.splitlines():
        line = raw.strip()
        parts = line.split("/")
        if len(parts) == 2 and parts[1] == "index.html" and valid_slug(parts[0]):
            slugs.add(parts[0])

    # Also include every currently present top-level demo index.
    for p in Path(".").glob("*/index.html"):
        slug = p.parent.name
        if valid_slug(slug):
            slugs.add(slug)

    # Include routes already written to the outreach Sheet. These may expose an URL typo
    # that never existed in Git history.
    if EXPECTED.exists():
        for raw in EXPECTED.read_text(encoding="utf-8").splitlines():
            slug = raw.strip().strip("/")
            if slug and not slug.startswith("#") and valid_slug(slug):
                slugs.add(slug)
    return sorted(slugs)


def latest_revision(path):
    return git("rev-list", "-n", "1", "--all", "--", path, check=False).strip()


def restore_path(path):
    rev = latest_revision(path)
    if not rev:
        return None
    git("checkout", rev, "--", path)
    return rev


def restore():
    slugs = historical_slugs()
    restored = []
    unresolved = []
    already_present = []

    for slug in slugs:
        index = Path(slug) / "index.html"
        if index.exists():
            already_present.append(slug)
        else:
            rev = restore_path(str(index))
            if rev:
                restored.append({"path": str(index), "from_commit": rev})
            else:
                unresolved.append({"slug": slug, "reason": "no index.html found in git history"})
                continue

        # Preserve whichever mobile preview format the historical site actually used.
        preview_png = Path(slug) / "preview-mobile.png"
        preview_svg = Path(slug) / "preview-mobile.svg"
        if not preview_png.exists() and not preview_svg.exists():
            for preview in (preview_png, preview_svg):
                rev = restore_path(str(preview))
                if rev:
                    restored.append({"path": str(preview), "from_commit": rev})
                    break

    report = {
        "mode": "restore",
        "total_expected_routes": len(slugs),
        "already_present": len(already_present),
        "restored_path_count": len(restored),
        "restored_paths": restored,
        "unresolved_count": len(unresolved),
        "unresolved": unresolved,
        "slugs": slugs,
    }
    REPORT_RESTORE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def request_url(url, timeout=20):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SCH-Agency-Pages-404-Audit/1.0",
            "Cache-Control": "no-cache",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(32768).decode("utf-8", "ignore").lower()
            status = int(getattr(r, "status", r.getcode()))
            ctype = r.headers.get("content-type", "")
            gh404 = "file not found" in body and "github pages" in body
            return {"status": status, "content_type": ctype, "github_pages_404": gh404, "error": ""}
    except urllib.error.HTTPError as e:
        body = e.read(32768).decode("utf-8", "ignore").lower()
        return {
            "status": int(e.code),
            "content_type": e.headers.get("content-type", "") if e.headers else "",
            "github_pages_404": "file not found" in body and "github pages" in body,
            "error": str(e),
        }
    except Exception as e:
        return {"status": None, "content_type": "", "github_pages_404": False, "error": repr(e)}


def check_slug(slug):
    url = f"{BASE}/{slug}/"
    preview_candidates = [
        f"{BASE}/{slug}/preview-mobile.png",
        f"{BASE}/{slug}/preview-mobile.svg",
    ]
    page = request_url(url)
    preview = None
    for u in preview_candidates:
        r = request_url(u)
        if r["status"] is not None and 200 <= r["status"] < 300:
            preview = {"url": u, **r}
            break
        if preview is None:
            preview = {"url": u, **r}
    ok = bool(page["status"] and 200 <= page["status"] < 300 and not page["github_pages_404"])
    return {"slug": slug, "url": url, "ok": ok, "page": page, "preview": preview}


def audit():
    slugs = historical_slugs()
    latest = []
    # Pages deployment after a restoration commit can be eventually consistent.
    # Retry only failing routes; successful routes are retained.
    pending = set(slugs)
    rows_by_slug = {}
    for attempt in range(1, 7):
        if not pending:
            break
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            rows = list(ex.map(check_slug, sorted(pending)))
        for row in rows:
            row["attempt"] = attempt
            rows_by_slug[row["slug"]] = row
        pending = {r["slug"] for r in rows if not r["ok"]}
        if pending and attempt < 6:
            print(f"Attempt {attempt}: {len(pending)} routes still failing; waiting for Pages propagation...", flush=True)
            time.sleep(20)

    latest = [rows_by_slug[s] for s in slugs]
    failed = [r for r in latest if not r["ok"]]
    report = {
        "mode": "audit",
        "base_url": BASE,
        "total_routes": len(latest),
        "passed": len(latest) - len(failed),
        "failed": len(failed),
        "all_ok": len(failed) == 0,
        "failed_routes": failed,
        "items": latest,
    }
    REPORT_AUDIT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("total_routes", "passed", "failed", "all_ok")}, ensure_ascii=False))
    if failed:
        for r in failed:
            print(f"FAIL {r['slug']}: {r['page']}")
    return 0 if not failed else 2


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"restore", "audit"}:
        print("Usage: all_pages_404_repair.py restore|audit", file=sys.stderr)
        return 64
    return restore() if sys.argv[1] == "restore" else audit()


if __name__ == "__main__":
    raise SystemExit(main())
