#!/usr/bin/env python3
import json
import pathlib
import sys
import time
from playwright.sync_api import sync_playwright

BASE = "https://dschaffer2006-cmd.github.io/sch-agency-demos/outreach"
PAGES = [
    ("LD-003-012", "kolibri-szepsegszalon", "Kolibri Szépségszalon és Szolárium"),
    ("LD-003-016", "image-szepsegszalon", "Image Szépségszalon"),
    ("LD-003-017", "roa-beauty", "ROA Beauty Szépségszalon"),
    ("LD-003-019", "frufru-szekesfehervar", "Frufru Székesfehérvár"),
    ("LD-003-021", "aniko-koromszalon", "Anikó Körömszalon"),
]
OUT = pathlib.Path("qa-artifacts/worker3-live")
OUT.mkdir(parents=True, exist_ok=True)

def url_for(lead_id, slug):
    return f"{BASE}/{lead_id}-{slug}/"

def goto_with_retry(page, url, attempts=8, wait_seconds=15):
    last = None
    for i in range(1, attempts + 1):
        try:
            response = page.goto(url, wait_until="networkidle", timeout=30000)
            status = response.status if response else None
            if status and 200 <= status < 300:
                return response, i
            last = f"HTTP {status}"
        except Exception as exc:
            last = repr(exc)
        if i < attempts:
            print(f"WAIT {url} attempt={i} reason={last}", flush=True)
            time.sleep(wait_seconds)
    raise RuntimeError(f"Live URL unavailable after {attempts} attempts: {url}; last={last}")

def headline_fits(page, width):
    box = page.locator("h1").first.bounding_box()
    return bool(box and box["width"] > 0 and box["height"] > 0 and box["x"] >= -2 and box["x"] + box["width"] <= width + 2)

def expose_reveals(page):
    page.evaluate("document.querySelectorAll('[data-reveal]').forEach(e=>e.classList.add('visible'))")
    page.wait_for_timeout(100)

