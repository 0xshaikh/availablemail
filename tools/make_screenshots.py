#!/usr/bin/env python3
"""Render realistic screenshots of the availablemail CLI output.

Produces three PNGs into assets/:
  - find_google_demo.png       — basic find across Gmail
  - find_suffixes_demo.png     — with custom suffixes
  - list_providers_demo.png    — list-providers output
  - webapp_demo.png            — the live web app UI (fake screenshot)
  - webapp_results.png         — results table populated

Pure stdlib + Pillow. Deterministic — same output every run.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Palette (matches the demo page's dark theme)
# ---------------------------------------------------------------------------
BG = (11, 15, 20)
PANEL = (15, 20, 27)
PANEL2 = (20, 27, 36)
BORDER = (31, 41, 55)
FG = (229, 231, 235)
MUTED = (139, 149, 165)
DIM = (91, 102, 117)
ACCENT = (124, 240, 189)
ACCENT2 = (92, 225, 168)
WARN = (240, 198, 116)
BAD = (240, 121, 124)
GREEN = (124, 240, 189)
YELLOW = (240, 198, 116)
RED = (240, 121, 124)


def load_font(size: int, mono: bool = True) -> ImageFont.FreeTypeFont:
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
        if mono
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        if mono
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_terminal(
    lines: list[tuple[str, int | None]],
    title: str,
    out_path: Path,
    width: int = 900,
    font_size: int = 15,
    extra_height: int = 0,
):
    """Draw a macOS-style terminal screenshot."""
    font = load_font(font_size, mono=True)
    # line spacing
    line_h = font_size + 8
    padding = 18
    term_bar_h = 36
    body_h = len(lines) * line_h + padding * 2
    img_h = term_bar_h + body_h + extra_height

    img = Image.new("RGB", (width, img_h), BG)
    d = ImageDraw.Draw(img)

    # Terminal bar
    d.rectangle([0, 0, width, term_bar_h], fill=PANEL2)
    d.line([0, term_bar_h, width, term_bar_h], fill=BORDER, width=1)
    for i, col in enumerate([RED, YELLOW, GREEN]):
        cx, cy = 20 + i * 20, term_bar_h // 2
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=col)
    d.text((80, term_bar_h // 2 - font_size // 2), title, font=font, fill=DIM)

    # Body background
    body_top = term_bar_h
    d.rectangle([0, body_top, width, img_h], fill=(5, 8, 12))

    y = body_top + padding
    x = padding
    for text, color in lines:
        c = color if color is not None else FG
        d.text((x, y), text, font=font, fill=c)
        y += line_h

    img.save(out_path, "PNG", optimize=True)
    print(f"wrote {out_path} ({width}x{img_h})")


def find_google_lines() -> list[tuple[str, int | None]]:
    lines = [
        ("$ availablemail anas shaikh --provider google --limit 15", FG),
        ("", None),
        ("  #  Score  Address", MUTED),
        ("-------------------", DIM),
    ]
    rows = [
        (100, "anas.shaikh@gmail.com"),
        (100, "a.shaikh@gmail.com"),
        (100, "ashaikh@gmail.com"),
        (100, "anasshaikh@gmail.com"),
        (100, "anas-shaikh@gmail.com"),
        (100, "shaikh.anas@gmail.com"),
        (100, "shaikh-anas@gmail.com"),
        (100, "sanas@gmail.com"),
        (96, "ashaikh.ai@gmail.com"),
        (96, "ashaikh.in@gmail.com"),
        (96, "ashaikh.io@gmail.com"),
        (96, "a.shaikh.ai@gmail.com"),
        (96, "a.shaikh.in@gmail.com"),
        (92, "ashaikh.dev@gmail.com"),
        (92, "ashaikh.hello@gmail.com"),
    ]
    for i, (score, addr) in enumerate(rows, 1):
        color = ACCENT if score >= 100 else ACCENT2
        lines.append((f"{i:>3}  {score:>5}  {addr}".ljust(60), color))
    return lines


def find_suffix_lines() -> list[tuple[str, int | None]]:
    lines = [
        ("$ availablemail anas shaikh --suffixes dev,hello,founder,io,ai --limit 15", FG),
        ("", None),
        ("  #  Score  Address", MUTED),
        ("-------------------", DIM),
    ]
    rows = [
        (96, "ashaikh.dev@gmail.com", "firstlast.suf"),
        (96, "ashaikh.ai@gmail.com", "firstlast.suf"),
        (96, "ashaikh.io@gmail.com", "firstlast.suf"),
        (96, "ashaikh.hello@gmail.com", "firstlast.suf"),
        (96, "ashaikh.founder@gmail.com", "firstlast.suf"),
        (95, "a.shaikh.dev@gmail.com", "f.last.suf"),
        (95, "a.shaikh.ai@gmail.com", "f.last.suf"),
        (92, "anas.dev@gmail.com", "first.suf"),
        (92, "anas.ai@gmail.com", "first.suf"),
        (92, "anas.io@gmail.com", "first.suf"),
        (92, "anas.hello@gmail.com", "first.suf"),
        (88, "ashaikh.dev.in@gmail.com", "first.suf1.suf2"),
        (88, "ashaikh.dev.ai@gmail.com", "first.suf1.suf2"),
        (88, "ashaikh.dev.io@gmail.com", "first.suf1.suf2"),
        (88, "ashaikh.ai.dev@gmail.com", "first.suf1.suf2"),
    ]
    for i, (score, addr, pat) in enumerate(rows, 1):
        color = ACCENT if score >= 96 else ACCENT2
        lines.append((f"{i:>3}  {score:>5}  {addr}".ljust(55) + pat, color))
    return lines


def list_providers_lines() -> list[tuple[str, int | None]]:
    providers = [
        ("gmail.com", "Gmail"),
        ("hotmail.com", "Hotmail"),
        ("outlook.com", "Outlook"),
        ("live.com", "Live"),
        ("yahoo.com", "Yahoo"),
        ("icloud.com", "iCloud"),
        ("aol.com", "AOL"),
        ("protonmail.com", "ProtonMail"),
        ("proton.me", "Proton"),
        ("tutanota.com", "Tutanota"),
        ("zoho.com", "Zoho"),
        ("gmx.com", "GMX"),
        ("yandex.com", "Yandex"),
        ("mail.ru", "Mail.ru"),
        ("rediffmail.com", "Rediff"),
        ("msn.com", "MSN"),
    ]
    lines = [
        ("$ availablemail list-providers", FG),
        ("", None),
        ("All providers:", FG),
    ]
    for domain, name in providers:
        lines.append((f"  {domain:<20} {name}", MUTED))
    lines.append(("", None))
    lines.append(("Groups:", FG))
    groups = [
        ("all", "gmail.com, hotmail.com, outlook.com, live.com, yahoo.com, ..."),
        ("google", "gmail.com"),
        ("microsoft", "hotmail.com, outlook.com, live.com, msn.com"),
        ("yahoo", "yahoo.com"),
        ("icloud", "icloud.com"),
        ("proton", "protonmail.com, proton.me"),
        ("aol", "aol.com"),
    ]
    for g, doms in groups:
        lines.append((f"  {g:<12} {doms}", MUTED))
    return lines


# ---------------------------------------------------------------------------
# Web app "screenshot" — a mock of the demo UI
# ---------------------------------------------------------------------------


def draw_webapp_screenshot(out_path: Path):
    W, H = 1200, 820  # noqa: N806 — screenshot canvas dimensions
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    font_h1 = load_font(30, mono=False)
    font_h2 = load_font(16, mono=False)
    font_p = load_font(14, mono=False)
    font_small = load_font(12, mono=False)
    font_mono = load_font(13, mono=True)
    font_mono_sm = load_font(11, mono=True)
    font_badge = load_font(11, mono=False)

    # Header bar
    d.rectangle([0, 0, W, 56], fill=PANEL)
    d.line([0, 56, W, 56], fill=BORDER, width=1)
    d.ellipse([22, 24, 30, 32], fill=ACCENT)
    d.text((40, 20), "availablemail", font=font_h2, fill=FG)
    nav_x = W - 260
    for label in ["Docs", "Live Demo", "GitHub"]:
        d.text((nav_x, 22), label, font=font_p, fill=FG if label == "Live Demo" else MUTED)
        nav_x += 90

    # Hero
    y = 90
    d.text((40, y), "Find a", font=font_h1, fill=FG)
    # gradient-ish "professional email"
    x = 40 + d.textlength("Find a ", font=font_h1)
    d.text((x, y), "professional email", font=font_h1, fill=ACCENT)
    d.text(
        (40 + d.textlength("Find a professional email ", font=font_h1), y),
        "in one click.",
        font=font_h1,
        fill=FG,
    )
    y += 52
    for line in [
        "Type your name, pick a provider, and get a ranked list of candidates — every pattern,",
        "every suffix, scored for LinkedIn-header quality. Runs entirely in your browser.",
    ]:
        d.text((40, y), line, font=font_p, fill=MUTED)
        y += 22

    # Badges
    y += 8
    badges = [
        "0 network calls",
        "16 providers",
        "10 patterns",
        "13 default suffixes",
        "100% client-side",
    ]
    bx = 40
    for b in badges:
        w = d.textlength(b, font=font_badge) + 20
        d.rounded_rectangle([bx, y, bx + w, y + 24], radius=12, fill=PANEL, outline=BORDER)
        d.text((bx + 10, y + 5), b, font=font_badge, fill=MUTED)
        bx += w + 8

    # Card 1: form
    card1_y = y + 40
    d.rounded_rectangle([40, card1_y, W - 40, card1_y + 220], radius=12, fill=PANEL, outline=BORDER)
    d.rounded_rectangle([56, card1_y + 16, 76, card1_y + 36], radius=5, fill=ACCENT)
    d.text((61, card1_y + 20), "1", font=font_small, fill=(8, 34, 26))
    d.text((84, card1_y + 14), "Your details", font=font_h2, fill=FG)

    # Two-column inputs
    inp_y = card1_y + 60
    for i, (label, value) in enumerate([("FIRST NAME", "Anas"), ("LAST NAME", "Shaikh")]):
        col_x = 56 + i * 300
        d.text((col_x, inp_y), label, font=font_small, fill=MUTED)
        d.rounded_rectangle(
            [col_x, inp_y + 18, col_x + 260, inp_y + 50],
            radius=8,
            fill=(17, 22, 29),
            outline=BORDER,
        )
        d.text((col_x + 12, inp_y + 26), value, font=font_p, fill=FG)

    inp_y2 = inp_y + 70
    for i, (label, value) in enumerate([("PROVIDER", "Gmail"), ("MAX RESULTS", "20")]):
        col_x = 56 + i * 300
        d.text((col_x, inp_y2), label, font=font_small, fill=MUTED)
        d.rounded_rectangle(
            [col_x, inp_y2 + 18, col_x + 260, inp_y2 + 50],
            radius=8,
            fill=(17, 22, 29),
            outline=BORDER,
        )
        d.text((col_x + 12, inp_y2 + 26), value, font=font_p, fill=FG)

    # Suffixes input
    inp_y3 = inp_y2 + 70
    d.text((56, inp_y3), "CUSTOM SUFFIXES", font=font_small, fill=MUTED)
    d.rounded_rectangle(
        [56, inp_y3 + 18, 56 + 560, inp_y3 + 50], radius=8, fill=(17, 22, 29), outline=BORDER
    )
    d.text((68, inp_y3 + 26), "dev, hello, founder, io, ai", font=font_p, fill=FG)

    # Generate button
    btn_y = card1_y + 200
    d.rounded_rectangle([56, btn_y, 220, btn_y + 36], radius=8, fill=ACCENT)
    d.text((78, btn_y + 8), "Generate candidates →", font=font_p, fill=(8, 34, 26))

    # Card 2: results
    card2_y = card1_y + 250
    d.rounded_rectangle([40, card2_y, W - 40, H - 10], radius=12, fill=PANEL, outline=BORDER)
    d.rounded_rectangle([56, card2_y + 16, 76, card2_y + 36], radius=5, fill=ACCENT)
    d.text((61, card2_y + 20), "2", font=font_small, fill=(8, 34, 26))
    d.text((84, card2_y + 14), "Results", font=font_h2, fill=FG)

    # Stats row
    stats = [("GENERATED", "20"), ("TOP SCORE", "100"), ("PROVIDERS", "1"), ("TIME", "3.4ms")]
    sx = 56
    for label, val in stats:
        w = 120
        d.rounded_rectangle(
            [sx, card2_y + 50, sx + w, card2_y + 90], radius=8, fill=(17, 22, 29), outline=BORDER
        )
        d.text((sx + 10, card2_y + 54), label, font=font_small, fill=MUTED)
        d.text((sx + 10, card2_y + 68), val, font=font_h2, fill=FG)
        sx += w + 8

    # Result rows
    rows = [
        (1, "anas.shaikh", "@gmail.com", "first.last", 100, "strong"),
        (2, "a.shaikh", "@gmail.com", "f.last", 100, "strong"),
        (3, "ashaikh", "@gmail.com", "firstlast", 100, "strong"),
        (4, "anasshaikh", "@gmail.com", "firstlast", 100, "strong"),
        (5, "anas-shaikh", "@gmail.com", "first-last", 100, "strong"),
        (6, "shaikh.anas", "@gmail.com", "last.first", 100, "strong"),
        (7, "shaikh-anas", "@gmail.com", "last-first", 100, "strong"),
        (8, "sanas", "@gmail.com", "firstlast", 100, "strong"),
        (9, "ashaikh.ai", "@gmail.com", "firstlast.suf", 96, "strong"),
        (10, "ashaikh.in", "@gmail.com", "firstlast.suf", 96, "strong"),
        (11, "ashaikh.io", "@gmail.com", "firstlast.suf", 96, "strong"),
        (12, "a.shaikh.ai", "@gmail.com", "f.last.suf", 96, "strong"),
    ]
    ry = card2_y + 105
    for rank, local, dom, pat, score, tag in rows:
        row_h = 26
        d.rounded_rectangle(
            [56, ry, W - 56, ry + row_h], radius=6, fill=(17, 22, 29), outline=BORDER
        )
        d.text((64, ry + 5), str(rank), font=font_mono_sm, fill=DIM)
        d.text((100, ry + 4), local, font=font_mono, fill=FG)
        d.text((100 + d.textlength(local, font=font_mono), ry + 4), dom, font=font_mono, fill=MUTED)
        # pattern pill
        pat_w = d.textlength(pat, font=font_mono_sm) + 12
        d.rounded_rectangle(
            [300, ry + 5, 300 + pat_w, ry + 20], radius=4, fill=PANEL2, outline=BORDER
        )
        d.text((306, ry + 7), pat, font=font_mono_sm, fill=MUTED)
        # score pill
        score_col = ACCENT if score >= 85 else (WARN if score >= 60 else MUTED)
        d.rounded_rectangle(
            [480, ry + 3, 520, ry + 22],
            radius=4,
            fill=score_col if score >= 85 else PANEL2,
            outline=None,
        )
        d.text(
            (488, ry + 5), str(score), font=font_mono_sm, fill=(8, 34, 26) if score >= 85 else FG
        )
        # avail tag
        tag_col = ACCENT2 if tag == "strong" else (WARN if tag == "decent" else BAD)
        tag_bg = tuple(int(c * 0.15 + 5) for c in tag_col)
        d.rounded_rectangle([550, ry + 4, 620, ry + 21], radius=4, fill=tag_bg)
        d.text((562, ry + 6), tag, font=font_mono_sm, fill=tag_col)
        # copy / mailto buttons
        d.rounded_rectangle([900, ry + 5, 960, ry + 20], radius=4, fill=PANEL2, outline=BORDER)
        d.text((910, ry + 6), "copy", font=font_mono_sm, fill=MUTED)
        d.rounded_rectangle([968, ry + 5, 1050, ry + 20], radius=4, fill=PANEL2, outline=BORDER)
        d.text((982, ry + 6), "mailto", font=font_mono_sm, fill=MUTED)
        ry += row_h + 4

    img.save(out_path, "PNG", optimize=True)
    print(f"wrote {out_path} ({W}x{H})")


def main():
    draw_terminal(
        find_google_lines(), "~", ASSETS / "find_google_demo.png", width=760, font_size=14
    )
    draw_terminal(
        find_suffix_lines(), "~", ASSETS / "find_suffixes_demo.png", width=840, font_size=14
    )
    draw_terminal(
        list_providers_lines(), "~", ASSETS / "list_providers_demo.png", width=760, font_size=13
    )
    draw_webapp_screenshot(ASSETS / "webapp_demo.png")


if __name__ == "__main__":
    main()
