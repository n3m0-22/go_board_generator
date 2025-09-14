# Go Board SVG Generator

This is a simple Python script that generates printable **Go board diagrams** (9×9, 13×13, 19×19) as SVG files.  
It uses only Python’s standard library, so it runs on **Linux, macOS, and Windows** without extra dependencies.

---

## Features

- Generates Go boards with correct grid and star points (hoshi).
- Supports 9×9, 13×13, and 19×19 board sizes.
- Fully configurable via `config.json`:
  - `grid_size`: board size (9, 13, or 19).
  - `line_thickness`: grid line stroke width (can be fractional, including `< 1`).
  - `star_diameter`: size of the star points (hoshi).
- White background with black grid and hoshi.
- Outputs as a standards-compliant SVG viewable in any modern browser or vector graphics program.

---

## Requirements

- Python **3.7+** (tested with 3.7–3.12).
- No external libraries required.

---

## Usage

1. Create a `config.json` file in the same directory as the script:

   ```json
   {
     "grid_size": 19,
     "line_thickness": 0.8,
     "star_diameter": 2.5
   }

