// ==========================================
// TEMPLATE: Basic Trembling Effect on Shapes
// Demonstrates: tremble struct, deform method, basic shapes with hand-drawn effect
// ==========================================
import trembling;

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
size(0, 200);

pen smoothPen = black + linewidth(0.8);
pen tremblePen = red + linewidth(0.8);

// ------------------------------------------
// GEOMETRY DEFINITION
// ------------------------------------------
pair centerO = (0, 0);
real radiusR = 1.5;

path smoothCircle = circle(centerO, radiusR);
path smoothSquare = shift((-0.7, -0.7)) * scale(1.4) * unitsquare;
path smoothLine = (-2, 0)--(2, 0);

// ------------------------------------------
// TREMBLE SETUP
// ------------------------------------------
tremble T = tremble(angle=4, frequency=0.5, random=2);

path trembleCircle = T.deform(smoothCircle);
path trembleSquare = T.deform(smoothSquare);
path trembleLine = T.deform(smoothLine);

// ------------------------------------------
// DRAWING
// ------------------------------------------
// Left column: smooth original paths
label("Original", (-2.5, 2.5), N);
draw(shift((-3, 0))*smoothCircle, smoothPen);
draw(shift((-3, -3.5)) * smoothSquare, smoothPen);
draw(shift((-3, -7)) * smoothLine, smoothPen);

// Right column: trembled paths
label("Trembled", (5, 2.5), N);
draw(shift((5, 0)) * trembleCircle, tremblePen);
draw(shift((5, -3.5)) * trembleSquare, tremblePen);
draw(shift((5, -7)) * trembleLine, tremblePen);

// Vertical separator
draw((1.5, 3)--(1.5, -8), dashed + gray(0.5));
