# Scientific Graphs with Asymptote

This document covers scientific plotting using Asymptote's `graph` module and the `colormap` module for color mapping in data visualization.

---

## 1. The `graph` Module

```asy
import graph;
```

The `graph` module provides comprehensive tools for 2D function plotting, data visualization, and coordinate axes. It is the standard tool for scientific graphs in Asymptote.

---

## 2. Basic Function Plotting

### 2.1 Plotting y = f(x)

```asy
import graph;

// Set canvas size
size(200, 150, IgnoreAspect);

// Plot sin(x) from 0 to 2*pi
draw(graph(sin, 0, 2pi));

// Axes
xaxis("$x$", BottomTop, LeftTicks);
yaxis("$y$", LeftRight, RightTicks);
```

### 2.2 The `graph()` Function

```asy
guide graph(real f(real), real a, real b, int n=ngraph,
            interpolate join=operator --);
```

| Parameter | Description |
|-----------|-------------|
| `f` | Function to plot: `real f(real)` |
| `a`, `b` | Domain bounds |
| `n` | Number of sample points (default: `ngraph` ≈ 100) |
| `join` | Interpolation method between points |

**Interpolation modes:**

```asy
// Linear segments (default)
draw(graph(sin, 0, 10), operator --);

// Cubic spline
draw(graph(sin, 0, 10), operator ..);

// Hermite spline (smooth with boundary conditions)
import graph_splinetype;
draw(graph(sin, 0, 10), Hermite);

// Monotonic spline (preserves monotonicity)
draw(graph(sin, 0, 10), monotonic);
```

### 2.3 Parametric Plots

```asy
// Parametric: x(t), y(t)
draw(graph(cos, sin, 0, 2pi));  // Circle

// Or using a pair function
pair parametric(real t) { return (cos(t), sin(t)); }
draw(graph(parametric, 0, 2pi));
```

### 2.4 Polar Plots

```asy
// r = f(theta)
draw(polargraph(sin(2theta), 0, 2pi));

// From data arrays
real[] r = {1, 2, 1.5, 3, 2};
real[] theta = {0, 45, 90, 135, 180};
draw(polargraph(r, theta));
```

---

## 3. Plotting from Data

### 3.1 Arrays of Points

```asy
// Using real arrays for x and y
real[] x = {1, 2, 3, 4, 5};
real[] y = {1, 4, 9, 16, 25};
draw(graph(x, y));

// Using pair array
pair[] points = {(1,1), (2,4), (3,9), (4,16), (5,25)};
draw(graph(points));
```

### 3.2 Reading from Files

```asy
// Read data from file
file fin = input("data.txt");
real[] x, y;
while (!eof(fin)) {
    x.push(fin);
    y.push(fin);
}
draw(graph(x, y), blue + linewidth(1));
```

### 3.3 Conditional Graphing (Discontinuous Functions)

```asy
// Skip points where function is undefined
bool3 cond(real x) {
    if (x == 0) return false;  // Skip x=0
    return true;
}

guide[] g = graph(f, -5, 5, cond=cond);
for (guide gi : g) draw(gi);
```

`bool3` values: `true` = include point, `false` = skip point, default = start new guide segment.

---

## 4. Axes and Ticks

### 4.1 Drawing Axes

```asy
// Both axes at once
axes("$x$", "$y$", extend=true);

// Individual axes with full control
xaxis("$x$", Bottom, LeftTicks);
yaxis("$y$", Left, RightTicks);
```

**Axis position presets:**

```asy
xaxis(Bottom);        // Bottom edge
xaxis(Top);           // Top edge
xaxis(BottomTop);     // Both edges
xaxis(YZero);         // Along y=0
xaxis(YEquals(2));    // Along y=2

yaxis(Left);          // Left edge
yaxis(Right);         // Right edge
yaxis(LeftRight);     // Both edges
yaxis(XZero);         // Along x=0
yaxis(XEquals(3));    // Along x=3
```

### 4.2 Tick Systems

```asy
// Automatic ticks
xaxis(LeftTicks);
yaxis(RightTicks);

// No ticks
xaxis(NoTicks);

// Custom ticks
xaxis(Ticks(new real[] {0, 1, 2, 3, 4, 5}));

// Omit specific ticks
xaxis(Ticks(OmitTick(0)));              // Remove tick at 0
xaxis(Ticks(OmitTickInterval(2, 4)));   // Remove ticks in [2,4]

// Custom format
xaxis(Ticks(Format("$%.2f$")));
```

### 4.3 Logarithmic Scales

