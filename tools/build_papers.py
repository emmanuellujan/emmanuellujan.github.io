"""Generate a page per paper from index.html's data plus the editorial overlay.

Run:  python3 tools/extract_papers.py && python3 tools/build_papers.py

Writes papers/<slug>/{index.html,citation.bib,card.png} and prints the links
and sitemap entries to add. Pages listed in papers.edit.json's _skip are left
alone — those were hand-built and carry bespoke figures.
"""
import html
import io
import json
import os
import re

from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/eljn/projects/emmanuellujan.github.io"
BASE = "https://www.emmanuellujan.com"
FONTS = "/usr/share/fonts/opentype/inter"

auto = {p["key"]: p for p in json.load(io.open(f"{ROOT}/tools/papers.auto.json", encoding="utf-8"))}
edit = json.load(io.open(f"{ROOT}/tools/papers.edit.json", encoding="utf-8"))
SKIP = set(edit.get("_skip", []))

E = html.escape


def render_bibtex(raw):
    """The stored BibTeX is JS template-literal source; collapse its escapes."""
    return raw.replace("\\\\", "\\")


def kind_of(p):
    tags = " ".join(p["tags"]).lower()
    if "preprint" in tags:
        return "preprint"
    if "journal" in tags:
        return "journal"
    return "conference"


def venue_short(p):
    """A compact venue for the eyebrow and card, cut on a word boundary."""
    v = p["venue"]
    v = re.sub(r",?\s*\d{4}\s*$", "", v)              # trailing year
    v = re.sub(r",?\s*vol\.\s*[\dIVX]+\.?", "", v, flags=re.I)
    v = re.sub(r",?\s*pp\.\s*[\d\u2013\u2014-]+", "", v, flags=re.I)
    v = re.sub(r"^PROCEEDINGS,\s*", "", v, flags=re.I)  # generic prefix
    head = v.split(",")[0].strip()
    if len(head) >= 18:
        v = head
    v = v.strip(" ,")
    if len(v) > 48:                                     # never split a word
        v = v[:48].rsplit(" ", 1)[0].rstrip(" ,") + "…"
    return v


# ── social card ─────────────────────────────────────────────────────────────
def make_card(p, meta, path):
    RED, INK, MUTED, FAINT = "#750014", "#000000", "#40464c", "#626a73"
    W, H, PAD = 1200, 630, 64
    card = Image.new("RGB", (W, H), "#ffffff")
    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, W, 10], fill=RED)

    f_eye = ImageFont.truetype(f"{FONTS}/Inter-SemiBold.otf", 19)
    f_title = ImageFont.truetype(f"{FONTS}/Inter-Bold.otf", 50)
    f_auth = ImageFont.truetype(f"{FONTS}/Inter-Regular.otf", 22)
    f_take = ImageFont.truetype(f"{FONTS}/Inter-Medium.otf", 25)
    f_foot = ImageFont.truetype(f"{FONTS}/Inter-Medium.otf", 19)

    def tracked(xy, text, font, fill, track=2.4):
        x, y = xy
        for ch in text:
            d.text((x, y), ch, font=font, fill=fill)
            x += d.textlength(ch, font=font) + track

    def wrap(text, font, max_w):
        lines, cur = [], ""
        for w_ in text.split():
            t = f"{cur} {w_}".strip()
            if d.textlength(t, font=font) <= max_w:
                cur = t
            else:
                lines.append(cur)
                cur = w_
        if cur:
            lines.append(cur)
        return lines

    TW = W - 2 * PAD
    label = {"journal": "JOURNAL ARTICLE", "conference": "CONFERENCE PAPER", "preprint": "PREPRINT"}[kind_of(p)]
    tracked((PAD, 76), f"{label}  ·  {venue_short(p).upper()}  ·  {p['year']}"[:74], f_eye, RED)

    y = 116
    title_lines = wrap(p["title"], f_title, TW)
    if len(title_lines) > 4:
        f_title = ImageFont.truetype(f"{FONTS}/Inter-Bold.otf", 40)
        title_lines = wrap(p["title"], f_title, TW)
    for line in title_lines[:5]:
        d.text((PAD, y), line, font=f_title, fill=INK)
        y += f_title.size + 10

    y += 16
    for line in wrap(meta["takeaway"], f_take, TW)[:2]:
        d.text((PAD, y), line, font=f_take, fill=MUTED)
        y += 34

    names = [a["name"] for a in p["authors"]]
    shown = "  ·  ".join(names if len(names) <= 4 else names[:3] + [f"+{len(names) - 3} more"])
    for line in wrap(shown, f_auth, TW)[:2]:
        y += 30
        d.text((PAD, y), line, font=f_auth, fill=FAINT)

    d.line([PAD, H - 62, W - PAD, H - 62], fill="#dde1e6", width=1)
    d.text((PAD, H - 44), "MIT CSAIL", font=f_foot, fill=RED)
    foot = "emmanuellujan.com"
    d.text((W - PAD - d.textlength(foot, font=f_foot), H - 44), foot, font=f_foot, fill=FAINT)
    card.save(path, optimize=True)


