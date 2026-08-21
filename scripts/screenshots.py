"""Capture full-page screenshots of the OctoPOS SQLAdmin panel.

Targets the server-rendered admin UI (``/admin``) that documents the main
product surface: dashboard, core model lists, reports, and the restock
workflow. Requires a running dev stack and the plaintext admin bootstrap
(non-production ``ADMIN_USERNAME``/``ADMIN_PASSWORD``).

Usage:
    BASE_URL=http://localhost:8001 python scripts/screenshots.py
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "docs/images"))

PAGES = [
    ("dashboard", "/admin"),
    ("orders", "/admin/order/list"),
    ("products", "/admin/product/list"),
    ("customers", "/admin/customer/list"),
    ("drawer-sessions", "/admin/drawer-session/list"),
    ("purchase-orders", "/admin/purchase-order/list"),
    ("reports", "/admin/reports"),
    ("restock-workflow", "/admin/workflows/restock"),
]

VIEWPORT = {"width": 1440, "height": 900}


def capture() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=1)

        page.goto(f"{BASE_URL}/admin/login", wait_until="networkidle")
        page.fill('input[name="username"]', ADMIN_USERNAME)
        page.fill('input[name="password"]', ADMIN_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        if "/login" in page.url:
            raise SystemExit(
                f"login failed — check ADMIN_USERNAME/ADMIN_PASSWORD for {BASE_URL}"
            )

        for name, path in PAGES:
            page.goto(f"{BASE_URL}{path}", wait_until="networkidle")
            page.wait_for_timeout(600)
            out = OUTPUT_DIR / f"{name}.png"
            page.screenshot(path=str(out), full_page=True)
            print(f"{path} -> {out}")

        browser.close()


if __name__ == "__main__":
    capture()
