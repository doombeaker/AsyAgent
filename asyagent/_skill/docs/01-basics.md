# Asymptote Basics

This document covers the core concepts, syntax, and conventions of the Asymptote vector graphics language. Master these fundamentals before working with the specialized modules documented in the other files.

---

## 1. Language Philosophy

Asymptote is a **descriptive vector graphics language** with a mathematical coordinate-based framework. It is **NOT** a WYSIWYG drawing tool — you write code that generates graphics.

Key characteristics:

- **LaTeX-quality typesetting** for labels and text
- **Strong mathematical orientation**: coordinates, paths, and transforms are first-class citizens
- **C++-like syntax** with implicit scaling (e.g., `2x` means `2*x`)
- **Reference semantics** for structs and arrays
- **Default units** are PostScript "big points" (1 bp = 1/72 inch)

---

## 2. Core Types

### 2.1 `pair` — 2D Coordinates

A `pair` represents a point in 2D space. It is the most fundamental type.

```asy
pair origin = (0, 0);
pair topRight = (3, 4);

// Access components (read-only!)
real xCoord = topRight.x;  // 3
real yCoord = topRight.y;  // 4

// Pair arithmetic
pair sum = origin + topRight;      // (3, 4)
pair scaled = 2 * topRight;        // (6, 8)
real dotProduct = origin * topRight; // 0*3 + 0*4 = 0

// Rotate
pair rotated = rotate(45) * topRight;
```

**Important:** `pair` components are **read-only**. You cannot do `topRight.x = 5;`. Instead, reassign the whole pair: `topRight = (5, topRight.y);`.

### 2.2 `path` vs `guide` — Critical Distinction

| Type | Resolution | Performance in Loops | Use Case |
|------|-----------|---------------------|----------|
| `path` | Immediate (fixed cubic spline) | **O(n²)** — copies entire path on each append | Final, resolved geometry |
| `guide` | Deferred (resolved at `draw()` time) | **O(n)** — appends are cheap | Incremental construction |

**Rule of thumb:** Always use `guide` when building paths incrementally (especially in loops), then cast to `path` at draw time.

```asy
// GOOD: O(n) — use guide for incremental construction
guide g;
for (int i = 0; i < 100; ++i) {
    g = g--(i, sin(i));
}
path p = g;  // resolve once
draw(p, blue);

// BAD: O(n²) — path copies entire structure on each append
path p;
for (int i = 0; i < 100; ++i) {
    p = p--(i, sin(i));  // SLOW!
}
```

### 2.3 `picture` and `frame`

- **`picture`** — User-coordinate canvas. What you draw on. Default: `currentpicture`.
- **`frame`** — PostScript-coordinate canvas. Lower-level.

```asy
// Create a new picture
picture pic = new picture;
size(pic, 200, 200, Aspect);  // 200x200 bp, preserve aspect ratio

// Draw on it
draw(pic, (0,0)--(1,1));

// Add to current picture
add(currentpicture, pic, (50, 50));

// Or ship out directly
shipout("output", pic);
```

**Key picture operations:**

```asy
size(200, 150);              // Set dimensions in bp
size(10cm, 8cm, IgnoreAspect);  // Force exact dimensions
unitsize(1cm);               // 1 user unit = 1 cm

// Bounding box
pair lowerLeft = min(currentpicture);
pair upperRight = max(currentpicture);

// Clear
erase(pic);

// Save/restore state
save();
// ... drawing ...
restore();
```

### 2.4 `pen` — Drawing Context

A `pen` encapsulates all drawing context: color, line width, dash pattern, line cap, fill rule, transparency.

```asy
// Default pen
pen currentPen = currentpen;  // black, solid, 0.5bp width

// Compose pens with +
pen redBold = red + linewidth(1.5);
pen dashedBlue = blue + dashed + linewidth(1);

// Scale color intensity
pen lightRed = 0.5 * red;
```

### 2.5 `transform` — Affine Transformations

Transforms are 6-parameter affine matrices applied via left-multiplication.

```asy
// Compose transforms (rightmost applied first)
transform t = shift(10, 20) * scale(2) * rotate(45);
pair p = t * (1, 1);

// Available transforms
shift(pair z);           // Translation
shift(real x, real y);
scale(real s);           // Uniform scale
scale(real x, real y);   // Non-uniform scale
xscale(real x);
yscale(real y);
rotate(real angle, pair z=(0,0));  // Degrees
reflect(pair a, pair b); // Reflection over line a--b
slant(real s);
```

**Transforms apply to:** `pair`, `guide`, `path`, `pen`, `string`, `frame`, `picture`.

