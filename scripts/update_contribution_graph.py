import json
import os
import math

CONTRIB_PATH = r"C:\Users\faraz\.gemini\antigravity\brain\d4af6c64-a00a-48a3-b658-5223096b7e5d\scratch\contributions.json"
ASSETS_DIR = r"C:\Users\faraz\.gemini\antigravity\brain\d4af6c64-a00a-48a3-b658-5223096b7e5d\scratch\farazmalik180\assets"

with open(CONTRIB_PATH, "r", encoding="utf-8-sig") as f:
    data = json.load(f)

calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]
num_weeks = len(weeks)  # typically 53

LEVEL_MAP = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}

# Build grid[col][row] -> level (0..4)
grid = {}
active_cells = []
for w_idx, w in enumerate(weeks):
    for d in w["contributionDays"]:
        r_idx = d["weekday"]
        lvl = LEVEL_MAP.get(d["contributionLevel"], 0)
        grid[(w_idx, r_idx)] = lvl
        if lvl > 0:
            active_cells.append((w_idx, r_idx, lvl))

# Build a smooth continuous path that sweeps across the grid eating all active cells
# Sort active cells into column groups or nearest-neighbor greedy path from left to right
unvisited = set((c, r) for c, r, _ in active_cells)
path = [(0, 3)]
curr = (0, 3)

while unvisited:
    # Find nearest unvisited cell, biased slightly toward moving left-to-right
    best = min(unvisited, key=lambda p: abs(p[0] - curr[0]) * 1.2 + abs(p[1] - curr[1]))
    # Step Manhattan-wise from curr to best
    cx, cy = curr
    bx, by = best
    while cx != bx:
        cx += 1 if bx > cx else -1
        path.append((cx, cy))
        if (cx, cy) in unvisited:
            unvisited.remove((cx, cy))
    while cy != by:
        cy += 1 if by > cy else -1
        path.append((cx, cy))
        if (cx, cy) in unvisited:
            unvisited.remove((cx, cy))
    curr = (cx, cy)
    if curr in unvisited:
        unvisited.remove(curr)

# Ensure loop back or clean finish at right edge
while curr[0] < num_weeks - 1:
    curr = (curr[0] + 1, curr[1])
    path.append(curr)

# Record first step each cell is visited
first_visit = {}
for step_idx, pos in enumerate(path):
    if pos not in first_visit:
        first_visit[pos] = step_idx

total_steps = len(path)
DURATION = 24.0  # seconds for full cycle

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD_X = 24
PAD_Y = 28
WIDTH = PAD_X * 2 + num_weeks * STEP
HEIGHT = PAD_Y + 7 * STEP + 18

def cell_center(col, row):
    return (PAD_X + col * STEP + CELL / 2.0, PAD_Y + row * STEP + CELL / 2.0)

