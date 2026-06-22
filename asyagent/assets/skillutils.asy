// skillutils.asy — Reusable picture-based diagram utilities
//
// Provides label_box_pic() and label_rounded_pic() for creating positioned,
// styled label boxes as picture components (rectangular and rounded-corner),
// roundbox() for creating rounded rectangle paths, pics_bbox() for computing
// the combined bounding box of multiple pictures using point() anchors,
// pics_cluster() for background cluster boxes, and connect_pics() for drawing
// connector lines (with arrows) between two pictures.
//
// Follow the picture + point() pattern:
//   - Create nodes with label_box_pic() or label_rounded_pic()
//   - Connect with connect_pics() (or point() anchors for custom routing)
//   - Add to parent picture with add()

// ==========================================
// settings for using Chinese with Asymptote
// ==========================================
import settings;
tex="xelatex";
usepackage("ctex");

// ==========================================
// LABEL BOX — picture component with built-in positioning
// ==========================================

// Create a labeled, filled, bordered box as a picture, shifted to `boxPosition`.
//
// Parameters:
//   boxPosition — shift vector applied to the returned picture,
//                 so the box center lands at this point in the parent
//                 coordinate system. Use (0,0) for an origin-centered
//                 picture; the caller can also ignore this and apply
//                 shift() externally if they prefer that style.
//   boxWidth    — total width of the box (user units)
//   boxHeight   — total height of the box (user units)
//   lineDy      — vertical spacing between consecutive text lines
//   lines       — array of label strings, drawn top-to-bottom
//   label_text  — pen for label rendering (font size, color, weight, etc.).
//                 Unlike the original which hardcodes fontsize(9pt), this
//                 gives the caller full control. Typical usage:
//                   fontsize(9pt)                 — size only
//                   fontsize(8pt) + rgb(0.5,0.5,0.5)  — size + color
//                   fontsize(10pt) + blue            — size + color
//   fillPen     — fill color/pen for the box interior
//   borderPen   — stroke color/pen for the box outline
//
// Returns:
//   A picture containing the box and labels, already shifted to `boxPosition`.
//   Use directly with add(dest, pic), or query anchors with point(pic, dir).
//
picture label_box_pic(pair boxPosition, real boxWidth, real boxHeight,
                      real lineDy, string[] lines,
                      pen label_text, pen fillPen, pen borderPen) {
    picture pic;

    // Draw box centered at origin
    pair bottomLeft = (-boxWidth / 2, -boxHeight / 2);
    pair topRight   = ( boxWidth / 2,  boxHeight / 2);
    fill(pic, box(bottomLeft, topRight), fillPen);
    draw(pic, box(bottomLeft, topRight), borderPen);

    // Lay out lines top-to-bottom, vertically centered.
    // y0 = topmost line's y-coordinate (positive = up).
    real y0 = (lines.length - 1) * lineDy / 2;
    for (int i = 0; i < lines.length; ++i)
        label(pic, lines[i], (0, y0 - i * lineDy), label_text);

    // Apply position shift and return
    return shift(boxPosition) * pic;
}

// Single-string convenience overload.
// Wraps the single text into a one-element string array.
picture label_box_pic(pair boxPosition, real boxWidth, real boxHeight,
                      real lineDy, string text,
                      pen label_text, pen fillPen, pen borderPen) {
    return label_box_pic(boxPosition, boxWidth, boxHeight, lineDy,
                         new string[]{text}, label_text, fillPen, borderPen);
}

// ==========================================
// BOUNDING BOX — combined extent of multiple pictures
// ==========================================

// Compute the axis-aligned bounding box enclosing all given pictures.
//
// Uses point(pic, SW) and point(pic, NE) instead of min(pic)/max(pic).
//
// WHY NOT min()/max():
//   min(pic)/max(pic) return coordinates through the picture's user→PS
//   transform. For a standalone sub-picture that has never been add()-ed
//   to a sized parent picture, this transform is the identity in PostScript
//   bp units (1/72 inch), NOT in user units. The resulting coordinates are
//   therefore in an unrelated scale and will appear wildly offset.
//
//   point(pic, dir) does NOT have this problem — it computes boundary
//   anchors from the picture's drawn content + stored transforms, returning
//   correct user-coordinate values even for standalone (un-added) pictures.
//
// Parameters:
//   pics — array of pictures whose combined extent is needed
//
// Returns:
//   A 2-element pair array: {bottomLeft, topRight}.
//   Usage:
//     pair[] bb = pics_bbox(new picture[]{pA, pB, pC});
//     pair lowCorner = bb[0];  // overall bottom-left (min x, min y)
//     pair highCorner = bb[1];  // overall top-right  (max x, max y)
//
pair[] pics_bbox(picture[] pics) {
    pair lowCorner = point(pics[0], SW);
    pair highCorner = point(pics[0], NE);

    for (int i = 1; i < pics.length; ++i) {
        pair lowCornerI  = point(pics[i], SW);
        pair highCornerI = point(pics[i], NE);
        lowCorner  = (min(lowCorner.x,  lowCornerI.x), min(lowCorner.y,  lowCornerI.y));
        highCorner = (max(highCorner.x, highCornerI.x), max(highCorner.y, highCornerI.y));
    }

    return new pair[]{lowCorner, highCorner};
}

