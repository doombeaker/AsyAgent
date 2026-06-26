# Asymptote Vector Graphics Skill

This is an OpenCode agent skill for generating high-quality technical vector graphics using the Asymptote language.

## Overview

Asymptote is a powerful descriptive vector graphics language that provides a mathematical coordinate-based framework for technical drawing, with LaTeX-quality typesetting of labels. This skill enables agents to produce professional geometric figures, scientific plots, and flowcharts with clean, maintainable code.

## Supported Drawing Types

- **2D Geometric Drawings**: Points, lines, circles, triangles, polygons, conics, transformations
- **Scientific Graphs**: 2D function plots, data visualization, parametric curves, polar plots, error bars, vector fields
- **Flowcharts**: Block diagrams, algorithm visualization using default Asymptote primitives
- **Picture Composition**: Reusable components, layered drawings, subplots, overlays using `add(picture, picture)`
- **Hand-Drawn Style**: Sketch-like, wobbly-line drawings using the `trembling` module for informal or artistic visuals

## Structure

```
├── SKILL.md              # Main skill definition and entry point
├── README.md             # This file
├── docs/                 # Knowledge base documentation
│   ├── 01-basics.md      # Core language syntax, paths, pens, transforms, coding standards
│   ├── 02-geometry.md    # 2D geometric constructions using the geometry module
│   ├── 03-scientific-graphs.md  # Scientific plotting with graph and colormap modules
│   ├── 04-modular-diagram.md    # Modular diagram construction with picture + point()
│   └── 05-skillutils-reference.md # Skillutils API reference
├── lib/                  # Shared Asymptote libraries (part of the skill)
│   └── skillutils.asy    # Reusable library: label_box_pic, label_rounded_pic, roundbox, pics_bbox, pics_cluster
├── scripts/              # Tooling for the skill
│   └── asy_render.py     # Network rendering client (renders .asy via a remote asyagent HTTP service)
├── templates/            # Ready-to-use Asymptote templates
│   ├── geometric_*.asy   # 2D geometric drawing templates
│   ├── scientific_*.asy  # Scientific graph templates
│   ├── *_flowchart.asy  # Flowchart templates
│   ├── *_diagram.asy    # System architecture templates
│   └── trembling_*.asy  # Hand-drawn / sketch-style templates
└── vendor/               # Reference source files
    ├── asymptote.texi    # Asymptote user manual
    ├── geometry.asy      # Geometry module source
    ├── graph.asy         # Graph module source
    ├── colormap.asy      # Colormap module source
    └── trembling.asy     # Hand-drawn path deformation module source
```

## Installation

This skill is **distributed by an asyagent server**, not via a standalone GitHub clone. An asyagent server bundles the skill and exposes a self-describing install endpoint, so any agent can discover the skill and install it just by talking to the server.

### Prerequisites

You need the URL of a running asyagent server (e.g. `http://localhost:8787`, or your deployed instance). No local `asy`, ImageMagick, or TeX installation is required — all compilation happens server-side. To run your own server, see the [asyagent project](../README.md) (`python3 -m asyagent`).

### For Users (install via the asyagent server)

1. **Fetch the install manifest** from the server — it describes the skill, lists every file with a download URL, and gives the exact install steps plus the render API:

   ```bash
   curl -s http://<asyagent-host>:8787/v1/skill
   ```

2. **Follow the `install.steps` in the manifest.** Typically this is a single archive download extracted into the OpenCode skills directory:

   ```bash
   curl -sL http://<asyagent-host>:8787/v1/skill/archive.tar.gz | tar xz -C ~/.config/opencode/skills
   ```

   `skillutils.asy` is bundled with the skill and is placed on the server's Asymptote module path automatically — `import skillutils;` works with no client-side setup.

3. **Load the skill on demand** from the agent:

   ```
   skill({ name: "asymptote" })
   ```

The manifest's `render_api` section also tells the agent how to call the server's `POST /v1/render` endpoint to turn `.asy` source into an image — so after install, the agent knows both how to write Asymptote code (from the skill docs) and how to render it (from the server).

### For Contributors

The skill source lives inside the asyagent package at `asyagent/_skill/`. The render client is `scripts/asy_render.py`; the server side is the `asyagent/` Python package.

## Usage

The skill is loaded automatically by OpenCode when working with Asymptote-related tasks. The main `SKILL.md` provides the entry point, with detailed documentation in the `docs/` directory.

### Quick Start

Once the skill is loaded, the agent can generate Asymptote code for various drawing tasks:

```asy
// Example: Draw a simple geometric figure
import geometry;

pair A = (0, 0);
pair B = (4, 0);
pair C = (2, 3);

draw(A--B--C--cycle);
dot("$A$", A, SW);
dot("$B$", B, SE);
dot("$C$", C, N);
```

## Key Design Principles

This skill enforces the following principles for all generated code:

1. **Professional coding standards**: Meaningful variable names, named constants, strategic comments mapping code to visual elements
2. **Default capabilities first**: Prefer Asymptote's built-in primitives over standard libraries (e.g., use default drawing for flowcharts instead of `import flowchart`)
3. **CJK support**: Chinese labels are supported via `xelatex` + `ctex`, enabled automatically by `import skillutils;` (or manually by adding `import settings; tex="xelatex"; usepackage("ctex");`)
4. **Clean aesthetics**: Minimal text in diagram elements (1-3 words per flowchart block), consistent styling, effective whitespace
5. **Picture-based composition**: Encapsulate repeated elements in `picture` functions, compose with `add(dest, src)`, and apply transforms (`shift`, `rotate`) before adding
6. **Shared utilities**: Use `import skillutils;` for common diagram building blocks (`label_box_pic`, `label_rounded_pic`, `roundbox`, `pics_bbox`, `pics_cluster`)
7. **Hand-drawn style**: When the user asks for sketch-like, informal, or artistic visuals (e.g. "手绘风格", "hand-drawn", "wobbly lines", "sketch"), use `import trembling;` and apply `tremble.deform()` to paths before drawing. See `templates/trembling_*.asy` for examples.

## Output Formats

The skill renders `.asy` source to images **over the network** via an asyagent server, using `scripts/asy_render.py` as the official client (see `SKILL.md` for full details):

- **Rendering** (`scripts/asy_render.py` against an asyagent server): supports **svg** (default), **pdf**, **png** — needs `ASY_API_KEY` (env var or `--api-key`); `ASY_BASE_URL` points at the server and has a built-in default.

Common formats: **PDF** (documents), **SVG** (web), **PNG** (preview/feedback).

## License

LGPL-3.0 (matching Asymptote's license)
