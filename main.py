#!/usr/bin/env python3
"""One-day world news image: Thursday 19 November 2026.

Draws a newspaper-style front page (1024x1024 PNG) summing up the day's
world news and writes it to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).

Standard library only. No network, no clock, no randomness: every run writes
identical bytes. All news content is baked into this file.

Layout: navy masthead naming the day, six story tiles (2 x 3) each with a
category tag, a two-line headline, a pictogram and a short factual summary,
plus a footer strip with five more one-line stories.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# Palette.
PAPER = (248, 245, 238)
INK = (22, 22, 22)
NAVY = (16, 32, 58)
GOLD = (198, 158, 38)
WHITE = (255, 255, 255)
TILE_BG = (255, 255, 255)
TILE_LINE = (214, 208, 194)
PIC_BG = (238, 235, 224)
FOOTER_BG = (28, 32, 40)
MUTED = (96, 94, 86)
SKY = (140, 185, 215)

# Category accent colours, one per tile.
ACCENTS = [
    (88, 70, 130),    # diplomacy: purple
    (13, 120, 118),   # tech: teal
    (172, 54, 44),    # middle east: red
    (40, 92, 158),    # ukraine: blue
    (196, 88, 16),    # gaza: orange
    (28, 118, 66),    # economy: green
]

# 5x7 bitmap font, all caps. '1' = set pixel. Only the characters the
# image uses are defined; anything else renders blank.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}


def _bold_glyph(rows):
    """Widen a glyph by one cell to the right: a cheap bold weight."""
    out = []
    for row in rows:
        cells = ['0'] * 6
        for i, ch in enumerate(row):
            if ch == '1':
                cells[i] = '1'
                cells[i + 1] = '1'
        out.append(''.join(cells))
    return out


BOLD_FONT = {ch: _bold_glyph(rows) for ch, rows in FONT.items()}


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            if 0 <= yy < self.h:
                xa = max(x, 0)
                xb = min(x + w, self.w)
                for xx in range(xa, xb):
                    i = (yy * self.w + xx) * 3
                    self.px[i:i + 3] = bytes(color)

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        """Bresenham line with a square brush of `width` pixels."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = width // 2
        while True:
            self.rect(x0 - r, y0 - r, width, width, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.hline(cx - dx, cy + dy, 2 * dx + 1, color)

    def ring(self, cx, cy, r, color, thickness=2):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                d = (dx * dx + dy * dy) ** 0.5
                if r - thickness < d <= r:
                    self.set(cx + dx, cy + dy, color)

    def text(self, x, y, s, scale, color, bold=False, align="left"):
        font = BOLD_FONT if bold else FONT
        adv = (7 if bold else 6) * scale
        if align == "center":
            width = len(s) * adv - scale
            x = x - width // 2
        for ci, ch in enumerate(s):
            rows = font.get(ch, FONT[' '])
            gx0 = x + ci * adv
            for gy, row in enumerate(rows):
                for gx, cell in enumerate(row):
                    if cell == '1':
                        self.rect(gx0 + gx * scale, y + gy * scale,
                                  scale, scale, color)
        return x


def text_width(s, scale, bold=False):
    adv = (7 if bold else 6) * scale
    return len(s) * adv - scale


# ---------------------------------------------------------------- pictograms
# Each draws inside a 100x99 box whose top-left corner is (bx, by).

def pic_summit(cv, bx, by, color):
    # Three leaders around a table: three discs joined to a centre disc.
    dots = [(25, 26, (172, 54, 44)), (75, 26, (198, 158, 38)),
            (50, 78, (40, 92, 158))]
    for (cx, cy, _) in dots:
        cv.line(bx + 50, by + 52, bx + cx, by + cy, MUTED, 2)
    cv.disc(bx + 50, by + 52, 9, WHITE)
    cv.ring(bx + 50, by + 52, 9, color, 3)
    for (cx, cy, dot) in dots:
        cv.disc(bx + cx, by + cy, 11, dot)
        cv.ring(bx + cx, by + cy, 11, INK, 1)


def pic_ipo(cv, bx, by, color):
    # Axes.
    cv.vline(bx + 12, by + 10, 72, INK)
    cv.hline(bx + 12, by + 82, 82, INK)
    # Steep rising line with an arrowhead.
    pts = [(16, 72), (32, 66), (48, 56), (64, 40), (86, 14)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        cv.line(bx + x0, by + y0, bx + x1, by + y1, color, 4)
    cv.line(bx + 86, by + 14, bx + 72, by + 14, color, 4)
    cv.line(bx + 86, by + 14, bx + 86, by + 28, color, 4)
    for (x, y) in pts:
        cv.disc(bx + x, by + y, 3, INK)
    # Dollar mark above the peak.
    cv.disc(bx + 68, by + 8, 2, GOLD)


def pic_gulf(cv, bx, by, color):
    # Interceptor dome over the Gulf.
    for dy in range(0, 32):
        dx = int((32 * 32 - (32 - dy) * (32 - dy)) ** 0.5) if dy <= 32 else 0
        cv.hline(bx + 50 - dx, by + 46 + dy, 2 * dx + 1, SKY)
    cv.hline(bx + 14, by + 78, 72, INK)
    # Incoming projectiles as small squares.
    for dx, dy in ((16, 10), (46, 4), (76, 12)):
        cv.rect(bx + dx, by + dy, 7, 7, INK)
    # Intercept burst at the dome's heart.
    cx, cy = bx + 50, by + 36
    cv.line(cx - 11, cy, cx + 11, cy, color, 3)
    cv.line(cx, cy - 11, cx, cy + 11, color, 3)
    cv.line(cx - 8, cy - 8, cx + 8, cy + 8, color, 3)
    cv.line(cx - 8, cy + 8, cx + 8, cy - 8, color, 3)
    cv.disc(cx, cy, 4, GOLD)


def pic_bridge(cv, bx, by, color):
    # Water at the bottom.
    for wy in (80, 88, 95):
        for wx in range(bx + 6, bx + 94, 15):
            cv.hline(wx, by + wy, 9, SKY)
    # Two pylons.
    cv.rect(bx + 16, by + 14, 6, 54, INK)
    cv.rect(bx + 72, by + 14, 6, 54, INK)
    # Suspension cables.
    cv.line(bx + 19, by + 14, bx + 6, by + 48, MUTED, 2)
    cv.line(bx + 19, by + 14, bx + 38, by + 48, MUTED, 2)
    cv.line(bx + 75, by + 14, bx + 56, by + 48, MUTED, 2)
    cv.line(bx + 75, by + 14, bx + 88, by + 48, MUTED, 2)
    # Deck: two standing spans with a gap in the middle.
    cv.rect(bx + 6, by + 48, 34, 6, color)
    cv.rect(bx + 60, by + 48, 34, 6, color)
    # Fallen middle span, tilted down into the strait.
    cv.line(bx + 42, by + 50, bx + 56, by + 68, color, 6)
    cv.disc(bx + 48, by + 42, 4, (200, 60, 40))


def pic_tank(cv, bx, by, color):
    # The Yellow Line, dashed across the box.
    for wx in range(bx + 4, bx + 96, 12):
        cv.hline(wx, by + 52, 7, GOLD)
    # Tank hull crossing the line.
    cv.rect(bx + 22, by + 58, 52, 14, INK)
    cv.rect(bx + 34, by + 46, 24, 12, INK)
    cv.line(bx + 58, by + 50, bx + 82, by + 42, INK, 4)
    # Tracks.
    for tx in range(bx + 22, bx + 74, 10):
        cv.disc(tx + 4, by + 76, 4, color)
    # Blast star at the barrel tip.
    cx, cy = bx + 86, by + 34
    cv.line(cx - 8, cy, cx + 8, cy, color, 3)
    cv.line(cx, cy - 8, cx, cy + 8, color, 3)
    cv.line(cx - 6, cy - 6, cx + 6, cy + 6, color, 3)
    cv.line(cx - 6, cy + 6, cx + 6, cy - 6, color, 3)


def pic_fed(cv, bx, by, color):
    # Rising bars.
    heights = [20, 34, 48, 64]
    for i, ht in enumerate(heights):
        x = bx + 12 + i * 21
        shade = color if i == 3 else tuple(min(255, c + 55) for c in color)
        cv.rect(x, by + 82 - ht, 14, ht, shade)
    cv.hline(bx + 6, by + 82, 88, INK)
    # Arrow climbing over the bars.
    cv.line(bx + 10, by + 30, bx + 88, by + 10, color, 4)
    cv.line(bx + 88, by + 10, bx + 74, by + 10, color, 4)
    cv.line(bx + 88, by + 10, bx + 88, by + 24, color, 4)
    # Percent mark.
    cv.disc(bx + 78, by + 66, 3, GOLD)


PICTOGRAMS = [pic_summit, pic_ipo, pic_gulf, pic_bridge, pic_tank, pic_fed]

# (tag, headline lines, summary lines) — all caps, verified 19 Nov 2026 news.
STORIES = [
    ("DIPLOMACY",
     ["THREE LEADERS", "MEET IN CHINA"],
     ["FIRST 3-WAY SUMMIT",
      "IN SHENZHEN AT",
      "APEC. ARMS CONTROL",
      "TOPS THE AGENDA."]),
    ("TECH",
     ["BIGGEST IPO", "EVER: $81.3B"],
     ["PRICED $83, ABOVE",
      "$70-$78 RANGE.",
      "TRADES TODAY AS",
      "ANT ON NASDAQ."]),
    ("MIDDLE EAST",
     ["IRAN WIDENS", "GULF ATTACKS"],
     ["FIRES ON US SITES",
      "IN KUWAIT; BAHRAIN",
      "INTERCEPTS 3RD",
      "ATTACK IN A WEEK."]),
    ("UKRAINE",
     ["KERCH BRIDGE", "HIT 3RD TIME"],
     ["RAIL SPAN TARGETED",
      "OVERNIGHT; TRAFFIC",
      "HALTED. 3RD STRIKE",
      "IN 3 DAYS."]),
    ("GAZA",
     ["TANKS CROSS", "YELLOW LINE"],
     ["FIRST GROUND OP",
      "SINCE OCT 2025",
      "CEASEFIRE. IDF",
      "TARGETS TUNNEL."]),
    ("ECONOMY",
     ["FED SIGNALS", "MORE HIKES"],
     ["MINUTES: ALMOST ALL",
      "SEE MORE RISES.",
      "HOLD 3.75-4%,",
      "VOTE 10-2."]),
]

FOOTER_ITEMS = [
    "VAN GOGH $190.4M",
    "VOYAGER 1 LIGHT-DAY",
    "EU EUR 45B LOAN",
    "GTA VI OUT NOW",
    "AKVAN NEARS INDIA",
]


def render():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    cv.rect(0, 0, W, 118, NAVY)
    cv.text(W // 2, 14, "THE WORLD IN ONE DAY", 3, GOLD, align="center")
    cv.text(W // 2, 48, "THURSDAY 19 NOVEMBER 2026", 5, WHITE, bold=True,
            align="center")
    cv.rect(0, 118, W, 4, GOLD)

    # Story tiles: 2 columns x 3 rows.
    tile_w, tile_h, gap, margin = 494, 252, 12, 12
    top = 132
    for idx, (tag, head, summary) in enumerate(STORIES):
        tx = margin + (idx % 2) * (tile_w + gap)
        ty = top + (idx // 2) * (tile_h + gap)
        accent = ACCENTS[idx]
        cv.rect(tx, ty, tile_w, tile_h, TILE_BG)
        # Border.
        cv.rect(tx, ty, tile_w, 2, TILE_LINE)
        cv.rect(tx, ty + tile_h - 2, tile_w, 2, TILE_LINE)
        cv.rect(tx, ty, 2, tile_h, TILE_LINE)
        cv.rect(tx + tile_w - 2, ty, 2, tile_h, TILE_LINE)
        # Accent bar on the left edge.
        cv.rect(tx, ty, 6, tile_h, accent)
        # Tag.
        tag_w = text_width(tag, 2) + 16
        cv.rect(tx + 18, ty + 12, tag_w, 24, accent)
        cv.text(tx + 26, ty + 17, tag, 2, WHITE)
        # Headline, two lines, bold.
        cv.text(tx + 18, ty + 48, head[0], 5, INK, bold=True)
        cv.text(tx + 18, ty + 88, head[1], 5, INK, bold=True)
        # Divider.
        cv.hline(tx + 18, ty + 132, tile_w - 36, TILE_LINE)
        # Pictogram box.
        px, py = tx + 18, ty + 142
        cv.rect(px, py, 100, 99, PIC_BG)
        cv.rect(px, py, 100, 2, TILE_LINE)
        cv.rect(px, py + 97, 100, 2, TILE_LINE)
        cv.rect(px, py, 2, 99, TILE_LINE)
        cv.rect(px + 98, py, 2, 99, TILE_LINE)
        PICTOGRAMS[idx](cv, px, py, accent)
        # Summary lines.
        for li, line in enumerate(summary):
            cv.text(tx + 132, ty + 144 + li * 24, line, 3, INK)

    # Footer strip.
    fy = 922
    cv.rect(0, 918, W, 4, GOLD)
    cv.rect(0, fy, W, H - fy, FOOTER_BG)
    cv.text(18, fy + 38, "ALSO TODAY", 3, GOLD)
    cols = [210, 500, 790]
    for i, item in enumerate(FOOTER_ITEMS):
        ix = cols[i % 3]
        iy = fy + 12 + (i // 3) * 44
        cv.rect(ix, iy + 6, 8, 8, GOLD)
        cv.text(ix + 18, iy, item, 2, WHITE)

    return cv.px


def png_bytes(rgb, w, h):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter: none
        raw += rgb[y * stride:(y + 1) * stride]

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(render(), W, H)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