// ==========================================
// ROUNDED BOX — picture component with rounded corners
// ==========================================

// Create a rounded rectangle path.
//
// Parameters:
//   bottomLeft — bottom-left corner of the bounding rectangle
//   topRight   — top-right corner of the bounding rectangle
//   radius     — corner radius (clamped to half the smaller dimension)
//
// Returns:
//   A cyclic path tracing the rounded rectangle, drawn clockwise
//   starting from the left edge above the bottom-left corner.
path roundbox(pair bottomLeft, pair topRight, real radius) {
    radius = min(radius, (topRight.x - bottomLeft.x) / 2, (topRight.y - bottomLeft.y) / 2);
    return (bottomLeft.x, bottomLeft.y + radius){down}..{right}(bottomLeft.x + radius, bottomLeft.y) --
           (topRight.x - radius, bottomLeft.y){right}..{up}(topRight.x, bottomLeft.y + radius) --
           (topRight.x, topRight.y - radius){up}..{left}(topRight.x - radius, topRight.y) --
           (bottomLeft.x + radius, topRight.y){left}..{down}(bottomLeft.x, topRight.y - radius) -- cycle;
}

// Create a labeled, filled, bordered rounded box as a picture,
// shifted to `boxPosition`.
//
// Parameters:
//   boxPosition — shift vector applied to the returned picture,
//                 so the box center lands at this point in the parent
//                 coordinate system.
//   boxWidth    — total width of the box (user units)
//   boxHeight   — total height of the box (user units)
//   radius      — corner radius (clamped to half the smaller dimension)
//   lineDy      — vertical spacing between consecutive text lines
//   lines       — array of label strings, drawn top-to-bottom
//   label_text  — pen for label rendering (font size, color, weight, etc.)
//   fillPen     — fill color/pen for the box interior
//   borderPen   — stroke color/pen for the box outline
//
// Returns:
//   A picture containing the rounded box and labels, already shifted
//   to `boxPosition`. Use directly with add(dest, pic), or query anchors
//   with point(pic, dir).
//
picture label_rounded_pic(pair boxPosition, real boxWidth, real boxHeight,
                          real radius, real lineDy, string[] lines,
                          pen label_text, pen fillPen, pen borderPen) {
    picture pic;

    // Draw rounded box centered at origin
    pair bottomLeft = (-boxWidth / 2, -boxHeight / 2);
    pair topRight   = ( boxWidth / 2,  boxHeight / 2);
    path rbox = roundbox(bottomLeft, topRight, radius);
    fill(pic, rbox, fillPen);
    draw(pic, rbox, borderPen);

    // Lay out lines top-to-bottom, vertically centered
    real y0 = (lines.length - 1) * lineDy / 2;
    for (int i = 0; i < lines.length; ++i)
        label(pic, lines[i], (0, y0 - i * lineDy), label_text);

    // Apply position shift and return
    return shift(boxPosition) * pic;
}

// Single-string convenience overload.
// Wraps the single text into a one-element string array.
picture label_rounded_pic(pair boxPosition, real boxWidth, real boxHeight,
                          real radius, real lineDy, string text,
                          pen label_text, pen fillPen, pen borderPen) {
    return label_rounded_pic(boxPosition, boxWidth, boxHeight, radius, lineDy,
                             new string[]{text}, label_text, fillPen, borderPen);
}

// ==========================================
// CLUSTER BOX — background box around a group of pictures
// ==========================================

