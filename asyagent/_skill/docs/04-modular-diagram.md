# Modular Diagram Construction with picture + point()

> Practical guide for building structured diagrams — system architectures, data flows, workflows, concept maps — using Asymptote's `picture` composition and `point()` boundary anchors.

This document merges two concerns that are inseparable in practice: **`picture` composition mechanics** (how to create, transform, and assemble sub-pictures) and **diagram layout techniques** (how to connect nodes, group clusters, and organize visual hierarchy). The core insight is that Asymptote's `picture` + `point()` pattern is the universal foundation — it applies equally to flowcharts, system diagrams, subplots, overlays, and any modular drawing.

The `flowchart` standard module is intentionally **not used** here. Its shapes (Start/End ovals, Decision diamonds) are too restrictive for general diagrams. Default primitives + `skillutils` provide full control over layout, grouping, and arrow styling.

---

## 1. Philosophy & Core Principles

### What Makes a Good Diagram

A good diagram answers: **What are the parts, and how do they relate?**

Key principles:

- **Nodes are `picture` components** — encapsulated in a function, returned as a `picture`, positioned with `shift()`
- **Arrows use `point()` anchors** — query a node's boundary (`N`, `S`, `E`, `W`, etc.) instead of manually computing `center ± half_width`
- **Grouping shows hierarchy** — clusters, layers, or logical boundaries
- **Color encodes role** — different colors for different types of entities
- **Minimal text in nodes** — name + one-line description; details go in captions

### Core Principles for `picture` Usage

These five rules govern all `picture`-based drawing. Violating any of them produces broken or misleading output.

**1. Prefer `add(dest, src)` where `src` is a `picture`**

`add(dest, src)` places `src`'s user coordinates directly into `dest`'s coordinate system, unified by `dest`'s final `user → PS` transform. This automatically maintains a common scale across all sub-pictures without manual size calculations.

`add(dest, src.fit(), pos)` (frame usage) first scales `src` to a fixed size and then places it at `pos`. **Only use this when you need strictly fixed physical-size labels or legends**; it is not recommended for routine sub-picture composition.

**2. The final picture must have `size()` set first**

Before adding any sub-picture with `add()`, call `size(final, ...)` on the final output picture. Otherwise `dest` falls back to the PostScript bp coordinate system (1/72 inch), making all added sub-pictures extremely tiny.

**3. Apply transforms to a `picture`, then `add`**

Adjust position or angle via `shift(t) * pic`, `rotate(a) * pic`, etc. These return a new `picture`. Then `add(dest, newPic)`. This fully decouples component definition from layout.

**4. Use `shipout()` with a `picture` argument, not a filename**

`shipout(final)` is sufficient. The output filename is controlled by external tooling (Makefile, scripts, or the `-o` flag). Avoid hard-coding filenames in code.

**5. Draw arrows first, add nodes second (z-order)**

Drawing arrows before adding nodes places arrows behind nodes visually. Since `point()` coordinates are valid regardless of add order, you can also reverse the order if you prefer arrows on top.

---

## 2. `point()`: Querying Picture Boundary Anchors

When composing sub-pictures into a diagram, you often need to know where a sub-picture's edges are — to draw arrows between nodes, align labels, or position adjacent elements. Instead of manually tracking box dimensions and computing `center ± half_width`, Asymptote provides `point()`.

### Function Signature

```
pair point(picture pic=currentpicture, pair dir, bool user=true);
```

Returns the point on `pic`'s bounding box in the direction `dir` relative to its center. With `user=true` (the default), the returned value is in user coordinates.

### Compass Direction Constants

Asymptote predefines standard compass directions as `pair` constants in the `plain` module:

| Constant | Value | Meaning |
|----------|-------|---------|
| `N` | `(0, 1)` | North (top center) |
| `S` | `(0, -1)` | South (bottom center) |
| `E` | `(1, 0)` | East (right center) |
| `W` | `(-1, 0)` | West (left center) |
| `NE` | `unit(N+E)` | Northeast corner |
| `NW` | `unit(N+W)` | Northwest corner |
| `SE` | `unit(S+E)` | Southeast corner |
| `SW` | `unit(S+W)` | Southwest corner |

Any `pair` can be used as a direction — `point(pic, (1, 2))` returns the boundary point toward (1,2) from center. If your variable shadows a direction constant (e.g., `real E = 2.718`), use `plain.E` to access the original.

### Core Workflow: Create → Shift → Point → Draw

```asy
// 1. CREATE: component function draws at origin, returns a picture
picture makeNode(string text, real boxWidth, real boxHeight, pen fillPen, pen borderPen) {
    picture pic;
    fill(pic, box((-boxWidth/2, -boxHeight/2), (boxWidth/2, boxHeight/2)), fillPen);
    draw(pic, box((-boxWidth/2, -boxHeight/2), (boxWidth/2, boxHeight/2)), borderPen);
    label(pic, text, fontsize(9pt));
    return pic;
}

// 2. SHIFT: position each instance in the parent coordinate system
real boxWidth = 3, boxHeight = 1;
picture nodeA = shift(0,  2) * makeNode("Upper", boxWidth, boxHeight, lightblue, blue);
picture nodeB = shift(0, -1) * makeNode("Lower", boxWidth, boxHeight, lightgreen, green);

// 3. POINT: query boundary anchors — no manual boxHeight/2 needed
pair aSouth = point(nodeA, S);   // bottom edge of nodeA
pair bNorth = point(nodeB, N);   // top edge of nodeB

// 4. DRAW: connect with arrows, then add nodes
picture final;
size(final, 10cm);

draw(final, aSouth -- bNorth, arrow = Arrow(TeXHead));
add(final, nodeA);
add(final, nodeB);

shipout(final);
```

### Adding Gaps

`point()` returns the exact edge. For visual breathing room, add a small offset in the appropriate direction:

```asy
real gap = 0.25;
pair start = point(topNode, S) + (0, -gap);   // slightly below south edge
pair end   = point(botNode, N) + (0,  gap);   // slightly above north edge
draw(dest, start -- end, arrow = Arrow(TeXHead));
```

### `point()` vs Manual Calculation

| Approach | Moving a node | Different box sizes | Code clarity |
|----------|--------------|---------------------|-------------|
| `center.y - boxHeight/2 - gap` | Must update every arrow | Must know each node's `boxHeight` | Scattered magic numbers |
| `point(node, S) - (0, gap)` | Just change `shift()` | Automatic | Self-documenting |

### Related Functions

```
pair min(picture pic, user=true);   // bottom-left corner of bounding box
pair max(picture pic, user=true);   // top-right corner of bounding box
pair size(picture pic, user=true);  // (width, height) of bounding box
```

Useful for centering a picture that has been `add()`-ed to a sized parent: `shift(-min(pic, true)) * pic` shifts so the bottom-left corner is at origin.

