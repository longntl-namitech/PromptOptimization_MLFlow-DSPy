"""Draw README diagrams in a hand-drawn style.

Draws the README pipeline diagram. Run:

    python docs/diagrams/make_diagrams.py

Standard library only. The output is deterministic (fixed seeds), so a re-run changes an SVG
only where the drawing code or its text changed. The font is Patrick Hand (SIL OFL 1.1, see
OFL.txt), cut down to Latin characters and embedded, so GitHub shows it without loading
anything.
"""

import base64
import html
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).parent
INK = "#1f1f1f"
FILLS = {
    "lilac": "#ECE3F8",
    "yellow": "#FFF3C4",
    "green": "#DFF2DC",
    "blue": "#DCEAF8",
    "pink": "#FBE1E3",
    "paper": "#FBFAF6",
}
FONT = "Hand, 'Patrick Hand', 'Comic Sans MS', cursive"

# Line icons in a 40 x 40 box, drawn with the ink stroke and no fill.
ICONS = {
    "doc": '<path d="M9 4 H26 L33 11 V36 H9 Z M26 4 V11 H33 M14 18 H28 M14 24 H28 M14 30 H23"/>',
    "folder": '<path d="M4 11 H15 L19 15 H36 V34 H4 Z"/>',
    "scissors": (
        '<circle cx="11" cy="30" r="5"/><circle cx="27" cy="30" r="5"/>'
        '<path d="M14 26 L31 5 M24 26 L7 5"/>'
    ),
    "bolt": '<path d="M23 3 L9 22 H19 L15 37 L31 15 H21 Z"/>',
    "layers": '<path d="M20 5 L36 13 L20 21 L4 13 Z M4 20 L20 28 L36 20 M4 27 L20 35 L36 27"/>',
    "search": '<circle cx="16" cy="16" r="10"/><path d="M24 24 L35 35"/>',
    "trophy": (
        '<path d="M11 5 H29 V14 A9 9 0 0 1 11 14 Z M11 8 H5 A6 6 0 0 0 12 17 '
        'M29 8 H35 A6 6 0 0 1 28 17 M20 23 V30 M13 35 H27 M15 30 H25"/>'
    ),
    "pencil": '<path d="M8 32 L29 11 L34 16 L13 37 L6 38 Z M25 15 L30 20"/>',
    "sparkle": '<path d="M20 4 L23 17 L36 20 L23 23 L20 36 L17 23 L4 20 L17 17 Z"/>',
    "bubble": '<path d="M5 7 H35 V27 H18 L10 34 V27 H5 Z M11 14 H29 M11 20 H24"/>',
    "chart": '<path d="M5 5 V35 H36 M9 28 L17 19 L24 24 L34 11"/>',
    "box": '<path d="M5 12 L20 5 L35 12 V29 L20 36 L5 29 Z M5 12 L20 19 L35 12 M20 19 V36"/>',
}