// Draw a fill+border rectangle enclosing all given pictures with padding,
// returned as a picture. Intended to be added BEFORE the node pictures
// so it appears behind them.
//
// Parameters:
//   pics      — array of pictures to enclose
//   padX      — horizontal padding between the nodes' bbox and the box edge
//   padY      — vertical padding between the nodes' bbox and the box edge
//   fillPen   — interior fill pen (use nullpen for no fill)
//   borderPen — outline stroke pen (use nullpen for no border)
//
// Returns:
//   A picture containing just the background rectangle, positioned to
//   surround all nodes. Add it before the nodes so it renders behind:
//
//     picture bg = pics_cluster(new picture[]{pA, pB, pC}, 0.4, 0.3, clusterFill, clusterPen);
//     add(diagram, bg);       // behind
//     add(diagram, pA);       // in front
//     add(diagram, pB);
//     add(diagram, pC);
//
picture pics_cluster(picture[] pics, real padX, real padY,
                     pen fillPen, pen borderPen) {
    pair[] bb = pics_bbox(pics);
    pair lowCorner  = bb[0] - (padX, padY);
    pair highCorner = bb[1] + (padX, padY);

    picture bg;
    filldraw(bg, box(lowCorner, highCorner), fillPen, borderPen);
    return bg;
}

// ==========================================
// CONNECTOR — line+arrow between two pictures
// ==========================================

// Draw a connector line (with arrow) from srcPic to destPic, returned as a
// picture. The endpoints are boundary anchors queried via point(): the line
// starts at srcPic's srcDir edge and ends at destPic's destDir edge, each
// pulled back by `gap` along its own direction for visual breathing room.
//
// The path uses tangent control {srcDir}..{-destDir}: the curve leaves srcPic
// heading outward in srcDir, and arrives at destPic heading inward (i.e., in
// direction -destDir). For aligned axes (e.g. E->W or S->N) this produces a
// straight line; for non-aligned axes (e.g. S->W) it produces a smooth L-curve.
// This mirrors the idiomatic pattern already used throughout the codebase:
//   draw(dest, a{E}..{E}b, ...)   // see system_diagram.asy / modular_flowchart.asy
//
// WHY A SINGLE linePen:
//   Asymptote pen addition combines color + linewidth + linetype (dashed /
//   dotted / solid). Passing one pen is the idiomatic way -- examples:
//     rgb(0.2,0.2,0.2) + linewidth(0.9)            // solid dark gray
//     rgb(0.5,0.5,0.5) + linewidth(0.7) + dashed   // dashed gray
//     blue + dotted + linewidth(0.8)               // dotted blue
//   Splitting into color / width / style params would be less idiomatic.
//
// WHY gap (manual offset) instead of margin=:
//   Asymptote's built-in margin parameter (PenMargin, TrueMargin, DotMargin)
//   shortens the path geometry. The rest of this codebase
//   (docs/04-modular-diagram.md, system_diagram.asy, modular_flowchart.asy)
//   consistently uses point(pic,dir) + gap*dir for connector endpoints, so
//   connect_pics() follows that same local convention for consistency.
//
// Parameters:
//   srcPic    -- source picture (already positioned via shift() or label_*_pic)
//   srcDir    -- boundary direction on srcPic (E, W, N, S, NE, NW, SE, SW, ...)
//   destPic   -- destination picture (already positioned)
//   destDir   -- boundary direction on destPic
//   gap       -- pullback distance from each anchor, along its own dir.
//                Use 0.2 for typical flowcharts; 0 to touch the box edge.
//   linePen   -- pen for the connector: color + linewidth + linetype combined.
//                Use nullpen for an invisible stroke (rarely useful).
//   arrowSpec -- arrowbar value controlling arrow style + position + size.
//                Common choices:
//                  Arrow(TeXHead)                  -- single end arrow
//                  Arrow(TeXHead, size=3mm)        -- larger arrowhead
//                  Arrows(TeXHead)                 -- arrows at BOTH ends
//                  BeginArrow(TeXHead)             -- arrow at start only
//                  None                            -- no arrow (just a line)
//
// Returns:
//   A picture containing ONLY the connector (no nodes). Add it BEFORE the
//   node pictures so it renders behind them (z-order convention):
//
//     picture conn = connect_pics(pA, E, pB, W, 0.2,
//                                 rgb(0.2,0.2,0.2) + linewidth(0.9),
//                                 Arrow(TeXHead));
//     add(diagram, conn);   // behind
//     add(diagram, pA);     // in front
//     add(diagram, pB);
//
picture connect_pics(picture srcPic, pair srcDir,
                     picture destPic, pair destDir,
                     real gap,
                     pen linePen,
                     arrowbar arrowSpec) {
    pair a = point(srcPic,  srcDir)  + gap * srcDir;
    pair b = point(destPic, destDir) + gap * destDir;
    picture pic;
    draw(pic, a{srcDir}..{-destDir}b, linePen, arrowSpec);
    return pic;
}