> **⚠️ Gotcha: `min()`/`max()` on standalone pictures**
>
> `min(pic)` and `max(pic)` return coordinates through the picture's `user → PS` transform. For a standalone sub-picture that has **never been `add()`-ed to a sized parent picture**, this transform is the PostScript bp identity — the returned coordinates are in an unrelated scale, not user coordinates.
>
> Use `point(pic, SW)` for bottom-left and `point(pic, NE)` for top-right instead. These compute boundary anchors from the picture's drawn content and stored transforms, returning correct user-coordinate values even for standalone pictures.
>
> The `skillutils` library provides `pics_bbox(picture[] pics)` which wraps this pattern safely.

---

## 3. Building Block Components

### 3.1 Configuration Pattern

All diagram parameters should be defined at the top as named constants. This makes the diagram easy to adjust and ensures consistency.

```asy
import skillutils;

// Box dimensions — still needed for component function parameters
real boxWidth       = 3.0;    // Box width
real boxHeight       = 0.9;    // Box height
real gap      = 0.2;    // Gap between box edge and arrow tip

// Layout grid
real xMain    = 0;      // Center column x-coordinate
real xLeft    = -4.5;   // Left branch x-coordinate
real xRight   = 4.5;    // Right branch x-coordinate
real yTop     = 10;     // Top of the diagram
real dy       = 1.5;    // Vertical step between nodes
```

**Key difference from raw-coordinate approach:** You define `boxWidth` and `boxHeight` once for the component function, but you **never** write `boxHeight/2` or `boxWidth/2` in arrow code — `point()` handles that automatically.

### 3.2 `label_box_pic()` — Rectangular Node

The fundamental unit. Use the `label_box_pic()` function from `skillutils.asy` — it creates a labeled, filled, bordered box as a `picture`, already shifted to the desired position.

```asy
import skillutils;

// label_box_pic signature (from skillutils.asy):
//
//   picture label_box_pic(pair boxPosition, real boxWidth, real boxHeight,
//                         real lineDy, string[] lines,
//                         pen label_text, pen fillPen, pen borderPen)
//
// Key features:
//   - boxPosition param: the box is shifted to boxPosition internally,
//     so you call label_box_pic((x, y), boxWidth, boxHeight, ...) directly
//     instead of shift(x, y) * label_box_pic(boxWidth, boxHeight, ...)
//   - label_text pen param: full control over font size, color, weight.
//   - Descriptive camelCase param names (boxWidth, boxHeight) avoid
//     collisions with Asymptote stdlib identifiers.
//
// Usage — create, then add to parent:
picture box1 = label_box_pic((0, 2), boxWidth, boxHeight, 0.32, "Gateway",
                             fontsize(9pt), gatewayFill, gatewayBorder);
picture box2 = label_box_pic((0, -1), boxWidth, boxHeight, 0.32,
                             new string[]{"Pod 1", "Agent + UI"},
                             fontsize(9pt), workerFill, workerBorder);

picture diagram;
add(diagram, box1);
add(diagram, box2);
```

**Why `picture` instead of `void`?**
- `point(box1, S)` gives the south boundary — no `boxHeight/2` math needed
- Moving a node only requires changing the `boxPosition` argument — all arrows follow automatically
- The same component function produces nodes of any size — `point()` adapts

### 3.3 `label_rounded_pic()` — Rounded Corner Node

For a softer, more modern "card" look, use `label_rounded_pic()`. It has the same interface as `label_box_pic()` with one additional `radius` parameter for corner rounding.

```asy
import skillutils;

// label_rounded_pic signature (from skillutils.asy):
//
//   picture label_rounded_pic(pair boxPosition, real boxWidth, real boxHeight,
//                             real radius, real lineDy, string[] lines,
//                             pen label_text, pen fillPen, pen borderPen)
//
// The radius parameter controls corner curvature. It is automatically
// clamped to half the smaller dimension, so you cannot overshoot.
//
// Usage:
picture card1 = label_rounded_pic((0, 2), boxWidth, boxHeight, 0.2, 0.32, "Service A",
                                  fontsize(9pt), svcFill, svcBorder);
picture card2 = label_rounded_pic((0, -1), boxWidth, boxHeight, 0.2, 0.32,
                                  new string[]{"Service B", "v2.1"},
                                  fontsize(9pt), svcFill, svcBorder);

picture diagram;
add(diagram, card1);
add(diagram, card2);
```

The underlying path helper `roundbox(bottomLeft, topRight, radius)` is also exported from `skillutils` if you need rounded rectangle paths directly:

```asy
// roundbox signature:
//   path roundbox(pair bottomLeft, pair topRight, real radius)
//
// Returns a cyclic path tracing a rounded rectangle from (bottomLeft.x, bottomLeft.y+radius)
// clockwise through all four rounded corners.
path rbox = roundbox((0, 0), (4, 2), 0.3);
filldraw(rbox, lightblue, blue);
```

### 3.4 Custom Component Pattern

You can define your own `picture`-returning components following the same pattern:

```asy
picture diamondNode(pair boxPosition, real w, real h, string text,
                    pen labelPen, pen fillPen, pen borderPen) {
    picture pic;
    pair top = (0, h/2), bot = (0, -h/2);
    pair left = (-w/2, 0), right = (w/2, 0);
    filldraw(pic, top--right--bot--left--cycle, fillPen, borderPen);
    label(pic, text, (0, 0), labelPen);
    return shift(boxPosition) * pic;
}
```

Any shape works — the key is: **draw at origin, return `shift(boxPosition) * pic`**. Then `point()` anchors work regardless of shape or size.

---

## 4. Connecting with Arrows

### 4.1 Arrow Helpers Using `point()`

Arrow helpers take `picture` arguments and use `point()` to find boundary anchors. No manual `boxHeight/2 + gap` calculations.

