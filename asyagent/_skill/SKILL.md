---
name: asymptote
description: Expert Asymptote vector graphics language skill for generating technical drawings, geometric figures, scientific graphs, and flowcharts with LaTeX-quality typesetting.
license: LGPL-3.0
compatibility: opencode
metadata:
  category: graphics
  language: asymptote
  version: "2.0"
---

# Asymptote Vector Graphics Skill

This skill enables the agent to generate high-quality technical vector graphics using the Asymptote language. Asymptote is a powerful descriptive vector graphics language that provides a mathematical coordinate-based framework for technical drawing, with LaTeX typesetting of labels.

## Capabilities

- **2D Geometric Drawings**: Points, lines, circles, polygons, curves, transformations
- **Scientific Graphs**: 2D function plots, data visualization, parametric curves, polar plots
- **Flowcharts**: Block diagrams, algorithm visualization using default primitives
- **Hand-Drawn Style**: Sketch-like drawings with wobbly lines using the `trembling` module (triggered by requests for "手绘风格", "hand-drawn", "sketch", or "wobbly lines")

## Skill Structure

This skill is organized into documentation files, utility libraries, and ready-to-use templates:

| File | Content |
|------|---------|
| `docs/01-basics.md` | Core language syntax, drawing primitives, paths, pens, transforms, coding standards |
| `docs/02-geometry.md` | 2D geometric constructions using the `geometry` module |
| `docs/03-scientific-graphs.md` | Scientific plotting with the `graph` module and `colormap` |
| `docs/04-modular-diagram.md` | Modular diagram construction with `picture` + `point()`: components, arrows, clusters, subplots, overlays |
| `docs/05-skillutils-reference.md` | Skillutils API reference: signatures, parameters, and usage examples |
| `lib/skillutils.asy` | Shared utility library: `label_box_pic`, `label_rounded_pic`, `roundbox`, `pics_bbox`, `pics_cluster` — `import skillutils;` |
| `scripts/asy_render.py` | Network rendering client — renders `.asy` source via a remote asyagent HTTP service (see Rendering below) |
| `templates/` | Ready-to-use templates for common drawing types (see list below) |

### Templates

The `templates/` directory contains production-ready Asymptote files that demonstrate best practices:

**2D Geometric Drawings:**
- `geometric_unit_circle.asy` — Unit circle with angle annotation and sector fill
- `geometric_theorem.asy` — Pythagorean theorem visualization with squares and labels
- `geometric_circumcircle.asy` — Triangle circumcircle construction
- `geometric_venn.asy` — Two-set Venn diagram with overlap coloring

**Scientific Graphs:**
- `scientific_function_plot.asy` — Function plot with axes, ticks, and labels
- `scientific_polar_plot.asy` — Polar plot with filled sector and radial lines
- `scientific_complex_function.asy` — Discontinuous function (Gamma) with branch handling

**Flowcharts:**
- `minimal_flowchart.asy` — Simple vertical flowchart (5 nodes or fewer)
- `modular_flowchart.asy` — Modular flowchart with parallel branches and curved arrows
- `system_diagram.asy` — System architecture with clusters and hierarchical layout

**Hand-Drawn Style:**
- `trembling_basic_shapes.asy` — Basic trembling effect on circle, square, and line
- `trembling_parameters.asy` — Parameter comparison (angle, frequency, random)
- `trembling_handdrawn_geometry.asy` — Hand-drawn style geometric diagram with triangle, altitude, and median

## How to Use

1. **Identify the drawing type** from the user's request
2. **Load the relevant module(s)** with `import module;`
3. **Set up the picture** with `size()`, `unitsize()`, or viewport settings
4. **Draw objects** using the appropriate commands
5. **Add labels** with LaTeX formatting: `label("$...$", position, align);`
6. **Ship out** with `shipout()` or implicit output

## Key Modules

### Automatically Imported (plain.asy)
- `draw()`, `fill()`, `clip()`, `label()` — basic commands
- `pair`, `path`, `pen`, `transform` — basic types
- Compass directions: `N`, `S`, `E`, `W`, `NE`, `NW`, etc.
- `unitsquare`, `unitcircle` — predefined paths