# ── page ────────────────────────────────────────────────────────────────────
CSS = io.open(f"{ROOT}/tools/paper_page.css", encoding="utf-8").read()

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Emmanuel Lujan</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{url}">
  <meta name="theme-color" content="#750014">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%23750014'/%3E%3Ctext x='32' y='44' text-anchor='middle' font-family='Georgia,serif' font-size='36' fill='white'%3EEL%3C/text%3E%3C/svg%3E">

  <meta name="citation_title" content="{title}">
{citation_authors}
  <meta name="citation_publication_date" content="{year}">
  <meta name="{venue_field}" content="{venue_full}">{doi_meta}
  <meta name="citation_abstract_html_url" content="{url}">{pdf_meta}
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Emmanuel Lujan">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{url}card.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{title} — {authors_plain}. {venue_full}.">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{url}card.png">
  <meta name="twitter:title" content="{short_title}">
  <meta name="twitter:description" content="{description}">
  <script type="application/ld+json">
{jsonld}
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
{css}  </style>
</head>
<body>
  <a class="skip-link" href="#paper">Skip to paper</a>
  <header class="site-header">
    <nav class="header-inner" aria-label="Main navigation">
      <div><a class="brand" href="../../index.html">Emmanuel Lujan</a><span class="affiliation">MIT CSAIL</span></div>
      <a class="back-link" href="../../index.html#publications">← All publications</a>
    </nav>
  </header>
  <main id="paper">
    <article aria-labelledby="paper-title">
      <header>
        <p class="eyebrow">{kind_label} · {venue_short} {year}</p>
        <h1 id="paper-title">{title}</h1>
        <p class="authors">{authors_html}</p>
        <p class="venue">{venue_full}</p>
        <div class="actions" aria-label="Paper resources">
{actions}
          <a class="button" href="#cite">Cite this paper <span aria-hidden="true">↓</span></a>
        </div>
      </header>

      <div class="paper-body">
        <section class="abstract" aria-labelledby="abstract-title">
          <h2 id="abstract-title">Abstract</h2>
{abstract_html}
          <p class="source-note">{source_note}</p>
        </section>
      </div>

      <section class="section" id="cite" aria-labelledby="cite-title">
        <div class="citation-heading">
          <h2 id="cite-title">Cite this paper</h2>
          <a href="citation.bib" download="{key}.bib">Download .bib ↓</a>
        </div>
        <p class="citation-text">{citation_text}</p>
        <div class="bibtex-box">
          <div class="bibtex-toolbar">
            <span class="bibtex-label">BibTeX · {kind_label}</span>
            <button class="button copy-button" id="copy-bibtex" type="button" hidden>Copy BibTeX</button>
          </div>
          <pre tabindex="0" aria-label="BibTeX citation"><code id="bibtex">{bibtex}</code></pre>
        </div>
        <p class="copy-status" id="copy-status" role="status" aria-live="polite"></p>
      </section>

      <section class="section related" aria-labelledby="related-title">
        <div>
          <h2 id="related-title">Related work</h2>
          <ul class="related-list">
{related}
          </ul>
        </div>
        <a href="../../index.html#publications">All publications →</a>
      </section>
    </article>
  </main>
  <footer class="site-footer" aria-label="Site footer">
    <div class="footer-inner">
      <div>
        <div class="footer-kicker">MIT CSAIL</div>
        <div class="footer-name">Emmanuel Lujan, Ph.D.</div>
        <p class="footer-affil">Research Scientist<br>MIT Computer Science &amp; Artificial Intelligence Laboratory</p>
      </div>
    </div>
    <p class="disclaimer">Some metadata, abstracts, and links on this page were AI-assisted and may contain inaccuracies.</p>
    <div class="footer-bottom">
      <span>&copy; 2026 Emmanuel Lujan. All rights reserved.</span>
      <span>Last updated: September 2026</span>
    </div>
  </footer>
  <script>
    const copyButton = document.getElementById('copy-bibtex');
    const bibtex = document.getElementById('bibtex');
    const copyStatus = document.getElementById('copy-status');
    copyButton.hidden = false;
    copyButton.addEventListener('click', async () => {{
      try {{
        await navigator.clipboard.writeText(bibtex.textContent.trim() + '\\n');
        copyStatus.textContent = 'BibTeX copied to clipboard.';
      }} catch {{
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(bibtex);
        selection.removeAllRanges();
        selection.addRange(range);
        copyStatus.textContent = 'Automatic copying is unavailable. The citation is selected for you to copy, or you can download the .bib file.';
      }}
    }});
  </script>