```asy
// ==========================================
// ARROW HELPERS — using point() boundary anchors
// ==========================================

// Vertical arrow: top node's south → bottom node's north
void arrowDown(picture dest, picture top, picture bot,
               real gap=0.2, pen p=currentpen) {
    pair a = point(top, S) + (0, -gap);
    pair b = point(bot, N) + (0,  gap);
    draw(dest, a -- b, arrow = Arrow(TeXHead), p);
}

// Horizontal arrow: left node's east → right node's west
void arrowH(picture dest, picture left, picture right,
            real gap=0.2, pen p=currentpen) {
    pair a = point(left, E) + (gap, 0);
    pair b = point(right, W) + (-gap, 0);
    draw(dest, a -- b, arrow = Arrow(TeXHead), p);
}

// Branch: parent forks to left and right children
void arrowBranch(picture dest, picture parent,
                 picture leftChild, picture rightChild,
                 real gap=0.2, pen p=currentpen) {
    pair fork = point(parent, S);
    pair l = point(leftChild,  N) + (0, gap);
    pair r = point(rightChild, N) + (0, gap);
    pair mid = (fork.x, fork.y - 0.6);
    draw(dest, fork -- mid, p);
    draw(dest, mid -- l, arrow = Arrow(TeXHead), p);
    draw(dest, mid -- r, arrow = Arrow(TeXHead), p);
}

// Side node joins main from the left
void arrowJoinLeft(picture dest, picture side, picture main,
                   real gap=0.2, pen p=currentpen) {
    pair a = point(side, S) + (0, -gap);
    pair b = point(main,  W) + (-gap, 0);
    draw(dest, a -- (a.x, b.y) -- b, arrow = Arrow(TeXHead), p);
}

// Side node joins main from the right
void arrowJoinRight(picture dest, picture side, picture main,
                    real gap=0.2, pen p=currentpen) {
    pair a = point(side, S) + (0, -gap);
    pair b = point(main,  E) + (gap, 0);
    draw(dest, a -- (a.x, b.y) -- b, arrow = Arrow(TeXHead), p);
}

// Curved arrow (for crossing routes or long jumps)
void arrowCurve(picture dest, picture src, pair srcDir,
                picture tgt, pair tgtDir,
                real gap=0.2, pen p=currentpen) {
    pair a = point(src, srcDir) + gap * srcDir;
    pair b = point(tgt, tgtDir) + gap * tgtDir;
    draw(dest, a{right}..{right}b, arrow = Arrow(TeXHead), p);
}
```

**Why `Arrow(TeXHead)`?** It produces clean, small arrowheads that don't overwhelm the diagram. The default `Arrow` can be too large and intrusive.

### 4.2 Closure Variant (Config-Driven Style)

In config-driven diagrams, these helpers are often simplified as closures that capture `gap` and `arrowPen` from the configuration section:

```asy
pen arrowPen = rgb(0.30, 0.20, 0.10) + linewidth(0.9);
real gap = 0.25;

void arrowDown(picture dest, picture top, picture bot) {
    pair a = point(top, S) + (0, -gap);
    pair b = point(bot, N) + (0,  gap);
    draw(dest, a -- b, arrow = Arrow(TeXHead), arrowPen);
}
```

This is more concise for config-driven diagrams. Use whichever style fits your project.

### 4.3 Straight vs Curved Arrows

| Scenario | Use | Rationale |
|---------|-----|-----------|
| Simple top-down flow (parent → child directly below) | **Straight** | Clean, reads naturally as "next step" |
| Short horizontal link (sibling nodes at same y-level) | **Straight** or **subtle curve** | Direct relationship, no ambiguity |
| Cross-layer connection (node A at row 2 → node B at row 4, offset horizontally) | **Curve** | Avoids cutting through intermediate rows |
| Two parallel branches merging to a single node below | **Curved** (outward then inward) | Prevents crossing, visually separates incoming flows |
| One node branching to two side nodes | **Straight** with `arrowBranch` | Fork pattern, clean fan-out |
| Long-distance jump or feedback loop | **Curve** (wide arc) | Signals non-local relationship |

---

## 5. Grouping: Clusters, Layers, and Annotations

### 5.1 `pics_cluster()` — Background Cluster Box

Use `pics_cluster()` from `skillutils.asy` to draw a background rectangle enclosing a group of pictures. It auto-computes the bounding box from the pictures array, so you no longer need to manually calculate corner coordinates.

```asy
import skillutils;

// pics_cluster signature:
//   picture pics_cluster(picture[] pics, real padX, real padY,
//                        pen fillPen, pen borderPen)
//
// Returns a picture containing the background rectangle. Add it
// BEFORE the node pictures so it renders behind them.

picture[] pics = new picture[]{pRouter, pPod1, pPod2, pPod3};
picture cluster = pics_cluster(pics, 0.4, 0.3, clusterFill, clusterPen);
add(diagram, cluster);   // behind the nodes
add(diagram, pRouter);
add(diagram, pPod1);
add(diagram, pPod2);
add(diagram, pPod3);
```

For a dashed group box (logical/optional grouping), pass `nullpen` for fill:

```asy
picture dashedGroup = pics_cluster(pics, 0.4, 0.3, nullpen, clusterBorderPen + dashed);
```

### 5.2 `pics_bbox()` — Safe Bounding Box Computation

```asy
import skillutils;

// pics_bbox signature:
//   pair[] pics_bbox(picture[] pics)
//
// Returns a 2-element pair array: {bottomLeft, topRight}.

pair[] bb = pics_bbox(new picture[]{pA, pB, pC});
pair lowCorner = bb[0];  // overall bottom-left (min x, min y)
pair highCorner = bb[1];  // overall top-right  (max x, max y)
```

Uses `point(pic, SW)` / `point(pic, NE)` instead of `min()`/`max()` to avoid the PostScript coordinate trap on standalone sub-pictures. See §2 gotcha for details.

### 5.3 Annotations

#### Layer Labels

For complex systems, add layer annotations so readers know which architectural level they're viewing.

```asy
// Use point() to align annotations with node positions
label(diagram, "Web Canvas",  (xLeft - 2.2, point(pUser, N).y + 0.5), fontsize(8pt));
label(diagram, "Frontend",    (xLeft - 2.2, point(pUser, N).y + 0.1), fontsize(7pt) + gray(0.5));
```

#### Step Numbering

```asy
real ySteps = point(pResult, S).y - 2.0;

label(diagram, "1. Send",     (point(pUser, S).x, ySteps), fontsize(8pt));
label(diagram, "2. Auth",     (point(pGateway, S).x, ySteps), fontsize(8pt));

// Dashed line above steps
draw(diagram, (point(pUser, W).x - 2, ySteps + 0.5)
           -- (point(pResult, E).x + 2, ySteps + 0.5),
      gray(0.5) + dashed + linewidth(0.5));
```

#### Phase Dividers

```asy
// Midpoint between two node rows
real yDivider = (point(pPhase1, S).y + point(pPhase2, N).y) / 2;
draw(diagram, (xLeft - 1, yDivider) -- (xRight + 1, yDivider),
      gray(0.5) + linewidth(0.5) + dashed);
label(diagram, "Phase Label", (xLeft - 1.8, yDivider), fontsize(7pt) + gray(0.5));
```

---

## 6. Layout Patterns

### 6.1 Vertical Timeline (Top to Bottom)

For sequential workflows with parallel branches.

