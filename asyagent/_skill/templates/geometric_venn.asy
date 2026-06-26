// ==========================================
// TEMPLATE: Venn Diagram (Two Sets)
// Demonstrates: overlapping circles, clipping, fill operations, annotation
// ==========================================
size(0, 150);

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
pair centerA = (-1, 0);
pair centerB = (1, 0);
real setRadius = 1.5;

pen setAPen      = red + opacity(0.5);
pen setBPen      = green + opacity(0.5);
pen intersectPen = blue + opacity(0.5);
pen outlinePen   = black + linewidth(0.8);

// ------------------------------------------
// GEOMETRY DEFINITION
// ------------------------------------------
path circleA = circle(centerA, setRadius);
path circleB = circle(centerB, setRadius);

// ------------------------------------------
// DRAWING
// ------------------------------------------
// Fill set A
fill(circleA, setAPen);

// Fill set B
fill(circleB, setBPen);

// Intersection: create clipped picture for proper overlap color
picture intersectionPic;
fill(intersectionPic, circleA, setAPen + setBPen);
clip(intersectionPic, circleB);
add(intersectionPic);

// Outlines
draw(circleA, outlinePen);
draw(circleB, outlinePen);

// Set labels
label("$A$", centerA, N);
label("$B$", centerB, N);

// Optional: annotations for regions
// pair annotationPoint = (0, -2);
// margin BigMargin = Margin(0, 3 * dot(unit(centerA - annotationPoint), unit((0,0) - annotationPoint)));
// draw(Label("$A \cap B$", 0), conj(annotationPoint)--(0,0), Arrow, BigMargin);
// draw(Label("$A \cup B$", 0), annotationPoint--(0,0), Arrow, BigMargin);
