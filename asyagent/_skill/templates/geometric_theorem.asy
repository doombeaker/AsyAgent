// ==========================================
// TEMPLATE: Pythagorean Theorem Visualization
// Demonstrates: squares, right angles, distance labels, perpendicular marks
// ==========================================
size(0, 150);
import geometry;

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
real sideA = 3;   // vertical leg
real sideB = 4;   // horizontal leg
real labelOffset = 0.3;

pen squarePen   = black + linewidth(0.8);
pen rightAnglePen = blue + linewidth(0.6);
pen measurePen  = red + linewidth(0.7);

// ------------------------------------------
// GEOMETRY DEFINITION
// ------------------------------------------
pair vertexA = (0, sideB);        // top of vertical leg
pair vertexB = (0, 0);            // right angle vertex
pair vertexC = (sideA, 0);        // end of horizontal leg
pair vertexD = (sideA + sideB, 0); // outer corner of big square

real hypotenuse = hypot(sideA, sideB);

// ------------------------------------------
// DRAWING
// ------------------------------------------
// Right angle markers
perpendicular(vertexA, NE, vertexA--vertexC, rightAnglePen);
perpendicular(vertexD, NW, vertexD--vertexA, rightAnglePen);

// Large square on hypotenuse
draw(square(vertexB, vertexD), squarePen);

// Small square on vertical leg
draw(square(vertexA, vertexC), squarePen);

// ------------------------------------------
// DIMENSION LABELS
// ------------------------------------------
pair dirAC = unit(vertexC - vertexA);  // hypotenuse direction

// Side labels with measurement bars
draw(baseline("$a$"), 
     (-labelOffset, 0)--(sideA - labelOffset, 0), 
     measurePen, Bars, Arrows, PenMargins);

draw(baseline("$b$"), 
     (sideA - labelOffset, 0)--(sideA + sideB - labelOffset, 0), 
     measurePen, Arrows, Bars, PenMargins);

draw("$c$", 
     vertexD + sideA * I - labelOffset * dirAC -- vertexC - labelOffset * dirAC, 
     measurePen, Arrows, PenMargins);

// Remaining sides of the squares
draw("$a$", vertexD + labelOffset -- vertexD + sideA * I + labelOffset, 
     measurePen, Arrows, Bars, PenMargins);

draw("$b$", vertexD + sideA * I + labelOffset -- vertexD + (sideA + sideB) * I + labelOffset, 
     measurePen, Arrows, Bars, PenMargins);