```asy
import skillutils;

// ==========================================
// VERTICAL WORKFLOW WITH PARALLEL BRANCHES
// ==========================================
real boxWidth = 3.0, boxHeight = 0.9, lineDy = 0.32, gap = 0.2;
real xMain = 0, xLeft = -2.8, xRight = 2.8, yTop = 0, dy = 1.6;

pen textPen = fontsize(9pt);

pen doneFill = rgb(0.90, 1.00, 0.95), doneBorder = rgb(0.20, 0.50, 0.40) + linewidth(1.2);
pen prepFill = rgb(1.00, 0.97, 0.90), prepBorder = rgb(0.50, 0.40, 0.20) + linewidth(1.2);
pen cookFill = rgb(1.00, 0.92, 0.85), cookBorder = rgb(0.60, 0.35, 0.15) + linewidth(1.2);
pen arrowPen = rgb(0.30, 0.20, 0.10) + linewidth(0.9);

// --- Create and position nodes ---
picture pStart = label_box_pic((xMain,  yTop),          boxWidth, boxHeight, lineDy, "Start", textPen, doneFill, doneBorder);
picture pPrep  = label_box_pic((xMain,  yTop - dy),     boxWidth, boxHeight, lineDy, new string[]{"Prep", "wash & measure"}, textPen, prepFill, prepBorder);
picture pCut   = label_box_pic((xLeft,  yTop - 2*dy),   boxWidth, boxHeight, lineDy, "Cut", textPen, prepFill, prepBorder);
picture pBeat  = label_box_pic((xRight, yTop - 2*dy),   boxWidth, boxHeight, lineDy, "Beat", textPen, prepFill, prepBorder);
picture pCook  = label_box_pic((xMain,  yTop - 3*dy),   boxWidth, boxHeight, lineDy, "Cook", textPen, cookFill, cookBorder);

// --- Assemble ---
picture diagram;
size(diagram, 10cm);

arrowDown(diagram, pStart, pPrep, gap, arrowPen);
arrowBranch(diagram, pPrep, pCut, pBeat, gap, arrowPen);
arrowJoinLeft(diagram, pCut, pCook, gap, arrowPen);
arrowJoinRight(diagram, pBeat, pCook, gap, arrowPen);

add(diagram, pStart);
add(diagram, pPrep);
add(diagram, pCut);
add(diagram, pBeat);
add(diagram, pCook);

pair[] bb = pics_bbox(new picture[]{pStart, pPrep, pCut, pBeat, pCook});
shipout(shift(-bb[0]) * diagram);
```

### 6.2 Horizontal Pipeline (Left to Right)

For sequential data flow: ingest → process → output.

```asy
import skillutils;

// ==========================================
// HORIZONTAL PIPELINE
// ==========================================
real boxWidth = 3.0, boxHeight = 0.9, lineDy = 0.32, gap = 0.2;
real yMain = 0, dx = 4.0, xStart = -6;

pen textPen = fontsize(9pt);

pen userFill = rgb(0.85, 0.92, 1.0),    userBorder = rgb(0.2, 0.4, 0.6) + linewidth(1.2);
pen gateFill = rgb(1.0, 0.95, 0.85),     gateBorder = rgb(0.5, 0.35, 0.15) + linewidth(1.2);
pen workFill = rgb(1.0, 0.95, 0.8),      workBorder = rgb(0.5, 0.4, 0.15) + linewidth(1.2);
pen resFill  = rgb(0.9, 1.0, 0.95),      resBorder  = rgb(0.2, 0.5, 0.4) + linewidth(1.2);
pen arrowPen = rgb(0.2, 0.2, 0.2) + linewidth(0.9);

// --- Create and position nodes ---
picture pUser    = label_box_pic((xStart,              yMain), boxWidth, boxHeight, lineDy, "User",    textPen, userFill, userBorder);
picture pGateway = label_box_pic((xStart + dx,         yMain), boxWidth, boxHeight, lineDy, "Gateway", textPen, gateFill, gateBorder);
picture pCore    = label_box_pic((xStart + 2*dx,       yMain), boxWidth, boxHeight, lineDy, "Core",    textPen, workFill, workBorder);
picture pResult  = label_box_pic((xStart + 3*dx,       yMain), boxWidth, boxHeight, lineDy, "Result",  textPen, resFill,  resBorder);

// --- Assemble ---
picture diagram;
size(diagram, 12cm);

arrowH(diagram, pUser,    pGateway, gap, arrowPen);
arrowH(diagram, pGateway, pCore,    gap, arrowPen);
arrowH(diagram, pCore,    pResult,  gap, arrowPen);

add(diagram, pUser);
add(diagram, pGateway);
add(diagram, pCore);
add(diagram, pResult);

pair[] bb = pics_bbox(new picture[]{pUser, pGateway, pCore, pResult});
shipout(shift(-bb[0]) * diagram);
```

### 6.3 Cluster with Internal Dispatch

For systems with a router dispatching to multiple workers inside a cluster. `pics_cluster()` auto-computes bounds — no manual coordinates.

```asy
import skillutils;

// ==========================================
// CLUSTER WITH DISPATCH
// ==========================================
real boxWidth = 3.0, boxHeight = 0.9, lineDy = 0.32, gap = 0.2;

pen textPen = fontsize(9pt);

pen routerFill  = rgb(0.85, 1.0, 0.9),  routerBorder = rgb(0.15, 0.45, 0.3) + linewidth(1.2);
pen workerFill  = rgb(1.0, 0.95, 0.8),  workerBorder = rgb(0.5, 0.4, 0.15) + linewidth(1.2);
pen clusterFill = rgb(0.96, 0.96, 1.0), clusterPen   = rgb(0.3, 0.3, 0.6) + linewidth(1.8);
pen dispatchPen = gray(0.5) + linewidth(0.7) + dashed;

picture pRouter = label_box_pic((5.5, -0.5), boxWidth, boxHeight, lineDy, new string[]{"Router", "Unique Instance"}, textPen, routerFill, routerBorder);
picture pPod1   = label_box_pic((3.0, -2.5), boxWidth, boxHeight, lineDy, new string[]{"Pod 1", "Agent + UI"}, textPen, workerFill, workerBorder);
picture pPod2   = label_box_pic((5.5, -2.5), boxWidth, boxHeight, lineDy, new string[]{"Pod 2", "Agent + UI"}, textPen, workerFill, workerBorder);
picture pPod3   = label_box_pic((8.0, -2.5), boxWidth, boxHeight, lineDy, new string[]{"Pod N", "Agent + UI"}, textPen, workerFill, workerBorder);

picture diagram;
size(diagram, 12cm);

picture[] clusterPics = new picture[]{pRouter, pPod1, pPod2, pPod3};
picture cluster = pics_cluster(clusterPics, 0.4, 0.3, clusterFill, clusterPen);
add(diagram, cluster);

pair routerSouth = point(pRouter, S) + (0, -gap);
for (picture pod : new picture[] {pPod1, pPod2, pPod3}) {
    pair podNorth = point(pod, N) + (0, gap);
    pair bend = (routerSouth.x, routerSouth.y - 0.8);
    draw(diagram, routerSouth -- bend -- (podNorth.x, bend.y) -- podNorth,
         dispatchPen);
}

add(diagram, pRouter);
add(diagram, pPod1);
add(diagram, pPod2);
add(diagram, pPod3);

shipout(diagram);
```

### 6.4 Side-by-Side Subplots (Different Coordinate Ranges)

