// ==========================================
// TEMPLATE: System Architecture Diagram
// Layers, clusters, dispatch lines, and annotations
// Uses picture + point() pattern for modular composition
// Connectors use connect_pics() from skillutils (single pen = color +
// linewidth + linetype combined, idiomatic Asymptote).
// ==========================================

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
import skillutils;

real boxWidth   = 3.8;
real boxHeight   = 1.2;
real lineDy     = 0.36;
real gap        = 0.2;
real dx         = 4.5;
real yTop       = 3.5;
real yBot       = -3.5;

pen textPen     = fontsize(9pt);
pen userColor    = rgb(0.90, 0.95, 1.00);  pen userBorder    = black + 1.2pt;
pen gatewayColor = rgb(1.00, 0.95, 0.85);  pen gatewayBorder = black + 1.2pt;
pen routerColor  = rgb(0.85, 1.00, 0.90);  pen routerBorder  = black + 1.2pt;
pen workerColor  = rgb(1.00, 0.95, 0.75);  pen workerBorder  = black + 1.2pt;
pen resultColor  = rgb(0.85, 1.00, 0.95);  pen resultBorder  = black + 1.2pt;
pen clusterFill  = rgb(0.96, 0.96, 0.99);
pen clusterPen   = rgb(0.3, 0.3, 0.6) + linewidth(1.8);
pen arrowPen     = rgb(0.2, 0.2, 0.2) + linewidth(0.9);
pen dispatchPen  = gray(0.5) + linewidth(0.7) + dashed;

// ------------------------------------------
// TODO: Replace components with your system architecture
// ------------------------------------------
real xStart = -11;

// --- Create and position nodes ---
picture pUser      = label_box_pic((xStart,            yTop),         boxWidth, boxHeight, lineDy, new string[]{"User",     "Client"},        textPen, userColor,    userBorder);
picture pGateway   = label_box_pic((xStart + dx,       yTop),         boxWidth, boxHeight, lineDy, new string[]{"Gateway",  "Auth, Routing"}, textPen, gatewayColor, gatewayBorder);
picture pRouter    = label_box_pic((xStart + 3.25*dx,  yTop - 1.5),   boxWidth, boxHeight, lineDy, new string[]{"Router",   "Load Balancer"}, textPen, routerColor,  routerBorder);
picture pWorker1   = label_box_pic((xStart + 2*dx,     yBot),         boxWidth, boxHeight, lineDy, new string[]{"Worker 1", "GPU Tasks"},     textPen, workerColor,  workerBorder);
picture pWorkerDot = label_box_pic((xStart + 3.25*dx,  yBot),         boxWidth, boxHeight, lineDy, new string[]{"Worker ...", "GPU Tasks"},   textPen, workerColor,  workerBorder);
picture pWorker2   = label_box_pic((xStart + 4.5*dx,   yBot),         boxWidth, boxHeight, lineDy, new string[]{"Worker N", "GPU Tasks"},     textPen, workerColor,  workerBorder);
picture pResult    = label_box_pic((xStart + 6.0*dx,   (yTop+yBot)/2), boxWidth, boxHeight, lineDy, new string[]{"Result",   "Output"},        textPen, resultColor,  resultBorder);

// ------------------------------------------
// ASSEMBLE DIAGRAM
// ------------------------------------------
picture diagram;
size(diagram, 20cm);

// --- Cluster background (drawn first) ---
picture bg = pics_cluster(new picture[]{pRouter, pWorker1, pWorkerDot, pWorker2}, 0.4, 1, clusterFill, clusterPen);
add(diagram, bg);
label(diagram, "Core Cluster", (point(bg, S).x, point(bg, S).y + 0.5), fontsize(11pt) + rgb(0.3, 0.3, 0.6));

// --- Connectors (added before nodes → render behind nodes) ---
// Each connect_pics(...) returns a picture containing just the connector;
// add() it to diagram before the node pictures so z-order puts arrows
// behind the boxes.

// User → Gateway: aligned E→W, tangents {E}..{E} produce a straight
// horizontal line (both endpoints at y = yTop).
add(diagram, connect_pics(pUser, E, pGateway, W, gap, arrowPen, Arrow(TeXHead)));

// Gateway → Router: src and dest offset in Y (yTop vs yTop-1.5); the
// {E}..{-W=E} tangents yield a smooth Bezier between them.
add(diagram, connect_pics(pGateway, E, pRouter, W, gap, arrowPen, Arrow(TeXHead)));

// Router → Workers (dashed dispatch, no arrowhead — None as arrowbar).
// Each connector is a smooth curve from pRouter's S to the worker's N:
//   - pWorkerDot (directly below pRouter): straight vertical line
//   - pWorker1 / pWorker2 (offset horizontally): gentle fan-out S-curve
add(diagram, connect_pics(pRouter, S, pWorker1,   N, gap, dispatchPen, None));
add(diagram, connect_pics(pRouter, S, pWorkerDot, N, gap, dispatchPen, None));
add(diagram, connect_pics(pRouter, S, pWorker2,   N, gap, dispatchPen, None));

// Worker N → Result: curved dashed E→W; arrowPen + dashed demonstrates
// linetype baked into the pen.
add(diagram, connect_pics(pWorker2, E, pResult, W, gap, arrowPen + dashed, Arrow(TeXHead)));

// --- Add nodes on top of connectors ---
add(diagram, pUser);
add(diagram, pGateway);
add(diagram, pRouter);
add(diagram, pWorker1);
add(diagram, pWorkerDot);
add(diagram, pWorker2);
add(diagram, pResult);

// --- Step numbering ---
real ySteps = point(pResult, S).y - 6;
label(diagram, "1. Request",  (point(pUser,    S).x, ySteps), fontsize(8pt));
label(diagram, "2. Auth",     (point(pGateway, S).x, ySteps), fontsize(8pt));
label(diagram, "3. Dispatch", (point(pRouter,  S).x, ySteps), fontsize(8pt));
label(diagram, "4. Process",  (point(pWorker2, S).x, ySteps), fontsize(8pt));
label(diagram, "5. Return",   (point(pResult,  S).x, ySteps), fontsize(8pt));

shipout(diagram);
