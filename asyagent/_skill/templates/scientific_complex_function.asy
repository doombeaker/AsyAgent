// ==========================================
// TEMPLATE: Complex Function Plot (Gamma Function)
// Demonstrates: discontinuous functions, axis limits, branch handling, labels
// ==========================================
import graph;

// ------------------------------------------
// CONFIGURATION
// ------------------------------------------
size(300, 200, IgnoreAspect);

real xMin = -4;
real xMax = 4;
real yMin = -6;
real yMax = 6;

pen curvePen = red + linewidth(0.9);
pen axisPen  = black + linewidth(0.6);

// ------------------------------------------
// BRANCH HANDLER
// ------------------------------------------
// Gamma function has poles at non-positive integers.
// This handler breaks the graph at those discontinuities.
bool3 branch(real x) {
    static int lastSign = 0;
    if (x <= 0 && x == floor(x)) return false;  // pole
    int sign = sgn(gamma(x));
    bool sameBranch = (lastSign == 0) || (sign == lastSign);
    lastSign = sign;
    return sameBranch ? true : default;
}

// ------------------------------------------
// DRAWING
// ------------------------------------------
// Plot Gamma function with branch handling
draw(graph(gamma, xMin, xMax, n=2000, branch), curvePen);

// Set axis limits and crop
crop();

// Axes with tick marks
xaxis("$x$", axisPen, RightTicks(NoZero));
yaxis("$y$", axisPen, LeftTicks(NoZero));

// Function label
label("$\Gamma(x)$", (1, 2), red);