### Optional Standard Modules
- `geometry` — advanced geometric constructions (points, lines, circles, triangles, conics)
- `graph` — scientific plotting (functions, data, axes, ticks, error bars)
- `colormap` — matplotlib-compatible color palettes for data visualization
- `trembling` — hand-drawn path deformation for sketch-like visuals (wobbly lines)

## Rendering: Compiling Source to Images

This skill renders `.asy` source into an image file **exclusively over the network** via an asyagent HTTP service. There is no local-compiler path — the agent does not need `asy`, ImageMagick, or a TeX installation on the host; all compilation happens server-side on the asyagent instance. The agent should **not** ask the user which rendering path to use: there is only one.

### Rendering (`scripts/asy_render.py`)

```bash
python3 <skill_dir>/scripts/asy_render.py -f <source>.asy -F <svg|pdf|png> -o <output_file>
# Inline source instead of a file:
python3 <skill_dir>/scripts/asy_render.py -s 'size(5cm); draw(unitcircle);' -F svg -o circle.svg
```

Supported formats: **svg** (default), **pdf**, **png**. The script is pure stdlib (Python 3.10+, no pip install). It reads source from `-f <file>`, `-s <string>`, or stdin (in that order); output goes to `-o <path>` (`-o -` for raw bytes on stdout).

**Credentials:** The script needs `ASY_API_KEY` (env var or `--api-key`). `ASY_BASE_URL` has a built-in default and rarely needs overriding. **If the script exits with code 2 and reports "missing API key", ask the user for the key** — do not silently fail. Auth failures (HTTP 403, exit 4) likewise mean the key is wrong or expired; surface the full stderr report (it includes the compiler output on 422 errors) so the user can diagnose.

**Error reporting:** The script writes a structured multi-line report to stderr on any failure — HTTP status, server error code, the `x-fn-trace-id`, and (for compile errors) the full Asymptote compiler output with line/column. Always relay this report verbatim to the user when something goes wrong; it is the fastest path to fixing broken source.

**Server-provided modules:** `skillutils.asy` is bundled with the skill and placed on the asyagent server's Asymptote module path, so `import skillutils;` works with no client-side setup. CJK labels also work out of the box via the server's `xelatex` + `ctex` configuration.

### Format Guidance

| Use case | Recommended format | Notes |
|----------|-------------------|-------|
| Visual preview / feedback loop | **png** | Raster, inspectable inline |
| Final vector deliverable (web) | **svg** | Scalable, browser-friendly |
| Final deliverable (print / PDF) | **pdf** | Best for documents |

## Important Conventions

1. **Language and CJK support**: By default, Asymptote uses LaTeX and cannot render CJK (Chinese, Japanese, Korean) characters. The `skillutils` library enables CJK support via `xelatex` + `ctex` — any file that `import skillutils;` can use Chinese labels directly (e.g. `label("流程图", pos)`). For files that do not import `skillutils`, add these lines at the top: `import settings; tex="xelatex"; usepackage("ctex");`. Variable names and comments should remain in English by convention.
2. **Coordinates**: Default in PostScript bp (1/72 inch). Use `unitsize(1cm)` for metric.
3. **Paths**: `--` for straight line, `..` for Bezier spline, `cycle` to close.
4. **Labels**: Double-quoted LaTeX strings: `label("$E=mc^2$", (0,0), N);`
5. **Pens**: Control color, line width, dash pattern: `red+linewidth(1)+dashed`
6. **Transforms**: `shift`, `scale`, `rotate`, `reflect`, `xscale`, `yscale`
7. **Arrowheads**: `Arrow`, `Arrows`, `MidArrow`, with optional `arrowhead=` parameter

**⚠️ Common Pen Mistakes (MUST read):**
- **`gray` is NOT a predefined color constant** — it may cause compilation errors. Use `gray(0.5)` (function call) or `rgb(0.5, 0.5, 0.5)` instead. Never write bare `gray` as a pen.
- **`bold` does NOT exist** as a pen attribute. For bold text, use LaTeX markup: `label("\textbf{Bold}", pos)`. Never write `fontsize(9pt) + bold`.

## Aesthetic Guidelines

