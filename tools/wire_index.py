"""Point index.html's publication entries at their generated paper pages.

Idempotent: entries already pointing at papers/<slug>/ are left alone.
Also refreshes sitemap.xml with one entry per paper page.
"""
import io
import json
import re

ROOT = "/home/eljn/projects/emmanuellujan.github.io"
BASE = "https://www.emmanuellujan.com"
IDX = f"{ROOT}/index.html"
SITEMAP = f"{ROOT}/sitemap.xml"

edit = json.load(io.open(f"{ROOT}/tools/papers.edit.json", encoding="utf-8"))
slugs = {k: v["slug"] for k, v in edit.items() if not k.startswith("_")}
slugs["lujan2025structure"] = "when-structure-is-silent"
slugs["marino2021openep"] = "openep-electroporation-simulator"

ICON = ('<svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" '
        'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M2 1h5.5L10 3.5V11H2V1z"/><path d="M7 1v3h3"/></svg>')

s = io.open(IDX, encoding="utf-8").read()
linked, already = [], []

for key, slug in sorted(slugs.items()):
    page = f"papers/{slug}/"
    # Match each <li> on its own, then pick the one holding this key. A single
    # regex anchored at the document start would span from the first entry.
    block = None
    for cand in re.finditer(r'<li class="pub-item[^"]*">.*?</li>', s, re.S):
        if f"toggleAbstract('{key}'" in cand.group(0) or f"copyBib('{key}'" in cand.group(0):
            block = cand.group(0)
            break
    if block is None:
        print(f"  !! entry not found for {key}")
        continue
    if f'href="{page}"' in block:
        already.append(key)
        continue
    new = block

    # Title points at the paper page instead of the publisher.
    new = re.sub(r'(<div class="pub-title">)<a href="[^"]+"(?: target="_blank")?(?: rel="noopener")?>',
                 r'\1<a href="' + page + r'">', new, count=1)

    # A "Paper page" action leads the row.
    new = new.replace('<div class="pub-actions">',
                      f'<div class="pub-actions"><a class="pub-btn" href="{page}">\n'
                      f'            {ICON}\n            Paper page\n          </a>\n          ', 1)
    if new == block:
        print(f"  !! no change applied for {key}")
        continue
    s = s.replace(block, new, 1)
    linked.append((key, slug))

io.open(IDX, "w", encoding="utf-8").write(s)
print(f"linked {len(linked)} entries ({len(already)} already linked)")
for k, sl in linked:
    print(f"   {k:<30} -> papers/{sl}/")

# ── sitemap ────────────────────────────────────────────────────────────────
urls = [f"{BASE}/"] + [f"{BASE}/papers/{sl}/" for sl in sorted(slugs.values())]
body = "".join(
    f"  <url>\n    <loc>{u}</loc>\n    <lastmod>2026-09-20</lastmod>\n"
    f"    <changefreq>{'monthly' if u.endswith('.com/') else 'yearly'}</changefreq>\n"
    f"    <priority>{'1.0' if u.endswith('.com/') else '0.8'}</priority>\n  </url>\n"
    for u in urls)
io.open(SITEMAP, "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n")
print(f"sitemap.xml: {len(urls)} urls")
