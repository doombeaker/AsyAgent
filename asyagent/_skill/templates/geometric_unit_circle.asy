// ==========================================
// TEMPLATE: Unit Circle with Angle Annotation
// Demonstrates: circles, arcs, filled sectors, labels, arrows
// ==========================================
size(0, 150);

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
real circleRadius = 1.0;
real angleTheta   = 30;   // degrees
real labelRadius  = 0.7;  // for angle arc

pen outlinePen    = black + linewidth(0.8);
pen fillPen       = lightgrey;
pen anglePen      = black + linewidth(0.6);
pen arrowPen      = black + linewidth(0.7);

// ------------------------------------------
// GEOMETRY DEFINITION
// ------------------------------------------
pair originO = (0, 0);
pair pointX  = (circleRadius, 0);
pair pointP  = dir(angleTheta);  // on circle at angle theta

path unitCircle = circle(originO, circleRadius);
path sector     = originO--arc(originO, circleRadius, 0, angleTheta)--cycle;

// ------------------------------------------
// DRAWING
// ------------------------------------------
// Main circle and filled sector
draw(unitCircle, outlinePen);
filldraw(sector, fillPen, outlinePen);

// Angle arc with label
draw("$\theta$", arc(originO, labelRadius, 0, angleTheta), 
     LeftSide, Arrow, PenMargin);

// Points
dot(originO);
dot(Label, pointX);
dot("$(x,y) = (\cos\theta, \sin\theta)$", pointP, NE);

// Area label with arrow
arrow("area $\frac{\theta}{2}$", dir(0.5 * angleTheta), 2E, arrowPen);
