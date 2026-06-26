import skillutils;

// Zheng He's Voyages - HORIZONTAL Timeline (Landscape)
// 1405-1433, Seven Voyages Across the Western Ocean
// Uses picture + point() pattern for modular composition.
// Node-to-node connectors use connect_pics() from skillutils.
//
// SCALING PRINCIPLE:
//   Labels use fixed font sizes (7pt). For text to fit inside boxes,
//   output width must roughly match coordinate extent so 1 unit ≈ 1 cm.
//   With ~50 user-units width, outputWidth should be ~50 cm.

// ==========================================
// LAYOUT PARAMETERS — adjust these to tune the diagram
// ==========================================
real boxWidth   = 2.6;      // Box width (user units ≈ cm at output)
real boxHeight   = 0.95;     // Box height
real lineDy     = 0.33;     // Line spacing inside box
real gap        = 0.18;     // Arrow pullback from box edge
real dx         = 3.0;      // Horizontal step between adjacent nodes
                            //   inter-box gap = dx - boxWidth = 0.4

real rowDy      = 2.2;      // Vertical distance: main row ↔ upper/lower rows
real xStart     = -22.5;    // X coordinate of leftmost node (≈ -7.5*dx for centering)

// Annotation spacing (offsets from nearest structure)
real annotPad   = 0.3;      // Gap above main-row box top edge to top annotation
real annotLine  = 0.35;     // Vertical step between two annotation lines
real dividerPad = 0.8;      // Gap above upper-row box tops to divider line
real dividerLbl = 0.4;      // Gap above divider line to reign label
real botAnnot   = 1.5;      // Gap below lower-row box bottoms to bottom annotations
real barPad     = 1.2;      // Gap below lower-row box bottoms to color bar
real barH       = 0.25;     // Color bar height
real quotePad   = 2.8;      // Gap below lower-row box bottoms to quote
real titlePad   = 2.2;      // Gap above divider line to title

real outputWidth = 50;      // Output width in cm (≈ coordinate extent)

// ==========================================
// DERIVED POSITIONS — computed from parameters, do not edit
// ==========================================
real yMain  = 0;
real yUpper = yMain + rowDy;
real yLower = yMain - rowDy;

real yDivider   = yUpper + boxHeight/2 + dividerPad;
real yAnnotTop  = yMain + boxHeight/2 + annotPad;
real yAnnotSub  = yAnnotTop - annotLine;
real yBotAnnot1 = yLower - boxHeight/2 - botAnnot;
real yBotAnnot2 = yBotAnnot1 - annotLine;
real yBar       = yLower - boxHeight/2 - barPad;
real yQuote     = yLower - boxHeight/2 - quotePad;
real yTitle     = yDivider + titlePad;

// ==========================================
// COLORS
// ==========================================
pen earlyColor   = rgb(0.90, 0.95, 1.00);  pen earlyBorder   = black + 1.0pt;
pen voyageColor  = rgb(1.00, 0.95, 0.85);  pen voyageBorder  = black + 1.0pt;
pen battleColor  = rgb(1.00, 0.85, 0.85);  pen battleBorder  = black + 1.0pt;
pen tributeColor = rgb(0.85, 1.00, 0.90);  pen tributeBorder = black + 1.0pt;
pen hongxiColor  = rgb(0.95, 0.90, 0.95);  pen hongxiBorder  = black + 1.0pt;
pen xuandeColor  = rgb(1.00, 0.90, 0.80);  pen xuandeBorder  = black + 1.0pt;
pen endColor     = gray(0.90);              pen endBorder     = black + 1.0pt;
// Connector pens: each is color + linewidth + linetype fused, Asymptote idiom.
pen arrowPen     = rgb(0.3, 0.2, 0.1) + linewidth(0.8);
pen lightArrow   = rgb(0.3, 0.2, 0.1) + linewidth(0.6);
pen textPen      = fontsize(9pt);

// ==========================================
// NODE COMPONENT — uses skillutils for label_box_pic
// ==========================================

// Convenience wrapper using global boxWidth/boxHeight/lineDy and textPen
picture box2(pair boxPosition, string[] lines, pen fillPen, pen borderPen) {
    return label_box_pic(boxPosition, boxWidth, boxHeight, lineDy, lines, textPen, fillPen, borderPen);
}
picture box2(pair boxPosition, string text, pen fillPen, pen borderPen) {
    return box2(boxPosition, new string[]{text}, fillPen, borderPen);
}

// ==========================================
// CREATE AND POSITION NODES
// ==========================================