Two subplots have different data ranges and need to be placed side by side.

```asy
// Left plot: 0..1 range
picture leftPlot;
draw(leftPlot, (0, 0) -- (1, 1), red);
for (int i = 0; i <= 5; ++i) {
    dot(leftPlot, (i / 5, i / 5));
}

// Right plot: 0..10 range
picture rightPlot;
draw(rightPlot, (0, 0) -- (10, 5), blue);
for (int i = 0; i <= 5; ++i) {
    dot(rightPlot, (i * 2, i));
}

picture combined;
size(combined, 10cm);
add(combined, shift(-2, 0) * leftPlot);
add(combined, shift(2, 0) * rightPlot);

shipout(combined);
```

**Key point:** `size(combined, 10cm)` must run first to establish the physical output size. `leftPlot` (0..1 range) and `rightPlot` (0..10 range) enter `combined`'s unified coordinate system. The right plot appears wider because its larger data range maps through the same physical scale.

### 6.5 Unified-Scale Layers

Several layers must stack with the exact same scale, e.g., markers on a map.

```asy
picture map;
size(map, 10cm);
draw(map, (0, 0) -- (10, 0) -- (10, 10) -- (0, 10) -- cycle);
for (int i = 0; i <= 10; ++i) {
    draw(map, (i, 0) -- (i, 10), gray(0.5));
    draw(map, (0, i) -- (10, i), gray(0.5));
}

// Marker component — drawn at origin, purely relative coordinates
picture markerComponent(pen p) {
    picture pic;
    fill(pic, scale(0.3) * unitcircle, p);
    return pic;
}

add(map, shift(0, 0)    * markerComponent(black));
add(map, shift(2, 3)    * markerComponent(red));
add(map, shift(5, 7)    * markerComponent(blue));
add(map, shift(8, 2)    * markerComponent(green));

shipout(map);
```

**Key point:** `markerComponent` contains no position information — position is controlled externally by `shift`, fully decoupling component definition from layout.

### 6.6 Overlay Elements (Compass, Legend, etc.)

Overlay a compass, scale bar, or legend on a large figure. With `add(picture, picture)`, everything scales through the final `picture`'s `size()`.

```asy
// Main map
picture map;
size(map, 10cm);
draw(map, (0, 0) -- (10, 0) -- (10, 10) -- (0, 10) -- cycle);

// Compass component — drawn at origin
picture compass() {
    picture pic;
    draw(pic, (0, 0) -- (0, 1.5), arrow = Arrow);
    label(pic, "N", (0, 1.8), N);
    draw(pic, (-0.3, 0) -- (0.3, 0));
    return pic;
}

// Merge
picture final;
size(final, 10cm);
add(final, map);
add(final, shift(12, 10) * compass());

shipout(final);
```

**Key distinction:** The compass's coordinates (0,0) to (0,1.8) map through `final`'s scale — about 1.8 cm. If you change to `size(final, 20cm)`, the compass scales proportionally. If you need strictly fixed physical size, use the frame approach: `add(dest, src.fit(), pos)`.

---

## 7. Color and Style

### 7.1 Color Coding System

Use color to distinguish entity roles at a glance.

| Role | Fill Color | Border Color | Example |
|------|-----------|-------------|---------|
| User / Client | `rgb(0.85,0.92,1.0)` | `rgb(0.2,0.4,0.6)` | Web browser, mobile app |
| Gateway / Proxy | `rgb(1.0,0.95,0.85)` | `rgb(0.5,0.35,0.15)` | Load balancer, API gateway |
| Router / Controller | `rgb(0.85,1.0,0.9)` | `rgb(0.15,0.45,0.3)` | Request router, scheduler |
| Worker / Pod | `rgb(1.0,0.95,0.8)` | `rgb(0.5,0.4,0.15)` | Compute nodes, containers |
| Storage / DB | `rgb(0.95,0.9,0.95)` | `rgb(0.4,0.3,0.5)` | Database, cache, object store |
| Result / Output | `rgb(0.9,1.0,0.95)` | `rgb(0.2,0.5,0.4)` | Response, output file |
| Cluster / Group | `rgb(0.96,0.96,1.0)` | `rgb(0.3,0.3,0.6)` | Bounding box for clusters |

```asy
pen userFill     = rgb(0.85, 0.92, 1.0);
pen userBorder   = rgb(0.2, 0.4, 0.6) + linewidth(1.2);
pen gatewayFill  = rgb(1.0, 0.95, 0.85);
pen gatewayBorder= rgb(0.5, 0.35, 0.15) + linewidth(1.2);
pen routerFill   = rgb(0.85, 1.0, 0.9);
pen routerBorder = rgb(0.15, 0.45, 0.3) + linewidth(1.2);
pen workerFill   = rgb(1.0, 0.95, 0.8);
pen workerBorder = rgb(0.5, 0.4, 0.15) + linewidth(1.2);
pen resultFill   = rgb(0.9, 1.0, 0.95);
pen resultBorder = rgb(0.2, 0.5, 0.4) + linewidth(1.2);
```

### 7.2 Style Guide Summary

| Element | Usage | Style |
|---------|-------|-------|
| Component box | Individual service/node/stage | `label_box_pic()` or `label_rounded_pic()` from `skillutils.asy` |
| Component placement | Positioning in parent picture | `label_box_pic((x, y), boxWidth, boxHeight, ...)` — position baked in |
| Arrow endpoints | Connecting nodes | `point(node, dir)` — no manual `boxHeight/2` math |
| Cluster box | Group of related components | `pics_cluster(pics, padX, padY, fillPen, borderPen)` — auto-computed |
| Dashed group | Logical/optional grouping | `pics_cluster(pics, padX, padY, nullpen, borderPen)` |
| Solid arrow | Primary data/control flow | `Arrow(TeXHead)`, 0.9bp |
| Dashed arrow | Internal dispatch, secondary flow | Gray, dashed, 0.7bp |
| Curved arrow | Avoid crossing other lines | Bezier curve with `{dir}..{dir}` |
| Layer label | Annotate architectural layer | Left-aligned gray text, y-aligned with `point()` |
| Step number | Bottom timeline annotation | Small gray text, evenly spaced |
| Node text | Name + one-line description | Name centered, description below in gray |

---

## 8. Complete Examples

### 8.1 System Architecture Diagram

A full system architecture diagram — layered components with clustering, dispatch, and step annotations.