class Sketch:
    def __init__(self, width: int, height: int, seed: int):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.parts: list[str] = []

    def _j(self, amp: float = 1.5) -> float:
        return self.rng.uniform(-amp, amp)

    def _stroke(self, d: str, width: float = 2.4, opacity: float = 1.0, dash: str = "") -> None:
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{width}" '
            f'stroke-opacity="{opacity}" stroke-linecap="round" stroke-linejoin="round"{extra}/>'
        )

    def _seg(self, x1: float, y1: float, x2: float, y2: float, bow: float = 2.0) -> str:
        """A cubic from the current point to (x2, y2) that bows a little, like a pen line."""
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        b1, b2 = self._j(bow), self._j(bow)
        c1 = (x1 + dx / 3 + nx * b1, y1 + dy / 3 + ny * b1)
        c2 = (x1 + 2 * dx / 3 + nx * b2, y1 + 2 * dy / 3 + ny * b2)
        return f"C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {x2:.1f} {y2:.1f}"

    def _rounded(self, x: float, y: float, w: float, h: float, r: float) -> str:
        j = self._j
        return " ".join(
            [
                f"M {x + r:.1f} {y + j(0.8):.1f}",
                self._seg(x + r, y, x + w - r, y),
                f"Q {x + w:.1f} {y:.1f} {x + w + j(0.8):.1f} {y + r:.1f}",
                self._seg(x + w, y + r, x + w, y + h - r),
                f"Q {x + w:.1f} {y + h:.1f} {x + w - r:.1f} {y + h + j(0.8):.1f}",
                self._seg(x + w - r, y + h, x + r, y + h),
                f"Q {x:.1f} {y + h:.1f} {x + j(0.8):.1f} {y + h - r:.1f}",
                self._seg(x, y + h - r, x, y + r),
                f"Q {x:.1f} {y:.1f} {x + r:.1f} {y:.1f}",
            ]
        )

    def text(
        self,
        x: float,
        y: float,
        s: str,
        size: float,
        anchor: str = "start",
        bold: bool = False,
        rotate: float = 0,
    ) -> None:
        extra = f' stroke="{INK}" stroke-width="{size / 40:.2f}"' if bold else ""
        if rotate:
            extra += f' transform="rotate({rotate} {x:.1f} {y:.1f})"'
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
            f'fill="{INK}"{extra}>{html.escape(s)}</text>'
        )

    def icon(self, name: str, x: float, y: float, scale: float = 1.0) -> None:
        self.parts.append(
            f'<g transform="translate({x:.1f} {y:.1f}) scale({scale})" fill="none" '
            f'stroke="{INK}" stroke-width="2.2" stroke-linecap="round" '
            f'stroke-linejoin="round">{ICONS[name]}</g>'
        )

    def _content(self, x, y, title, bullets, icon, title_size, size) -> None:
        titles = [title] if isinstance(title, str) else list(title)
        tx = x + 22
        if icon:
            self.icon(icon, x + 18, y + 20)
            tx = x + 70
        ty = y + 50
        for line in titles:
            self.text(tx, ty, line, title_size, bold=True)
            ty += title_size + 6
        ty += 8
        for bullet in bullets:
            self.text(x + 24, ty, f"• {bullet}", size)
            ty += size + 11

    def box(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str,
        title,
        bullets=(),
        icon: str | None = None,
        title_size: float = 30,
        size: float = 22,
        r: float = 22,
    ) -> None:
        self.parts.append(f'<path d="{self._rounded(x, y, w, h, r)}" fill="{FILLS[fill]}"/>')
        self._stroke(self._rounded(x, y, w, h, r))
        self._stroke(self._rounded(x, y, w, h, r), width=1.2, opacity=0.5)
        self._content(x, y, title, bullets, icon, title_size, size)

    def label_box(
        self, x: float, y: float, w: float, h: float, fill: str, label: str, size: float = 22
    ) -> None:
        """A small box with one centred line, for lists of names."""
        self.parts.append(f'<path d="{self._rounded(x, y, w, h, 14)}" fill="{FILLS[fill]}"/>')
        self._stroke(self._rounded(x, y, w, h, 14), width=2.0)
        self.text(x + w / 2, y + h / 2 + size / 3, label, size, anchor="middle")

    def frame(self, x: float, y: float, w: float, h: float, label: str) -> None:
        self.parts.append(f'<path d="{self._rounded(x, y, w, h, 26)}" fill="{FILLS["paper"]}"/>')
        self._stroke(self._rounded(x, y, w, h, 26), width=2.0, dash="14 10")
        self.text(x + 28, y + 44, label, 30, bold=True)

    def cylinder(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str,
        title,
        bullets=(),
        icon: str | None = None,
    ) -> None:
        rx, ry = w / 2, 20
        body = (
            f"M {x} {y + ry} L {x} {y + h - ry} A {rx} {ry} 0 0 0 {x + w} {y + h - ry} "
            f"L {x + w} {y + ry} A {rx} {ry} 0 0 0 {x} {y + ry} Z"
        )
        self.parts.append(f'<path d="{body}" fill="{FILLS[fill]}"/>')
        for width, opacity in ((2.4, 1.0), (1.2, 0.5)):
            top_ry = ry + self._j(1.2)
            self._stroke(
                f"M {x} {y + ry} A {rx} {top_ry:.1f} 0 0 1 {x + w} {y + ry} "
                f"A {rx} {top_ry:.1f} 0 0 1 {x} {y + ry}",
                width,
                opacity,
            )
            self._stroke(
                f"M {x} {y + ry} {self._seg(x, y + ry, x, y + h - ry)} "
                f"A {rx} {ry + self._j(1.2):.1f} 0 0 0 {x + w} {y + h - ry} "
                f"{self._seg(x + w, y + h - ry, x + w, y + ry)}",
                width,
                opacity,
            )
        self._content(x, y + 2 * ry - 8, title, bullets, icon, 30, 22)

    def arrow(self, *points, dash: str = "", head: float = 16) -> None:
        d = f"M {points[0][0]:.1f} {points[0][1]:.1f} " + " ".join(
            self._seg(a[0], a[1], b[0], b[1], bow=1.4)
            for a, b in zip(points, points[1:], strict=False)
        )
        self._stroke(d, dash=dash)
        (x1, y1), (x2, y2) = points[-2], points[-1]
        angle = math.atan2(y2 - y1, x2 - x1)
        for side in (-1, 1):
            a = angle + math.pi + side * 0.45
            self._stroke(
                f"M {x2:.1f} {y2:.1f} L {x2 + head * math.cos(a):.1f} {y2 + head * math.sin(a):.1f}"
            )

    def dashed_rule(self, y: float) -> None:
        self._stroke(f"M 30 {y} {self._seg(30, y, self.width - 30, y, bow=1)}", dash="20 14")

    def person(self, cx: float, top: float, label: str) -> None:
        self._stroke(
            f"M {cx + 18} {top + 18} A 18 18 0 1 1 {cx + 17.9} {top + 17} "
            f"M {cx} {top + 36} {self._seg(cx, top + 36, cx, top + 92)} "
            f"M {cx - 30} {top + 58} {self._seg(cx - 30, top + 58, cx + 30, top + 58)} "
            f"M {cx} {top + 92} L {cx - 26} {top + 134} M {cx} {top + 92} L {cx + 26} {top + 134}"
        )
        self.text(cx, top + 170, label, 26, anchor="middle")

    def heading(self, title: str, subtitle: str) -> None:
        self.text(40, 70, title, 52, bold=True)
        self.text(40, 116, subtitle, 25)

    def svg(self) -> str:
        font = base64.b64encode((HERE / "PatrickHand-Latin.ttf").read_bytes()).decode()
        style = (
            "@font-face{font-family:Hand;src:url(data:font/ttf;base64,"
            f"{font}) format('truetype');}}text{{font-family:{FONT};}}"
        )
        return "\n".join(
            [
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} '
                f'{self.height}" width="{self.width}" height="{self.height}">',
                f"<style>{style}</style>",
                f'<rect width="{self.width}" height="{self.height}" fill="#FFFFFF"/>',
                *self.parts,
                "</svg>",
            ]
        )




