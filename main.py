#!/usr/bin/env python3
"""The world in one day -- Thursday 19 November 2026.

A newspaper front page drawn with the Python standard library only.
Reads nothing, uses no network, takes no input: the same bytes come out
on every run. Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
"""
import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024
MARGIN = 30
CONTENT = WIDTH - 2 * MARGIN

PAPER = (251, 247, 237)
INK = (26, 26, 26)
SOFT = (74, 74, 74)
RULE_RED = (185, 28, 28)

# 5x7 bitmap font. Each glyph is seven rows; bit 4 is the leftmost pixel.
# Only capitals are defined: all copy is uppercased before it is drawn.
FONT = {
    'A': (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'B': (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    'C': (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    'D': (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    'E': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    'F': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    'G': (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    'H': (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'I': (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'J': (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    'K': (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    'L': (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    'M': (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    'N': (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    'O': (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'P': (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    'Q': (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    'R': (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    'S': (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    'T': (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    'U': (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'V': (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'W': (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    'X': (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'Y': (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    'Z': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    '3': (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ' ': (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    '.': (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ',': (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    ':': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ';': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    '!': (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    '?': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    '-': (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    '"': (0x0A, 0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00),
    '(': (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ')': (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '/': (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    '&': (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    '%': (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    '$': (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    '+': (0x00, 0x04, 0x04, 0x0E, 0x04, 0x04, 0x00),
    '=': (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    '*': (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
    '#': (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    '@': (0x0E, 0x11, 0x17, 0x15, 0x16, 0x10, 0x0E),
}

# (kicker, accent colour, headline, body) -- every fact verified in at
# least two sources for Thursday 19 November 2026. Scheduled meetings are
# worded as meeting today, never as outcomes already known.
TILES = [
    ("DIPLOMACY", (29, 78, 158), "TRUMP, XI AND PUTIN MEET IN SHENZHEN",
     "First three-way meeting of the three leaders, on the APEC sidelines. "
     "Trump pushes nuclear arms control; Ukraine war not expected to be raised."),
    ("TECH", (124, 58, 237), "ANTHROPIC DEBUTS IN BIGGEST IPO EVER",
     "Priced at $83 a share, above the $70-$78 range. Raised $81.3B from "
     "980M shares, a record. Shares start trading on Nasdaq Thursday under ticker ANT."),
    ("MIDDLE EAST", (180, 83, 9), "IRAN WIDENS GULF ATTACKS",
     "Iran fired on US drone and missile sites in Kuwait overnight. "
     "Bahrain says it has now intercepted Iranian attacks three times in a week."),
    ("UKRAINE", (185, 28, 28), "KERCH BRIDGE HIT A THIRD TIME",
     "Ukraine struck the bridge for the third time in three days, this time "
     "the rail span, after a 227m road section was destroyed Tuesday. Traffic suspended."),
    ("GAZA", (15, 118, 110), "ISRAELI TANKS CROSS THE YELLOW LINE",
     "First ground operation since the 2025 ceasefire, around "
     "Nuseirat and Bureij. The IDF says the target is a Hamas tunnel; Hamas calls it a violation."),
    ("ECONOMY", (54, 83, 20), "FED MINUTES POINT TO MORE HIKES",
     "Minutes of the Oct 27-28 meeting: almost all officials judged further "
     "rate rises likely. Vote was 10-2 to hold at 3.75-4%. Next meeting Dec 8-9."),
]

FOOTER_ITEMS = [
    "VAN GOGH SELLS FOR A RECORD $190.4M AT SOTHEBY'S NEW YORK",
    "VOYAGER 1 IS NOW ONE LIGHT-DAY FROM EARTH, 16.1B MILES OUT",
    "EU PROPOSES A 45B EURO LOAN TO UKRAINE FOR 2027",
    "CYCLONE AKVAN NEARS INDIA; LANDFALL BY NOON FRIDAY",
    "GTA VI ROLLS OUT WORLDWIDE, STARTING IN NEW ZEALAND",
]


def new_canvas():
    return bytearray(bytes(PAPER) * (WIDTH * HEIGHT))


def fill_rect(buf, x, y, w, h, color):
    rgb = bytes(color)
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(WIDTH, x + w)
    y1 = min(HEIGHT, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = rgb * (x1 - x0)
    for yy in range(y0, y1):
        off = (yy * WIDTH + x0) * 3
        buf[off:off + len(row)] = row


def clean(text):
    return (text.upper()
            .replace("\u2019", "'").replace("\u2018", "'")
            .replace("\u201c", '"').replace("\u201d", '"')
            .replace("\u2013", "-").replace("\u2014", "-"))


def text_width(text, scale):
    return len(clean(text)) * 6 * scale


def draw_text(buf, x, y, text, scale, color):
    cx = x
    for ch in clean(text):
        glyph = FONT.get(ch)
        if glyph is not None:
            for row in range(7):
                bits = glyph[row]
                if not bits:
                    continue
                for col in range(5):
                    if bits >> (4 - col) & 1:
                        fill_rect(buf, cx + col * scale, y + row * scale,
                                  scale, scale, color)
        cx += 6 * scale


def draw_text_centered(buf, cx, y, text, scale, color):
    draw_text(buf, cx - text_width(text, scale) // 2, y, text, scale, color)


def wrap(text, max_width, scale):
    lines = []
    current = ""
    for word in clean(text).split(" "):
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_lines(buf, x, y, lines, scale, color, leading):
    for i, line in enumerate(lines):
        draw_text(buf, x, y + i * leading, line, scale, color)


def draw_masthead(buf):
    fill_rect(buf, MARGIN, 30, CONTENT, 3, INK)
    draw_text_centered(buf, WIDTH // 2, 48, "THE WORLD IN ONE DAY", 6, INK)
    draw_text_centered(buf, WIDTH // 2, 104, "THURSDAY 19 NOVEMBER 2026", 3, RULE_RED)
    draw_text_centered(buf, WIDTH // 2, 134, "SIX STORIES THAT DEFINED THE DAY", 2, SOFT)
    fill_rect(buf, MARGIN, 158, CONTENT, 2, INK)
    fill_rect(buf, MARGIN, 164, CONTENT, 4, RULE_RED)


def draw_tile(buf, x, y, w, h, kicker, accent, headline, body):
    fill_rect(buf, x, y, w, 4, accent)
    draw_text(buf, x, y + 16, kicker, 2, accent)
    head_lines = wrap(headline, w, 3)
    draw_lines(buf, x, y + 44, head_lines, 3, INK, 28)
    body_lines = wrap(body, w, 2)
    draw_lines(buf, x, y + 110, body_lines, 2, INK, 21)


def draw_tiles(buf):
    tile_w = (CONTENT - 18) // 2
    tile_h = 212
    top = 184
    for i, (kicker, accent, headline, body) in enumerate(TILES):
        col = i % 2
        row = i // 2
        x = MARGIN + col * (tile_w + 18)
        y = top + row * (tile_h + 16)
        draw_tile(buf, x, y, tile_w, tile_h, kicker, accent, headline, body)


def draw_footer(buf):
    y = 872
    draw_text(buf, MARGIN, y, "ALSO TODAY", 2, RULE_RED)
    fill_rect(buf, MARGIN + text_width("ALSO TODAY", 2) + 14, y + 5,
              CONTENT - text_width("ALSO TODAY", 2) - 14, 2, INK)
    for i, item in enumerate(FOOTER_ITEMS):
        iy = y + 26 + i * 20
        fill_rect(buf, MARGIN, iy + 3, 8, 8, RULE_RED)
        draw_text(buf, MARGIN + 16, iy, item, 2, INK)


def chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))


def write_png(path, buf):
    raw = bytearray()
    for yy in range(HEIGHT):
        raw.append(0)
        raw += buf[yy * WIDTH * 3:(yy + 1) * WIDTH * 3]
    ihdr = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
           chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    buf = new_canvas()
    draw_masthead(buf)
    draw_tiles(buf)
    draw_footer(buf)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path, buf)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
