"""Travel poster for Aurelia, the Floating Isles.

This is the entrypoint of a make.fun submission. It draws one travel
poster, 1024 by 1024 pixels, for a place that does not exist: Aurelia,
a chain of islands that drift above a sea of clouds at golden hour.
The drawing is procedural -- every hill, cloud, bird and letter is
placed by this program from a fixed seed, so two runs produce the
same bytes. Nothing here touches the network.

The finished poster is written to the directory named by the
``MAKEFUN_OUTPUT_DIR`` environment variable (``/output`` when the
variable is absent) as ``entry.png``. After writing, the program
checks the result: it must be 1024 by 1024 pixels and no larger than
1,048,576 bytes. If either check fails, the program stops with a
``RuntimeError`` instead of leaving a bad file behind.

The fonts this poster uses ship in the repository under ``assets/``,
so the drawing does not depend on whatever fonts a machine happens
to have installed. If Pillow itself is missing, the program falls
back to the copy of the poster that ships in this repository as
``entry.png`` -- the same image this program draws -- and verifies
that copy the same way before reporting success.

Written for Python 3.13. Only the standard library plus Pillow are
used, and Pillow is only needed on the drawing path.
"""

import hashlib
import os
import random
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SIZE = 1024
MAX_BYTES = 1_048_576
FALLBACK_OUTPUT_DIR = "/output"
SOURCE_NAME = "entry.png"
SEED = 20261121

# The invented place. Nothing here names a real destination, quotes
# anyone, or rates anything: just the name and one honest tagline.
PLACE_NAME = "AURELIA"
TAGLINE = "ABOVE THE CLOUDS, BEYOND THE MAP"
DESCRIPTOR = "THE FLOATING ISLES"

# Sunset palette, top of the sky down to the horizon.
SKY_STOPS = [
    (0.00, (26, 20, 58)),     # deep violet night
    (0.22, (66, 32, 86)),     # dusk purple
    (0.42, (138, 55, 102)),   # magenta
    (0.58, (214, 92, 96)),    # rose
    (0.74, (242, 140, 74)),   # warm orange
    (0.88, (255, 196, 107)),  # gold
    (1.00, (255, 227, 163)),  # pale gold at the horizon
]
SKY_BOTTOM = 700

SUN_CENTER = (760, 415)
SUN_RADIUS = 62

CLOUD_TOP = 650

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _lerp(a, b, t):
    return a + (b - a) * t


def _mix(c1, c2, t):
    return tuple(int(round(_lerp(a, b, t))) for a, b in zip(c1, c2))


def _sky_color(y):
    """Interpolate the sunset gradient at height *y*."""
    t = max(0.0, min(1.0, y / SKY_BOTTOM))
    for i in range(len(SKY_STOPS) - 1):
        t0, c0 = SKY_STOPS[i]
        t1, c1 = SKY_STOPS[i + 1]
        if t0 <= t <= t1:
            return _mix(c0, c1, (t - t0) / (t1 - t0))
    return SKY_STOPS[-1][1]


def _font_path(name):
    """Find a font file: bundled in assets/ first, then system paths."""
    here = Path(__file__).resolve().parent
    bundled = here / "assets" / name
    if bundled.is_file():
        return str(bundled)
    for candidate in (
        Path("/usr/share/fonts/truetype/dejavu") / name,
        Path("/usr/share/fonts/truetype/liberation") / name,
    ):
        if candidate.is_file():
            return str(candidate)
    return None


def _tracked_width(draw, text, font, tracking):
    width = 0
    for ch in text:
        width += draw.textlength(ch, font=font) + tracking
    return width - tracking if text else 0


def _draw_tracked(draw, center_x, y, text, font, fill, tracking):
    """Draw *text* centred on *center_x*, with even letter spacing."""
    width = _tracked_width(draw, text, font, tracking)
    x = center_x - width / 2
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------


def _draw_sky(img, draw):
    for y in range(SKY_BOTTOM + 1):
        draw.line([(0, y), (SIZE, y)], fill=_sky_color(y))
    # Faint early stars high up, where the sky is still dark.
    rng = random.Random(SEED + 1)
    for _ in range(46):
        x = rng.randint(20, SIZE - 20)
        y = rng.randint(16, 210)
        r = rng.choice((1, 1, 2))
        alpha = rng.randint(70, 170)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=(255, 244, 214, alpha))


