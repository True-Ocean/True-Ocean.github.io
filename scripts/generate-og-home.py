#!/usr/bin/env python3
"""Generate assets/og-home.png from the top-page hero composition (1200x630)."""

from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "og-home.png"
POSTER = ROOT / "assets" / "chatnoir-poster-figure.png"
BANNER = ROOT / "assets" / "chatnoir-top-banner.png"

W, H = 1200, 630
PAPER = (240, 237, 230, 255)
MUTED = (170, 167, 159, 255)
GOLD = (216, 173, 97, 255)
GOLD_BRIGHT = (242, 212, 154, 255)


def find_font(pred):
    for path in Path("/System/Library/Fonts").iterdir():
        if pred(path.name):
            return path
    raise FileNotFoundError(pred)


def load_font(path, size, index=0):
    return ImageFont.truetype(str(path), size=size, index=index)


def radial_glow(size, cx, cy, radius, color, peak_alpha):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    px = layer.load()
    r, g, b = color
    r2 = radius * radius
    x0, x1 = max(0, int(cx - radius)), min(size[0], int(cx + radius) + 1)
    y0, y1 = max(0, int(cy - radius)), min(size[1], int(cy + radius) + 1)
    for y in range(y0, y1):
        dy = y - cy
        for x in range(x0, x1):
            d2 = (x - cx) * (x - cx) + dy * dy
            if d2 >= r2:
                continue
            t = 1.0 - (d2 ** 0.5) / radius
            a = int(peak_alpha * t * t)
            if a:
                px[x, y] = (r, g, b, a)
    return layer


def linear_gradient(size, stops, horizontal=True):
    img = Image.new("RGBA", size)
    px = img.load()
    w, h = size
    span = (w - 1) if horizontal else (h - 1)
    for i in range(span + 1):
        t = i / span
        for a, b in zip(stops, stops[1:]):
            if t <= b[0] or b is stops[-1]:
                local = 0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
                local = max(0.0, min(1.0, local))
                color = tuple(int(a[1][c] + (b[1][c] - a[1][c]) * local) for c in range(4))
                break
        if horizontal:
            for y in range(h):
                px[i, y] = color
        else:
            for x in range(w):
                px[x, i] = color
    return img


