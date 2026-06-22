// Example: unit circle with angle annotation
size(6cm);

pair O = (0,0);
real r = 2;

path circ = circle(O, r);
pair A = r * dir(0);
pair B = r * dir(55);

fill(O--arc(O, r, 0, 55)--cycle, paleblue + opacity(0.5));
draw(circ, blue + linewidth(1));
draw(O--A, arrow=Arrow(TeXHead));
draw(O--B, arrow=Arrow(TeXHead));

label("$O$", O, SW);
label("$A$", A, E);
label("$B$", B, NE);
label("$r$", (A+O)/2, S);
label("$\theta$", (0.8, 0.27), E);

dot(O); dot(A); dot(B);