def run():
    report = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        for lead_id, slug, company in PAGES:
            url = url_for(lead_id, slug)
            problems = []
            row = {"lead_id": lead_id, "company": company, "url": url, "desktop": {}, "mobile": {}, "reduced_motion": {}}

            page = browser.new_page(viewport={"width": 1440, "height": 900})
            console_errors, page_errors, request_failures = [], [], []
            page.on("console", lambda msg, arr=console_errors: arr.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda exc, arr=page_errors: arr.append(str(exc)))
            page.on("requestfailed", lambda req, arr=request_failures: arr.append(req.url))
            try:
                response, attempts = goto_with_retry(page, url)
                page.wait_for_timeout(600)
                row["desktop"]["http"] = response.status
                row["desktop"]["attempts"] = attempts
                row["desktop"]["title"] = page.title()
                row["desktop"]["console_errors"] = console_errors
                row["desktop"]["page_errors"] = page_errors
                row["desktop"]["request_failures"] = request_failures
                if console_errors: problems.append("desktop.console")
                if page_errors: problems.append("desktop.pageerror")
                if request_failures: problems.append("desktop.requestfailed")
                if page.locator('meta[name="viewport"]').count() != 1: problems.append("viewport.meta")
                if not page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"): problems.append("desktop.overflow")
                if not headline_fits(page, 1440): problems.append("desktop.headline")
                body = page.locator("body").inner_text().lower()
                for forbidden in ("lorem ipsum", "todo", "image here", "photo here"):
                    if forbidden in body: problems.append("forbidden:" + forbidden)
                if "koncepciódemó – sch agency" not in body: problems.append("demo.disclaimer")
                if "demó időpontok – nem valós szabad helyek" not in body: problems.append("booking.demo-label")
                booking = page.locator("[data-booking]")
                if booking.count() != 1:
                    problems.append("booking.missing")
                else:
                    booking.locator('[data-key="service"]').first.click()
                    booking.locator('[data-key="date"]').first.click()
                    booking.locator('[data-key="time"]').first.click()
                    booking.locator('[name="name"]').fill("QA Minta")
                    booking.locator('[name="contact"]').fill("qa@example.test")
                    booking.locator('button[type="submit"]').click()
                    if not booking.get_by_text("Demó foglalás sikeres", exact=True).is_visible(): problems.append("booking.flow")
                expose_reveals(page)
                page.screenshot(path=str(OUT / f"{lead_id}-desktop.png"), full_page=True)
            except Exception as exc:
                problems.append("desktop.exception:" + repr(exc))
            finally:
                page.close()

            mobile = browser.new_page(viewport={"width": 390, "height": 844})
            console_errors, page_errors, request_failures = [], [], []
            mobile.on("console", lambda msg, arr=console_errors: arr.append(msg.text) if msg.type == "error" else None)
            mobile.on("pageerror", lambda exc, arr=page_errors: arr.append(str(exc)))
            mobile.on("requestfailed", lambda req, arr=request_failures: arr.append(req.url))
            try:
                response, attempts = goto_with_retry(mobile, url)
                mobile.wait_for_timeout(500)
                row["mobile"]["http"] = response.status
                row["mobile"]["attempts"] = attempts
                row["mobile"]["console_errors"] = console_errors
                row["mobile"]["page_errors"] = page_errors
                row["mobile"]["request_failures"] = request_failures
                if console_errors: problems.append("mobile.console")
                if page_errors: problems.append("mobile.pageerror")
                if request_failures: problems.append("mobile.requestfailed")
                if not mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"): problems.append("mobile.overflow")
                if not headline_fits(mobile, 390): problems.append("mobile.headline")
                menu = mobile.locator("[data-menu]")
                if not menu.is_visible():
                    problems.append("mobile.menu-button")
                else:
                    menu.click()
                    if not mobile.locator("[data-nav]").evaluate("e => e.classList.contains('open')"):
                        problems.append("mobile.menu-open")
                    mobile.locator('[data-nav] a[href="#szolgaltatasok"]').click()
                    if mobile.locator("[data-nav]").evaluate("e => e.classList.contains('open')"):
                        problems.append("mobile.menu-close")
                mobile.locator('[data-key="service"]').first.click()
                mobile.locator('[data-key="date"]').first.click()
                mobile.locator('[data-key="time"]').first.click()
                mobile.locator('[name="name"]').fill("QA Mobil")
                mobile.locator('[name="contact"]').fill("qa-mobile@example.test")
                mobile.locator('button[type="submit"]').click()
                if not mobile.get_by_text("Demó foglalás sikeres", exact=True).is_visible(): problems.append("mobile.booking-flow")
                expose_reveals(mobile)
                mobile.screenshot(path=str(OUT / f"{lead_id}-mobile.png"), full_page=True)
            except Exception as exc:
                problems.append("mobile.exception:" + repr(exc))
            finally:
                mobile.close()

            reduced = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
            try:
                response, attempts = goto_with_retry(reduced, url)
                reduced.wait_for_timeout(250)
                row["reduced_motion"]["http"] = response.status
                row["reduced_motion"]["attempts"] = attempts
                reveal_ok = reduced.evaluate("[...document.querySelectorAll('[data-reveal]')].every(e=>{const s=getComputedStyle(e);return Number(s.opacity)>0 && s.visibility!=='hidden'})")
                heading_ok = reduced.locator("h1").first.is_visible() and reduced.locator("h2").first.is_visible()
                if not (reveal_ok and heading_ok): problems.append("reduced-motion.readability")
                if not reduced.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"): problems.append("reduced-motion.overflow")
            except Exception as exc:
                problems.append("reduced.exception:" + repr(exc))
            finally:
                reduced.close()

            row["problems"] = problems
            row["result"] = "PASS" if not problems else "FAIL"
            report.append(row)
            print(f"{lead_id} {row['result']} {problems}", flush=True)
        browser.close()

    report_path = OUT / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    passed = sum(r["result"] == "PASS" for r in report)
    print(json.dumps({"total": len(report), "passed": passed, "failed": len(report)-passed}, ensure_ascii=False), flush=True)
    return 0 if passed == len(report) else 1

if __name__ == "__main__":
    raise SystemExit(run())