---

## 3. Path Construction

### 3.1 Path Connectors

| Operator | Meaning | Example |
|----------|---------|---------|
| `--` | Straight line segment | `(0,0)--(1,1)` |
| `..` | Cubic Bezier spline (auto control points) | `(0,0)..(1,1)..(2,0)` |
| `::` | Inflection-free curve (`..tension atleast 1..`) | `(0,0)::(1,1)::(2,0)` |
| `---` | Straight line via tension | `(0,0)---(1,1)` |
| `&` | Concatenate paths (strips last node of first) | `p1 & p2` |
| `^^` | Move pen without drawing | Creates disjoint subpaths |

### 3.2 Curvature Control

```asy
// Explicit control points
draw((0,0)..controls (0,100) and (100,100)..(100,0));

// Tension: higher = straighter (default 1, min 0.75)
draw((0,0)..tension 2 ..(100,0));
draw((0,0)..tension atleast 2 ..(100,0));

// Direction specifiers at nodes
draw((0,0){up}..{left}(100,100));

// Curl: 0 = straight, 1 ≈ circular
draw((0,0){curl 0}..(100,100)..{curl 0}(200,0));
```

**Caution:** There **must be a space** between tension values and `..`. `tension2..` parses as `tension 2. ..` (the `2.` is a float).

### 3.3 Built-in Paths

```asy
path unitcircle = E..N..W..S..cycle;  // ~0.06% error from true circle
path unitsquare = (0,0)--(1,0)--(1,1)--(0,1)--cycle;

// Functions returning paths
path circle(pair center, real radius);
path arc(pair center, real radius, real startAngle, real endAngle);
path ellipse(pair center, real a, real b);
path box(pair min, pair max);
path brace(pair a, pair b, real amplitude);
```

### 3.4 Path Inspection and Manipulation

```asy
int nSegments = length(path p);     // Number of segments
int nNodes = size(path p);          // Number of nodes
bool isClosed = cyclic(path p);     // Is the path closed?

// Point and direction at parameter t (0..length)
pair pt = point(path p, real t);
pair tangent = dir(path p, real t);

// Arc length operations
real totalLength = arclength(path p);
pair midPt = midpoint(path p);
pair ptAtDist = arcpoint(path p, real dist);

// Subpath and reverse
path sub = subpath(path p, real a, real b);
path rev = reverse(path p);

// Intersections
real[] times = intersect(path p, path q);  // [t_p, t_q]
pair intersectionPt = intersectionpoint(path p, path q);
pair[] allIntersections = intersectionpoints(path p, path q);

// Point-in-polygon test
bool contained = inside(path p, pair z);
```

---

## 4. Drawing Primitives

### 4.1 `draw()`

```asy
void draw(picture pic=currentpicture, Label L="", path g,
          align align=NoAlign, pen p=currentpen,
          arrowbar arrow=None, arrowbar bar=None,
          margin margin=NoMargin, Label legend="", marker marker=nomarker);
```

**Examples:**

```asy
// Basic
draw((0,0)--(1,1));

// With pen
draw((0,0)--(1,1), red + linewidth(1.5));

// With arrow
draw((0,0)--(1,1), arrow=Arrow);
draw((0,0)--(1,1), arrow=Arrows);  // Both ends
draw((0,0)--(1,1), arrow=Arrow(size=3mm, angle=20));

// Dimension bars
draw((0,0)--(1,1), bar=BeginBar + EndBar);

// Margin (shorten line at ends)
draw((0,0)--(1,1), margin=EndMargin);
```

### 4.2 `fill()` and `filldraw()`

```asy
// Fill a cyclic path
fill(unitsquare, lightyellow);

// Fill + draw boundary with different pens
filldraw(unitcircle, lightblue, black + linewidth(1));

// Shading
axialshade(unitsquare, red, (0,0), blue, (1,1));
radialshade(unitcircle, yellow, (0,0), 0, red, (0,0), 1);
```

### 4.3 `clip()`

```asy
clip(unitsquare);
draw(unitcircle);  // Only visible inside the square
```

**Note:** Clipping transcends layers. Use a temporary `picture` for localized clipping.

### 4.4 `label()`

```asy
// Basic label
label("Hello", (0,0));

// LaTeX math
label("$E = mc^2$", (0,0), N);

// With alignment (compass directions)
label("$A$", (0,0), SW);
label("$B$", (1,0), SE);
label("$C$", (0.5, 0.866), N);

// Label on a path
label("midpoint", path g);
label("start", path g, BeginPoint);
label("end", path g, EndPoint);
label("25% along", path g, Relative(0.25));

// Arrow label (label with arrow pointing to position)
arrow("Target", (1,1), E, length=5mm);
```

