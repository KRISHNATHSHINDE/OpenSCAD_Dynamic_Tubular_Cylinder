
module dynamic_hepta_tubular_cylinder(outer_d, inner_d, length, max_holes, gap) {
    difference() {
        cylinder(d=outer_d, h=length, $fn=100);
        translate([0, 0, -1])
            cylinder(d=inner_d, h=length + 2, $fn=100);
        place_holes(outer_d, inner_d, length, min(max_holes, 8));
        num_peripheries = ceil(max_holes / 8);
        for (j = [1 : num_peripheries - 1]) {
            d_inner = outer_d - 2 * (inner_d + gap) * j;
            if (d_inner > inner_d) {
                place_holes(d_inner, inner_d, length, min(max_holes - 8 * j, 8));
            }
        }
    }
}

module place_holes(d, inner_d, h, num_holes) {
    angle = 360 / num_holes;
    for (i = [0 : num_holes - 1]) {
        x = (d / 2 - (inner_d + gap) / 2 - 1) * cos(i * angle);
        y = (d / 2 - (inner_d + gap) / 2 - 1) * sin(i * angle);
        translate([x, y, -1])
            cylinder(d=inner_d, h=h + 2, $fn=100);
    }
}

outer_d = 100.0;
inner_d = 12.0;
length = 112.0;
max_holes = 12;

num_peripheries = ceil(max_holes / 8);
total_diameter_covered = inner_d * (2 * num_peripheries + 1);
remaining_diameter = outer_d - total_diameter_covered;
num_gaps = num_peripheries * 2 + 2;
gap = ceil(remaining_diameter / num_gaps);

dynamic_hepta_tubular_cylinder(outer_d, inner_d, length, max_holes, gap);