```asy
import skillutils;

// ==========================================
// SYSTEM ARCHITECTURE: REQUEST FLOW
// ==========================================

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
real boxWidth         = 3.8;
real boxHeight         = 1.2;
real lineDy     = 0.36;
real gap        = 0.2;
real dx         = 4.5;
real yTop       = 3.5;
real yBot       = -3.5;
real xStart     = -11;

pen textPen = fontsize(9pt);

pen userColor    = rgb(0.90, 0.95, 1.00);  pen userBorder    = black + 1.2pt;
pen gatewayColor = rgb(1.00, 0.95, 0.85);  pen gatewayBorder = black + 1.2pt;
pen routerColor  = rgb(0.85, 1.00, 0.90);  pen routerBorder  = black + 1.2pt;
pen podColor     = rgb(1.00, 0.95, 0.75);  pen podBorder     = black + 1.2pt;
pen resultColor  = rgb(0.85, 1.00, 0.95);  pen resultBorder  = black + 1.2pt;
pen clusterFill  = rgb(0.96, 0.96, 0.99);
pen clusterPen   = rgb(0.3, 0.3, 0.6) + linewidth(1.8);
pen arrowPen     = rgb(0.2, 0.2, 0.2) + linewidth(0.9);
pen dispatchPen  = gray(0.5) + linewidth(0.7) + dashed;

// ------------------------------------------
// CREATE AND POSITION NODES
// ------------------------------------------
picture pUser    = label_box_pic((xStart,              yTop),        boxWidth, boxHeight, lineDy, new string[]{"User", "bizyair.cn Canvas"}, textPen, userColor, userBorder);
picture pSCX     = label_box_pic((xStart + dx,         yTop),        boxWidth, boxHeight, lineDy, new string[]{"SCX Gateway", "Auth, Quota, Billing"}, textPen, gatewayColor, gatewayBorder);
picture pCGR     = label_box_pic((xStart + 3*dx,       yTop - 1.5), boxWidth, boxHeight, lineDy, new string[]{"CGR Router", "Unique Instance"}, textPen, routerColor, routerBorder);
picture pPod1    = label_box_pic((xStart + 2.5*dx,     yBot),        boxWidth, boxHeight, lineDy, new string[]{"Pod 1", "ComfyAgent + ComfyUI"}, textPen, podColor, podBorder);
picture pPod2    = label_box_pic((xStart + 3.5*dx,     yBot),        boxWidth, boxHeight, lineDy, new string[]{"Pod 2", "ComfyAgent + ComfyUI"}, textPen, podColor, podBorder);
picture pPodN    = label_box_pic((xStart + 5.5*dx,     yBot),        boxWidth, boxHeight, lineDy, new string[]{"Pod N", "ComfyAgent + ComfyUI"}, textPen, podColor, podBorder);
picture pResult  = label_box_pic((xStart + 7.0*dx,     (yTop+yBot)/2), boxWidth, boxHeight, lineDy, new string[]{"Result", "Image / Video / Data"}, textPen, resultColor, resultBorder);

// ------------------------------------------
// ASSEMBLE DIAGRAM
// ------------------------------------------
picture diagram;
size(diagram, 20cm);

label(diagram, "BizyAir.cn Architecture: Request Flow", (0, 7.5), fontsize(16pt));

picture[] clusterPics = new picture[]{pCGR, pPod1, pPod2, pPodN};
picture cluster = pics_cluster(clusterPics, 0.4, 0.3, clusterFill, clusterPen);
add(diagram, cluster);

pair uEast  = point(pUser, E) + (gap, 0);
pair sWest  = point(pSCX,  W) + (-gap, 0);
draw(diagram, uEast -- sWest, arrow = Arrow(TeXHead), arrowPen);

pair sEast  = point(pSCX, E) + (gap, 0);
pair cWest  = point(pCGR, W) + (-gap, 0);
draw(diagram, sEast{E}..{E}cWest, arrow = Arrow(TeXHead), arrowPen);

pair cgrSouth = point(pCGR, S) + (0, -gap);
for (picture pod : new picture[] {pPod1, pPod2, pPodN}) {
    pair podNorth = point(pod, N) + (0, gap);
    pair bend = (cgrSouth.x, cgrSouth.y - 0.8);
    draw(diagram, cgrSouth -- bend -- (podNorth.x, bend.y) -- podNorth,
         dispatchPen);
}

pair podEast  = point(pPodN, E) + (gap, 0);
pair resWest  = point(pResult, W) + (-gap, 0);
draw(diagram, podEast{E}..{E}resWest,
     arrow = Arrow(TeXHead), arrowPen + dashed);

add(diagram, pUser);
add(diagram, pSCX);
add(diagram, pCGR);
add(diagram, pPod1);
add(diagram, pPod2);
add(diagram, pPodN);
add(diagram, pResult);

real ySteps = point(pResult, S).y - 2.5;
label(diagram, "1. Send",     (point(pUser,  S).x, ySteps), fontsize(8pt));
label(diagram, "2. Auth",     (point(pSCX,   S).x, ySteps), fontsize(8pt));
label(diagram, "3. Route",    (point(pCGR,   S).x, ySteps), fontsize(8pt));
label(diagram, "4. Dispatch", (point(pCGR,   S).x, ySteps - 0.5), fontsize(8pt));
label(diagram, "5. Parallel", (point(pPod2,  S).x, ySteps), fontsize(8pt));
label(diagram, "6. Merge",    (point(pResult,S).x, ySteps), fontsize(8pt));

real yAnnTopMain = yTop + 2.2;
real yAnnSubMain = yTop + 1.8;
label(diagram, "Web Canvas", (point(pUser,   S).x, yAnnTopMain), fontsize(8pt));
label(diagram, "Frontend",   (point(pUser,   S).x, yAnnSubMain), fontsize(7pt) + gray(0.5));
label(diagram, "Permission", (point(pSCX,    S).x, yAnnTopMain), fontsize(8pt));
label(diagram, "Gateway",    (point(pSCX,    S).x, yAnnSubMain), fontsize(7pt) + gray(0.5));
label(diagram, "Cluster",    (point(pCGR,    S).x, yAnnTopMain), fontsize(8pt));
label(diagram, "Router",     (point(pCGR,    S).x, yAnnSubMain), fontsize(7pt) + gray(0.5));
label(diagram, "Return",     (point(pResult, S).x, yAnnTopMain), fontsize(8pt));
label(diagram, "Output",     (point(pResult, S).x, yAnnSubMain), fontsize(7pt) + gray(0.5));

label(diagram, "FaaS: Function-as-a-Service / CGR: Comfy Grid Runtime / SCX: Service Control X",
      (0, yBot - 3.5), fontsize(9pt));

shipout(diagram);
```

### 8.2 Workflow Diagram: Tomato Scrambled Eggs

A workflow showing parallel preparation paths.