```asy
// Log scale on one or both axes
scale(Log, Linear);     // x: log, y: linear
scale(Log, Log);        // log-log plot
scale(Linear, Log);     // x: linear, y: log

// Use log-specific tick formatting
xaxis(Ticks(NoZeroFormat));  // Don't show 0 on log axis
yaxis(LeftTicks(DefaultLogFormat));
```

### 4.4 Setting Limits and Cropping

```asy
// Set axis limits
xlimits(0, 10);
ylimits(-1, 1);
limits((0, -1), (10, 1));  // Set both at once

// Crop to limits (hide data outside)
limits((0, -1), (10, 1), Crop);
```

---

## 5. Plot Customization

### 5.1 Multiple Curves

```asy
// Plot multiple functions with different styles
pen[] pens = {red, blue, green};
string[] labels = {"$\sin x$", "$\sin 2x$", "$\sin 3x$"};

for (int i = 0; i < 3; ++i) {
    real f(real x) { return sin((i+1)*x); }
    draw(graph(f, 0, 2pi), pens[i], labels[i]);
}

xaxis("$x$", Bottom, LeftTicks);
yaxis("$y$", Left, RightTicks);
```

### 5.2 Markers

```asy
// Predefined markers
marker[] markers = {
    marker(scale(2)*unitcircle),      // Circle
    marker(polygon(3)),                // Triangle
    marker(polygon(4)),                // Square
    marker(cross(4)),                  // Cross
    marker(diamond),                   // Diamond
    marker(plus)                       // Plus
};

// Apply to data points
real[] x = {1, 2, 3, 4, 5};
real[] y = {1, 2, 1.5, 3, 2};
draw(graph(x, y), marker(markers[0]));

// Mark nodes (Bezier control points)
draw(graph(sin, 0, 10), marker(markuniform(centered=false, n=10)));
```

### 5.3 Legends

```asy
// Add legend label to draw command
draw(graph(sin, 0, 2pi), red, " $\sin x$");
draw(graph(cos, 0, 2pi), blue, " $\cos x$");

// Position legend
attach(legend(), N, 10S);
```

### 5.4 Filling Under Curves

```asy
// Fill area under curve
path p = graph(sin, 0, pi)--(pi,0)--(0,0)--cycle;
fill(p, lightyellow);
draw(graph(sin, 0, pi), blue);
```

---

## 6. Error Bars

```asy
// Single error bar
errorbar(pair z, pair dp, pair dm, pen p=currentpen, real size=5);

// Array error bars
real[] x = {1, 2, 3, 4, 5};
real[] y = {2, 4, 3, 5, 4};
real[] dy = {0.2, 0.3, 0.1, 0.4, 0.2};  // Symmetric errors
real[] dyp = {0.3, 0.4, 0.2, 0.5, 0.3};  // Positive errors
real[] dyn = {0.1, 0.2, 0.05, 0.3, 0.1}; // Negative errors

errorbars(x, y, dy);          // Symmetric
errorbars(x, y, dyp, dyn);    // Asymmetric
```

---

## 7. Vector Fields

```asy
// Vector field along a path
path direction(real t) { return (0,1)--(1,0); }
picture field = vectorfield(direction, (0,0)--(10,0), 20);
add(field);

// Vector field over a rectangle
path vec(pair z) { return (0,0)--(z.y, -z.x); }  // Rotation field
picture field = vectorfield(vec, (0,0), (10,10), 10, 10);
add(field);
```

---

## 8. Secondary Axes

```asy
// Create a secondary y-axis
picture primary;
// ... draw primary plot ...

picture secondaryY = secondaryY(primary, new void(picture pic) {
    yaxis(pic, Right, RightTicks);
    draw(pic, graph(f2, a, b), red);
});

add(secondaryY);
```

---

## 9. The `colormap` Module

```asy
import colormap;
```

The `colormap` module provides ~70 colormaps ported from matplotlib 3.0.2. It is self-contained and integrates with the standard `draw()` mechanism via `pen[]` arrays.

### 9.1 Using Colormaps

```asy
import colormap;

// Get a palette as pen array
pen[] colors = viridis.palette(256);  // 256 colors

// Use in drawing
for (int i = 0; i < 100; ++i) {
    real t = i / 100.0;
    draw((i, 0)--(i, sin(i)), colors[floor(t * 255)]);
}
```

### 9.2 Colormap Types

**Segmented palettes** (with gamma control):

```asy
pen[] palette = viridis.palette(256, gamma=1.0);
pen[] palette = plasma.palette(256, gamma=1.2);
pen[] palette = inferno.palette(256);
pen[] palette = magma.palette(256);
pen[] palette = cividis.palette(256);
pen[] palette = jet.palette(256);
pen[] palette = hot.palette(256);
pen[] palette = coolwarm.palette(256);
```

**List palettes** (fixed number of colors):

