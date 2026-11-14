"""Scale-matched comparison against the reference illustration.

All three images are calibrated automatically from their own silhouette so the
comparison is honest: every panel is scaled so that hair-top -> sole spans the
same number of pixels, and the body axis is centred on the same column.
"""
from PIL import Image, ImageDraw
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / 'shots'
ART = Path(r'D:\workspace\myrepo\ai-video-workflow\outputs\phantom-blade-zero-sui\models'
           r'\new-outfit-20261114\single-image-trial-v1\sui-front-input.png')

RENDER_BG = (98, 102, 109)


def silhouettes(im, bg, tol):
    """Character mask.

    Background-coloured pixels are only removed when they are connected to the
    image border, so the illustration's white hair and the eye whites stay
    inside the silhouette instead of being punched out as holes.
    """
    a = np.asarray(im.convert('RGB')).astype(int)
    like_bg = np.abs(a - np.array(bg)).max(axis=2) <= tol
    m = Image.fromarray((like_bg * 255).astype(np.uint8), 'L').copy()
    ImageDraw.floodfill(m, (0, 0), 128)
    return np.asarray(m) != 128


def landmarks(im, m):
    """hair top (skipping the off-axis halo), sole, and body axis."""
    ys, xs = np.where(m)
    y0, y1 = int(ys.min()), int(ys.max())
    widths = m.sum(axis=1)
    # body axis: centre of the widest row band between hips and knees
    band = m[y0 + int((y1 - y0) * 0.56): y0 + int((y1 - y0) * 0.66)]
    bx = np.where(band.any(axis=0))[0]
    cx = float((bx.min() + bx.max()) / 2) if len(bx) else float((xs.min() + xs.max()) / 2)
    # hair top: first row that is reasonably wide and straddles the axis
    top = y0
    for y in range(y0, y1):
        row = np.where(m[y])[0]
        if len(row) < 40:
            continue
        if row.min() < cx - 12 and row.max() > cx + 12:
            top = y
            break
    return dict(top=top, bot=y1, cx=cx)


def place(im, m, lm, t_top, t_bot, t_cx, size, bg=(126, 126, 132)):
    span = lm['bot'] - lm['top']
    scale = (t_bot - t_top) / span
    w, h = int(round(im.width * scale)), int(round(im.height * scale))
    rgb = im.convert('RGB').resize((w, h), Image.LANCZOS)
    alpha = Image.fromarray((m * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)
    canvas = Image.new('RGB', size, bg)
    canvas.paste(rgb, (int(round(t_cx - lm['cx'] * scale)),
                       int(round(t_top - lm['top'] * scale))), alpha)
    return canvas, scale


def row_width(m, y):
    row = np.where(m[y])[0]
    return 0 if not len(row) else int(row.max() - row.min() + 1)


def main():
    art = Image.open(ART)
    v6 = Image.open(SHOTS / 'v6-front.png')
    v7 = Image.open(SHOTS / 'v7-front.png')

    ma = silhouettes(art, (255, 255, 255), 18)
    m6 = silhouettes(v6, RENDER_BG, 20)
    m7 = silhouettes(v7, RENDER_BG, 20)
    la, l6, l7 = landmarks(art, ma), landmarks(v6, m6), landmarks(v7, m7)

    # normalised width profile: how wide is the figure at a given height fraction
    print('landmarks')
    for tag, lm in (('art', la), ('v6', l6), ('v7', l7)):
        print(f'  {tag}: top={lm["top"]} bot={lm["bot"]} cx={lm["cx"]:.1f} '
              f'span={lm["bot"]-lm["top"]}')
    print('width / body height at fractions of hair-top->sole')
    print('  frac   art    v6     v7')
    for f in (0.18, 0.22, 0.26, 0.31, 0.38, 0.45):
        wa = row_width(ma, la['top'] + int((la['bot'] - la['top']) * f))
        w6 = row_width(m6, l6['top'] + int((l6['bot'] - l6['top']) * f))
        w7 = row_width(m7, l7['top'] + int((l7['bot'] - l7['top']) * f))
        sa, s6, s7 = (la['bot'] - la['top'], l6['bot'] - l6['top'], l7['bot'] - l7['top'])
        print(f'  {f:.2f}  {wa/sa:.3f}  {w6/s6:.3f}  {w7/s7:.3f}')

    H, TOP, BOT, PANEL = 1000, 60, 960, 980
    CX = PANEL // 2
    panels = []
    for im, m, lm in ((art, ma, la), (v6, m6, l6), (v7, m7, l7)):
        p, _ = place(im, m, lm, TOP, BOT, CX, (PANEL, H))
        d = ImageDraw.Draw(p)
        for f, lab in ((0.0, 'hair'), (0.18, 'shoulder'), (0.45, 'hip'), (1.0, 'sole')):
            y = TOP + int((BOT - TOP) * f)
            d.line([(0, y), (PANEL - 1, y)], fill=(255, 255, 255, 60), width=1)
            d.text((6, y + 2), lab, fill=(210, 210, 210))
        d.line([(CX, 0), (CX, H - 1)], fill=(255, 255, 255), width=1)
        panels.append(p)

    pad = 8
    strip = Image.new('RGB', (PANEL * 3 + pad * 2, H), (22, 22, 26))
    for i, p in enumerate(panels):
        strip.paste(p, (i * (PANEL + pad), 0))
    strip.save(SHOTS / 'compare-art-v6-v7.png')

    blend = Image.blend(panels[0], panels[2], 0.5)
    side = Image.new('RGB', (PANEL * 2 + pad, H), (22, 22, 26))
    side.paste(blend, (0, 0))
    side.paste(panels[2], (PANEL + pad, 0))
    side.save(SHOTS / 'compare-art-overlay.png')
    print('written')


main()
