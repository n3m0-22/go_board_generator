#!/usr/bin/env python3
"""
Go Board SVG Generator (refactored)

- Generates SVG diagrams for 9x9, 13x13, or 19x19 Go boards.
- Optional SGF overlay (setup stones + linear move list).
- Export variants: board-only, stones-only, and combined, each with independent background options.

Configuration: config.json
- Top-level board styling and colors.
- Optional SGF overlay block (enabled + path + render options).
- Export block: which variants to produce and backgrounds for each.

This script uses only the Python standard library.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Literal, Optional, Tuple

# =============================================================================
# Types & Constants
# =============================================================================

BoardSize = Literal[9, 13, 19]
NumberingMode = Literal["none", "moves", "all"]
RenderMode = Literal["position", "moves"]
Variant = Literal["board", "stones", "both"]

DEFAULT_LINE_SPACING_MM = 22.0
DEFAULT_MARGIN_MM = 18.0

# =============================================================================
# Data Models
# =============================================================================

@dataclass(frozen=True)
class ExportOptions:
    variants: List[Variant] = field(default_factory=lambda: ["both"])
    board_background: str = "use_config_background"   # "transparent" | "use_config_background" | CSS color
    stones_background: str = "transparent"            # same options
    both_background: str = "use_config_background"    # same options
    name_suffix: str = ""                              # optional filename suffix

@dataclass(frozen=True)
class SGFRenderOptions:
    mode: RenderMode = "position"
    moves_limit: int = 0               # 0 = all
    numbering: NumberingMode = "none"  # "none" | "moves" | "all"
    number_color: str = "#ffffff"
    outline_color: str = "#000000"
    stone_radius_scale: float = 0.42
    move_number_font_scale: float = 0.44

@dataclass(frozen=True)
class SGFOptions:
    enabled: bool = False
    path: str = ""
    render: SGFRenderOptions = field(default_factory=SGFRenderOptions)

@dataclass(frozen=True)
class Config:
    grid_size: BoardSize = 19
    line_thickness: float = 1.0
    star_diameter: float = 2.2
    grid_color: str = "black"
    background_color: str = "white"
    sgf: SGFOptions = field(default_factory=SGFOptions)
    export: ExportOptions = field(default_factory=ExportOptions)

@dataclass(frozen=True)
class GoBoardSpec:
    size: BoardSize
    intersections: int
    mid: int
    hoshi: List[Tuple[int, int]]  # 1-based (row, col)

@dataclass(frozen=True)
class SGFParsed:
    size: Optional[int]
    ab: List[str]      # Add Black setup coords (SGF letters)
    aw: List[str]      # Add White setup coords
    ae: List[str]      # Add Empty (clear)
    moves: List[Tuple[str, str]]  # [('B','dd'), ('W','pp'), ...]

# =============================================================================
# Config I/O
# =============================================================================

def load_config(path: str = "config.json") -> Config:
    """Load config.json and coerce into typed Config (with defaults)."""
    raw = _load_json(path) or {}
    sgf_raw = raw.get("sgf", {}) or {}
    render_raw = sgf_raw.get("render", {}) or {}
    export_raw = raw.get("export", {}) or {}

    # Coerce/validate simple fields
    grid_size = int(raw.get("grid_size", 19))
    if grid_size not in (9, 13, 19):
        _fatal(f"config.grid_size must be 9, 13, or 19 (got {grid_size})")
    line_thickness = float(raw.get("line_thickness", 1.0))
    star_diameter = float(raw.get("star_diameter", 2.2))

    cfg = Config(
        grid_size=grid_size,  # type: ignore[arg-type]
        line_thickness=line_thickness,
        star_diameter=star_diameter,
        grid_color=str(raw.get("grid_color", "black")),
        background_color=str(raw.get("background_color", "white")),
        sgf=SGFOptions(
            enabled=bool(sgf_raw.get("enabled", False)),
            path=str(sgf_raw.get("path", "") or ""),
            render=SGFRenderOptions(
                mode=_coerce_literal(render_raw.get("mode", "position"), ("position", "moves"), "sgf.render.mode"),  # type: ignore[arg-type]
                moves_limit=int(render_raw.get("moves_limit", 0)),
                numbering=_coerce_literal(render_raw.get("numbering", "none"), ("none", "moves", "all"), "sgf.render.numbering"),  # type: ignore[arg-type]
                number_color=str(render_raw.get("number_color", "#ffffff")),
                outline_color=str(render_raw.get("outline_color", "#000000")),
                stone_radius_scale=float(render_raw.get("stone_radius_scale", 0.42)),
                move_number_font_scale=float(render_raw.get("move_number_font_scale", 0.44)),
            ),
        ),
        export=ExportOptions(
            variants=[_coerce_literal(v, ("board", "stones", "both"), "export.variants[]")  # type: ignore[arg-type]
                      for v in (export_raw.get("variants") or ["both"])],
            board_background=str(export_raw.get("board_background", "use_config_background")),
            stones_background=str(export_raw.get("stones_background", "transparent")),
            both_background=str(export_raw.get("both_background", "use_config_background")),
            name_suffix=str(export_raw.get("name_suffix", "")),
        )
    )
    return cfg

def _load_json(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        _fatal(f"could not load {path} -> {e}")
    return None

def _coerce_literal(value: str, allowed: Iterable[str], label: str) -> str:
    v = str(value).strip().lower()
    if v not in allowed:
        _fatal(f"{label} must be one of {tuple(allowed)} (got {value!r})")
    return v

def _fatal(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)

# =============================================================================
# Board Specs & Geometry
# =============================================================================

def make_go_board_spec(size: BoardSize) -> GoBoardSpec:
    """Return board spec with hoshi points for 9/13/19 (1-based indices)."""
    if size == 19:
        k, mid = 4, 10
        pts = [
            (k, k), (k, mid), (k, 19 - k + 1),
            (mid, k), (mid, mid), (mid, 19 - k + 1),
            (19 - k + 1, k), (19 - k + 1, mid), (19 - k + 1, 19 - k + 1),
        ]
    elif size == 13:
        k, mid = 4, 7
        pts = [(k, k), (k, 13 - k + 1), (13 - k + 1, k),
               (13 - k + 1, 13 - k + 1), (mid, mid)]
    elif size == 9:
        k, mid = 3, 5
        pts = [(k, k), (k, 9 - k + 1), (9 - k + 1, k),
               (9 - k + 1, 9 - k + 1), (mid, mid)]
    else:
        _fatal(f"unsupported board size {size}")

    return GoBoardSpec(
        size=size,
        intersections=size * size,
        mid=(size + 1) // 2,
        hoshi=sorted(pts),
    )

# =============================================================================
# SGF Parsing (minimal subset)
# =============================================================================

def parse_sgf_minimal(s: str) -> SGFParsed:
    """
    Minimal SGF parser:
      - SZ board size
      - AB/AW/AE setup lists
      - Linear B/W move sequence (ignores variations/branches)
    """
    s = s.replace("\r", "")
    idx = 0
    props: Dict[str, List[str]] = {}
    order: List[Tuple[str, str]] = []

    def read_ident(i: int) -> Tuple[str, int]:
        j = i
        ident_chars: List[str] = []
        while j < len(s) and s[j].isalpha():
            ident_chars.append(s[j])
            j += 1
        return ("".join(ident_chars), j)

    def read_bracket_val(j: int) -> Tuple[str, int]:
        if j >= len(s) or s[j] != "[":
            _fatal("SGF parse error: expected '['")
        j += 1
        val_chars: List[str] = []
        while j < len(s):
            ch = s[j]
            if ch == "\\" and j + 1 < len(s):
                val_chars.append(s[j + 1])
                j += 2
                continue
            if ch == "]":
                j += 1
                break
            val_chars.append(ch)
            j += 1
        return ("".join(val_chars), j)

    while idx < len(s):
        ch = s[idx]
        if ch in ";()":
            idx += 1
            continue
        if ch.isalpha():
            ident, idx2 = read_ident(idx)
            vals: List[str] = []
            j = idx2
            while j < len(s) and s[j] == "[":
                val, j = read_bracket_val(j)
                vals.append(val)
            up = ident.upper()
            if up in ("B", "W"):
                move_coord = vals[0] if vals else ""
                order.append((up, move_coord))
            else:
                props.setdefault(up, []).extend(vals)
            idx = j
        else:
            idx += 1

    # Extract SZ as int if present
    size_val: Optional[int] = None
    for v in props.get("SZ", [])[::-1]:
        try:
            size_val = int(v)
            break
        except Exception:
            pass

    return SGFParsed(
        size=size_val,
        ab=props.get("AB", []),
        aw=props.get("AW", []),
        ae=props.get("AE", []),
        moves=order,
    )

def sgf_to_rc(coord: str) -> Optional[Tuple[int, int]]:
    """SGF coord 'aa' -> (1,1). Empty coord -> None (pass)."""
    if not coord:
        return None
    if len(coord) != 2:
        return None
    r = ord(coord[1]) - ord("a") + 1
    c = ord(coord[0]) - ord("a") + 1
    if r < 1 or c < 1:
        return None
    return (r, c)

# =============================================================================
# SVG Rendering
# =============================================================================

def render_svg(
    spec: GoBoardSpec,
    *,
    line_thickness: float,
    star_diameter: float,
    grid_color: str,
    background_color: str,
    line_spacing_mm: float = DEFAULT_LINE_SPACING_MM,
    margin_mm: float = DEFAULT_MARGIN_MM,
    include_grid: bool = True,
    include_background_rect: bool = True,
    stones: Optional[List[Tuple[int, int, str]]] = None,   # (row,col,'B'|'W')
    numbers: Optional[List[Tuple[int, int, int]]] = None,  # (row,col,num)
    number_color: str = "#ffffff",
    outline_color: str = "#000000",
    stone_radius_scale: float = 0.42,
    move_number_font_scale: float = 0.44,
) -> str:
    """Build an SVG string with the requested layers."""
    n = spec.size
    s = line_spacing_mm
    m = margin_mm
    width = height = m * 2 + s * (n - 1)

    def pt(i: int) -> float:
        return m + (i - 1) * s

    parts: List[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">'
    )

    if include_background_rect:
        parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background_color}"/>')

    if include_grid:
        # Lines
        for i in range(1, n + 1):
            y = pt(i)
            parts.append(
                f'<line x1="{pt(1)}" y1="{y}" x2="{pt(n)}" y2="{y}" '
                f'stroke="{grid_color}" stroke-width="{line_thickness}"/>'
            )
            x = pt(i)
            parts.append(
                f'<line x1="{x}" y1="{pt(1)}" x2="{x}" y2="{pt(n)}" '
                f'stroke="{grid_color}" stroke-width="{line_thickness}"/>'
            )
        # Hoshi
        r_hoshi = star_diameter / 2.0
        for r, c in spec.hoshi:
            parts.append(f'<circle cx="{pt(c)}" cy="{pt(r)}" r="{r_hoshi}" fill="{grid_color}"/>')

    if stones:
        stone_r = s * stone_radius_scale
        for r, c, color in stones:
            fill = "#000000" if color == "B" else "#ffffff"
            parts.append(
                f'<circle cx="{pt(c)}" cy="{pt(r)}" r="{stone_r}" '
                f'fill="{fill}" stroke="{outline_color}" stroke-width="{line_thickness}"/>'
            )
        if numbers:
            font_size = s * move_number_font_scale
            for r, c, num in numbers:
                parts.append(
                    f'<text x="{pt(c)}" y="{pt(r)}" font-family="sans-serif" font-size="{font_size}" '
                    f'fill="{number_color}" text-anchor="middle" dominant-baseline="central">{num}</text>'
                )

    parts.append("</svg>")
    return "\n".join(parts)

# =============================================================================
# Export Pipeline
# =============================================================================

def choose_background(setting: str, config_bg: str) -> Tuple[bool, str]:
    """
    Decide background behavior from a variant's background setting.
    Returns (include_background_rect, color_if_any).
    """
    s = setting.strip().lower()
    if s == "transparent":
        return (False, config_bg)
    if s == "use_config_background":
        return (True, config_bg)
    return (True, setting)  # any CSS color

def write_svg(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {path}")

def export_variants(
    cfg: Config,
    spec: GoBoardSpec,
    stones: Optional[List[Tuple[int, int, str]]],
    numbers: Optional[List[Tuple[int, int, int]]],
) -> None:
    suffix = f"_{cfg.export.name_suffix}" if cfg.export.name_suffix else ""
    base = f"go_{spec.size}x{spec.size}{suffix}"

    # Precompute common render args (exclude background_color here)
    common = dict(
        spec=spec,
        line_thickness=cfg.line_thickness,
        star_diameter=cfg.star_diameter,
        grid_color=cfg.grid_color,
        number_color=(cfg.sgf.render.number_color if cfg.sgf.enabled else "#ffffff"),
        outline_color=(cfg.sgf.render.outline_color if cfg.sgf.enabled else "#000000"),
        stone_radius_scale=(cfg.sgf.render.stone_radius_scale if cfg.sgf.enabled else 0.42),
        move_number_font_scale=(cfg.sgf.render.move_number_font_scale if cfg.sgf.enabled else 0.44),
    )

    for v in cfg.export.variants:
        if v == "board":
            include_bg, color = choose_background(cfg.export.board_background, cfg.background_color)
            svg = render_svg(
                **common,
                include_grid=True,
                include_background_rect=include_bg,
                background_color=color,
                stones=None,
                numbers=None,
            )
            write_svg(f"{base}_board.svg", svg)

        elif v == "stones":
            include_bg, color = choose_background(cfg.export.stones_background, cfg.background_color)
            svg = render_svg(
                **common,
                include_grid=False,
                include_background_rect=include_bg,
                background_color=color,
                stones=stones,
                numbers=numbers,
            )
            write_svg(f"{base}_stones.svg", svg)

        elif v == "both":
            include_bg, color = choose_background(cfg.export.both_background, cfg.background_color)
            svg = render_svg(
                **common,
                include_grid=True,
                include_background_rect=include_bg,
                background_color=color,
                stones=stones,
                numbers=numbers,
            )
            write_svg(f"{base}_both.svg", svg)

        else:
            print(f"warning: unknown export variant '{v}' (use board|stones|both)")

# =============================================================================
# SGF → Stones/Numbers
# =============================================================================

def build_stones_and_numbers(parsed: SGFParsed, render: SGFRenderOptions) -> Tuple[List[Tuple[int, int, str]], Optional[List[Tuple[int, int, int]]]]:
    """
    Return (stones, numbers) from parsed SGF and render options.

    NOTES:
    - This is a simple overlay. It does not compute captures/ko; later plays overwrite earlier stones at the same point.
    - 'all' numbering: numbers setup stones first (in file order), then moves (play order).
    - 'moves' numbering: numbers only the applied moves.
    """
    stones: Dict[Tuple[int, int], str] = {}
    sequence: List[Tuple[int, int, str, str]] = []  # (r,c,color, origin 'setup'|'move')

    # Setup stones
    for code in parsed.ab:
        rc = sgf_to_rc(code)
        if rc:
            stones[rc] = "B"
            sequence.append((rc[0], rc[1], "B", "setup"))
    for code in parsed.aw:
        rc = sgf_to_rc(code)
        if rc:
            stones[rc] = "W"
            sequence.append((rc[0], rc[1], "W", "setup"))
    for code in parsed.ae:
        rc = sgf_to_rc(code)
        if rc and rc in stones:
            del stones[rc]

    # Moves
    applied_moves: List[Tuple[int, int, str]] = []
    if render.mode == "moves":
        remaining = render.moves_limit if render.moves_limit > 0 else 10**12
        for color, code in parsed.moves:
            if remaining <= 0:
                break
            rc = sgf_to_rc(code)
            if rc is None:  # pass
                continue
            stones[rc] = color
            applied_moves.append((rc[0], rc[1], color))
            sequence.append((rc[0], rc[1], color, "move"))
            remaining -= 1
    else:
        for color, code in parsed.moves:
            rc = sgf_to_rc(code)
            if rc is None:
                continue
            stones[rc] = color
            applied_moves.append((rc[0], rc[1], color))
            sequence.append((rc[0], rc[1], color, "move"))

    stones_list: List[Tuple[int, int, str]] = [(r, c, stones[(r, c)]) for (r, c) in stones.keys()]

    # Numbers
    if render.numbering == "none":
        return (stones_list, None)

    numbers_list: List[Tuple[int, int, int]] = []
    if render.numbering == "moves":
        n = 1
        for r, c, _color in applied_moves:
            numbers_list.append((r, c, n))
            n += 1
    elif render.numbering == "all":
        n = 1
        for r, c, _color, _origin in sequence:
            numbers_list.append((r, c, n))
            n += 1

    return (stones_list, numbers_list)

# =============================================================================
# Main
# =============================================================================

def main() -> None:
    cfg = load_config()

    # Base spec (SGF can override via SZ)
    spec = make_go_board_spec(cfg.grid_size)

    stones: Optional[List[Tuple[int, int, str]]] = None
    numbers: Optional[List[Tuple[int, int, int]]] = None

    if cfg.sgf.enabled:
        if not cfg.sgf.path:
            print("warning: sgf.enabled is true but no path provided; exporting without stones")
        elif not os.path.exists(cfg.sgf.path):
            print(f"warning: SGF file not found: {cfg.sgf.path}; exporting without stones")
        else:
            with open(cfg.sgf.path, "r", encoding="utf-8") as f:
                sgf_text = f.read()

            parsed = parse_sgf_minimal(sgf_text)

            # If SZ present, it overrides config grid_size
            if parsed.size in (9, 13, 19):
                spec = make_go_board_spec(parsed.size)  # type: ignore[arg-type]

            stones, numbers = build_stones_and_numbers(parsed, cfg.sgf.render)

    export_variants(cfg, spec, stones, numbers)

if __name__ == "__main__":
    main()