def cover_crop(im, tw, th, fx=0.5, fy=0.22):
    iw, ih = im.size
    scale = max(tw / iw, th / ih)
    nw, nh = max(tw, round(iw * scale)), max(th, round(ih * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = int(round(nw * fx - tw / 2))
    top = int(round(nh * fy - th / 2))
    left = max(0, min(left, nw - tw))
    top = max(0, min(top, nh - th))
    return im.crop((left, top, left + tw, top + th))


def fade_mask(width, height, opacity=0.86):
    mask = Image.new("L", (width, height), 0)
    px = mask.load()
    fade = max(1, int(width * 0.34))
    peak = int(255 * opacity)
    for x in range(width):
        t = 1.0 if x >= fade else x / fade
        val = int(peak * t)
        for y in range(height):
            px[x, y] = val
    return mask


def draw_tracked(draw, xy, text, font, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking
    return x


def load_banner(path, height=100, max_width=700):
    im = Image.open(path).convert("RGBA")
    gray = im.convert("L")
    bbox = gray.point(lambda p: 255 if p > 32 else 0).getbbox()
    if bbox:
        pad = 2
        left = max(0, bbox[0] - pad)
        top = max(0, bbox[1] - pad)
        right = min(im.width, bbox[2] + pad)
        bottom = min(im.height, bbox[3] + pad)
        im = im.crop((left, top, right, bottom))
    scale = height / im.height
    size = (max(1, round(im.width * scale)), height)
    if size[0] > max_width:
        scale = max_width / im.width
        size = (max_width, max(1, round(im.height * scale)))
    im = im.resize(size, Image.Resampling.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(1.35)
    im = ImageEnhance.Brightness(im).enhance(1.18)
    luma = im.convert("L")
    alpha = luma.point(lambda p: 0 if p < 26 else 255 if p > 48 else int((p - 26) * (255 / 22)))
    im.putalpha(alpha)
    return im.filter(ImageFilter.UnsharpMask(radius=1.4, percent=160, threshold=1))


def main():
    mincho_path = find_font(lambda n: "ProN.ttc" in n and "明朝" in n)
    sans_path = find_font(lambda n: n.endswith("W6.ttc") and "角" in n)
    menlo = Path("/System/Library/Fonts/Menlo.ttc")

    kicker_font = load_font(Path("/System/Library/Fonts/Supplemental/Georgia Bold.ttf"), 18)
    title_font = load_font(mincho_path, 68, index=2)
    lead_font = load_font(sans_path, 22)
    rule_font = load_font(menlo, 15, index=1)

    canvas = Image.new("RGBA", (W, H), (8, 9, 10, 255))
    canvas = Image.alpha_composite(
        canvas,
        radial_glow((W, H), int(W * 0.78), int(H * 0.28), 340, (232, 169, 56), 72),
    )
    canvas = Image.alpha_composite(
        canvas,
        radial_glow((W, H), int(W * 0.18), int(H * 0.88), 260, (185, 228, 83), 36),
    )

    poster_w = 520
    poster = Image.open(POSTER).convert("RGB")
    poster = ImageEnhance.Color(poster).enhance(0)
    poster = ImageEnhance.Contrast(poster).enhance(1.08)
    poster = cover_crop(poster, poster_w, H).convert("RGBA")
    poster.putalpha(fade_mask(poster_w, H, opacity=0.88))
    canvas.paste(poster, (W - poster_w, 0), poster)

    overlay = linear_gradient(
        (W, H),
        [
            (0.0, (18, 16, 14, 250)),
            (0.42, (18, 16, 14, 194)),
            (1.0, (18, 16, 14, 38)),
        ],
    )
    canvas = Image.alpha_composite(canvas, overlay)

    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grid)
    step = 38
    line = (240, 237, 230, 20)
    for x in range(0, W, step):
        gdraw.line((x, 0, x, H), fill=line)
    for y in range(0, H, step):
        gdraw.line((0, y, W, y), fill=line)
    fade = linear_gradient(
        (W, H),
        [(0.0, (255, 255, 255, 76)), (0.84, (255, 255, 255, 0)), (1.0, (255, 255, 255, 0))],
        horizontal=False,
    )
    grid.putalpha(ImageChops.multiply(grid.split()[-1], fade.split()[-1]))
    canvas = Image.alpha_composite(canvas, grid)

    banner = load_banner(BANNER)
    draw = ImageDraw.Draw(canvas)
    x0 = 56
    canvas.paste(banner, (x0, 18), banner)
    y = 18 + banner.size[1] + 18

    draw_tracked(draw, (x0, y), "INDEPENDENT APPLICATIONS / JAPAN", kicker_font, GOLD_BRIGHT, tracking=2.8)
    y += 46

    line1 = "好奇心のままに、"
    line2_gold = "新しい体験"
    line2_rest = "をつくる。"
    tracking = -68 * 0.075
    draw_tracked(draw, (x0, y), line1, title_font, PAPER, tracking=tracking)
    y += 78
    x = draw_tracked(draw, (x0, y), line2_gold, title_font, GOLD, tracking=tracking)
    draw_tracked(draw, (x, y), line2_rest, title_font, PAPER, tracking=tracking)
    y += 92

    for line in (
        "ChatNoir Studioは、",
        "遊び心と実用性をあわせ持つ",
        "様々なアプリケーションを個人開発しています。",
    ):
        draw.text((x0, y), line, font=lead_font, fill=MUTED)
        y += 34

    y += 28
    rule = "CREATE WITH CURIOSITY"
    rule_w = rule_font.getlength(rule) + 2.2 * (len(rule) - 1)
    rule_x = x0
    draw.line((rule_x, y + 8, rule_x + 72, y + 8), fill=GOLD, width=1)
    draw_tracked(draw, (rule_x + 86, y), rule, rule_font, GOLD, tracking=2.2)
    draw.line((rule_x + 86 + rule_w + 14, y + 8, rule_x + 86 + rule_w + 86, y + 8), fill=GOLD, width=1)

    canvas = canvas.filter(ImageFilter.UnsharpMask(radius=0.6, percent=80, threshold=2))
    canvas.convert("RGB").save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} {canvas.size}")


if __name__ == "__main__":
    main()
