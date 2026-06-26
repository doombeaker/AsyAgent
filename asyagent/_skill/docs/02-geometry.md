# Geometry with Asymptote

This document covers 2D geometric constructions using Asymptote's `geometry` module. The `geometry` module (by Philippe Ivaldi) provides rich structures for points, lines, circles, conics, and triangles with full support for intersections, tangents, and derived objects.

---

## 1. Module Overview

```asy
import geometry;
```

The `geometry` module replaces raw `pair` coordinates with semantic geometric objects:

- **`point`** — Enhanced coordinate with embedded coordinate system and mass support
- **`line`** / **`segment`** — Infinite lines and finite segments with equation coefficients
- **`circle`** / **`ellipse`** / **`parabola`** / **`hyperbola`** — Conic sections
- **`triangle`** — Rich triangle structure with 30+ derived objects (centers, circles, associated triangles)
- **`arc`** — Oriented arcs on ellipses

**Key design principle:** Geometry objects cast to `path` for drawing. You can `draw()` them directly, or cast to `path`/`pair` when needed.

---

## 2. Points and Coordinate Systems

### 2.1 Creating Points

```asy
import geometry;

// Basic point in current coordinate system
point origin = point((0, 0));
point pointA = point((3, 4));

// Point in a custom coordinate system
coordsys customCS = cartesiansystem((1, 2), (1, 0), (0, 1));
point customPoint = point(customCS, (0, 0));  // At (1, 2) in default coords

// Cast to pair for raw coordinates
pair raw = (pair)pointA;  // or use locate(pointA)
```

### 2.2 Point Operations

```asy
// Distance and angle
real dist = abs(pointA);           // Distance from origin
real ang = degrees(pointA);        // Angle in degrees

// Dot product and collinearity
real dotProd = dot(pointA, pointB);
bool col = collinear(vectorA, vectorB);

// Unit vector
point unitVec = unit(pointA);

// Between-ness check
bool isBetween = between(pointA, origin, pointB);
```

---

## 3. Lines and Segments

### 3.1 Creating Lines

```asy
// Through two points
line lineAB = line(pointA, pointB);

// Through one point with angle (degrees)
line lineAtAngle = line(45, pointA);

// From slope and y-intercept
line slopeLine = line(1.0, 2.0);  // y = x + 2

// Vertical / horizontal
line vert = vline();
line horiz = hline();

// X-axis and Y-axis
line xAxis = Ox();
line yAxis = Oy();
```

### 3.2 Line Operations

```asy
// Parallel and perpendicular
line parallelLine = parallel(pointC, lineAB);
line perpLine = perpendicular(pointC, lineAB);

// Intersection
point intersection = intersectionpoint(lineAB, lineCD);

// Angle between lines
real angleDeg = degrees(lineAB, lineCD);
real sharpAngle = sharpdegrees(lineAB, lineCD);  // Always acute

// Distance from point to line
real dist = distance(pointC, lineAB);

// Reflection and projection
transform reflectLine = reflect(lineAB);
transform projLine = projection(lineAB);

// Bisectors
line angleBisector = bisector(lineAB, lineCD);
segment perpBisector = bisector(segmentAB);  // Perpendicular bisector

// Check relationships
bool areParallel = parallel(lineAB, lineCD);
bool arePerp = perpendicular(lineAB, lineCD);
bool concurrent = concurrent(new line[] {lineAB, lineCD, lineEF});
```

### 3.3 Segments

```asy
// Create segment
segment segAB = segment(pointA, pointB);

// Properties
real segLength = length(segAB);
point mid = midpoint(segAB);

// Cast to path
path segPath = (path)segAB;  // Equivalent to pointA--pointB
```

---

## 4. Circles

### 4.1 Creating Circles

```asy
// By center and radius
circle centerRadius = circle(pointO, 3.0);

// By diameter (two points)
circle diamCircle = circle(pointA, pointB);

// By three points (circumcircle)
circle circum = circle(pointA, pointB, pointC);
circle circum2 = circumcircle(pointA, pointB, pointC);

// Circumcenter and incenter
point circumCenter = circumcenter(pointA, pointB, pointC);
point inCenter = incenter(pointA, pointB, pointC);
real inRadius = inradius(pointA, pointB, pointC);

// Incircle and excircles
circle incircle = incircle(pointA, pointB, pointC);
circle excircle = excircle(pointA, pointB, pointC);
point exCenter = excenter(pointA, pointB, pointC);
```

### 4.2 Circle Operations

```asy
// Tangents from external point
line[] tangentLines = tangents(circleO, pointP);

// Point on circle (parameterized)
point topPoint = point(circleO, angabscissa(90));
point relPoint = relpoint(circleO, 0.25);  // 25% around circle

// Power of a point
real power = pointP ^ circleO;  // Using ^ operator

// Check if point is on circle
bool onCircle = (pointP @ circleO);  // Using @ operator

// Intersections
point[] lineCircleIntersections = intersectionpoints(lineAB, circleO);
point[] circleCircleIntersections = intersectionpoints(circleO1, circleO2);
```

### 4.3 Drawing Circles