// --- Main timeline (Yongle Reign) ---
picture pOrigin    = box2((xStart,          yMain), new string[]{"Origin", "Yunnan"}, earlyColor, earlyBorder);
picture pService   = box2((xStart + dx,     yMain), new string[]{"Serve", "Prince Yan"}, earlyColor, earlyBorder);
picture pV1        = box2((xStart + 2*dx,   yMain), new string[]{"1st Voyage", "1405-1407"}, voyageColor, voyageBorder);
picture pV1ret     = box2((xStart + 3*dx,   yMain), new string[]{"Return", "Envoys"}, tributeColor, tributeBorder);
picture pV2        = box2((xStart + 4*dx,   yMain), new string[]{"2nd Voyage", "1409-1411"}, voyageColor, voyageBorder);
picture pV2ret     = box2((xStart + 5*dx,   yMain), new string[]{"Return", "Captives"}, battleColor, battleBorder);
picture pV3        = box2((xStart + 6*dx,   yMain), new string[]{"3rd Voyage", "1413-1415"}, voyageColor, voyageBorder);
picture pV3ret     = box2((xStart + 7*dx,   yMain), new string[]{"Return", "1415"}, tributeColor, tributeBorder);
picture pV4        = box2((xStart + 8*dx,   yMain), new string[]{"4th Voyage", "1417-1419"}, tributeColor, tributeBorder);
picture pV5        = box2((xStart + 9*dx,   yMain), new string[]{"5th Voyage", "1421-1422"}, voyageColor, voyageBorder);
picture pV6        = box2((xStart + 10*dx,  yMain), new string[]{"6th Voyage", "1424"}, voyageColor, voyageBorder);

// --- Battle branches (below main) ---
picture pBattle1 = box2((xStart + 3*dx,  yLower), new string[]{"Old Port", "Chen Zuyi"}, battleColor, battleBorder);
picture pBattle2 = box2((xStart + 4*dx,  yLower), new string[]{"Ceylon", "Capture king"}, battleColor, battleBorder);
picture pBattle3 = box2((xStart + 6*dx,  yLower), new string[]{"Samudera", "Victory"}, battleColor, battleBorder);

// --- Transition: Yongle → Hongxi ---
picture pTransition = box2((xStart + 11.5*dx, yMain), new string[]{"1425", "Guard Nanjing"}, hongxiColor, hongxiBorder);

// --- Xuande: 7th Voyage ---
picture pV7        = box2((xStart + 13*dx, yMain),  new string[]{"7th Voyage", "1433"}, xuandeColor, xuandeBorder);
picture pV7detail  = box2((xStart + 13*dx, yUpper), new string[]{"17 States", "Hormuz"}, xuandeColor, xuandeBorder);

// --- Legacy ---
picture pLegacy        = box2((xStart + 15*dx, yMain),  new string[]{"Legacy", "7 Voyages"}, endColor, endBorder);
picture pLegacyDetail  = box2((xStart + 15*dx, yUpper), new string[]{"30+ Countries", "Treasure Fleet"}, endColor, endBorder);

// ==========================================
// ASSEMBLE DIAGRAM
// ==========================================
picture diagram;
size(diagram, outputWidth*cm);

// --- Title ---
label(diagram, "Zheng He: Seven Voyages (1405-1433) — Landscape Timeline",
      (0, yTitle), fontsize(14pt));

// --- Phase dividers ---
label(diagram, "Yongle Reign (1405-1424)", (xStart + 5.5*dx, yDivider + dividerLbl), fontsize(10pt));
draw(diagram, (xStart - 2, yDivider) -- (xStart + 17*dx, yDivider),
     gray(0.5) + linewidth(0.8) + dashed);
label(diagram, "Xuande Reign (1433)", (xStart + 13*dx, yDivider + dividerLbl), fontsize(10pt));

// --- Connectors (added before nodes → render behind nodes) ---
// Each connect_pics(src, srcDir, tgt, tgtDir, gap, pen, arrowbar) returns
// a picture containing just the connector; add() it BEFORE the node pictures
// so arrows render behind the boxes (z-order convention, docs/04 §1 rule 5).

// Main horizontal flow (Yongle → Xuande → Legacy). All consecutive pairs
// share y = yMain, so {E}..{-W=E} tangents collapse to straight horizontal
// lines — visually identical to the original `a -- b` chords.
picture[] mainFlow = new picture[]
    {pOrigin, pService, pV1, pV1ret, pV2, pV2ret,
     pV3, pV3ret, pV4, pV5, pV6, pTransition, pV7, pLegacy};
for (int i = 0; i < mainFlow.length - 1; ++i)
    add(diagram, connect_pics(mainFlow[i], E, mainFlow[i+1], W, gap, arrowPen, Arrow(TeXHead)));

// Branch arrows: main → battles (down). srcDir=S, destDir=N => tangents
// {S}..{-N=S}; aligned x => straight vertical lines.
add(diagram, connect_pics(pV1ret,  S, pBattle1, N, gap, lightArrow, Arrow(TeXHead)));
add(diagram, connect_pics(pV2,     S, pBattle2, N, gap, lightArrow, Arrow(TeXHead)));
add(diagram, connect_pics(pV3,     S, pBattle3, N, gap, lightArrow, Arrow(TeXHead)));

// Branch arrow: battle → main (up). pBattle2 and pV2ret are offset in x;
// {N}..{-S=N} produces a gentle diagonal S-curve (visually smoother than the
// original straight `--` diagonal).
add(diagram, connect_pics(pBattle2, N, pV2ret,       S, gap, lightArrow, Arrow(TeXHead)));

