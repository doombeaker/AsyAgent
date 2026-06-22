// Example: function plot with axes
import graph;

size(8cm, 5cm, IgnoreAspect);

real f(real x) { return sin(x) * exp(-x/6); }

pair pmin = (-0.5, -0.6);
pair pmax = (12, 1.05);

xaxis(Bottom, pmin.x, pmax.x, Ticks("$x$", Step=2, step=1, beginlabel=false, endlabel=false));
yaxis(Left, pmin.y, pmax.y, Ticks("$y$", Step=0.5));

draw(graph(f, 0, 12, 100), red+linewidth(1.2));
label("$f(x) = \sin(x)\,e^{-x/6}$", (6, 0.8), S);
