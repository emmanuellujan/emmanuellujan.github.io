from PIL import Image, ImageDraw, ImageFont

SP = "/tmp/claude-1000/-home-eljn-projects-emmanuellujan-github-io/47216750-be82-4d82-9ec6-330efff50e2b/scratchpad"
F = "/usr/share/fonts/opentype/inter"
RED, INK, MUTED, FAINT = "#750014", "#000000", "#40464c", "#626a73"
W, H, PAD = 1200, 630, 64

card = Image.new("RGB", (W, H), "#ffffff")
d = ImageDraw.Draw(card)
d.rectangle([0, 0, W, 10], fill=RED)

f_eyebrow = ImageFont.truetype(f"{F}/Inter-SemiBold.otf", 19)
f_title = ImageFont.truetype(f"{F}/Inter-Bold.otf", 56)
f_sub = ImageFont.truetype(f"{F}/Inter-Medium.otf", 27)
f_auth = ImageFont.truetype(f"{F}/Inter-Regular.otf", 21)
f_foot = ImageFont.truetype(f"{F}/Inter-Medium.otf", 17)


def tracked(draw, xy, text, font, fill, track=2.4):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + track


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = f"{cur} {w_}".strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


TEXT_W = W - 2 * PAD
y = 76
tracked(d, (PAD, y), "JOURNAL ARTICLE  ·  SCIENTIFIC REPORTS  ·  2021", f_eyebrow, RED)

y = 106
d.text((PAD, y), "OpenEP", font=f_title, fill=INK)
y += 70

for line in wrap(d, "An open-source simulator for electroporation-based tumor treatments",
                 f_sub, TEXT_W):
    d.text((PAD, y), line, font=f_sub, fill=MUTED)
    y += 36
y += 14

d.text((PAD, y), "Matías Marino  ·  Emmanuel Lujan  ·  Esteban Mocskos  ·  Guillermo Marshall",
       font=f_auth, fill=FAINT)

# Figure 2: simulated temperature plumes around the electrodes.
fig = Image.open(f"{SP}/openep_fig2_strip.png").convert("RGB")
fw = W - 2 * PAD
fig = fig.resize((fw, round(fig.height * fw / fig.width)), Image.LANCZOS)
card.paste(fig, (PAD, 292))

d.line([PAD, H - 56, W - PAD, H - 56], fill="#dde1e6", width=1)
d.text((PAD, H - 40), "MIT CSAIL  ·  emmanuellujan.com", font=f_foot, fill=RED)
credit = "Fig. 2 · Marino et al., Sci Rep 11:1423 · CC BY 4.0"
d.text((W - PAD - d.textlength(credit, font=f_foot), H - 40), credit, font=f_foot, fill=FAINT)

out = ("/home/eljn/projects/emmanuellujan.github.io/papers/"
       "openep-electroporation-simulator/card.png")
card.save(out, optimize=True)
print("wrote", out, card.size)
