"""Pull the publication data already in index.html into a machine-readable file.

index.html is the source of truth for titles, authors, venues, abstracts and
BibTeX; this keeps the generated paper pages from drifting away from it.
"""
import html
import io
import json
import re

import os
ROOT = os.environ.get("SITE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = f"{ROOT}/index.html"
OUT = f"{ROOT}/tools/papers.auto.json"

s = io.open(SRC, encoding="utf-8").read()

bibblock = re.search(r"const bibtex = \{(.*?)\n\};", s, re.S).group(1)
BIB = dict(re.findall(r"\n  (\w+): `(.*?)`", bibblock, re.S))


def text(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x))).strip()


papers = []
for m in re.finditer(r'<li class="pub-item[^"]*">(.*?)</li>', s, re.S):
    b = m.group(1)
    km = re.search(r"toggleAbstract\('([^']+)'", b) or re.search(r"copyBib\('([^']+)'", b)
    if not km:
        continue                                   # manuscript in preparation
    key = km.group(1)
    absm = re.search(r'<div class="pub-abstract"[^>]*>(.*?)</div>', b, re.S)
    if not absm:
        continue

    title_m = re.search(r'<div class="pub-title">(?:<a[^>]*>)?(.*?)(?:</a>)?\s*(?:<span|</div>)', b, re.S)
    authors_m = re.search(r'<div class="pub-authors">(.*?)</div>', b, re.S)
    venue_m = re.search(r'<div class="pub-venue"><em>(.*?)</em>', b, re.S)
    year_m = re.search(r'pub-year-tag">(.*?)<', b)
    tags = [text(t) for t in re.findall(r'<span class="tag[^"]*">(.*?)</span>', b, re.S)]

    authors = []
    for part in re.split(r",\s*(?![^(]*\))", authors_m.group(1)):
        name = text(part)
        if name:
            authors.append({"name": name, "me": 'class="me"' in part})

    links = []
    title_href = re.search(r'<div class="pub-title"><a href="([^"]+)"', b)
    if title_href and title_href.group(1).startswith("http"):
        links.append({"url": html.unescape(title_href.group(1)), "label": "Publisher"})
    for href, label in re.findall(r'<a class="pub-btn" href="([^"]+)"[^>]*>(.*?)</a>', b, re.S):
        href = html.unescape(href)
        if href.startswith("http") and all(href != l["url"] for l in links):
            links.append({"url": href, "label": text(label) or "Link"})

    bib = BIB.get(key, "")
    doi = re.search(r"doi=\{(.*?)\}", bib)

    papers.append({
        "key": key,
        "title": text(title_m.group(1)) if title_m else "",
        "authors": authors,
        "venue": text(venue_m.group(1)) if venue_m else "",
        "year": text(year_m.group(1)) if year_m else "",
        "tags": tags,
        "abstract": text(absm.group(1)),
        "links": links,
        "doi": doi.group(1) if doi else None,
        "bibtex": bib,
    })

# wire_index.py rewrites each title link to papers/<slug>/, so a later run of
# this script can no longer see the publisher URL that used to be there. Merge
# with whatever was captured before so re-running never loses a link.
if os.path.exists(OUT):
    previous = {p["key"]: p for p in json.load(io.open(OUT, encoding="utf-8"))}
    for p in papers:
        old_links = previous.get(p["key"], {}).get("links", [])
        have = {l["url"] for l in p["links"]}
        for l in old_links:
            if l["url"] not in have:
                p["links"].append(l)
        if not p["doi"]:
            p["doi"] = previous.get(p["key"], {}).get("doi")

io.open(OUT, "w", encoding="utf-8").write(json.dumps(papers, indent=2, ensure_ascii=False) + "\n")
print(f"extracted {len(papers)} papers -> {OUT}")
for p in papers:
    print(f"  {p['key']:<30} doi={'yes' if p['doi'] else ' no'}  links={len(p['links'])}  authors={len(p['authors'])}")