**Predefined compass directions:**

```asy
E  = (1, 0)     W  = (-1, 0)
N  = (0, 1)     S  = (0, -1)
NE = unit(N+E)  NW = unit(N+W)
SE = unit(S+E)  SW = unit(S+W)
up = N          down = S
right = E       left = W
```

### 4.5 `dot()`

```asy
dot((0,0), red);
dot("$P$", (0,0), E);  // Labeled dot
dot((0,0), Fill(red));  // Filled dot
```

---

## 5. Color and Line Style

### 5.1 Color Creation

```asy
// Grayscale (0=black, 1=white)
pen gray50 = gray(0.5);

// RGB (0-1 range)
pen redPen = rgb(1, 0, 0);

// RGB (0-255 range)
pen redPen255 = RGB(255, 0, 0);

// CMYK
pen redCMYK = cmyk(0, 1, 1, 0);

// Hex string
pen redHex = rgb("#ff0000");

// HSV
pen hsvPen = hsv(180, 0.5, 0.75);

// Named colors (in plain module)
black, white, red, green, blue, cyan, magenta, yellow

// WARNING: `gray` is NOT a predefined color constant.
// Use gray(r) function or rgb() instead:
pen midGray = gray(0.5);              // Correct — function call
pen midGray2 = rgb(0.5, 0.5, 0.5);   // Correct — explicit RGB
// pen midGray3 = gray;               // WRONG — may cause compilation errors

// Additional palettes
import x11colors;  // 140 X11 colors
import texcolors;  // 68 TeX CMYK colors
```

### 5.2 Line Types

```asy
solid;           // Continuous (default)
dotted;          // Dots
dashed;          // 8bp on, 8bp off
longdashed;      // 24bp on, 8bp off
dashdotted;      // Dash-dot pattern
longdashdotted;

// Custom pattern
linetype(new real[] {8, 4, 2, 4});
```

### 5.3 Line Width, Cap, and Join

```asy
linewidth(2);       // 2bp width
linecap(0);         // 0=squarecap, 1=roundcap (default), 2=extendcap
linejoin(0);        // 0=miterjoin, 1=roundjoin (default), 2=beveljoin
miterlimit(10);     // Default 10
```

### 5.4 Fill Rules

```asy
zerowinding;   // Nonzero winding number (default)
evenodd;       // Even-odd rule
```

### 5.5 Font Styling in Labels

Asymptote does **not** have a `bold` pen attribute. To produce bold text in labels, use LaTeX markup:

```asy
// Bold text — use LaTeX \textbf, NOT a pen attribute
label("\textbf{Bold Title}", (0, 5), fontsize(14pt));

// WRONG — `bold` does not exist as a pen attribute
// label("Title", (0, 5), fontsize(14pt) + bold);  // COMPILE ERROR

// Italic text — use LaTeX \textit
label("\textit{Note}", (0, 3), fontsize(9pt));
```

Font size is controlled by `fontsize()`, which takes a `real` (typically with `pt` unit):

```asy
pen titleText = fontsize(14pt);
pen bodyText  = fontsize(9pt);
pen smallText = fontsize(7pt);
```

### 5.6 Transparency (PDF output only)

```asy
pen semiTransparent = opacity(0.5);
pen multiplyBlend = opacity(0.5, "Multiply");
// Blend modes: Normal, Multiply, Screen, Overlay, SoftLight, HardLight,
// ColorDodge, ColorBurn, Darken, Lighten, Difference, Exclusion,
// Hue, Saturation, Color, Luminosity
```

---

## 6. Programming Constructs

### 6.1 Data Types

Built-in types: `void`, `bool`, `bool3`, `int`, `real`, `pair`, `triple`, `string`, `path`, `guide`, `pen`, `transform`, `picture`, `frame`, and more.

**Implicit scaling** (unique Asymptote feature):

```asy
real cm = 72/2.540005;
write(3x);          // 3 * x
write(0.5(x, y));   // (0.5, 0.5)
write(10cm);        // 10 * cm
write(3sin(x));     // 3 * sin(x)
```

### 6.2 Control Flow

```asy
// For loop (C-style)
for (int i = 0; i < 10; ++i) {
    write(i);
}

// Range-based for
int[] fib = {1, 1, 2, 3, 5, 8};
for (int k : fib) {
    write(k);
}

// While and do-while
while (condition) { ... }
do { ... } while (condition);

// Break and continue
break; continue;

// Range iterator
for (int i : range(10)) { write(i); }  // 0..9
```

### 6.3 Functions