```asy
// Direct draw
draw(circleO, blue + linewidth(1));

// Fill and draw
filldraw(circleO, lightyellow, black);

// With label
draw(circleO, "$\mathcal{C}$");
```

---

## 5. Ellipses, Parabolas, and Hyperbolas

### 5.1 Ellipses

```asy
// By foci and semimajor axis
ellipse el = ellipse(focus1, focus2, 5.0);

// By center, semiaxes, and rotation angle
ellipse el2 = ellipse(center, 4.0, 2.0, 30);  // 30-degree rotation

// By five points
ellipse el3 = ellipse(point1, point2, point3, point4, point5);

// Drawing
draw(el, red);

// Check inside
bool inside = inside(el, pointP);

// Arc of ellipse
arc elArc = arc(el, 0, 90);  // From 0° to 90°
draw(elArc, dashed);
```

### 5.2 Parabolas

```asy
// By focus and directrix
parabola par = parabola(focusPoint, directrixLine);

// By focus and vertex
parabola par2 = parabola(focusPoint, vertexPoint);

// Drawing
draw(par, green);

// Tangent
line tangentLine = tangent(par, abscissaParam);
line[] tangentsFromPoint = tangents(par, externalPoint);
```

### 5.3 Hyperbolas

```asy
// By foci and semimajor axis
hyperbola hyp = hyperbola(focus1, focus2, 3.0);

// By center and semiaxes
hyperbola hyp2 = hyperbola(center, 4.0, 3.0, 0);  // No rotation

// Conjugate hyperbola
hyperbola conjHyp = conj(hyp);

// Drawing
draw(hyp, purple);
```

---

## 6. Arcs

```asy
// Arc on ellipse
circle circleO = circle((0, 0), 3);
arc semiCircle = arc(circleO, 0, 180);
draw(semiCircle, red + linewidth(2));

// Arc through three points
arc arcAMB = arccircle(pointA, pointM, pointB);

// Arc subtending an angle
arc arcAB = arcsubtended(pointA, pointB, 60);  // 60° arc

// Complementary and reverse
arc complement = complementary(arcAB);
arc reversed = reverse(arcAB);

// Arc properties
real arcAngle = degrees(arcAB);
real arcLen = arclength(arcAB);
```

---

## 7. Triangles — The Powerhouse

The `triangle` struct is the most feature-rich object in the geometry module.

### 7.1 Creating Triangles

```asy
// By three vertices
triangle tri = triangle(pointA, pointB, pointC);

// By three lines
triangle tri2 = triangle(line1, line2, line3);

// By angle and two sides
triangle tri3 = triangleAbc(60, 4, 5);  // angle=60°, sides b=4, c=5

// By three side lengths (SSS)
triangle tri4 = triangleabc(3, 4, 5);
```

### 7.2 Triangle Centers

```asy
// Classical centers
point orthoCenter = orthocenter(tri);
point centroid = centroid(tri);
point circumCenter = circumcenter(tri);
point inCenter = incenter(tri);

// Fermat points (minimize total distance to vertices)
point[] fermatPoints = fermat(tri);

// Symmedian point
point symmedianPoint = symmedian(tri);

// Gergonne point
point gergonnePoint = gergonne(tri);
```

### 7.3 Triangle Circles

```asy
// Circumcircle and incircle
circle circum = circumcircle(tri);
circle incircle = incircle(tri);

// Excircles (one per side)
circle excircleA = excircle(tri.AB);  // Opposite vertex A
```

### 7.4 Derived Triangles

```asy
// Orthic triangle (feet of altitudes)
triangle orthicTri = orthic(tri);

// Medial triangle (midpoints of sides)
triangle medialTri = medial(tri);

// Intouch triangle (contact points of incircle)
triangle intouchTri = intouch(tri);

// Extouch triangle (contact points of excircles)
triangle extouchTri = extouch(tri);

// Tangential triangle
triangle tangentialTri = tangent(tri);

// Pedal triangle (feet of perpendiculars from a point)
triangle pedalTri = pedal(tri, pointP);

// Cevian triangle
triangle cevianTri = cevian(tri, pointP);

// Anticomplementary triangle
triangle antiComp = anticomplementary(tri);

// Symmedial triangle
triangle symmedialTri = symmedial(tri);

// Incentral triangle
triangle incentralTri = incentral(tri);
```

### 7.5 Lines in Triangles

```asy
// Altitude from vertex A
line altitudeA = altitude(tri.VA);  // tri.VA is vertex A
point footA = foot(tri.VA);         // Foot of altitude

// Median from vertex A
line medianA = median(tri.VA);

// Angle bisector from vertex A
line bisectorA = bisector(tri.VA);
```

### 7.6 Drawing Triangles

```asy
// Draw triangle edges
draw(tri, black + linewidth(1));

// Fill triangle
fill(tri, lightyellow);

// Show with labels (debug helper)
show(tri);  // Draws triangle with labeled vertices and side lengths
```

---

## 8. Marking Angles and Distances

### 8.1 Angle Marks

```asy
// Mark angle with arc
markangle(pointA, vertexO, pointB);
markangle("$\alpha$", pointA, vertexO, pointB);

// Right angle symbol
markrightangle(pointA, vertexO, pointB);

// Perpendicular mark
perpendicularmark(vertexO, dir(45), E);
```

