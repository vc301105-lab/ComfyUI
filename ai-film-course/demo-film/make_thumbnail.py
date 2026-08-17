#!/usr/bin/env python3
"""Composit thumbnail.png (1280x720) from the film poster + DejaVu titles.

Run:  python3 make_thumbnail.py   ->  thumbnail.png
"""
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from pathlib import Path

HERE = Path(__file__).parent
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

im = Image.open(HERE / "frames" / "poster.png").convert("RGB")
sw, sh = im.size
scale = max(1280 / sw, 720 / sh)
im = im.resize((int(sw * scale), int(sh * scale)), Image.LANCZOS)
left = (im.width - 1280) // 2
top = (im.height - 720) // 2
im = im.crop((left, top, left + 1280, top + 720))

im = ImageEnhance.Contrast(im).enhance(1.08)
im = ImageEnhance.Color(im).enhance(1.05)

grad = Image.new("L", (1, 720), 0)
for y in range(720):
    grad.putpixel((0, y), int(200 * max(0.0, (y - 430) / 290) ** 1.4))
grad = grad.resize((1280, 720))
black = Image.new("RGB", (1280, 720), (0, 0, 0))
im = Image.composite(im, black, grad)

draw = ImageDraw.Draw(im)


def tracked(draw, xy, text, font, tracking, fill):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getbbox(ch)[2] + tracking


def center(text, size, tracking, y, fill=(255, 255, 255)):
    font = ImageFont.truetype(FONT, size)
    widths = [font.getbbox(ch)[2] + tracking for ch in text]
    total = sum(widths) - tracking
    tracked(draw, ((1280 - total) // 2 + 3, y + 3), text, font, tracking, (0, 0, 0))
    tracked(draw, ((1280 - total) // 2, y), text, font, tracking, fill)


center("THE LAST LIGHTHOUSE", 84, 12, 500)
center("A  6 0 - S E C O N D  A I  S H O R T  F I L M", 26, 6, 610, fill=(240, 200, 140))
im.save(HERE / "thumbnail.png")
print("thumbnail.png written (1280x720)")
