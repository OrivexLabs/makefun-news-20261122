#!/usr/bin/env python3
"""
Sum up 22 November's world news in one image.

Deterministic, offline generator: draws a one-page newspaper front page
summarising the world news of Sunday, 22 November 2026 and writes it to
/output/entry.png (override with the ENTRY_OUT environment variable).

Same input data + same drawing code -> byte-identical PNG on every run.
Standard library + Pillow only. News facts were compiled on 2026-11-23
from that day's reports (Open Chronicle, KIRO 7 News, Standard Topic,
The Russell Record) and are frozen into this file.
"""

import os

from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------
# Canvas / palette
# --------------------------------------------------------------------------
W = H = 1024
MARGIN = 46
CONTENT_W = W - 2 * MARGIN

PAPER = (248, 245, 238)
INK = (18, 18, 18)
MUTED = (92, 88, 80)
ACCENT = (168, 32, 24)        # newspaper red
RULE = (30, 30, 30)
LIGHT_RULE = (196, 189, 172)
CHIP_BG = (238, 232, 219)

# --------------------------------------------------------------------------
# Fonts: try the usual system serif/sans faces, fall back gracefully.
# --------------------------------------------------------------------------
SERIF_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf",
]
SERIF_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf",
]
SANS_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
]
SANS_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
]


def _load(candidates, size):
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


class Fonts:
    def __init__(self):
        self.masthead = _load(SERIF_BOLD_CANDIDATES, 66)
        self.date_line = _load(SANS_CANDIDATES, 19)
        self.top_kicker = _load(SANS_BOLD_CANDIDATES, 17)
        self.kicker = _load(SANS_BOLD_CANDIDATES, 16)
        self.lead_head = _load(SERIF_BOLD_CANDIDATES, 46)
        self.lead_body = _load(SANS_CANDIDATES, 21)
        self.chip = _load(SANS_BOLD_CANDIDATES, 17)
        self.head = _load(SERIF_BOLD_CANDIDATES, 26)
        self.body = _load(SANS_CANDIDATES, 18)
        self.brief_head = _load(SANS_BOLD_CANDIDATES, 19)
        self.brief = _load(SANS_CANDIDATES, 18)
        self.footer = _load(SANS_CANDIDATES, 14)


# --------------------------------------------------------------------------
# The day's news — Sunday, 22 November 2026 (frozen data)
# --------------------------------------------------------------------------
LEAD = {
    "kicker": "CLIMATE DIPLOMACY  ·  ANTALYA, TÜRKIYE  ·  TOP STORY",
    "headline": "COP31 Climate Talks Collapse Without a Deal",
    "body": (
        "The UN climate summit ended in disarray: nearly 200 countries failed "
        "to agree on fossil fuels or climate finance despite two days of "
        "overtime talks, leaving the world's climate effort without a roadmap."
    ),
    "chips": ["≈200 nations at the table", "2 days into overtime", "No deal on fossil fuels"],
}

STORIES = [
    {
        "kicker": "RUSSIA–UKRAINE WAR",
        "headline": "Sea Drones Sink Russian Warship off Libya",
        "body": (
            "President Zelenskyy confirmed Ukraine was behind the attack on a "
            "Russian naval vessel docked at Benghazi — a Mediterranean strike, "
            "far from the front line, that widens the war's map."
        ),
    },
    {
        "kicker": "WORLD COURT  ·  THE HAGUE",
        "headline": "ICJ: Myanmar Committed Genocide Against the Rohingya",
        "body": (
            "The International Court of Justice ruled Myanmar's military "
            "committed genocide against the Rohingya. Refugees in Bangladesh "
            "welcomed the verdict — and still want to go home."
        ),
    },
    {
        "kicker": "MIDDLE EAST  ·  THE GULF",
        "headline": "Tankers Struck Near Hormuz; Iran Unveils 'Missile City'",
        "body": (
            "Two tankers were hit near the Strait of Hormuz; Bahrain blamed "
            "Iran for a strike on an industrial site in Sitra. Tehran showed "
            "off a vast underground missile base amid rising US tensions."
        ),
    },
    {
        "kicker": "WEST BANK",
        "headline": "Settler Attacks Torch Homes and Cars Overnight",
        "body": (
            "Israeli settlers raided Palestinian villages near Ramallah, burning "
            "vehicles and homes. Opposition leader Gadi Eisenkot condemned the "
            "attacks as 'terrorism'."
        ),
    },
]

BRIEFS = [
    ("MEXICO", "Cartel boss 'El Chapo Isidro' captured in Sinaloa after a firefight that left 11 dead."),
    ("INDONESIA", "Crews recover more remains in the search for 34 workers missing after a candy-factory fire."),
    ("NIGERIA", "At least 24 people die as a boat carrying mourners to a funeral capsizes."),
    ("TECH", "US officials probe how Nvidia's AI chips reached China despite export controls."),
    ("US POLITICS", "Trump says he'll work with Democrats on a proposed 10% credit-card interest cap."),
]

