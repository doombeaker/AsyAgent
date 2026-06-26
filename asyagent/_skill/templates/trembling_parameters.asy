// ==========================================
// TEMPLATE: Trembling Parameter Comparison
// Demonstrates: angle, frequency, random parameters and their visual effects
// ==========================================
import trembling;

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
size(0, 250);

pen basePen = black + linewidth(0.7);
pen labelPen = black + fontsize(9pt);

real rowSpacing = 3.5;
real colSpacing = 4.5;

// ------------------------------------------
// BASE SHAPE
// ------------------------------------------
pair centerO = (0, 0);
path baseCircle = circle(centerO, 1.2);

// ------------------------------------------
// TREMBLE INSTANCES WITH DIFFERENT PARAMETERS
// ------------------------------------------
// Row 1: varying angle
tremble T_lowAngle = tremble(angle=1, frequency=0.5, random=0);
tremble T_midAngle = tremble(angle=4, frequency=0.5, random=0);
tremble T_highAngle = tremble(angle=8, frequency=0.5, random=0);

// Row 2: varying frequency
tremble T_lowFreq = tremble(angle=4, frequency=0.2, random=0);
tremble T_midFreq = tremble(angle=4, frequency=0.5, random=0);
tremble T_highFreq = tremble(angle=4, frequency=2.0, random=0);

// Row 3: varying random
tremble T_noRandom = tremble(angle=4, frequency=0.5, random=0);
tremble T_midRandom = tremble(angle=4, frequency=0.5, random=2);
tremble T_highRandom = tremble(angle=4, frequency=0.5, random=5);

// ------------------------------------------
// DRAWING
// ------------------------------------------
real labelOffset = 1.6;

// Row 1: angle comparison (y = 2*rowSpacing)
label("angle=1", (-colSpacing, 2*rowSpacing + labelOffset), N, labelPen);
label("angle=4", (0, 2*rowSpacing + labelOffset), N, labelPen);
label("angle=8", (colSpacing, 2*rowSpacing + labelOffset), N, labelPen);
label("angle", (-2.3*colSpacing, 2*rowSpacing), E, labelPen);

draw(shift((-colSpacing, 2*rowSpacing)) * T_lowAngle.deform(baseCircle), basePen);
draw(shift((0, 2*rowSpacing)) * T_midAngle.deform(baseCircle), basePen);
draw(shift((colSpacing, 2*rowSpacing)) * T_highAngle.deform(baseCircle), basePen);

// Row 2: frequency comparison (y = 0)
label("freq=0.2", (-colSpacing, labelOffset), N, labelPen);
label("freq=0.5", (0, labelOffset), N, labelPen);
label("freq=2.0", (colSpacing, labelOffset), N, labelPen);
label("frequency", (-2.3*colSpacing, 0), E, labelPen);

draw(shift((-colSpacing, 0)) * T_lowFreq.deform(baseCircle), basePen);
draw(shift((0, 0)) * T_midFreq.deform(baseCircle), basePen);
draw(shift((colSpacing, 0)) * T_highFreq.deform(baseCircle), basePen);

// Row 3: random comparison (y = -2*rowSpacing)
label("random=0", (-colSpacing, -2*rowSpacing + labelOffset), N, labelPen);
label("random=2", (0, -2*rowSpacing + labelOffset), N, labelPen);
label("random=5", (colSpacing, -2*rowSpacing + labelOffset), N, labelPen);
label("random", (-2.3*colSpacing, -2*rowSpacing), E, labelPen);

draw(shift((-colSpacing, -2*rowSpacing)) * T_noRandom.deform(baseCircle), basePen);
draw(shift((0, -2*rowSpacing)) * T_midRandom.deform(baseCircle), basePen);
draw(shift((colSpacing, -2*rowSpacing)) * T_highRandom.deform(baseCircle), basePen);
