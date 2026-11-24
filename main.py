#!/usr/bin/env python3
"""THE WORLD IN ONE PAGE -- Tuesday 24 November 2026.

Draws a dense dated broadsheet of the day's world news with pure stdlib
Python: own bitmap font, own vector icons, own PNG writer. No network,
no images, no randomness. Deterministic: two runs write identical bytes.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   -> out/entry.png
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 227)
INK = (26, 26, 26)
RED = (163, 22, 33)
BLUE = (29, 78, 137)
GREEN = (34, 110, 72)
GOLD = (176, 124, 20)
TEAL = (14, 110, 110)
PURPLE = (94, 58, 130)
BROWN = (122, 74, 30)
GREY = (110, 105, 92)
LIGHT = (232, 224, 205)
WHITE = (255, 255, 255)

# ------------------------------------------------------------- 5x7 font
# Uppercase + digits + punctuation. Rows are 5 chars, '#' = ink.
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".....", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ':': (".....", ".....", ".##..", ".....", ".##..", ".....", "....."),
    ';': (".....", ".....", ".##..", ".....", ".##..", ".#...", "....."),
    "'": ("..#..", "..#..", "...#.", ".....", ".....", ".....", "....."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '/': ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    '&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '%': ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '$': ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    '#': ("#.#.#", "#.#.#", "#####", "#.#.#", "#####", "#.#.#", "#.#.#"),
    '@': (".###.", "#...#", "#.###", "#.#.#", "#.##.", "#....", ".###."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    '*': (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    '[': (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    ']': (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
    '_': (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    '>': ("#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."),
    '<': ("....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"),
}

# ------------------------------------------------------------- canvas
buf = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i], buf[i + 1], buf[i + 2] = c


def fill(x, y, w, h, c):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            buf[i], buf[i + 1], buf[i + 2] = c


def rect(x, y, w, h, c, t=1):
    fill(x, y, w, t, c)
    fill(x, y + h - t, w, t, c)
    fill(x, y, t, h, c)
    fill(x + w - t, y, t, h, c)


def line(x0, y0, x1, y1, c, t=1):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        fill(x - t // 2, y - t // 2, t, t, c)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def circle(cx, cy, r, c, filled=True):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d2 = (xx - cx) ** 2 + (yy - cy) ** 2
            if filled:
                if d2 <= r * r:
                    px(xx, yy, c)
            else:
                if r * r - 2 * r <= d2 <= r * r:
                    px(xx, yy, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    # filled triangle via scanline
    pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
    (ax, ay), (bx, by), (cx, cy) = pts
    if ay == cy:
        return
    for yy in range(ay, cy + 1):
        t1 = (yy - ay) / (cy - ay) if cy != ay else 0
        xa = ax + (cx - ax) * t1
        if yy < by:
            t2 = (yy - ay) / (by - ay) if by != ay else 0
            xb = ax + (bx - ax) * t2
        else:
            t2 = (yy - by) / (cy - by) if cy != by else 0
            xb = bx + (cx - bx) * t2
        for xx in range(int(min(xa, xb)), int(max(xa, xb)) + 1):
            px(xx, yy, c)


# ------------------------------------------------------------- text
def tw(s, scale):
    return len(s) * 6 * scale - scale


def text(x, y, s, scale, c):
    s = s.upper()
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[' '])
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row[col] == '#':
                    fill(cx + col * scale, y + r * scale, scale, scale, c)
        cx += 6 * scale


def ctext(cx, y, s, scale, c):
    text(cx - tw(s, scale) // 2, y, s, scale, c)


def wrap(s, max_chars):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------- icons
# Each draws a small pictogram inside a square (x, y, size s) in colour c.
def icon_globe(x, y, s, c):
    r = s // 2
    cx, cy = x + r, y + r
    circle(cx, cy, r - 1, c, filled=False)
    line(cx - r + 2, cy, cx + r - 2, cy, c)
    line(cx, cy - r + 2, cx, cy + r - 2, c)
    line(cx - r + 3, cy - r // 2, cx + r - 3, cy - r // 2, c)
    line(cx - r + 3, cy + r // 2, cx + r - 3, cy + r // 2, c)


def icon_flame(x, y, s, c):
    tri(x + s // 2, y + 1, x + 1, y + s - 1, x + s - 1, y + s - 1, c)
    tri(x + s // 2, y + s // 2, x + s // 4, y + s - 1, x + 3 * s // 4, y + s - 1,
        GOLD)


def icon_ship(x, y, s, c):
    tri(x + 1, y + s // 2, x + s - 1, y + s // 2, x + s - 2, y + s - 1, c)
    tri(x + 2, y + s // 2, x + 1, y + s - 1, x + 2, y + s - 1, c)
    line(x + s // 2, y + 1, x + s // 2, y + s // 2, c, 2)
    tri(x + s // 2, y + 2, x + s // 2, y + s // 2 - 1, x + s - 2, y + s // 2 - 1,
        c)


def icon_chip(x, y, s, c):
    fill(x + s // 4, y + s // 4, s // 2, s // 2, c)
    fill(x + s // 3, y + s // 3, s // 3, s // 3, PAPER)
    for k in range(3):
        t = y + s // 4 + k * s // 4
        line(x, t, x + s // 4, t, c, 1)
        line(x + 3 * s // 4, t, x + s, t, c, 1)


def icon_ballot(x, y, s, c):
    rect(x + s // 6, y + s // 3, 2 * s // 3, s // 2, c, 1)
    line(x + s // 4, y + s // 2 + 2, x + s // 2, y + 2 * s // 3 + 2, c, 2)
    line(x + s // 2, y + 2 * s // 3 + 2, x + 5 * s // 6, y + s // 4, c, 2)


def icon_scales(x, y, s, c):
    line(x + s // 2, y + 1, x + s // 2, y + s - 2, c, 2)
    line(x + 1, y + s // 4, x + s - 1, y + s // 4, c, 2)
    tri(x + 2, y + s // 4, x + 1, y + s // 2, x + s // 4, y + s // 2, c)
    tri(x + s - 2, y + s // 4, x + 3 * s // 4, y + s // 2, x + s - 1, y + s // 2,
        c)
    fill(x + s // 4, y + s - 2, s // 2, 2, c)


def icon_ball(x, y, s, c):
    r = s // 2 - 1
    cx, cy = x + s // 2, y + s // 2
    circle(cx, cy, r, c, filled=False)
    line(cx - r, cy, cx + r, cy, c)
    line(cx, cy - r, cx, cy + r, c)


def icon_bars(x, y, s, c):
    for k, h in enumerate((s // 3, 2 * s // 3, s // 2, s - 2)):
        fill(x + 1 + k * (s // 4), y + s - 1 - h, s // 5, h, c)


def icon_cross(x, y, s, c):
    fill(x + s // 2 - 1, y + 1, 3, s - 2, c)
    fill(x + 1, y + s // 2 - 1, s - 2, 3, c)


def icon_bolt(x, y, s, c):
    tri(x + 2 * s // 3, y + 1, x + s // 3, y + s // 2, x + 2 * s // 3,
        y + s // 2, c)
    tri(x + s // 3, y + s // 2, x + 2 * s // 3, y + s // 2, x + s // 3,
        y + s - 1, c)


def icon_moon(x, y, s, c):
    circle(x + s // 2, y + s // 2, s // 2 - 1, c, filled=False)
    fill(x + s // 2, y + 2, s // 3, s // 3, PAPER)
    px(x + s - 2, y + 2, c)
    px(x + s - 3, y + s - 3, c)


def icon_star(x, y, s, c):
    cx, cy = x + s // 2, y + s // 2
    line(cx, y + 1, cx, y + s - 1, c, 2)
    line(x + 1, cy, x + s - 1, cy, c, 2)
    line(x + 2, y + 2, x + s - 2, y + s - 2, c, 1)
    line(x + s - 2, y + 2, x + 2, y + s - 2, c, 1)


def icon_book(x, y, s, c):
    rect(x + 1, y + 1, s - 2, s - 2, c, 1)
    line(x + s // 2, y + 1, x + s // 2, y + s - 1, c, 1)
    line(x + 3, y + s // 3, x + s // 2 - 2, y + s // 3, c, 1)
    line(x + 3, y + s // 2, x + s // 2 - 2, y + s // 2, c, 1)


ICONS = {
    'globe': icon_globe, 'flame': icon_flame, 'ship': icon_ship,
    'chip': icon_chip, 'ballot': icon_ballot, 'scales': icon_scales,
    'ball': icon_ball, 'bars': icon_bars, 'cross': icon_cross,
    'bolt': icon_bolt, 'moon': icon_moon, 'star': icon_star,
    'book': icon_book,
}

# ------------------------------------------------------------- stories
# (headline, source, icon, colour)
ASIA = [
    ("RUSSIAN JET IN S. KOREAN AIRSPACE",
     "REUTERS", 'bolt', RED),
    ("N. KOREA MAY SHUT SWISS OFFICE", "REUTERS / KCNA",
     'globe', BLUE),
    ("JAPAN LAUNCHES ASIAN OIL RESERVE", "JAPAN / IEA", 'bars',
     TEAL),
    ("MODI OPENS AI CENTRE AT IIT PATNA", "TIMES OF INDIA", 'chip', PURPLE),
    ("INDIA, CHINA HOLD BORDER TALKS", "TIMES OF INDIA",
     'ballot', BLUE),
    ("INDONESIA FACTORY FIRE KILLS 24", "TIMES OF INDIA",
     'flame', RED),
    ("GUKESH DEFENDS CHESS CROWN", "CHESSBASE INDIA",
     'book', BROWN),
]
EUROPE = [
    ("COP31 COLLAPSES WITH NO DEAL", "BBC / CNN", 'flame', RED),
    ("DENMARK COURT BACKS GHETTO LAW", "REUTERS", 'scales',
     BLUE),
    ("UKRAINE SINKS SHIP OFF LIBYA", "CS MONITOR",
     'ship', TEAL),
    ("RUSSIAN SHIP ABLAZE AFTER DRONE HIT", "REUTERS", 'ship',
     RED),
    ("GREENLAND BACKS US SECURITY DEAL", "AL JAZEERA", 'star',
     BLUE),
    ("TAJIKISTAN QUITS THE ICC", "REUTERS", 'scales',
     BLUE),
    ("UK TO HOST 2035 WOMEN'S WORLD CUP", "FIFA", 'ball',
     GREEN),
]
NAMERICA = [
    ("HUANG BACK AS NVIDIA CEO", "REUTERS", 'chip',
     PURPLE),
    ("US STOCKS SURGE ON HUANG RETURN",
     "STRAITS TIMES", 'bars', GREEN),
    ("DEMOCRATS WIN 258 HOUSE SEATS",
     "AP", 'ballot', BLUE),
    ("DEMOCRATS PLAN 12 DEBATES FOR 2028", "CNN",
     'ballot', BLUE),
    ("TRUMP HALTS LEAD-AZIDE BLAST IN IOWA", "REUTERS", 'bolt', RED),
    ("MEGASPEED ON US TRADE BLACKLIST", "BLOOMBERG", 'chip',
     PURPLE),
]
SAMERICA = [
    ("MEXICO NABS SINALOA KINGPIN IN RAID", "AP", 'star', RED),
    ("BUKELE SEEKS THIRD TERM", "BREITBART",
     'ballot', BLUE),
    ("BRAZIL PROBES VANCE-LINKED NETWORK", "WASHINGTON POST",
     'scales', BLUE),
    ("M6.7 QUAKE SHAKES PERU ANDES", "USGS", 'bolt',
     BROWN),
    ("PAREDES FAINTS ON LIVE TV", "AP", 'ball',
     GREEN),
]
AFRICA = [
    ("SENEGAL PRESIDENT RULES BY DECREE", "REUTERS", 'ballot',
     BLUE),
    ("454 MIGRANTS LOST OFF WEST AFRICA", "IOM", 'ship',
     TEAL),
    ("MIGRANT BOAT SINKS OFF SENEGAL", "REUTERS", 'ship',
     RED),
    ("ECOWAS PLANS ANTI-TERROR FORCE", "ECOWAS", 'star',
     TEAL),
]
MIDEAST = [
    ("IRAN VOWS TO FIGHT US BLOCKADE", "AL JAZEERA", 'bolt',
     RED),
    ("OXFAM: GAZA A TOXIC WASTELAND", "BBC", 'flame', RED),
    ("ISRAELI STRIKE KILLS UN WORKER", "REUTERS", 'cross',
     RED),
    ("IRANIAN SINGER FLOGGED 74 TIMES", "REUTERS / CNN",
     'scales', BLUE),
    ("BAHRAIN ACCUSES IRAN OF ATTACK", "FRANCE 24", 'bolt',
     RED),
]
OCEANIA = [
    ("ALL BLACKS FALL TO LOWEST-EVER NO. 5", "WORLD RUGBY", 'ball',
     GREEN),
    ("NZ AWAITS OFFICIAL RESULT", "BBC", 'ballot',
     BLUE),
    ("INDIA-NZ TEST DRAWN IN WELLINGTON", "ICC", 'ball', GREEN),
    ("AUSTRALIA EDGE WALES 29-26 IN CARDIFF", "RUGBYPASS", 'ball',
     GREEN),
]
SPORT = [
    ("ALCARAZ WINS MAIDEN ATP FINALS", "TIMES OF INDIA",
     'ball', GREEN),
    ("DE BRUYNE: LOVE FOR CITY UNCHANGED", "BBC", 'ball',
     GREEN),
    ("SUPERMOON MEETS THE PLEIADES TONIGHT", "CNET", 'moon', PURPLE),
]

REGIONS = [
    ("ASIA", RED, ASIA),
    ("EUROPE", BLUE, EUROPE),
    ("NORTH AMERICA", TEAL, NAMERICA),
    ("SOUTH AMERICA", GREEN, SAMERICA),
    ("AFRICA", BROWN, AFRICA),
    ("MIDDLE EAST", PURPLE, MIDEAST),
    ("OCEANIA", GOLD, OCEANIA),
    ("SPORT & SKY", INK, SPORT),
]

LEADS = [
    ("CLIMATE", "COP31 COLLAPSES", "NO DEAL ON FOSSIL FUELS",
     "AS THE LONGEST CLIMATE", "SUMMIT ENDS EMPTY-HANDED.",
     "BBC / CNN", 'flame', RED),
    ("TECH", "HUANG IS BACK", "NVIDIA REINSTATES ITS CEO",
     "AFTER TRUMP INTERVENES;", "SHARES JUMP A THIRD.",
     "REUTERS / THE TIMES", 'chip', PURPLE),
    ("WAR", "WAR SPILLS OVER", "UKRAINE SINKS A RUSSIAN",
     "WARSHIP OFF LIBYA; A", "SHIP BURNS IN THE BALTIC.",
     "CHRISTIAN SCIENCE MONITOR", 'ship', TEAL),
]

# ------------------------------------------------------------- draw
fill(0, 0, W, H, PAPER)
rect(6, 6, W - 12, H - 12, INK, 2)
rect(12, 12, W - 24, H - 24, INK, 1)

# masthead
ctext(512, 28, "THE WORLD IN ONE PAGE", 6, INK)
fill(120, 92, 784, 3, RED)
ctext(512, 102, "TUESDAY 24 NOVEMBER 2026", 4, RED)
ctext(512, 134, "41 STORIES  -  7 REGIONS  -  EVERY STORY DATED  -  SOURCES NAMED",
      2, GREY)
fill(16, 162, 992, 2, INK)

# lead band: three big stories
LX, LW, LG = 16, 322, 8
LY, LH = 170, 108
for i, (kicker, h1, d1, d2, d3, src, icon, col) in enumerate(LEADS):
    x = LX + i * (LW + LG)
    fill(x, LY, LW, LH, LIGHT)
    rect(x, LY, LW, LH, INK, 1)
    fill(x, LY, LW, 20, col)
    text(x + 8, LY + 4, kicker, 2, WHITE)
    ICONS[icon](x + LW - 28, LY + 1, 18, WHITE)
    text(x + 8, LY + 27, h1, 3, INK)
    text(x + 8, LY + 52, d1, 2, INK)
    text(x + 8, LY + 67, d2, 2, INK)
    text(x + 8, LY + 82, d3, 2, INK)
    text(x + 8, LY + 96, src + "  -  24 NOV 2026", 1, GREY)

# region grid: 4 columns x 2 rows
GX, GY = 16, 288
CW, CH, CG = 242, 330, 8
ROW2Y = GY + CH + 8
for idx, (name, col, stories) in enumerate(REGIONS):
    row = idx // 4
    cidx = idx % 4
    x = GX + cidx * (CW + CG)
    y = GY if row == 0 else ROW2Y
    h = CH if row == 0 else 322
    fill(x, y, CW, h, WHITE)
    rect(x, y, CW, h, INK, 1)
    fill(x, y, CW, 26, col)
    text(x + 8, y + 6, name, 2, WHITE)
    n = str(len(stories))
    text(x + CW - 8 - tw(n, 2), y + 6, n, 2, WHITE)
    sy = y + 34
    slot = (h - 40) // len(stories)
    for (headline, src, icon, icol) in stories:
        ICONS[icon](x + 6, sy + 2, 16, icol)
        maxc = (CW - 34) // 12
        lines = wrap(headline, maxc)[:2]
        for li, ln in enumerate(lines):
            text(x + 28, sy + li * 14, ln, 2, INK)
        text(x + 28, sy + len(lines) * 14 + 1, src + " - 24 NOV 2026", 1,
             GREY)
        sy += slot
        if sy < y + h - 4:
            line(x + 8, sy - 4, x + CW - 8, sy - 4, LIGHT, 1)

# footer
fy = 968
fill(16, fy, 992, 2, INK)
ctext(512, fy + 8,
      "DRAWN BY CODE  -  NO PHOTOGRAPHS  -  ALL 41 STORIES SOURCED AND DATED",
      2, INK)
ctext(512, fy + 26,
      "REUTERS  -  BBC  -  CNN  -  AL JAZEERA  -  TIMES OF INDIA  -  FIFA  -  ICC  -  WORLD RUGBY",
      1, GREY)

# ------------------------------------------------------------- PNG write
def png_chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += buf[yy * W * 3:(yy + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr)
           + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + png_chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


if __name__ == "__main__":
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path)
    print("wrote", path, size, "bytes")