FOOTER = "Compiled from the day's reports: Open Chronicle · KIRO 7 News · Standard Topic · The Russell Record"

# --------------------------------------------------------------------------
# Drawing helpers
# --------------------------------------------------------------------------


def wrap(draw, text, font, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines, current = [], ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_block(draw, x, y, text, font, fill, max_width, line_gap=6):
    """Draw wrapped text; returns the y just below the block."""
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    line_h = (bbox[3] - bbox[1]) + line_gap
    for line in wrap(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h
    return y


def centered(draw, y, text, font, fill):
    w = draw.textlength(text, font=font)
    draw.text(((W - w) / 2, y), text, font=font, fill=fill)
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    return y + (bbox[3] - bbox[1])


def hline(draw, x0, x1, y, fill, width=1):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


# --------------------------------------------------------------------------
# Compose the front page
# --------------------------------------------------------------------------


def build():
    f = Fonts()
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # Outer frame
    d.rectangle([14, 14, W - 15, H - 15], outline=LIGHT_RULE, width=2)

    x0, x1 = MARGIN, W - MARGIN
    y = 40

    # Masthead
    y = centered(d, y, "O N E - P A G E   W O R L D   B R I E F I N G", f.top_kicker, ACCENT) + 10
    y = centered(d, y, "THE WORLD TODAY", f.masthead, INK) + 8
    y = centered(d, y, "Sunday, November 22, 2026  ·  The day's biggest stories, summed up in a single image",
                 f.date_line, MUTED) + 14
    hline(d, x0, x1, y, RULE, 3)
    hline(d, x0, x1, y + 4, RULE, 1)
    y += 22

    # Lead story
    d.text((x0, y), LEAD["kicker"], font=f.kicker, fill=ACCENT)
    y += 26
    y = text_block(d, x0, y, LEAD["headline"], f.lead_head, INK, CONTENT_W, line_gap=8) + 6
    y = text_block(d, x0, y, LEAD["body"], f.lead_body, (40, 40, 40), CONTENT_W, line_gap=9) + 14

    # Lead stat chips
    cx = x0
    for chip in LEAD["chips"]:
        tw = d.textlength(chip, font=f.chip)
        d.rounded_rectangle([cx, y, cx + tw + 28, y + 34], radius=8, fill=CHIP_BG)
        d.text((cx + 14, y + 7), chip, font=f.chip, fill=(60, 50, 30))
        cx += tw + 44
    y += 48

    hline(d, x0, x1, y, LIGHT_RULE, 2)
    y += 20

    # 2 x 2 story grid
    col_gap = 36
    col_w = (CONTENT_W - col_gap) // 2
    grid_top = y
    row_heights = []
    for row in range(2):
        col_x = [x0, x0 + col_w + col_gap]
        max_bottom = grid_top
        for col in range(2):
            s = STORIES[row * 2 + col]
            sy = grid_top
            d.text((col_x[col], sy), s["kicker"], font=f.kicker, fill=ACCENT)
            sy += 25
            sy = text_block(d, col_x[col], sy, s["headline"], f.head, INK, col_w, line_gap=5) + 4
            sy = text_block(d, col_x[col], sy, s["body"], f.body, (40, 40, 40), col_w, line_gap=6)
            max_bottom = max(max_bottom, sy)
        # vertical divider between the two columns
        d.line([(x0 + col_w + col_gap // 2, grid_top + 2),
                (x0 + col_w + col_gap // 2, max_bottom - 4)], fill=LIGHT_RULE, width=1)
        row_heights.append(max_bottom)
        grid_top = max_bottom + 20
        if row == 0:
            hline(d, x0, x1, grid_top - 10, LIGHT_RULE, 1)
    y = grid_top + 4

    hline(d, x0, x1, y, RULE, 2)
    y += 12

    # In brief
    d.text((x0, y), "AROUND THE WORLD — IN BRIEF", font=f.brief_head, fill=INK)
    y += 32
    for place, line in BRIEFS:
        label = place + "  —  "
        lw = d.textlength(label, font=f.brief_head)
        d.text((x0, y), label, font=f.brief_head, fill=ACCENT)
        y = text_block(d, x0 + lw, y, line, f.brief, (40, 40, 40), CONTENT_W - lw, line_gap=5) + 5

    # Footer pinned near the foot of the page
    y = max(y + 8, H - 92)
    hline(d, x0, x1, y, RULE, 1)
    y += 12
    centered(d, y, FOOTER, f.footer, MUTED)

    return img


def main():
    img = build()
    out = os.environ.get("ENTRY_OUT", "/output/entry.png")
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    img.save(out, format="PNG")


if __name__ == "__main__":
    main()
