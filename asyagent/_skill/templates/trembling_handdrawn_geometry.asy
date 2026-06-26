// ==========================================
// TEMPLATE: Hand-Drawn Style Geometric Diagram
// Demonstrates: trembling applied to a practical geometric figure for sketch aesthetic
// ==========================================
import trembling;

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
size(0, 180);

pen sketchPen = black + linewidth(0.9);
pen labelPen = black + fontsize(10pt);

// ------------------------------------------
// GEOMETRY DEFINITION
// ------------------------------------------
pair A = (0, 0);
pair B = (4, 0);
pair C = (2, 3);

path triangle = A--B--C--cycle;
path altitude = C--(2, 0);
path medianA = A--(B+C)/2;
path angleArc = arc(A, 0.6, 0, 60);

// ------------------------------------------
// TREMBLE SETUP
// ------------------------------------------
// Use moderate trembling for hand-drawn look
tremble T = tremble(angle=3, frequency=0.6, random=2);

path sketchTriangle = T.deform(triangle);
path sketchAltitude = T.deform(altitude);
path sketchMedian = T.deform(medianA);
path sketchAngleArc = T.deform(angleArc);

// ------------------------------------------
// DRAWING
// ------------------------------------------
// Main triangle
draw(sketchTriangle, sketchPen);

// Internal lines
draw(sketchAltitude, sketchPen + dashed);
draw(sketchMedian, sketchPen + dotted);

// Angle arc
draw(sketchAngleArc, sketchPen);

// Vertices with hand-drawn dots
dot(A);
dot(B);
dot(C);

// Labels
label("$A$", A, SW, labelPen);
label("$B$", B, SE, labelPen);
label("$C$", C, N, labelPen);
label("$a$", (B+C)/2, NE, labelPen);
label("$b$", (A+C)/2, NW, labelPen);
label("$c$", (A+B)/2, S, labelPen);

// Right angle marker (small trembled square)
pair D = (2, 0);
path rightAngle = D--(2.3, 0)--(2.3, 0.3)--(2, 0.3)--cycle;
draw(T.deform(rightAngle), sketchPen);