```asy
import skillutils;

// ==========================================
// WORKFLOW: TOMATO SCRAMBLED EGGS
// ==========================================

real boxWidth       = 3.0;
real boxHeight       = 0.9;
real lineDy   = 0.32;
real gap      = 0.25;
real nodeDy   = 1.6;

real xMain   = 0;
real xLeftB  = -2.8;
real xRightB =  2.8;
real y0      = 0;

pen textPen = fontsize(9pt);

pen prepFill    = rgb(1.00, 0.97, 0.90);
pen prepBorder  = rgb(0.50, 0.40, 0.20) + linewidth(1.2);
pen cookFill    = rgb(1.00, 0.92, 0.85);
pen cookBorder  = rgb(0.60, 0.35, 0.15) + linewidth(1.2);
pen doneFill    = rgb(0.90, 1.00, 0.95);
pen doneBorder  = rgb(0.20, 0.50, 0.40) + linewidth(1.2);
pen arrowPen    = rgb(0.30, 0.20, 0.10) + linewidth(0.9);

// ------------------------------------------
// ARROW HELPERS
// ------------------------------------------
void arrowDown(picture dest, picture top, picture bot) {
    pair a = point(top, S) + (0, -gap);
    pair b = point(bot, N) + (0,  gap);
    draw(dest, a -- b, arrow = Arrow(TeXHead), arrowPen);
}

void arrowBranch(picture dest, picture parent,
                 picture leftChild, picture rightChild) {
    pair p = point(parent, S);
    pair l = point(leftChild,  N) + (0, gap);
    pair r = point(rightChild, N) + (0, gap);
    pair fork = (p.x, p.y - 0.6);
    draw(dest, p -- fork, arrowPen);
    draw(dest, fork -- l, arrow = Arrow(TeXHead), arrowPen);
    draw(dest, fork -- r, arrow = Arrow(TeXHead), arrowPen);
}

void arrowJoinLeft(picture dest, picture side, picture main) {
    pair a = point(side, S) + (0, -gap);
    pair b = point(main,  W) + (-gap, 0);
    draw(dest, a -- (a.x, b.y) -- b, arrow = Arrow(TeXHead), arrowPen);
}

void arrowJoinRight(picture dest, picture side, picture main) {
    pair a = point(side, S) + (0, -gap);
    pair b = point(main,  E) + (gap, 0);
    draw(dest, a -- (a.x, b.y) -- b, arrow = Arrow(TeXHead), arrowPen);
}

// ------------------------------------------
// BUILD DIAGRAM
// ------------------------------------------
picture pStart  = label_box_pic((xMain,            y0),            boxWidth, boxHeight, lineDy, "Start", textPen, doneFill, doneBorder);
picture pPrep   = label_box_pic((xMain,            y0 - nodeDy),  boxWidth, boxHeight, lineDy, new string[]{"Prep", "wash \& measure"}, textPen, prepFill, prepBorder);
picture pCut    = label_box_pic((xLeftB,            y0 - 2*nodeDy), boxWidth, boxHeight, lineDy, "Cut Tomato", textPen, prepFill, prepBorder);
picture pBeat   = label_box_pic((xRightB,           y0 - 2*nodeDy), boxWidth, boxHeight, lineDy, "Beat Eggs", textPen, prepFill, prepBorder);
picture pHeat   = label_box_pic((xMain,             y0 - 3*nodeDy), boxWidth, boxHeight, lineDy, "Heat Oil", textPen, cookFill, cookBorder);
picture pFryE   = label_box_pic((xMain,             y0 - 4*nodeDy), boxWidth, boxHeight, lineDy, "Fry Eggs", textPen, cookFill, cookBorder);
picture pFryT   = label_box_pic((xMain,             y0 - 5*nodeDy), boxWidth, boxHeight, lineDy, "Fry Tomato", textPen, cookFill, cookBorder);
picture pMix    = label_box_pic((xMain,             y0 - 6*nodeDy), boxWidth, boxHeight, lineDy, "Mix", textPen, cookFill, cookBorder);
picture pSeason = label_box_pic((xMain,             y0 - 7*nodeDy), boxWidth, boxHeight, lineDy, "Season", textPen, cookFill, cookBorder);
picture pDone   = label_box_pic((xMain,             y0 - 8*nodeDy), boxWidth, boxHeight, lineDy, "Serve", textPen, doneFill, doneBorder);

// --- Assemble ---
picture diagram;

arrowDown(diagram, pStart, pPrep);
arrowBranch(diagram, pPrep, pCut, pBeat);
arrowJoinLeft(diagram, pCut, pHeat);
arrowJoinRight(diagram, pBeat, pHeat);
arrowDown(diagram, pHeat, pFryE);
arrowDown(diagram, pFryE, pFryT);
arrowDown(diagram, pFryT, pMix);
arrowDown(diagram, pMix, pSeason);
arrowDown(diagram, pSeason, pDone);

add(diagram, pStart);
add(diagram, pPrep);
add(diagram, pCut);
add(diagram, pBeat);
add(diagram, pHeat);
add(diagram, pFryE);
add(diagram, pFryT);
add(diagram, pMix);
add(diagram, pSeason);
add(diagram, pDone);

label(diagram, "\textbf{Workflow: Tomato Scrambled Eggs}",
      (xMain, y0 + 1.2), fontsize(14pt));

real xAnnotLeft  = xLeftB  - 2.2;
real xAnnotRight = xRightB + 2.2;

label(diagram, "Ingredients", (xAnnotLeft,  point(pPrep,   N).y - boxHeight/2), fontsize(8pt));
label(diagram, "Tomato",      (xAnnotLeft,  point(pCut,  S).y + 0.35), fontsize(8pt));
label(diagram, "Eggs",        (xAnnotLeft,  point(pBeat, S).y - 0.35), fontsize(8pt));
label(diagram, "Cooking",     (xAnnotLeft,  point(pHeat, S).y),        fontsize(8pt));

label(diagram, "2 tomatoes",  (xAnnotRight, point(pCut,   S).y + 0.35), fontsize(8pt));
label(diagram, "3 eggs",      (xAnnotRight, point(pBeat,  S).y - 0.35), fontsize(8pt));

real ySteps = y0 - 9.5*nodeDy;
label(diagram, "1. Prep",     (xMain - 3.5, ySteps), fontsize(8pt));
label(diagram, "2. Parallel", (xMain - 1.0, ySteps), fontsize(8pt));
label(diagram, "3. Heat",     (xMain + 1.0, ySteps), fontsize(8pt));
label(diagram, "4. Cook",     (xMain + 3.0, ySteps), fontsize(8pt));
label(diagram, "5. Serve",    (xMain + 5.0, ySteps), fontsize(8pt));

pair[] bb = pics_bbox(new picture[]{pStart, pPrep, pCut, pBeat, pHeat, pFryE, pFryT, pMix, pSeason, pDone});
shipout(shift(-bb[0]) * diagram);
```

---

## 9. Transforms and Parameterized Generation

### 9.1 Multiple Transforms on the Same Component

For symmetric patterns, rotational arrays, or different poses of the same object.

```asy
picture arrowComponent() {
    picture pic;
    draw(pic, (0, 0) -- (2, 0), arrow = Arrow);
    return pic;
}

picture scene;
size(scene, 10cm);

add(scene, arrowComponent());

picture arrow45 = rotate(45) * arrowComponent();
add(scene, shift(3, 0) * arrow45);

picture arrowMirror = reflect((0, 0), (0, 1)) * arrowComponent();
add(scene, shift(-3, 0) * arrowMirror);

shipout(scene);
```