def generate_pacman_svg(filename, is_dark=True):
    bg_color = "#0d1117" if is_dark else "#ffffff"
    empty_color = "#161b22" if is_dark else "#ebedf0"
    border_color = "#30363d" if is_dark else "#d0d7de"
    wall_color = "#58a6ff" if is_dark else "#0969da"
    text_color = "#8b949e" if is_dark else "#57606a"
    palette = (
        ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
        if is_dark
        else ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
    )

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    lines.append(f'  <rect width="{WIDTH}" height="{HEIGHT}" rx="10" fill="{bg_color}" stroke="{border_color}" stroke-width="1"/>')

    # Month labels across top
    months = ["Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
    for i, m in enumerate(months):
        mx = PAD_X + int(i * (num_weeks / 12.0)) * STEP
        lines.append(f'  <text x="{mx}" y="18" fill="{text_color}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="10">{m}</text>')

    # Draw grid cells with eating animation
    for (col, row), lvl in grid.items():
        x = PAD_X + col * STEP
        y = PAD_Y + row * STEP
        color = palette[lvl]
        if lvl == 0:
            lines.append(f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{empty_color}"/>')
        else:
            visit_step = first_visit.get((col, row), total_steps - 1)
            frac = min(0.95, max(0.02, visit_step / float(total_steps)))
            frac_next = min(0.97, frac + 0.015)
            lines.append(f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}">')
            lines.append(f'    <animate attributeName="fill" values="{color};{color};{empty_color};{empty_color};{color}" keyTimes="0;{frac:.3f};{frac_next:.3f};0.98;1" dur="{DURATION}s" repeatCount="indefinite"/>')
            lines.append('  </rect>')

    # Decorative Pacman arcade maze walls across empty zones
    maze_segments = [
        (3, 1, 3, 5), (3, 1, 7, 1), (8, 5, 13, 5), (13, 2, 13, 5),
        (17, 1, 22, 1), (19, 1, 19, 4), (25, 2, 25, 6), (25, 6, 30, 6),
        (34, 1, 39, 1), (36, 1, 36, 5), (42, 3, 47, 3), (45, 3, 45, 6)
    ]
    for c1, r1, c2, r2 in maze_segments:
        if c2 < num_weeks:
            x1, y1 = cell_center(c1, r1)
            x2, y2 = cell_center(c2, r2)
            lines.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{wall_color}" stroke-width="2" stroke-opacity="0.45" stroke-linecap="round"/>')

    # Build motion path string for Pacman
    pts = [cell_center(c, r) for c, r in path]
    d_str = f"M {pts[0][0]:.1f},{pts[0][1]:.1f} " + " ".join(f"L {p[0]:.1f},{p[1]:.1f}" for p in pts[1:])

    # Pacman character following the path
    lines.append('  <g>')
    lines.append('    <path d="M 0,0 L 6,-4 A 7,7 0 1,0 6,4 Z" fill="#FFD700">')
    lines.append('      <animate attributeName="d" values="M 0,0 L 6,-4.5 A 7,7 0 1,0 6,4.5 Z; M 0,0 L 7,-0.5 A 7,7 0 1,0 7,0.5 Z; M 0,0 L 6,-4.5 A 7,7 0 1,0 6,4.5 Z" dur="0.35s" repeatCount="indefinite"/>')
    lines.append('    </path>')
    lines.append('    <circle cx="1" cy="-3.5" r="1.1" fill="#0d1117"/>')
    lines.append(f'    <animateMotion dur="{DURATION}s" repeatCount="indefinite" path="{d_str}" rotate="auto"/>')
    lines.append('  </g>')

    # 4 Classic Ghosts (Blinky, Pinky, Inky, Clyde) trailing/patrolling
    ghosts = [
        ("#FF2A55", 18),  # Red Blinky
        ("#FF8AE2", 45),  # Pink Pinky
        ("#00E5FF", 75),  # Cyan Inky
        ("#FF9F1C", 105), # Orange Clyde
    ]
    for g_color, offset in ghosts:
        g_pts = pts[offset:] + pts[:offset]
        gd_str = f"M {g_pts[0][0]:.1f},{g_pts[0][1]:.1f} " + " ".join(f"L {p[0]:.1f},{p[1]:.1f}" for p in g_pts[1:])
        lines.append('  <g>')
        lines.append(f'    <path d="M -6,6 L -6,0 A 6,6 0 0,1 6,0 L 6,6 L 4,4 L 2,6 L 0,4 L -2,6 L -4,4 Z" fill="{g_color}"/>')
        lines.append('    <circle cx="-2.2" cy="-1" r="1.6" fill="#ffffff"/><circle cx="2.2" cy="-1" r="1.6" fill="#ffffff"/>')
        lines.append('    <circle cx="-1.8" cy="-1" r="0.8" fill="#1d4ed8"/><circle cx="2.6" cy="-1" r="0.8" fill="#1d4ed8"/>')
        lines.append(f'    <animateMotion dur="{DURATION}s" repeatCount="indefinite" path="{gd_str}"/>')
        lines.append('  </g>')

    lines.append('</svg>')
    with open(os.path.join(ASSETS_DIR, filename), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated {filename} ({len(active_cells)} active contribution days animated)")

generate_pacman_svg("pacman-contribution-graph-dark.svg", is_dark=True)
generate_pacman_svg("pacman-contribution-graph.svg", is_dark=False)