### 8.2 Distance Marks

```asy
// Draw distance arrow between points
distance("$d$", pointA, pointB);

// With specific direction
distance("$h$", pointA, pointB, N);
```

### 8.3 Arc Marks

```asy
// Mark arc with sector lines
markarc("$\theta$", arcAB);
```

---

## 9. Inversion

```asy
// Create inversion with center C and power k
inversion inv = inversion(pointC, 9.0);

// Apply inversion
point inversePoint = inverse(inv, pointP);
line inverseLine = inverse(inv, lineAB);    // Line -> Circle (or line)
circle inverseCircle = inverse(inv, circleO);  // Circle -> Circle or line

// Radical axis and center
line radical = radicalline(circleO1, circleO2);
point radicalCenter = radicalcenter(circleO1, circleO2, circleO3);
```

---

## 10. Complete Example: Euler Line

This example demonstrates professional coding standards while constructing the Euler line of a triangle.

```asy
import geometry;

// ==========================================
// CONFIGURATION
// ==========================================
pen mainPen = black + linewidth(1);
pen dashedPen = dashed + gray(0.5);
pen highlightPen = red + linewidth(1.5);

// ==========================================
// TRIANGLE DEFINITION
// ==========================================
// Main triangle vertices
pair vertexA = (0, 0);
pair vertexB = (6, 0);
pair vertexC = (2, 4);

triangle tri = triangle(vertexA, vertexB, vertexC);

// ==========================================
// TRIANGLE CENTERS
// ==========================================
// Centroid: intersection of medians
point centroidPt = centroid(tri);

// Circumcenter: center of circumcircle
point circumCenterPt = circumcenter(tri);

// Orthocenter: intersection of altitudes
point orthoCenterPt = orthocenter(tri);

// ==========================================
// CONSTRUCT EULER LINE
// ==========================================
line eulerLine = line(circumCenterPt, orthoCenterPt);

// ==========================================
// DRAWING
// ==========================================
// Triangle edges
filldraw(tri, lightyellow, mainPen);

// Altitudes
draw(altitude(tri.VA), dashedPen);
draw(altitude(tri.VB), dashedPen);
draw(altitude(tri.VC), dashedPen);

// Medians
draw(median(tri.VA), dashedPen);
draw(median(tri.VB), dashedPen);
draw(median(tri.VC), dashedPen);

// Circumcircle
draw(circumcircle(tri), dashedPen);

// Euler line (extended for visibility)
draw(eulerLine, highlightPen);

// ==========================================
// MARKS AND LABELS
// ==========================================
// Mark right angles at feet of altitudes
markrightangle(vertexA, foot(tri.VA), vertexC);
markrightangle(vertexB, foot(tri.VB), vertexA);
markrightangle(vertexC, foot(tri.VC), vertexB);

// Label vertices
label("$A$", vertexA, SW);
label("$B$", vertexB, SE);
label("$C$", vertexC, N);

// Label centers
dot("$G$", centroidPt, SE);
dot("$O$", circumCenterPt, E);
dot("$H$", orthoCenterPt, NW);

// Label Euler line
label("Euler line", relpoint(eulerLine, 0.8), NE);
```

---

## 11. Common Patterns Summary

| Task | Function |
|------|----------|
| Create point | `point(pair p)` |
| Create line | `line(pointA, pointB)` |
| Create circle | `circle(center, radius)` |
| Create triangle | `triangle(A, B, C)` |
| Intersection of lines | `intersectionpoint(line1, line2)` |
| Line-circle intersections | `intersectionpoints(line, circle)` |
| Parallel line | `parallel(point, line)` |
| Perpendicular line | `perpendicular(point, line)` |
| Angle bisector | `bisector(line1, line2)` |
| Perpendicular bisector | `bisector(segment)` |
| Circumcenter | `circumcenter(triangle)` or `circumcenter(A, B, C)` |
| Incenter | `incenter(triangle)` or `incenter(A, B, C)` |
| Orthocenter | `orthocenter(triangle)` |
| Centroid | `centroid(triangle)` |
| Incircle | `incircle(triangle)` |
| Circumcircle | `circumcircle(triangle)` |
| Tangent from point | `tangents(circle, point)` |
| Mark angle | `markangle(A, O, B)` |
| Mark right angle | `markrightangle(A, O, B)` |

---

## 12. Important Notes

1. **Coordinate systems:** `point` embeds a `coordsys`. Operations between points in different coordinate systems may fail. Use `changecoordsys()` or ensure all points share the same system.

2. **Casting to path:** `line` does NOT cast to `path` directly — use `draw(line)`. `circle`, `ellipse`, `arc`, and `triangle` all cast to `path`.

3. **Drawing infinite lines:** `draw(line)` automatically clips the infinite line to the picture's bounding box.

4. **`@` and `^` operators:** `point @ circle` tests membership. `point ^ circle` computes power of a point.

5. **`show()` helpers:** `show(triangle)`, `show(line)`, `show(coordsys)` are useful for debugging geometric constructions.