def pipeline() -> Sketch:
    s = Sketch(2000, 780, seed=1)
    s.heading(
        "PromptOptimization_MLFlow-DSPy: from prompt to optimized program",
        "Each box is a module; arrows are data flow. MLflow autolog tracks runs and traces.",
    )
    w, gap, top, bottom = 520, 160, 170, 470
    xs = [60 + i * (w + gap) for i in range(3)]
    s.box(xs[0], top, w, 200, "green", "init_prompt.py", ["register base prompts", "business_filter_card", "business_filter_payment_account"], "pencil")
    s.box(xs[1], top, w, 200, "yellow", "BusinessFilter", ["dspy.Predict, gpt-4o-mini", "prompt@latest + scope text", "returns reason, in_scope"], "sparkle")
    s.box(xs[2], top, w, 200, "lilac", "Data (data/)", ["BOT_FAQS.json: labelled questions", "business_filter.xlsx: scope sheets"], "folder")
    s.box(xs[0], bottom, w, 200, "green", "Evaluate baseline", ["dspy.Evaluate on eval split", "in_scope == label", "main.py eval"], "search")
    s.box(xs[1], bottom, w, 200, "yellow", "GEPA optimize", ["teacher gpt-5-mini reflects", "judge gpt-4.1-mini gives feedback", "main.py optimize"], "bolt")
    s.box(xs[2], bottom, w, 200, "green", "Saved program", ["<prompt name>_results/", "<prompt name>.json"], "doc")
    s.arrow((xs[0] + w + 10, top + 100), (xs[1] - 12, top + 100))
    s.arrow((xs[2] - 10, top + 100), (xs[1] + w + 12, top + 100))
    s.arrow((xs[1] + 120, top + 210), (xs[1] + 120, bottom - 12))
    s.arrow((xs[1] + 60, top + 210), (xs[1] + 60, top + 250), (xs[0] + w / 2, top + 250), (xs[0] + w / 2, bottom - 12))
    s.arrow((xs[1] + w + 10, bottom + 100), (xs[2] - 12, bottom + 100))
    s.text(60, 725, "Fill: lilac = data input, yellow = calls an LLM, green = plain code.", 24)
    s.text(60, 758, "The MLflow prompt registry feeds BusinessFilter through load_prompt(prompts:/<name>@latest).", 24)
    return s


def main() -> None:
    (HERE / "pipeline.svg").write_text(pipeline().svg(), encoding="utf-8")
    print("wrote pipeline.svg")


if __name__ == "__main__":
    main()