// Detail arrows: main → upper detail (up). Aligned x => straight vertical.
add(diagram, connect_pics(pV7,     N, pV7detail,     S, gap, lightArrow, Arrow(TeXHead)));
add(diagram, connect_pics(pLegacy, N, pLegacyDetail, S, gap, lightArrow, Arrow(TeXHead)));

// --- Add all nodes on top of connectors ---
add(diagram, pOrigin);
add(diagram, pService);
add(diagram, pV1);      add(diagram, pV1ret);
add(diagram, pV2);      add(diagram, pV2ret);
add(diagram, pV3);      add(diagram, pV3ret);
add(diagram, pV4);
add(diagram, pV5);
add(diagram, pV6);
add(diagram, pBattle1); add(diagram, pBattle2); add(diagram, pBattle3);
add(diagram, pTransition);
add(diagram, pV7);      add(diagram, pV7detail);
add(diagram, pLegacy);  add(diagram, pLegacyDetail);

// --- Top annotations (above main row) ---
label(diagram, "Yunnan",       (point(pOrigin, N).x, yAnnotTop), fontsize(7pt));
label(diagram, "Zhu Di",       (point(pService, N).x, yAnnotTop), fontsize(7pt));
label(diagram, "Fleet sails",  (point(pV1, N).x,      yAnnotTop), fontsize(7pt));
label(diagram, "Emperor",      (point(pV1ret, N).x,   yAnnotTop), fontsize(7pt));
label(diagram, "delighted",    (point(pV1ret, N).x,   yAnnotSub), fontsize(7pt));
label(diagram, "Indian",       (point(pV2, N).x,      yAnnotTop), fontsize(7pt));
label(diagram, "Ocean",        (point(pV2, N).x,      yAnnotSub), fontsize(7pt));
label(diagram, "1411",         (point(pV2ret, N).x,   yAnnotTop), fontsize(7pt));
label(diagram, "Sumatra",      (point(pV3, N).x,      yAnnotTop), fontsize(7pt));
label(diagram, "1415",         (point(pV3ret, N).x,   yAnnotTop), fontsize(7pt));
label(diagram, "Malacca",      (point(pV4, N).x,      yAnnotTop), fontsize(7pt));
label(diagram, "Calicut",      (point(pV4, N).x,      yAnnotSub), fontsize(7pt));
label(diagram, "Persian",      (point(pV5, N).x,      yAnnotTop), fontsize(7pt));
label(diagram, "Gulf",         (point(pV5, N).x,      yAnnotSub), fontsize(7pt));
label(diagram, "Bestow",       (point(pV6, N).x,      yAnnotTop), fontsize(7pt));
label(diagram, "seal",         (point(pV6, N).x,      yAnnotSub), fontsize(7pt));
label(diagram, "Nanjing",      (point(pTransition, N).x, yAnnotTop), fontsize(7pt));
label(diagram, "Guard",        (point(pTransition, N).x, yAnnotSub), fontsize(7pt));

// --- Bottom annotations ---
label(diagram, "27,800 men",   (point(pV1, S).x,       yBotAnnot1), fontsize(7pt));
label(diagram, "LiuJia Port",  (point(pV1, S).x,       yBotAnnot2), fontsize(7pt));
label(diagram, "Ceylon king",  (point(pBattle2, S).x,  yBotAnnot1), fontsize(7pt));
label(diagram, "Alagakkonara", (point(pBattle2, S).x,  yBotAnnot2), fontsize(7pt));
label(diagram, "Su Ganla",     (point(pBattle3, S).x,  yBotAnnot1), fontsize(7pt));
label(diagram, "19 states",    (point(pV4, S).x,       yBotAnnot1), fontsize(7pt));
label(diagram, "tribute",      (point(pV4, S).x,       yBotAnnot2), fontsize(7pt));
label(diagram, "Bestow seal",  (point(pV6, S).x,       yBotAnnot1), fontsize(7pt));
label(diagram, "Old Port",     (point(pV6, S).x,       yBotAnnot2), fontsize(7pt));
label(diagram, "Hongxi",       (point(pTransition, S).x, yBotAnnot1), fontsize(7pt));
label(diagram, "Emperor",      (point(pTransition, S).x, yBotAnnot2), fontsize(7pt));
label(diagram, "Final",        (point(pV7, S).x,       yBotAnnot1), fontsize(7pt));
label(diagram, "voyage",       (point(pV7, S).x,       yBotAnnot2), fontsize(7pt));

// --- Bottom quote ---
label(diagram, "\"After Zheng He, all who sailed overseas praised him to foreign lands.\"",
      (0, yQuote), fontsize(9pt));

// --- Dynasty color bar (bottom decorative) ---
fill(diagram, box((xStart-1, yBar), (xStart+11.5*dx, yBar+barH)), voyageColor);
fill(diagram, box((xStart+11.5*dx, yBar), (xStart+13*dx, yBar+barH)), hongxiColor);
fill(diagram, box((xStart+13*dx, yBar), (xStart+15.5*dx, yBar+barH)), xuandeColor);
fill(diagram, box((xStart+15.5*dx, yBar), (xStart+17.5*dx, yBar+barH)), endColor);

shipout(diagram);