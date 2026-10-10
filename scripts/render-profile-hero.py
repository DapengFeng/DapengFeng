#!/usr/bin/env python3
"""Generate the profile's self-contained hacker-terminal SVGs.

Run from the repository root: python3 scripts/render-profile-hero.py
Python's standard library is sufficient. Desktop and mobile layouts share the
same copy and use native monospace fonts, with no remote assets or scripts.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "profile"


def build(theme, mobile=False):
    dark = theme == "dark"
    palette = {
        "bg": "#0d1117" if dark else "#ffffff",
        "bar": "#161b22" if dark else "#f6f8fa",
        "line": "#30363d" if dark else "#d0d7de",
        "text": "#e6edf3" if dark else "#1f2328",
        "muted": "#9da7b3" if dark else "#57606a",
        "green": "#7ee787" if dark else "#1a7f37",
    }
    layout = (
        dict(width=600, height=430, x=28, bar=50, bar_size=20, bar_y=32,
             command_size=23, whoami_y=100, name_size=52, name_y=164,
             roles_size=23, roles_y=205, cat_y=261, log_size=24,
             merged_y=298, date_y=333, value_x=153, comment_size=23,
             comment_y=389, cursor_x=152, cursor_y=82, cursor_width=11)
        if mobile else
        dict(width=1000, height=350, x=34, bar=44, bar_size=16, bar_y=28,
             command_size=20, whoami_y=88, name_size=54, name_y=146,
             roles_size=20, roles_y=181, cat_y=224, log_size=20,
             merged_y=256, date_y=285, value_x=160, comment_size=18,
             comment_y=321, cursor_x=142, cursor_y=72, cursor_width=10)
    )
    p, d = palette, layout
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{d['width']}" height="{d['height']}" viewBox="0 0 {d['width']} {d['height']}" fill="none" role="img" aria-labelledby="title description">
  <title id="title">I'm Dapeng Feng.</title>
  <desc id="description">A GitHub-style terminal introducing Dapeng Feng. Computer vision, robotics, and graphics. Ph.D. at Sun Yat-sen University, completed June 21, 2026. PhD merged. Questions still open.</desc>
  <defs>
    <clipPath id="terminal"><rect width="{d['width']}" height="{d['height']}" rx="10"/></clipPath>
  </defs>
  <style>
    text {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; }}
    .cursor {{ animation: cursor 1.2s step-end infinite; }}
    @keyframes cursor {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .cursor {{ animation: none; }} }}
  </style>
  <g clip-path="url(#terminal)">
    <rect width="{d['width']}" height="{d['height']}" fill="{p['bg']}"/>
    <path d="M0 0H{d['width']}V{d['bar']}H0Z" fill="{p['bar']}"/>
    <path d="M0 {d['bar']}H{d['width']}" stroke="{p['line']}"/>
    <g font-size="{d['bar_size']}">
      <text x="{d['x']}" y="{d['bar_y']}" fill="{p['muted']}">dapeng@github:~/profile</text>
      <text x="{d['width']-d['x']}" y="{d['bar_y']}" text-anchor="end" fill="{p['green']}">main</text>
    </g>
    <text x="{d['x']}" y="{d['whoami_y']}" font-size="{d['command_size']}" fill="{p['text']}"><tspan fill="{p['green']}">$</tspan> whoami</text>
    <rect class="cursor" x="{d['cursor_x']}" y="{d['cursor_y']}" width="{d['cursor_width']}" height="{d['command_size']}" fill="{p['green']}" aria-hidden="true"/>
    <text x="{d['x']-2}" y="{d['name_y']}" font-size="{d['name_size']}" font-weight="500" letter-spacing="-1.5" fill="{p['text']}">I'm Dapeng Feng.</text>
    <text x="{d['x']}" y="{d['roles_y']}" font-size="{d['roles_size']}" fill="{p['muted']}">Computer vision / Robotics / Graphics</text>
    <text x="{d['x']}" y="{d['cat_y']}" font-size="{d['command_size']}" fill="{p['text']}"><tspan fill="{p['green']}">$</tspan> cat education.log</text>
    <g font-size="{d['log_size']}">
      <text x="{d['x']}" y="{d['merged_y']}" fill="{p['green']}">[merged]</text>
      <text x="{d['value_x']}" y="{d['merged_y']}" fill="{p['text']}">Ph.D. · Sun Yat-sen University</text>
      <text x="{d['x']}" y="{d['date_y']}" fill="{p['muted']}">[date]</text>
      <text x="{d['value_x']}" y="{d['date_y']}" fill="{p['text']}">2026-06-21</text>
    </g>
    <text x="{d['x']}" y="{d['comment_y']}" font-size="{d['comment_size']}" fill="{p['muted']}">// PhD merged. Questions still open.</text>
    <rect x=".5" y=".5" width="{d['width']-1}" height="{d['height']-1}" rx="9.5" stroke="{p['line']}"/>
  </g>
</svg>
'''


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        for mobile in (False, True):
            suffix = "-mobile" if mobile else ""
            target = OUT / f"hero-{theme}{suffix}.svg"
            target.write_text(build(theme, mobile), encoding="utf-8")
            print(f"Generated {target.relative_to(ROOT)}")