</body>
</html>
"""

DOC_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            '<path d="M6 2h8l4 4v16H6z"/><path d="M14 2v5h4M9 12h6M9 16h6"/></svg>')

ALL = {k: v for k, v in edit.items() if not k.startswith("_")}
ALL["lujan2025structure"] = {"slug": "when-structure-is-silent",
                             "cluster": "Algorithmic discovery",
                             "keywords": ["Algorithmic dispatch", "Structured matrices",
                                          "LU factorization", "High-performance computing"]}
ALL["marino2021openep"] = {"slug": "openep-electroporation-simulator",
                           "cluster": "Electroporation",
                           "keywords": ["Electroporation", "Tumor treatment simulation",
                                        "Electrochemotherapy", "Gene electrotransfer",
                                        "Shared-memory parallelism"]}


def related_to(key, n=3):
    """Same cluster first — the author's own grouping from ~/publications/.

    Ordered by shared keywords then recency. Papers alone in their cluster get
    no siblings rather than a link invented from a coincidental keyword.
    """
    mine_cluster = ALL[key].get("cluster")
    if not mine_cluster:
        return []
    mine_kw = {k.lower() for k in ALL[key]["keywords"]}
    sibs = []
    for other, meta_o in ALL.items():
        if other == key or meta_o.get("cluster") != mine_cluster:
            continue
        shared = len(mine_kw & {k.lower() for k in meta_o["keywords"]})
        sibs.append((shared, int(auto[other]["year"]) if auto[other]["year"].isdigit() else 0, other))
    sibs.sort(key=lambda t: (-t[0], -t[1]))
    return [k for _, _, k in sibs[:n]]


KIND_LABEL = {"journal": "Journal article", "conference": "Conference paper", "preprint": "Preprint"}
built, report = [], []

for key, meta in edit.items():
    if key.startswith("_") or key in SKIP:
        continue
    p = auto[key]
    slug = meta["slug"]
    url = f"{BASE}/papers/{slug}/"
    outdir = f"{ROOT}/papers/{slug}"
    os.makedirs(outdir, exist_ok=True)
    kind = kind_of(p)

    names = [a["name"] for a in p["authors"]]
    authors_html = '<span aria-hidden="true"> &nbsp;·&nbsp; </span>'.join(
        f'<a href="../../index.html">{E(a["name"])}</a>' if a["me"]
        else f'<span class="coauthor">{E(a["name"])}</span>' for a in p["authors"])
    citation_authors = "\n".join(
        f'  <meta name="citation_author" content="{E(n.split()[-1])}, {E(" ".join(n.split()[:-1]))}">'
        for n in names)

    desc = f'{meta["takeaway"]} {p["venue"]}.'
    if len(desc) > 300:
        desc = desc[:297] + "…"

    doi_meta = f'\n  <meta name="citation_doi" content="{E(p["doi"])}">' if p["doi"] else ""
    pdf_meta = f'\n  <meta name="citation_pdf_url" content="{E(meta["pdf"])}">' if meta.get("pdf") else ""
    venue_field = "citation_journal_title" if kind == "journal" else "citation_conference_title"
    if kind == "preprint":
        venue_field = "citation_journal_title"

    actions = []
    if meta.get("link") and not meta.get("pdf"):
        # Full text exists but could not be verified as a direct PDF, so it is
        # offered as a link without claiming citation_pdf_url.
        actions.append(f'          <a class="button primary" href="{E(meta["link"])}">\n'
                       f'            {DOC_ICON}\n            Full text <span aria-hidden="true">↗</span>\n          </a>')
    if meta.get("pdf"):
        actions.append(f'          <a class="button primary" href="{E(meta["pdf"])}">\n'
                       f'            {DOC_ICON}\n            Read PDF <span aria-hidden="true">↗</span>\n          </a>')
    # Prefer the DOI for the publisher link: raw publisher URLs rot, and some
    # (Elsevier in particular) answer visitors with a bot challenge.
    if p["doi"]:
        cls = "button" if actions else "button primary"
        actions.append(f'          <a class="{cls}" href="https://doi.org/{E(p["doi"])}">'
                       f'Publisher <span aria-hidden="true">↗</span></a>')
    def same_target(a, b):
        """OJS serves one galley at both /view/ and /download/."""
        if not a or not b:
            return False
        return a.replace("/download/", "/view/") == b.replace("/download/", "/view/")

    drop = set(meta.get("drop", []))
    for l in p["links"]:
        if l["url"] in drop:
            continue                       # verified inaccessible; see papers.edit.json
        if same_target(l["url"], meta.get("pdf")) or same_target(l["url"], meta.get("link")):
            continue
        if l["label"] in ("Publisher", "DOI") and p["doi"]:
            continue                        # already covered by the DOI button
        label = "Publisher" if l["label"] == "DOI" else l["label"]
        cls = "button" if actions else "button primary"
        actions.append(f'          <a class="{cls}" href="{E(l["url"])}">{label} <span aria-hidden="true">↗</span></a>')

    lang_attr = ' lang="es"' if meta.get("lang") == "es" else ""
    paras = re.split(r"(?<=[.;])\s+(?=[A-ZÁÉÍÓÚÑ])", p["abstract"])
    chunks, cur = [], ""
    for s_ in paras:
        cur = f"{cur} {s_}".strip()
        if len(cur) > 380:
            chunks.append(cur)
            cur = ""
    if cur:
        chunks.append(cur)
    abstract_html = "\n".join(f"          <p{lang_attr}>{E(c)}</p>" for c in chunks)

    src_bits = []
    if meta.get("pdf"):
        src_bits.append(f'The full text is available as a <a href="{E(meta["pdf"])}">PDF</a>')
    if p["doi"]:
        src_bits.append(f'the version of record is at <a href="https://doi.org/{E(p["doi"])}">doi:{E(p["doi"])}</a>')
    source_note = "; ".join(src_bits) + "." if src_bits else f'Published in {E(p["venue"])}.'
    source_note = source_note[0].upper() + source_note[1:]

    jsonld = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "@id": f"{url}#article",
        "headline": p["title"], "name": p["title"],
        "author": [
            ({"@type": "Person", "name": a["name"], "url": f"{BASE}/",
              "sameAs": "https://orcid.org/0000-0002-5945-4766"} if a["me"]
             else {"@type": "Person", "name": a["name"]}) for a in p["authors"]],
        "datePublished": p["year"], "url": url,
        "isPartOf": {"@type": "Periodical" if kind != "conference" else "PublicationEvent",
                     "name": p["venue"]},
        "inLanguage": "es" if meta.get("lang") == "es" else "en",
        "keywords": meta["keywords"],
    }
    if p["doi"]:
        jsonld["identifier"] = {"@type": "PropertyValue", "propertyID": "DOI", "value": p["doi"]}
        jsonld["sameAs"] = [f'https://doi.org/{p["doi"]}']

    cite_names = ", ".join(names[:-1]) + (" and " + names[-1] if len(names) > 1 else names[0] if names else "")
    citation_text = f'{E(cite_names)}, &ldquo;{E(p["title"])},&rdquo; <em>{E(p["venue"])}</em>.'
    if p["doi"]:
        citation_text += f'<br><a class="doi" href="https://doi.org/{E(p["doi"])}">doi:{E(p["doi"])}</a>'

    bib = render_bibtex(p["bibtex"])
    io.open(f"{outdir}/citation.bib", "w", encoding="utf-8").write(bib.strip() + "\n")
    make_card(p, meta, f"{outdir}/card.png")

    page = PAGE.format(
        title=E(p["title"]), short_title=E(p["title"][:60]), description=E(desc),
        url=url, year=E(p["year"]), citation_authors=citation_authors,
        venue_field=venue_field, venue_full=E(p["venue"]), venue_short=E(venue_short(p)),
        doi_meta=doi_meta, pdf_meta=pdf_meta, authors_plain=E(", ".join(names)),
        authors_html=authors_html, kind_label=KIND_LABEL[kind],
        actions="\n".join(actions), abstract_html=abstract_html, source_note=source_note,
        takeaway=E(meta["takeaway"]), context=E(meta["context"]),
        topics="\n".join(f"            <li>{E(k)}</li>" for k in meta["keywords"]),
        key=key, citation_text=citation_text, bibtex=E(bib.strip()),
        related="\n".join([
            f'            <li><a href="../../index.html#publications">All publications by Emmanuel Lujan</a></li>'
        ] if not related_to(key) else [
            f'            <li><a href="../{ALL[r]["slug"]}/">{E(auto[r]["title"])}</a>'
            f' <span class="rel-year">{E(auto[r]["year"])}</span></li>'
            for r in related_to(key)]),
        jsonld=json.dumps(jsonld, indent=4, ensure_ascii=False), css=CSS)
    io.open(f"{outdir}/index.html", "w", encoding="utf-8").write(page)

    built.append((key, slug, bool(meta.get("pdf"))))

print(f"built {len(built)} pages\n")
for key, slug, has_pdf in built:
    print(f"  {'pdf' if has_pdf else '   '}  papers/{slug}/   ({key})")