```asy
pen[] palette = tab10.palette();   // 10 categorical colors
pen[] palette = tab20.palette();   // 20 categorical colors
pen[] palette = Set1.palette();    // 9 categorical colors
pen[] palette = Blues.palette();   // Blue gradient
pen[] palette = Reds.palette();    // Red gradient
```

### 9.3 Recommended Colormaps by Use Case

| Category | Key Colormaps | Use Case |
|----------|--------------|----------|
| Perceptually uniform | `viridis`, `plasma`, `inferno`, `magma`, `cividis` | Heatmaps, continuous data |
| Diverging | `RdBu`, `PuOr`, `PiYG`, `seismic`, `bwr`, `brg` | Positive/negative data |
| Sequential | `Blues`, `Greens`, `Reds`, `Oranges`, `Purples`, `YlOrRd` | Monotonic data |
| Qualitative | `tab10`, `tab20`, `Set1`, `Set2`, `Set3`, `Paired` | Categorical data |
| Classic | `jet`, `hot`, `gray`, `bone`, `copper` | Legacy/compat |

### 9.4 Colormap Example: Heatmap

```asy
import graph;
import colormap;

// Configuration
int nx = 50;
int ny = 50;
pen[] colors = viridis.palette(256);

// Generate data
real f(pair z) { return sin(z.x) * cos(z.y); }

// Draw heatmap cells
for (int i = 0; i < nx; ++i) {
    for (int j = 0; j < ny; ++j) {
        real x0 = 2pi * i / nx;
        real y0 = 2pi * j / ny;
        real x1 = 2pi * (i + 1) / nx;
        real y1 = 2pi * (j + 1) / ny;

        real value = f((x0 + x1) / 2, (y0 + y1) / 2);
        int colorIdx = floor((value + 1) / 2 * 255);
        colorIdx = max(0, min(255, colorIdx));

        fill((x0, y0)--(x1, y0)--(x1, y1)--(x0, y1)--cycle, colors[colorIdx]);
    }
}

// Axes
xaxis("$x$", Bottom, LeftTicks);
yaxis("$y$", Left, RightTicks);
```

---

## 10. Complete Example: Multi-Curve Scientific Plot

```asy
import graph;
import colormap;

// ==========================================
// CONFIGURATION
// ==========================================
size(300, 200, IgnoreAspect);
pen[] linePens = {red, blue, green, orange};
string[] labels = {
    " $f(x) = \sin x$",
    " $f(x) = \sin 2x$",
    " $f(x) = \sin 3x$",
    " $f(x) = \sin 4x$"
};

// ==========================================
// PLOTTING
// ==========================================
for (int i = 0; i < 4; ++i) {
    real f(real x) { return sin((i + 1) * x); }
    draw(graph(f, 0, 2pi), linePens[i] + linewidth(1), labels[i]);
}

// ==========================================
// AXES
// ==========================================
xaxis("$x$", Bottom, Ticks(Label("$%.1f$"), Step=pi/2, step=pi/4));
yaxis("$y$", Left, RightTicks);

// ==========================================
// LEGEND
// ==========================================
attach(legend(), NE, 10SW);
```

---

## 11. Common Patterns Summary

| Task | Pattern |
|------|---------|
| Plot y = f(x) | `draw(graph(f, a, b))` |
| Parametric plot | `draw(graph(x, y, a, b))` |
| Data plot | `draw(graph(xArray, yArray))` |
| Log scale | `scale(Log, Linear)` |
| Custom ticks | `Ticks(Format("$%.2f$"), Step=1)` |
| Error bars | `errorbars(x, y, dy)` |
| Multiple curves | Loop with `draw(graph(...), pen, label)` |
| Fill under curve | Construct closed path, `fill()` |
| Colormap | `viridis.palette(256)` |

---

## 12. Important Notes

1. **Interpolation:** The default `operator --` creates linear segments. Use `operator ..` or `Hermite` for smooth curves.

2. **Axis placement:** By default, axes are drawn at `YZero` and `XZero`. Use `Bottom`/`Top`/`Left`/`Right` for edge axes.

3. **`Crop` vs `NoCrop`:** `limits(..., Crop)` clips objects outside the bounds. Without `Crop`, all data is visible.

4. **`graph()` returns `guide`:** This means resolution is deferred until draw time — efficient for complex plots.

5. **`bool3` for discontinuities:** Use a `bool3 cond(real)` function to handle discontinuities (undefined points, piecewise functions).

6. **File I/O:** `graph()` does not read files directly. Use Asymptote's `input()` to load data into arrays first.

7. **Colormap independence:** `colormap.asy` is self-contained. It produces `pen[]` arrays usable with any drawing command.
