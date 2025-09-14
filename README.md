# Go Board SVG Generator

A simple Python script that generates printable **Go board diagrams** (9×9, 13×13, 19×19) as SVG files.  
It uses only Python’s standard library, so it runs on **Linux, macOS, and Windows** without extra dependencies.

---

## Features

- Generates Go boards with correct grid and star points (hoshi).
- Supports 9×9, 13×13, and 19×19 board sizes.
- Fully configurable via `config.json`:
  - `grid_size`: board size (9, 13, or 19).  
    *Note: if SGF overlay is enabled, this is overridden by the `SZ[...]` in the SGF file.*
  - `line_thickness`: grid line stroke width (can be fractional, even `< 1`).
  - `star_diameter`: size of the star points (hoshi).
  - `grid_color`: color of the lines and hoshi (any valid CSS color).
  - `background_color`: default board background color (any valid CSS color).
- White background by default, but you can also make wood-tone boards by using:
  - `background_color: "#f1d18a"`
- **SGF overlay support**:
  - Load any `.sgf` file to render game positions or problems on top of the board.
  - Works with SGF files exported from [Online-Go.com](https://online-go.com) and other servers/clients that follow the SGF standard.
  - Initial stones (`AB`, `AW`, `AE`) and sequential moves (`B[...]`, `W[...]`) are supported.
  - Board size from the SGF (`SZ[...]`) automatically overrides the `grid_size` in config.
- **Flexible rendering options** (in `config.json → sgf.render`):
  - `mode`:  
    - `"position"` → apply all moves, show the final position.  
    - `"moves"` → apply the first N moves (controlled by `moves_limit`).
  - `moves_limit`: limit number of moves applied (0 = all).
  - `numbering`:  
    - `"none"` → no numbers.  
    - `"moves"` → number only the played moves.  
    - `"all"` → number setup stones and moves in order.
  - Stone drawing and labels are customizable:
    - `stone_radius_scale` → stone size relative to grid spacing.
    - `move_number_font_scale` → font size for numbers relative to grid spacing.
    - `number_color` → text color for move numbers.
    - `outline_color` → stroke around stones to improve visibility.
- **Export control**:
  - Choose which SVGs to generate in `config.json → export.variants`:  
    - `"board"` → grid + hoshi only.  
    - `"stones"` → stones (and optional numbers) only.  
    - `"both"` → full board (grid + hoshi + stones).  
  - Independent background control for each variant:  
    - `"transparent"` → no background fill.  
    - `"use_config_background"` → uses the top-level `background_color`.  
    - Or any CSS color string (e.g., `"black"`, `"#000000"`, `"beige"`).  
  - Example: transparent board + transparent stones + board+stones with background.  

Because the output is **SVG**, you can scale and print at **any size** without losing quality.

---

## Requirements

- Python **3.7+** (tested with 3.7–3.12).
- No external libraries required.

---

## Usage

1. Place the script, your `config.json`, and any `.sgf` files in the same directory.

2. Example `config.json` without SGF (empty board):

   ```json
   {
     "grid_size": 19,
     "line_thickness": 0.8,
     "star_diameter": 2.5,
     "grid_color": "black",
     "background_color": "white",
     "sgf": {
       "enabled": false
     },
     "export": {
       "variants": ["board", "stones", "both"],
       "board_background": "use_config_background",
       "stones_background": "transparent",
       "both_background": "use_config_background",
       "name_suffix": ""
     }
   }
   ```

3. Example `config.json` with SGF overlay:

   ```json
   {
     "grid_size": 19,
     "line_thickness": 0.8,
     "star_diameter": 2.5,
     "grid_color": "black",
     "background_color": "white",

     "sgf": {
       "enabled": true,
       "path": "example_9x9.sgf",
       "render": {
         "mode": "moves",
         "moves_limit": 0,
         "numbering": "moves",
         "number_color": "#ffffff",
         "outline_color": "#000000",
         "stone_radius_scale": 0.42,
         "move_number_font_scale": 0.44
       }
     },

     "export": {
       "variants": ["board", "stones", "both"],
       "board_background": "transparent",
       "stones_background": "transparent",
       "both_background": "use_config_background",
       "name_suffix": ""
     }
   }
   ```

4. Run the script:

   ```bash
   # Linux / macOS
   chmod +x go_board.py
   ./go_board.py

   # Windows
   python go_board.py
   ```

5. The script creates files like:

   ```
   go_9x9_board.svg
   go_9x9_stones.svg
   go_9x9_both.svg
   ```

---

## Notes

- If SGF overlay is enabled, `grid_size` is ignored — the board size from the SGF takes priority.
- For multiple games, keep `.sgf` files alongside the script and update `config.json` to point at the one you want.
- Output path: the SVG files are written to the **current working directory**.
- Works with SGF files exported from Online-Go.com and most SGF-compatible clients.
- The default line spacing and margins (in mm) are set inside the script.  
  You can change them if you need precise physical dimensions for printing.

---

## License

This project is free to use and modify.
