// ==========================================
// TEMPLATE: Triangle Circumcircle
// Demonstrates: triangle geometry, perpendicular bisectors, circle construction
// ==========================================
unitsize(1inch);

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
pair vertexA = (0, 0);
pair vertexB = (1, 0);
pair vertexC = (2, 1);

pen trianglePen = red + linewidth(1.0);
pen circlePen   = black + linewidth(0.8);
pen centerPen   = black + linewidth(1.2);

// ------------------------------------------
// GEOMETRY DEFINITION
// ------------------------------------------
path trianglePath = vertexA--vertexB--vertexC--cycle;

// Midpoints of two sides
pair midAB = point(trianglePath, 0.5);
pair midBC = point(trianglePath, 1.5);

// Perpendicular directions at midpoints
pair perpAB = I * dir(trianglePath, 0.5);  // I = (0,1), rotates by 90°
pair perpBC = I * dir(trianglePath, 1.5);

// Circumcenter = intersection of perpendicular bisectors
pair circumCenter = extension(midAB, midAB + perpAB, midBC, midBC + perpBC);

real circumRadius = abs(circumCenter - vertexA);

// ------------------------------------------
// DRAWING
// ------------------------------------------
// Circumcircle
draw(circle(circumCenter, circumRadius), circlePen);

// Triangle
draw(trianglePath, trianglePen);

// Circumcenter marker
dot(circumCenter, centerPen);

// Optional: draw perpendicular bisectors (for educational purposes)
// draw(midAB--circumCenter, dashed + grey);
// draw(midBC--circumCenter, dashed + grey);
