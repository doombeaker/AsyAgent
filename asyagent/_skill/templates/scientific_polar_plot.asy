// ==========================================
// TEMPLATE: Polar Plot with Filled Sector
// Demonstrates: polar graphs, radial fills, angle annotations
// ==========================================
import graph;

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
size(0, 150);

real func(real theta) {
    return 5 + cos(10 * theta);
}

real angleStart = pi / 8;
real angleEnd   = pi / 3;

pen axisPen       = black + linewidth(0.6);
pen sectorFillPen = lightgray;
pen curvePen      = black + linewidth(0.8);
pen radiusPen     = dotted + black;
pen angleArcPen   = red + linewidth(0.8);

// ------------------------------------------
// DRAWING
// ------------------------------------------
// Cartesian axes for reference
xaxis("$x$", axisPen);
yaxis("$y$", axisPen);

// Polar curve over the angular range
path polarCurve = polargraph(func, angleStart, angleEnd, operator ..);

// Filled sector from origin
path sector = (0, 0)--polarCurve--cycle;
fill(sector, sectorFillPen);
draw(sector, curvePen);

// Boundary radial lines
real rMax = 6;  // slightly larger than max of func
draw((0, 0)--rMax * expi(angleStart), radiusPen);
draw((0, 0)--rMax * expi(angleEnd),   radiusPen);

// Angle annotation
real midAngle = (angleStart + angleEnd) / 2;
pair labelPos = 0.5 * rMax * expi(midAngle);
label("$\theta$", labelPos, angleArcPen);