- **Keep diagrams clean and minimal**: Avoid cluttering elements with excessive text.
- **Flowchart blocks should contain only keywords**: Each block should hold a brief keyword or short phrase (1-3 words). If detailed explanation is needed, place it in a separate text area or caption outside the diagram, not inside the blocks.
- **Use whitespace effectively**: Ensure adequate spacing between elements for readability.
- **Consistent styling**: Maintain uniform colors, line widths, and font sizes throughout a single diagram.

## Programming Best Practices

Asymptote is often used by scientists and mathematicians who may not be professional programmers. This skill enforces professional coding standards to ensure generated code is readable, maintainable, and easy to modify.

### 1. Use Meaningful Variable Names

Store geometric data in descriptively named variables. This makes the code self-documenting and much easier to map back to the visual diagram.

**Good:**
```asy
pair origin = (0,0);
pair topVertex = (0,3);
pair leftBase = (-2,0);
pair rightBase = (2,0);

triangle tri = triangle(leftBase, rightBase, topVertex);
path altitude = topVertex--foot(topVertex, leftBase, rightBase);

draw(tri);
draw(altitude, dashed);
```

**Avoid:**
```asy
pair a = (0,0), b = (2,0), c = (1,2);
draw(a--b--c--cycle);
draw(c--(1,0), dashed);
```

### 2. Never Use Reserved Keywords as Variable Names

Asymptote reserves several keywords that **must not** appear as identifiers (variable names, parameter names, function names). Using them causes cryptic syntax errors.

**Full reserved word list:**

| Category | Keywords |
|----------|----------|
| Conditional | `if`, `else` |
| Loop | `while`, `for`, `do`, `break`, `continue` |
| Return | `return` |
| Declaration | `struct`, `typedef`, `using` |
| Object | `new`, `operator`, `this`, `explicit` |
| Import | `import`, `include`, `access`, `from`, `unravel`, `quote` |

> **`from` is the most common accidental violation** — it looks natural as a parameter name (e.g., `pair fromDir`) but `from` is a keyword used in `from module access symbol;`. Always choose an alternative name.

**Safe alternatives:**

| Avoid | Use instead |
|-------|-------------|
| `from` | `src` (source), `origin` (starting point), `startDir` (direction from source) |
| `to` | `tgt` (target), `dest` (destination), `endDir` (direction to target) |
| `new` | `fresh`, `created`, `initial` |
| `access` | `entry`, `retrieval` |
| `include` | `embed`, `insert` |

**Bad — `from` is a keyword:**
```asy
void arrowCurve(picture dest, picture src, pair fromDir,
                picture to, pair toDir) {
    pair a = point(src, fromDir) + gap * fromDir;  // COMPILE ERROR
}
```

**Good — use `srcDir` instead:**
```asy
void arrowCurve(picture dest, picture src, pair srcDir,
                picture tgt, pair tgtDir) {
    pair a = point(src, srcDir) + gap * srcDir;
}
```

### 3. Avoid Magic Numbers — Use Named Constants

Never hard-code the same value multiple times. Define constants at the top of your script so adjustments (e.g., changing a radius or spacing) require only a single edit.

**Good:**
```asy
real nodeSpacing = 2.5;
real boxWidth = 3.0;
real boxHeight = 1.2;
pair startPos = (0,0);
pair processPos = (0, -nodeSpacing);
pair decisionPos = (0, -2*nodeSpacing);
```

**Avoid:**
```asy
block b1 = rectangle("Start", (0,0));
block b2 = rectangle("Process", (0,-2.5));
block b3 = diamond("Valid?", (0,-5.0));
```

### 4. Comment Strategically

Comments should explain *what visual element* a block of code produces, making it easy for someone reading the code to locate the corresponding part of the image.

**Good:**
```asy
// Main triangle vertices
pair vertexA = (0,0);
pair vertexB = (4,0);
pair vertexC = (2,3);

// Draw the triangle and label vertices
draw(vertexA--vertexB--vertexC--cycle);
label("$A$", vertexA, SW);
label("$B$", vertexB, SE);
label("$C$", vertexC, N);

// Altitude from C to base AB
pair footD = foot(vertexC, vertexA, vertexB);
draw(vertexC--footD, dashed);
label("$D$", footD, S);
```

