// ==========================================
// TEMPLATE: Function Plot with Axes
// Demonstrates: function graphs, axis labels, tick marks, curve annotation
// ==========================================
import graph;

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
size(200, 150, IgnoreAspect);

real xMin = 0.01;
real xMax = 10;
real yMin = -2;
real yMax = 3;

pen curvePen   = blue + linewidth(1.0);
pen axisPen    = black + linewidth(0.6);
pen labelPen   = black + fontsize(10pt);

// ------------------------------------------
// FUNCTION DEFINITION
// ------------------------------------------
real func(real x) {
    return log(x);
}

// ------------------------------------------
// DRAWING
// ------------------------------------------
// Axes
xaxis("$x$", axisPen, RightTicks(NoZero));
yaxis("$y$", axisPen, LeftTicks(NoZero));

// Function curve
draw(graph(func, xMin, xMax, operator ..), curvePen);

// Key point annotation
pair keyPoint = (1, func(1));
label("$(1,0)$", keyPoint, SE, labelPen);

// Curve label
pair labelPoint = (7, func(7));
label("$y = \ln x$", labelPoint, SE, labelPen);

// Optional: add grid
// xaxis("", axisPen, RightTicks(Step=1, step=0.5), above=true);
// yaxis("", axisPen, LeftTicks(Step=1, step=0.5), above=true);
