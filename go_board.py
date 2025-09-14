#!/usr/bin/env python3
import json
import sys
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class GoBoardSpec:
    size: int
    intersections: int
    mid: int
    hoshi: List[Tuple[int,int]]
    corner_offset: int
    side_points_included: bool
    notes: str

def _hoshi_for_size(n: int) -> Tuple[List[Tuple[int,int]], int, bool]:
    if n == 19:
        k, mid = 4, (n + 1) // 2
        pts = [
            (k, k), (k, mid), (k, n - k + 1),
            (mid, k), (mid, mid), (mid, n - k + 1),
            (n - k + 1, k), (n - k + 1, mid), (n - k + 1, n - k + 1),
        ]
        return pts, k, True
    elif n == 13:
        k, mid = 4, (n + 1) // 2
        pts = [(k, k), (k, n - k + 1), (n - k + 1, k),
               (n - k + 1, n - k + 1), (mid, mid)]
        return pts, k, False
    elif n == 9:
        k, mid = 3, (n + 1) // 2
        pts = [(k, k), (k, n - k + 1), (n - k + 1, k),
               (n - k + 1, n - k + 1), (mid, mid)]
        return pts, k, False
    else:
        raise ValueError("grid_size must be 9, 13, or 19")

def make_go_board_spec(n: int) -> GoBoardSpec:
    hoshi, k, sides = _hoshi_for_size(n)
    return GoBoardSpec(
        size=n,
        intersections=n * n,
        mid=(n + 1) // 2,
        hoshi=sorted(hoshi),
        corner_offset=k,
        side_points_included=sides,
        notes=("stones on intersections; coordinates are 1-based (row,col); "
               f"{'9-star pattern' if sides else '5-star pattern'} with center (tengen)")
    )

def spec_to_svg(spec: GoBoardSpec,
                line_spacing_mm: float = 22.0,
                margin_mm: float = 18.0,
                line_thickness: float = 1.0,
                star_diameter: float = 2.2) -> str:
    n = spec.size
    s = line_spacing_mm
    m = margin_mm
    width = height = m * 2 + s * (n - 1)

    def pt(idx: int) -> float:
        return m + (idx - 1) * s

    lines = []
    for i in range(1, n + 1):
        y = pt(i)
        lines.append(
            f'<line x1="{pt(1)}" y1="{y}" x2="{pt(n)}" y2="{y}" '
            f'stroke="black" stroke-width="{line_thickness}"/>'
        )
        x = pt(i)
        lines.append(
            f'<line x1="{x}" y1="{pt(1)}" x2="{x}" y2="{pt(n)}" '
            f'stroke="black" stroke-width="{line_thickness}"/>'
        )

    hoshi = []
    r = star_diameter / 2.0
    for row, col in spec.hoshi:
        hoshi.append(f'<circle cx="{pt(col)}" cy="{pt(row)}" r="{r}" fill="black"/>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="white"/>
  {''.join(lines)}
  {''.join(hoshi)}
</svg>'''
    return svg

def main():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        print("error: could not load config.json ->", e)
        sys.exit(1)

    n = cfg.get("grid_size", 19)
    line_thickness = float(cfg.get("line_thickness", 1.0))
    star_diameter = float(cfg.get("star_diameter", 2.2))

    try:
        spec = make_go_board_spec(n)
    except ValueError as e:
        print("error:", e)
        sys.exit(1)

    filename = f"go_{spec.size}x{spec.size}.svg"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(spec_to_svg(spec,
                            line_thickness=line_thickness,
                            star_diameter=star_diameter))
    print(f"Generated {filename} with {spec.intersections} intersections.")

if __name__ == "__main__":
    main()


