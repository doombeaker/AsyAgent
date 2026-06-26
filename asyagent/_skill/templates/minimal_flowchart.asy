// ==========================================
// TEMPLATE: Minimal Vertical Flowchart
// Demonstrates: picture components, label_box_pic(), connect_pics() arrows
// Use this as the starting point for simple sequential workflows
// ==========================================

import skillutils;

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
real boxWidth = 3.0;    // Box width
real boxHeight = 0.9;   // Box height
real gap    = 0.25;   // Pullback from each box edge to arrow endpoint
real lineDy = 0.32;   // Line spacing inside multi-line box
real nodeDy = 2.0;    // Vertical step between rows

real xCenter = 0;     // Center column x-coordinate
real yTop    = 0;     // Top of diagram

pen textPen = fontsize(9pt);

// Colors — one pen pair per role
pen startFill   = rgb(0.90, 0.95, 1.00);  pen startBorder   = rgb(0.25, 0.40, 0.60) + linewidth(1.2);
pen processFill = rgb(1.00, 0.97, 0.90);  pen processBorder = rgb(0.50, 0.40, 0.20) + linewidth(1.2);
pen doneFill    = rgb(0.90, 1.00, 0.95);  pen doneBorder    = rgb(0.20, 0.50, 0.40) + linewidth(1.2);
// Connector pen = color + linewidth + linetype (solid) combined, Asymptote idiom.
pen arrowPen    = rgb(0.25, 0.25, 0.25) + linewidth(0.9);

// ------------------------------------------
// BUILD DIAGRAM
// ------------------------------------------

// --- Create and position nodes ---
picture pStart = label_box_pic((xCenter, yTop),             boxWidth, boxHeight, lineDy, "Start", textPen, startFill,   startBorder);
picture pStep1 = label_box_pic((xCenter, yTop - nodeDy),    boxWidth, boxHeight, lineDy, new string[]{"Step 1", "Describe"}, textPen, processFill, processBorder);
picture pStep2 = label_box_pic((xCenter, yTop - 2*nodeDy),  boxWidth, boxHeight, lineDy, new string[]{"Step 2", "Describe"}, textPen, processFill, processBorder);
picture pStep3 = label_box_pic((xCenter, yTop - 3*nodeDy),  boxWidth, boxHeight, lineDy, new string[]{"Step 3", "Describe"}, textPen, processFill, processBorder);
picture pDone  = label_box_pic((xCenter, yTop - 4*nodeDy),  boxWidth, boxHeight, lineDy, "Done",  textPen, doneFill,    doneBorder);

// --- Assemble ---
picture diagram;
size(diagram, 10cm);

// Connectors: connect_pics(top, S, bot, N, ...) produces a straight vertical
// line because srcDir=S and -destDir=-N=S both align with the chord (the two
// nodes share the same x = xCenter).
//
// Each connect_pics call returns a picture containing just the connector;
// add it to the diagram BEFORE the node pictures so arrows render behind
// the boxes (z-order convention, see docs/04-modular-diagram.md §1 rule 5).
add(diagram, connect_pics(pStart, S, pStep1, N, gap, arrowPen, Arrow(TeXHead)));
add(diagram, connect_pics(pStep1, S, pStep2, N, gap, arrowPen, Arrow(TeXHead)));
add(diagram, connect_pics(pStep2, S, pStep3, N, gap, arrowPen, Arrow(TeXHead)));
add(diagram, connect_pics(pStep3, S, pDone,  N, gap, arrowPen, Arrow(TeXHead)));

// Add nodes on top of arrows
add(diagram, pStart);
add(diagram, pStep1);
add(diagram, pStep2);
add(diagram, pStep3);
add(diagram, pDone);

// ------------------------------------------
// CENTER AND SHIP
// ------------------------------------------
// Use pics_bbox() (the skillutils sentinel-safe helper) rather than
// min(diagram, true) to compute the bottom-left anchor for the centering
// shift. pics_bbox() uses point(pic, SW) which is well-defined even for
// standalone sub-pictures.
pair[] bb = pics_bbox(new picture[]{pStart, pStep1, pStep2, pStep3, pDone});
shipout(shift(-bb[0]) * diagram);