### 5. Group Related Drawing Operations

Organize code into logical sections with blank lines and section comments. Group setup, drawing, labeling, and annotations separately.

```asy
// ==========================================
// CONFIGURATION
// ==========================================
real circleRadius = 2.0;
pen mainPen = black + linewidth(1);
pen highlightPen = red + linewidth(1.5);

// ==========================================
// GEOMETRY DEFINITION
// ==========================================
pair centerO = (0,0);
pair pointA = (circleRadius, 0);
pair pointB = rotate(60) * pointA;
pair pointC = rotate(120) * pointA;

path circumcircle = circle(centerO, circleRadius);
path trianglePath = pointA--pointB--pointC--cycle;

// ==========================================
// DRAWING
// ==========================================
draw(circumcircle, mainPen);
filldraw(trianglePath, lightyellow, highlightPen);

// ==========================================
// LABELS
// ==========================================
label("$O$", centerO, SW);
label("$A$", pointA, E);
label("$B$", pointB, NE);
label("$C$", pointC, NW);
```

### 6. Reusable Components as Functions

For repeated visual elements (circuit symbols, custom arrows, grid nodes), define reusable functions rather than duplicating code.

For flowchart/system diagrams specifically, use the shared `skillutils` library which provides:
- **`label_box_pic(boxPosition, boxWidth, boxHeight, lineDy, lines, labelPen, fillPen, borderPen)`** — creates a positioned, styled label box as a `picture`
- **`label_rounded_pic(boxPosition, boxWidth, boxHeight, radius, lineDy, lines, labelPen, fillPen, borderPen)`** — same as `label_box_pic` but with rounded corners
- **`roundbox(bottomLeft, topRight, radius)`** — creates a rounded rectangle path
- **`pics_bbox(pictures)`** — safely computes combined bounding box using `point()` (avoids `min()`/`max()` coordinate trap)
- **`pics_cluster(pictures, padX, padY, fillPen, borderPen)`** — draws a background cluster box auto-sized from its contents

**How to use `skillutils.asy`:** All generated code uses `import skillutils;` to access these functions. Because rendering happens on the asyagent server, `skillutils.asy` is provided server-side — bundled with the skill and placed on the server's Asymptote module path automatically. No client-side installation is needed; `import skillutils;` simply works.

```asy
import skillutils;

pen textPen = fontsize(9pt);
picture pStart = label_box_pic((0, 2), 3.0, 0.9, 0.32, "Start", textPen, startFill, startBorder);
picture pProc  = label_box_pic((3, 0), 3.0, 0.9, 0.32, new string[]{"Process", "compute"}, textPen, procFill, procBorder);

// Cluster background auto-sized from its contents
picture bg = pics_cluster(new picture[]{pStart, pProc}, 0.4, 0.3, clusterFill, clusterPen);
```

```asy
// Reusable resistor symbol
path resistorSymbol(pair start, pair end, real width=0.3, int zigzags=5) {
    pair mid = (start + end) / 2;
    pair dir = unit(end - start);
    pair perp = rotate(90) * dir;
    real len = length(end - start);
    real step = len / zigzags;

    guide g = start;
    for (int i = 0; i < zigzags; ++i) {
        real t = i * step;
        g = g--(start + t*dir + width*perp)
             --(start + (t + step/2)*dir - width*perp);
    }
    return g--end;
}
```

### 7. Use Visual Feedback When Available

If the execution environment supports image viewing, use an iterative visual feedback loop to refine the output:

1. **Generate a preview**: Render to **png** via the render client — `python3 scripts/asy_render.py -f file.asy -F png -o preview.png`. PNG is inspectable immediately.
2. **Inspect visually**: Evaluate proportions, alignment, color balance, label placement, and whitespace directly from the rendered image.
3. **Adjust code**: Tweak coordinates, pens, sizes, or transforms based on what you see, then regenerate.
4. **Final export**: Once the visual result is satisfactory, re-render to the desired final format (usually **svg** or **pdf**).

This loop is especially valuable for complex multi-layer compositions where purely analytical coordinate calculations are not enough to guarantee a clean layout.