```asy
// Standard function
real square(real x) { return x * x; }

// Default arguments (can appear anywhere in parameter list)
real foo(int a = 1, real b = 0) { return a + b; }

// Named arguments
real bar(int x, int y) { return 10 * x + y; }
write(bar(4, x = 3));  // 34 (y=4, x=3)

// Anonymous functions
real(real) f = new real(real x) { return x * x; };

// Higher-order functions
using intOp = int(int);
intOp adder(int m) {
    return new int(int n) { return m + n; };
}
intOp addBy7 = adder(7);
write(addBy7(1));  // 8
```

### 6.4 Arrays

```asy
// Declaration and initialization
real[] values = {0, 1, 2, 3, 5};

// Copy behavior: shallow by default
real[] alias = values;     // alias shares data with values
real[] copy = copy(values); // deep copy

// Virtual members
values.push(8);          // Append
values.pop();            // Remove last
values.insert(1, 99);    // Insert at index
values.delete(0, 2);     // Delete range
values.delete();         // Clear all
values.length;           // Array length
values.cyclic = true;    // Wrap-around indexing

// Slices (Python-like)
int[] x = {0, 1, 2, 3, 4, 5};
int[] y = x[2:4];   // {2, 3}
int[] z = x[:3];    // {0, 1, 2}
int[] w = x[3:];    // {3, 4, 5}

// Built-in array functions
sequence(5);              // {0, 1, 2, 3, 4}
real[] mapped = map(f, values);  // Apply function to each
real[] sorted = sort(values);    // Sorted copy
real total = sum(values);
real minVal = min(values);
real maxVal = max(values);
pair[] zipped = pairs(xArray, yArray);  // Zip two arrays
```

### 6.5 Structures

```asy
// Basic struct
struct Point {
    real x;
    real y;
}

// With constructor (operator init)
struct Circle {
    pair center;
    real radius;

    void operator init(pair center, real radius) {
        this.center = center;
        this.radius = radius;
    }

    real area() {
        return pi * radius * radius;
    }
}

// Usage
Circle c = Circle((0, 0), 5);
write(c.area());

// Operator overloading
Circle operator +(Circle c, pair offset) {
    return Circle(c.center + offset, c.radius);
}
```

---

## 7. Modules and Imports

```asy
// Full import (most common) — names available directly
import graph;
axes();

// Access only — must prefix with module name
access graph;
graph.axes();

// Selective import
from graph access axes, xaxis, yaxis;
axes();

// Rename
import graph as graph2d;
graph2d.axes();

// Wildcard
from graph access *;
```

**Difference between `import` and `include`:**

- `import` — Loads module, resolves dependencies, and "unravels" (imports) names
- `include` — Verbatim text inclusion (like C `#include`)

---

## 8. File I/O

```asy
// Reading
file fin = input("data.txt");
real a = fin;        // Read a real
string s = fin;      // Read string (up to newline)
pair p = fin;        // Read pair (parentheses optional)

// Writing
file fout = output("output.txt");
write(fout, "Value:", a, tab);  // Tab-separated
write(fout, endl);              // Newline

// Suffixes: none, flush, endl, newl, DOSendl, DOSnewl, tab, comma

// Binary output (portable XDR)
file fout = output("data.xdr", mode="xdr");
```

---

## 9. Coding Standards for Asymptote

Asymptote is often used by scientists and mathematicians who may not follow software engineering best practices. **This skill enforces professional coding standards.**

### 9.1 Use Meaningful Variable Names