### Available Transforms

| Transform | Description |
|-----------|-------------|
| `scale(s)` | Uniform scale |
| `scale(sx, sy)` | Non-uniform scale |
| `rotate(angle)` | Rotation in degrees |
| `reflect(p1, p2)` | Mirror along line `p1--p2` |
| `shift(x, y)` | Translation |
| `shift(pair)` | Vector translation |
| **Chained** | `scale(2) * rotate(45) * shift(3, 0) * pic` |

**Notes:**
- Transforms are **right-associative**: `scale(2) * rotate(45) * pic` = first rotate 45°, then scale 2×.
- Transforms **do not mutate** the original `picture`; they return a new one. You can safely transform the same base component in a loop.

### 9.2 Parameterized Batch Generation

Generate sets of similar shapes differing in color or size.

```asy
picture coloredSquare(pen p, real scaleFactor = 1) {
    picture pic;
    fill(pic, scale(scaleFactor) * unitsquare, p);
    draw(pic, scale(scaleFactor) * unitsquare, black);
    return pic;
}

pen[] paletteColors = {red, orange, yellow, green, cyan, blue, purple};

picture palette;
size(palette, 10cm);
for (int i = 0; i < paletteColors.length; ++i) {
    picture sq = coloredSquare(paletteColors[i], 1);
    add(palette, shift(i * 1.5, 0) * sq);
}

shipout(palette);
```

### 9.3 Multi-Step Drawing with Final Merge

A figure consisting of multiple independent parts, drawn separately and then assembled.

```asy
import graph;

// Part 1: Axes
picture axes;
draw(axes, (-2, 0) -- (2, 0), arrow = Arrow);
draw(axes, (0, -2) -- (0, 2), arrow = Arrow);

// Part 2: Function curve
picture curve;
draw(curve, graph(new real(real x) { return x ^ 2; }, -1.5, 1.5), red);

// Part 3: Labels
picture labels;
label(labels, "$y = x^2$", (1.5, 2), E);

// Merge
picture final;
size(final, 10cm);
add(final, axes);
add(final, curve);
add(final, labels);

shipout(final);
```

**Benefits:** Each part can be debugged independently. Any part can be commented out for isolated testing. Parts can be reused in different figures. All sub-pictures enter `final`'s coordinate system via `add(final, ...)` — no inconsistent scales.

---

## 10. Common Pitfalls

### Pitfall 1: Computing Arrow Endpoints Manually

Use `point(node, S)` instead of `center.y - boxHeight/2 - gap`. `point()` adapts automatically to any box size and transform.

### Pitfall 2: Overcrowding Nodes

Keep to name + one short line. Put details in side annotations or captions.

### Pitfall 3: Inconsistent Arrow Styles

Use solid for main flow, dashed for internal/subordinate flow.

### Pitfall 4: Missing Cluster Labels

Every bounding box should have a label indicating what the group represents.

### Pitfall 5: Arrow Crossings

Route around clusters or use curves. Avoid crossing solid arrows.

### Pitfall 6: Monochrome Diagrams

Use the color palette to distinguish roles. Color is faster to parse than text.

### Pitfall 7: No Layer Context

For complex systems, add layer annotations so readers know which architectural level they're viewing.

### Pitfall 8: Using `void` Node Functions Instead of `picture`-Returning Functions

A `void boxLabel(pair c, ...)` function draws directly on `currentpicture`, making it impossible to query boundary anchors or reposition the node later. Always use `picture label_box_pic(...)` so you can `point()` and `shift()`.

### Pitfall 9: Using `min()`/`max()` on Standalone Pictures

`min(pic)` and `max(pic)` return coordinates through the picture's user-to-PostScript transform. For a standalone sub-picture that has never been `add()`-ed to a sized parent, this transform is the identity in PostScript bp units (1/72 inch), NOT in user units. The resulting coordinates will be wildly offset. Use `point(pic, SW)` and `point(pic, NE)` instead, or the convenience function `pics_bbox(pics)` which returns `{bottomLeft, topRight}` using `point()` anchors.

### Pitfall 10: Failing to `size()` the Destination Before `add`

```asy
picture scene;
picture dotPic;
dot(dotPic, (0, 0));
add(scene, dotPic);
shipout(scene);  // WRONG — scene has no size, defaults to PS coordinates

// Correct
size(scene, 5cm);
add(scene, dotPic);
shipout(scene);
```

### Pitfall 11: Overusing `.fit()` and Breaking Coordinate Coherence

```asy
// Not recommended: intermediate frame breaks unified user-transform
add(scene, subPic.fit());

// Recommended: use picture directly to preserve user-coordinate consistency
add(scene, shift(pos) * subPic);
```

### Pitfall 12: Forgetting to Store the Transformed Picture

```asy
// Clearer: explicit instantiation
for (int i = 0; i < 3; ++i) {
    picture instance = shift(i, 0) * base;
    add(scene, instance);
}
```

> `shift(i, 0) * base` always returns a new `picture`; explicit variable binding improves readability.

---

## Quick Reference Card

| Need | Pattern |
|------|---------|
| Define component | `picture func(params) { picture pic; ...; return pic; }` |
| Reuse component | `picture inst = func(args); add(scene, shift(pos) * inst);` |
| Labeled box (skillutils) | `import skillutils; picture p = label_box_pic(pos, w, h, dy, text, textPen, fill, border);` |
| Rounded box (skillutils) | `import skillutils; picture p = label_rounded_pic(pos, w, h, r, dy, text, textPen, fill, border);` |
| Rounded rect path | `path rbox = roundbox(bl, tr, r);` |
| Transform component | `rotate(45) * scale(2) * pic` |
| Subplots side by side | `add(dest, shift(pos) * src)` |
| Unified coordinates | `add(dest, src)` (no fit) |
| Query boundary anchor | `point(pic, dir)` where `dir` is `N`/`S`/`E`/`W`/`NE`/etc. |
| Query bbox (safe) | `pics_bbox(pics)` from skillutils — returns `{bottomLeft, topRight}` |
| Cluster background | `pics_cluster(pics, padX, padY, fill, border)` from skillutils |
| Connect nodes vertically | `arrowDown(dest, top, bot, gap, pen)` helper |
| Connect nodes horizontally | `arrowH(dest, left, right, gap, pen)` helper |
| Branch to two children | `arrowBranch(dest, parent, leftChild, rightChild, gap, pen)` helper |
| Curved arrow | `arrowCurve(dest, src, srcDir, tgt, tgtDir, gap, pen)` helper |
| Control output | `size(pic, 5cm); shipout(pic);` |
| Center and ship | `pair[] bb = pics_bbox(pics); shipout(shift(-bb[0]) * diagram);` |
