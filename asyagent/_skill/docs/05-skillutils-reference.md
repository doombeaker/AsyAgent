# Skillutils API Reference

API reference for the `skillutils` library. All functions are accessed via `import skillutils;`. Because rendering happens on the asyagent server, `skillutils.asy` is provided server-side — bundled with the skill and placed on the server's Asymptote module path automatically. No client-side installation is needed; `import skillutils;` simply works.

---

## label_box_pic

Creates a labeled, filled, bordered box as a `picture`, shifted to `boxPosition`. This is the fundamental building block for modular diagram nodes.

### Signatures

```asy
picture label_box_pic(pair boxPosition, real boxWidth, real boxHeight,
                      real lineDy, string[] lines,
                      pen label_text, pen fillPen, pen borderPen)

picture label_box_pic(pair boxPosition, real boxWidth, real boxHeight,
                      real lineDy, string text,
                      pen label_text, pen fillPen, pen borderPen)
```

The single-string overload wraps `text` into a one-element `string[]` and delegates to the array version.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `boxPosition` | `pair` | Shift vector — box center lands at this point in the parent coordinate system |
| `boxWidth` | `real` | Total width of the box (user units) |
| `boxHeight` | `real` | Total height of the box (user units) |
| `lineDy` | `real` | Vertical spacing between consecutive text lines |
| `lines` | `string[]` | Array of label strings, drawn top-to-bottom |
| `label_text` | `pen` | Pen for label rendering (e.g. `fontsize(9pt)`, `fontsize(8pt) + rgb(0.5,0.5,0.5)`) |
| `fillPen` | `pen` | Fill pen for the box interior |
| `borderPen` | `pen` | Stroke pen for the box outline |

### Usage

```asy
import skillutils;

pen textPen = fontsize(9pt);

// Single-line node
picture pStart = label_box_pic((0, 2), 3.0, 0.9, 0.32, "Start", textPen, startFill, startBorder);

// Multi-line node
picture pProc = label_box_pic((3, 0), 3.0, 0.9, 0.32, new string[]{"Process", "compute"}, textPen, procFill, procBorder);

add(diagram, pStart);
add(diagram, pProc);
pair anchor = point(pStart, S);  // query boundary — no boxHeight/2 math needed
```

---

## roundbox

Creates a rounded rectangle path. Used internally by `label_rounded_pic()`, but also available directly for custom shapes.

### Signature

```asy
path roundbox(pair bottomLeft, pair topRight, real radius)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `bottomLeft` | `pair` | Bottom-left corner of the bounding rectangle |
| `topRight` | `pair` | Top-right corner of the bounding rectangle |
| `radius` | `real` | Corner radius (clamped to half the smaller dimension) |

### Usage

```asy
import skillutils;

path rbox = roundbox((0, 0), (4, 2), 0.3);
filldraw(rbox, lightblue, blue);
```

---

## label_rounded_pic

Creates a labeled, filled, bordered rounded box as a `picture`, shifted to `boxPosition`. Same interface as `label_box_pic()` with an additional `radius` parameter.

### Signatures

```asy
picture label_rounded_pic(pair boxPosition, real boxWidth, real boxHeight,
                          real radius, real lineDy, string[] lines,
                          pen label_text, pen fillPen, pen borderPen)

picture label_rounded_pic(pair boxPosition, real boxWidth, real boxHeight,
                          real radius, real lineDy, string text,
                          pen label_text, pen fillPen, pen borderPen)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `boxPosition` | `pair` | Shift vector — box center lands at this point in the parent coordinate system |
| `boxWidth` | `real` | Total width of the box (user units) |
| `boxHeight` | `real` | Total height of the box (user units) |
| `radius` | `real` | Corner radius (clamped to half the smaller dimension) |
| `lineDy` | `real` | Vertical spacing between consecutive text lines |
| `lines` | `string[]` | Array of label strings, drawn top-to-bottom |
| `label_text` | `pen` | Pen for label rendering (e.g. `fontsize(9pt)`) |
| `fillPen` | `pen` | Fill pen for the box interior |
| `borderPen` | `pen` | Stroke pen for the box outline |

### Usage

```asy
import skillutils;

pen textPen = fontsize(9pt);

// Single-line rounded card
picture card1 = label_rounded_pic((0, 2), 3.0, 0.9, 0.2, 0.32, "Service A", textPen, svcFill, svcBorder);

// Multi-line rounded card
picture card2 = label_rounded_pic((0, -1), 3.0, 0.9, 0.2, 0.32,
                                  new string[]{"Service B", "v2.1"}, textPen, svcFill, svcBorder);

add(diagram, card1);
add(diagram, card2);
pair anchor = point(card1, S);  // boundary query works the same as label_box_pic
```

---

## pics_bbox

Computes the axis-aligned bounding box enclosing all given pictures. Uses `point(pic, SW)` / `point(pic, NE)` instead of `min()` / `max()` to avoid the PostScript coordinate trap on standalone sub-pictures.

### Signature

```asy
pair[] pics_bbox(picture[] pics)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `pics` | `picture[]` | Array of pictures whose combined extent is needed |

### Returns

A 2-element `pair[]` array: `{bottomLeft, topRight}`.

### Why not `min()` / `max()`?

`min(pic)` / `max(pic)` return coordinates through the picture's `user → PS` transform. For a standalone sub-picture that has never been `add()`-ed to a sized parent picture, this transform is the identity in PostScript bp units (1/72 inch), **not** user units. The resulting coordinates appear wildly offset.

`point(pic, dir)` does not have this problem — it computes boundary anchors from the picture's drawn content and stored transforms, returning correct user-coordinate values even for standalone pictures.

### Usage

```asy
import skillutils;

pair[] bb = pics_bbox(new picture[]{pA, pB, pC});
pair bottomLeft = bb[0];   // (min x, min y)
pair topRight  = bb[1];    // (max x, max y)
```

---

## pics_cluster

Draws a fill+border rectangle enclosing all given pictures with padding, returned as a `picture`. Add it **before** the node pictures so it renders behind them.

### Signature

```asy
picture pics_cluster(picture[] pics, real padX, real padY,
                     pen fillPen, pen borderPen)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `pics` | `picture[]` | Array of pictures to enclose |
| `padX` | `real` | Horizontal padding between nodes' bbox and the box edge |
| `padY` | `real` | Vertical padding between nodes' bbox and the box edge |
| `fillPen` | `pen` | Interior fill pen (`nullpen` for no fill) |
| `borderPen` | `pen` | Outline stroke pen (`nullpen` for no border) |

### Usage

```asy
import skillutils;

picture bg = pics_cluster(new picture[]{pRouter, pPod1, pPod2}, 0.4, 0.3, clusterFill, clusterPen);

add(diagram, bg);     // behind
add(diagram, pRouter);  // in front
add(diagram, pPod1);
add(diagram, pPod2);

// Optional: cluster label positioned below the box
label(diagram, "Cluster Name", (point(bg, S).x, point(bg, S).y + 0.5), clusterLabelPen);
```