**Good:**
```asy
pair origin = (0, 0);
pair topVertex = (0, 3);
pair leftBase = (-2, 0);
pair rightBase = (2, 0);

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

#### 9.1.1 Never Use Reserved Keywords as Identifiers

Asymptote reserves several keywords that **must not** appear as variable names, parameter names, or function names. Using them causes cryptic compile errors that don't clearly identify the problem.

**Full reserved word list:**

| Category | Keywords |
|----------|----------|
| Conditional | `if`, `else` |
| Loop | `while`, `for`, `do`, `break`, `continue` |
| Return | `return` |
| Declaration | `struct`, `typedef`, `using` |
| Object | `new`, `operator`, `this`, `explicit` |
| Import | `import`, `include`, `access`, **`from`**, `unravel`, `quote` |

> ⚠️ **`from` is the most common accidental violation.** It looks natural as a parameter name (`pair fromDir`, `real from`) but `from` is a keyword used in `from module access symbol;`. Always choose an alternative.

**Safe alternatives:**

| Avoid | Use instead | Why |
|-------|-------------|-----|
| `from` | `src`, `origin`, `startDir` | `from` is an import keyword |
| `to` | `tgt`, `dest`, `endDir` | `to` is not reserved but pairs confusingly with `from` |
| `new` | `fresh`, `created` | `new` is an allocation keyword |
| `access` | `entry`, `retrieval` | `access` is an import keyword |
| `include` | `embed`, `insert` | `include` is an import keyword |

**Bad — `from` is a keyword:**
```asy
void arrowCurve(picture dest, picture src, pair fromDir,
                picture to, pair toDir) {
    pair a = point(src, fromDir) + gap * fromDir;  // COMPILE ERROR
}
```

**Good:**
```asy
void arrowCurve(picture dest, picture src, pair srcDir,
                picture tgt, pair tgtDir) {
    pair a = point(src, srcDir) + gap * srcDir;    // OK
}
```

### 9.2 Avoid Magic Numbers — Use Named Constants

**Good:**
```asy
real nodeSpacing = 2.5;
real boxWidth = 3.0;
real boxHeight = 1.2;
pair startPos = (0, 0);
pair processPos = (0, -nodeSpacing);
pair decisionPos = (0, -2 * nodeSpacing);
```

**Avoid:**
```asy
block b1 = rectangle("Start", (0,0));
block b2 = rectangle("Process", (0,-2.5));
block b3 = diamond("Valid?", (0,-5.0));
```

### 9.3 Comment Strategically — Map Code to Visual Elements

Comments should explain **what visual element** a block of code produces, making it easy to locate the corresponding part of the image.

**Good:**
```asy
// Main triangle vertices
pair vertexA = (0, 0);
pair vertexB = (4, 0);
pair vertexC = (2, 3);

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

### 9.4 Group Related Drawing Operations

Organize code into logical sections with blank lines and section comments.

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
pair centerO = (0, 0);
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

### 9.5 Reusable Components as Functions

For repeated visual elements, define reusable functions rather than duplicating code.

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

### 9.6 Performance Tips

1. **Use `guide` for incremental path construction** — O(n) vs O(n²) for `path`
2. **Space after `tension` values** — `tension 2 ..` not `tension2..`
3. **Use `copy()` for array deep copies** — Default assignment is shallow
4. **Use `layer()` for draw order control** — Labels and PostScript objects have default ordering

---

## 10. Quick Reference

### Common Operators

```asy
// Arithmetic: + - * / # (int div) % ^ (power)
// Boolean: == != < <= > >= && || ^ !
// Path: -- .. ^^ :: --- &
// Pen: p1 + p2 (combine), p * real (scale color)
// Transform: t1 * t2 (compose), t * pair (apply)
```

### Size Specification

```asy
size(200, 150);                    // width, height in bp
size(5in, 0);                      // 5 inches wide, auto height
size(10cm, 8cm, Aspect);           // preserve aspect ratio (default)
size(10cm, 8cm, IgnoreAspect);     // force exact dimensions
unitsize(1cm);                     // 1 user unit = 1 cm
```

### Output Formats

Source is rendered to an image file by the skill via network rendering against an asyagent HTTP service (see `SKILL.md` → "Rendering"):

```
# Render via the official client (supports svg | pdf | png)
python3 scripts/asy_render.py -f file.asy -F svg -o out.svg
```

---

## 11. Hand-Drawn Style with `trembling`

The `trembling` module provides **path deformation** that makes lines look hand-drawn or sketched. Use it when the user asks for a casual, informal, or artistic visual style.

### Trigger Keywords

Request for any of these should activate the `trembling` module:
- **Chinese**: "手绘风格", "手绘体", "随意线条", "草稿风格"
- **English**: "hand-drawn", "sketch style", "wobbly lines", "rough drawing", "casual style"

### Basic Usage

```asy
import trembling;

// Create a tremble instance
tremble T = tremble(angle=4, frequency=0.5, random=2);

// Deform a path before drawing
path smooth = circle((0,0), 1);
path sketch = T.deform(smooth);
draw(sketch);
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `angle` | 4 | Rotation amplitude in degrees. Higher = more wobble. |
| `frequency` | 0.5 | Node density. <1 adds extra nodes; ≥1 uses one node per floor(frequency). |
| `random` | 2 | Randomization strength. 0 = deterministic; higher = more chaotic. |

### Design Notes

- `trembling` operates on `path` objects, not on `picture` components. To make a `skillutils` box look hand-drawn, you would need to draw its border with a trembled path rather than using the standard `draw(pic, box(...))`.
- The effect is **not suitable** for precise technical diagrams or formal publications.
- See `templates/trembling_*.asy` for working examples.

