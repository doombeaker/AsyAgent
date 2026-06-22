// Example: multi-shipout — produces TWO output files (bundled as ZIP by default)
size(4cm);

draw(unitcircle, blue);
label("$c=1$", (0,0));
shipout("page1");

draw(unitsquare, red);
label("$s=1$", (0,0));
shipout("page2");
