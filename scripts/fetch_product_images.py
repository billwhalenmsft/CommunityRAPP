"""Fetch product images from Navico websites using Playwright."""
import os
from playwright.sync_api import sync_playwright

img_dir = os.path.join("customers", "navico", "d365", "demo-assets", "product-images")
os.makedirs(img_dir, exist_ok=True)

products = [
    ("SIM-NSX-3007", "https://www.simrad-yachting.com/chartplotters/nsx-ultrawide/nsx-3007/"),
    ("LWR-HDS9-LIVE", "https://www.lowrance.com/fishfinders-chartplotters/hds-live/hds-9-live/"),
    ("BG-Triton2", "https://www.bandg.com/sailing-instruments/triton2/triton2-digital-display/"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for name, url in products:
        try:
            page.goto(url, timeout=25000, wait_until="networkidle")

            img_srcs = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('img')).map(img => ({
                    src: img.src || img.getAttribute('data-src') || '',
                    alt: img.alt || '',
                    w: img.naturalWidth || 0,
                    h: img.naturalHeight || 0
                })).filter(i => i.src && i.src.length > 10)
            }""")

            print(f"{name}: {len(img_srcs)} images found")
            for img in img_srcs[:15]:
                print(f"  {img['w']}x{img['h']} alt=\"{img['alt'][:40]}\" src={img['src'][:100]}")

            # Try to download the largest product image
            best = None
            for img in sorted(img_srcs, key=lambda x: x["w"] * x["h"], reverse=True):
                src = img["src"]
                if any(skip in src.lower() for skip in ["logo", "icon", "svg", "pixel", "tracking", "badge"]):
                    continue
                if img["w"] >= 200 and img["h"] >= 200:
                    best = img
                    break

            if best:
                print(f"  -> Best: {best['src'][:100]}")
                try:
                    resp = page.request.get(best["src"])
                    if resp.ok and len(resp.body()) > 5000:
                        body = resp.body()
                        if body[:2] == b"\xff\xd8":
                            ext = ".jpg"
                        elif body[:4] == b"\x89PNG":
                            ext = ".png"
                        elif body[:4] == b"RIFF":
                            ext = ".webp"
                        else:
                            ext = ".jpg"
                        path = os.path.join(img_dir, name + ext)
                        with open(path, "wb") as f:
                            f.write(body)
                        print(f"  SAVED: {name}{ext} ({len(body)//1024}KB)")
                    else:
                        print(f"  Download failed: {resp.status} / {len(resp.body())} bytes")
                except Exception as e:
                    print(f"  Download error: {e}")
            else:
                print(f"  No suitable image found")
        except Exception as e:
            print(f"ERROR: {name} - {e}")

    browser.close()

print("\nFiles in product-images/:")
for f in os.listdir(img_dir):
    fpath = os.path.join(img_dir, f)
    print(f"  {f} ({os.path.getsize(fpath)//1024}KB)")