def _draw_sun(img):
    """A low golden sun with a soft halo, on its own layer."""
    from PIL import Image, ImageDraw, ImageFilter

    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cx, cy = SUN_CENTER
    for radius, alpha in ((190, 26), (150, 40), (115, 60), (88, 90)):
        ld.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                   fill=(255, 214, 130, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(layer)
    draw = ImageDraw.Draw(img)
    draw.ellipse([cx - SUN_RADIUS, cy - SUN_RADIUS,
                  cx + SUN_RADIUS, cy + SUN_RADIUS],
                 fill=(255, 236, 180, 255))
    draw.ellipse([cx - SUN_RADIUS + 10, cy - SUN_RADIUS + 10,
                  cx + SUN_RADIUS - 10, cy + SUN_RADIUS - 10],
                 fill=(255, 248, 220, 255))


def _draw_cloud_layer(img, rng, puffs, y_lo, y_hi, base_alpha, tint):
    """One bank of soft, blurred cloud puffs."""
    from PIL import Image, ImageDraw, ImageFilter

    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for _ in range(puffs):
        x = rng.randint(-60, SIZE + 60)
        y = rng.randint(y_lo, y_hi)
        w = rng.randint(120, 300)
        h = rng.randint(28, 62)
        a = rng.randint(int(base_alpha * 0.6), base_alpha)
        ld.ellipse([x - w // 2, y - h // 2, x + w // 2, y + h // 2],
                   fill=tint + (a,))
    layer = layer.filter(ImageFilter.GaussianBlur(16))
    img.alpha_composite(layer)


def _draw_cloud_sea(img, rng):
    """The sea of clouds the islands float above."""
    from PIL import ImageDraw

    draw = ImageDraw.Draw(img)
    for y in range(CLOUD_TOP, SIZE):
        t = (y - CLOUD_TOP) / (SIZE - CLOUD_TOP)
        draw.line([(0, y), (SIZE, y)],
                  fill=_mix((255, 205, 150), (196, 158, 214), t))
    _draw_cloud_layer(img, rng, 60, CLOUD_TOP - 10, 760, 150,
                      (255, 226, 190))
    _draw_cloud_layer(img, rng, 55, 780, 950, 120, (232, 196, 228))
    _draw_cloud_layer(img, rng, 34, 930, SIZE + 10, 110, (210, 180, 222))
    # A few small detached clouds drifting high in the sky.
    _draw_cloud_layer(img, rng, 7, 300, 400, 70, (255, 210, 180))


def _jagged_rock(draw, left, top, right, tip_x, tip_y, rng, color):
    """A rocky underside: a polygon tapering to a point, jagged edges."""
    points = [(left, top)]
    steps = 7
    for i in range(1, steps):
        t = i / steps
        x = left + (tip_x - left) * t + rng.randint(-14, 14)
        y = top + (tip_y - top) * t + rng.randint(-8, 10)
        points.append((x, y))
    points.append((tip_x, tip_y))
    for i in range(steps - 1, 0, -1):
        t = i / steps
        x = right - (right - tip_x) * t + rng.randint(-14, 14)
        y = top + (tip_y - top) * t + rng.randint(-8, 10)
        points.append((x, y))
    points.append((right, top))
    draw.polygon(points, fill=color)


def _draw_trees(draw, rng, x_lo, x_hi, ground_y, count, scale=1.0):
    for _ in range(count):
        x = rng.randint(x_lo, x_hi)
        h = int(rng.randint(22, 40) * scale)
        w = int(h * 0.55)
        base = ground_y + rng.randint(-4, 2)
        draw.polygon([(x, base - h), (x - w, base), (x + w, base)],
                     fill=(24, 74, 54, 255))
        draw.ellipse([x - w // 2, base - h - w // 3,
                      x + w // 2, base - h + w // 3],
                     fill=(34, 96, 66, 255))


def _draw_island(img, draw, rng, left, top, right, tip_y, with_fall=True):
    """One floating island: grassy top, rocky point, trees, waterfall."""
    from PIL import Image, ImageDraw, ImageFilter

    tip_x = (left + right) // 2
    _jagged_rock(draw, left, top + 6, right, tip_x, tip_y, rng,
                 (58, 34, 62, 255))
    # Sunlit rim along the rock's left edge.
    draw.line([(left, top + 6), (tip_x, tip_y)], fill=(255, 170, 110, 255),
              width=3)
    # Grassy cap.
    draw.ellipse([left - 6, top - 16, right + 6, top + 18],
                 fill=(52, 128, 84, 255))
    draw.ellipse([left - 6, top - 16, right + 6, top + 2],
                 fill=(86, 168, 104, 255))
    _draw_trees(draw, rng, left + 24, right - 24, top - 6,
                count=max(3, (right - left) // 60))

    if with_fall:
        # A waterfall spilling off the island's edge into the clouds.
        layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        fx = left + (right - left) // 4
        for k in range(4):
            x = fx + k * 9
            points = []
            y = top + 10
            while y < CLOUD_TOP + 60:
                points.append((x + rng.randint(-4, 4), y))
                y += 26
            ld.line(points, fill=(214, 236, 248, 170), width=5)
        layer = layer.filter(ImageFilter.GaussianBlur(2))
        img.alpha_composite(layer)


def _draw_lighthouse(draw, x, base_y):
    """The poster's landmark: a striped lighthouse on the main island."""
    from PIL import Image, ImageDraw, ImageFilter

    # Warm beam sweeping left across the sky.
    beam = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    bd.polygon([(x, base_y - 122), (x - 330, base_y - 184),
                (x - 330, base_y - 72)], fill=(255, 226, 150, 70))
    beam = beam.filter(ImageFilter.GaussianBlur(10))
    # The beam layer is composited by the caller through img; do it here
    # via the draw's image instead: handled by caller passing img.
    return beam


def _draw_birds(draw, rng):
    for _ in range(7):
        x = rng.randint(60, SIZE - 120)
        y = rng.randint(350, 480)
        s = rng.randint(9, 16)
        draw.arc([x - s, y - s // 2, x, y + s // 2], 200, 340,
                 fill=(40, 24, 60, 220), width=3)
        draw.arc([x, y - s // 2, x + s, y + s // 2], 200, 340,
                 fill=(40, 24, 60, 220), width=3)


def _draw_type(img, draw):
    """The place name, set big and centred, with its tagline."""
    from PIL import ImageFont

    title_path = _font_path("DejaVuSerif-Bold.ttf")
    sans_path = _font_path("DejaVuSans-Bold.ttf")
    title_font = (ImageFont.truetype(title_path, 148) if title_path
                  else ImageFont.load_default())
    # Shrink the tagline until it fits the poster with room to spare.
    tag_size, tag_tracking = 34, 10
    tag_font = (ImageFont.truetype(sans_path, tag_size) if sans_path
                else ImageFont.load_default())
    while (sans_path and tag_size > 20 and
           _tracked_width(draw, TAGLINE, tag_font, tag_tracking) > 940):
        tag_size -= 2
        tag_tracking = max(4, tag_tracking - 1)
        tag_font = ImageFont.truetype(sans_path, tag_size)
    desc_font = (ImageFont.truetype(sans_path, 26) if sans_path
                 else ImageFont.load_default())

    cx = SIZE // 2
    shadow = (38, 20, 62, 255)
    cream = (255, 247, 232, 255)
    gold = (255, 214, 138, 255)

    # Title with a soft drop shadow so it reads over the bright sky.
    _draw_tracked(draw, cx + 4, 96, PLACE_NAME, title_font, shadow, 26)
    _draw_tracked(draw, cx, 92, PLACE_NAME, title_font, cream, 26)

    # Thin gold rule under the title.
    rule_w = _tracked_width(draw, PLACE_NAME, title_font, 26)
    draw.line([(cx - rule_w // 2, 268), (cx + rule_w // 2, 268)],
              fill=gold, width=3)

    _draw_tracked(draw, cx, 292, TAGLINE, tag_font, gold, tag_tracking)
    _draw_tracked(draw, cx + 2, 962, DESCRIPTOR, desc_font,
                  (60, 30, 70, 255), 8)
    _draw_tracked(draw, cx, 960, DESCRIPTOR, desc_font,
                  (255, 247, 232, 255), 8)


def build_poster():
    """Draw the poster and return it as a Pillow image."""
    from PIL import Image, ImageDraw

    rng = random.Random(SEED)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    _draw_sky(img, draw)
    _draw_sun(img)
    _draw_cloud_sea(img, rng)

    # Two hazy islands far away on the horizon, for depth.
    haze = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    hd = ImageDraw.Draw(haze)
    _jagged_rock(hd, 120, 626, 250, 185, 698, random.Random(SEED + 2),
                 (122, 74, 110, 130))
    _jagged_rock(hd, 800, 636, 900, 850, 694, random.Random(SEED + 3),
                 (122, 74, 110, 130))
    img.alpha_composite(haze)

    # Small islands left and right, then the main island in front.
    _draw_island(img, draw, rng, 92, 590, 268, 700, with_fall=False)
    _draw_island(img, draw, rng, 772, 555, 936, 665, with_fall=False)

    # Main island with the lighthouse.
    main_left, main_top, main_right, main_tip = 306, 505, 726, 700
    _draw_island(img, draw, rng, main_left, main_top, main_right, main_tip)

    lx = 560
    beam = _draw_lighthouse(draw, lx, main_top)
    img.alpha_composite(beam)
    # Lighthouse tower: tapered white body, red bands, lamp room.
    draw.polygon([(lx - 16, main_top), (lx - 11, main_top - 100),
                  (lx + 11, main_top - 100), (lx + 16, main_top)],
                 fill=(250, 244, 230, 255))
    for band_y, band_h in ((main_top - 78, 12), (main_top - 48, 12)):
        draw.polygon([(lx - 14, band_y), (lx - 12, band_y - band_h),
                      (lx + 12, band_y - band_h), (lx + 14, band_y)],
                     fill=(198, 64, 72, 255))
    draw.rectangle([lx - 15, main_top - 116, lx + 15, main_top - 100],
                   fill=(52, 36, 58, 255))
    draw.ellipse([lx - 11, main_top - 130, lx + 11, main_top - 114],
                 fill=(255, 226, 150, 255))
    draw.polygon([(lx - 15, main_top - 130), (lx + 15, main_top - 130),
                  (lx + 9, main_top - 141), (lx - 9, main_top - 141)],
                 fill=(52, 36, 58, 255))

    _draw_birds(draw, rng)
    _draw_type(img, draw)

    return img.convert("RGB")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_png(path):
    """Check size and dimensions using only the standard library.

    The PNG header (IHDR) carries the width and height in plain bytes,
    so this works even on a machine without Pillow -- which is exactly
    the situation the fallback copy path is for.
    """
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        raise RuntimeError(
            "entry.png is %d bytes, over the 1,048,576-byte cap" % size)
    with open(path, "rb") as handle:
        header = handle.read(33)
    if len(header) < 33 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("entry.png is not a PNG file")
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    if (width, height) != (SIZE, SIZE):
        raise RuntimeError(
            "entry.png is %dx%d, expected 1024x1024" % (width, height))
    return size


def _write_drawn(output_path):
    poster = build_poster()
    poster.save(output_path, format="PNG", optimize=True)
    return _verify_png(output_path)


def _write_fallback(output_path):
    """Copy the bundled poster when Pillow is unavailable."""
    here = Path(__file__).resolve().parent
    source = here / SOURCE_NAME
    if not source.is_file():
        raise RuntimeError(
            "Pillow is missing and no bundled %s to fall back to"
            % SOURCE_NAME)
    shutil.copyfile(source, output_path)
    if _sha256_of(output_path) != _sha256_of(source):
        raise RuntimeError("fallback copy failed its checksum")
    return _verify_png(output_path)


def main():
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or FALLBACK_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "entry.png"
    try:
        import PIL  # noqa: F401  -- drawing needs Pillow
        size = _write_drawn(output_path)
        mode = "drawn"
    except ImportError:
        size = _write_fallback(output_path)
        mode = "fallback copy"
    print("wrote %s (%s, %d bytes, sha256 %s)"
          % (output_path, mode, size, _sha256_of(output_path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
