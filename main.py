import os
import math
import numpy as np
from flask import Flask, request, send_file, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from stl import mesh
import subprocess

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'stl'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def generate_scad_code(file_path, outer_d, inner_d, length, max_holes):
    num_peripheries = math.ceil(max_holes / 8)
    total_diameter_covered = inner_d * (2 * num_peripheries + 1)
    remaining_diameter = outer_d - total_diameter_covered
    num_gaps = num_peripheries * 2 + 2
    gap = math.ceil(remaining_diameter / num_gaps)

    scad_code = f"""
module dynamic_hepta_tubular_cylinder(outer_d, inner_d, length, max_holes, gap) {{
    difference() {{
        cylinder(d=outer_d, h=length, $fn=100);
        translate([0, 0, -1])
            cylinder(d=inner_d, h=length + 2, $fn=100);
        place_holes(outer_d, inner_d, length, min(max_holes, 8));
        num_peripheries = ceil(max_holes / 8);
        for (j = [1 : num_peripheries - 1]) {{
            d_inner = outer_d - 2 * (inner_d + gap) * j;
            if (d_inner > inner_d) {{
                place_holes(d_inner, inner_d, length, min(max_holes - 8 * j, 8));
            }}
        }}
    }}
}}

module place_holes(d, inner_d, h, num_holes) {{
    angle = 360 / num_holes;
    for (i = [0 : num_holes - 1]) {{
        x = (d / 2 - (inner_d + gap) / 2 - 1) * cos(i * angle);
        y = (d / 2 - (inner_d + gap) / 2 - 1) * sin(i * angle);
        translate([x, y, -1])
            cylinder(d=inner_d, h=h + 2, $fn=100);
    }}
}}

outer_d = {outer_d};
inner_d = {inner_d};
length = {length};
max_holes = {max_holes};

num_peripheries = ceil(max_holes / 8);
total_diameter_covered = inner_d * (2 * num_peripheries + 1);
remaining_diameter = outer_d - total_diameter_covered;
num_gaps = num_peripheries * 2 + 2;
gap = ceil(remaining_diameter / num_gaps);

dynamic_hepta_tubular_cylinder(outer_d, inner_d, length, max_holes, gap);
"""
    with open(file_path, 'w') as f:
        f.write(scad_code)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    outer_d = float(request.form['outer_d'])
    inner_d = float(request.form['inner_d'])
    length = float(request.form['length'])
    max_holes = int(request.form['max_holes'])

    scad_file = 'dynamic_hepta_tubular_cylinder.scad'
    stl_file = 'dynamic_hepta_tubular_cylinder.stl'
    scad_file_path = os.path.join(app.config['UPLOAD_FOLDER'], scad_file)
    stl_file_path = os.path.join(app.config['UPLOAD_FOLDER'], stl_file)

    generate_scad_code(scad_file_path, outer_d, inner_d, length, max_holes)

    subprocess.run(['openscad', '-o', stl_file_path,
                   scad_file_path], check=True)

    return render_template('download.html', scad_file=scad_file, stl_file=stl_file)


@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)


@app.route('/view_stl')
def view_stl():
    filename = 'dynamic_hepta_tubular_cylinder.stl'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return "STL file not found", 404

    # Load the STL file
    your_mesh = mesh.Mesh.from_file(filepath)

    # Bounding Box Dimensions
    minx = your_mesh.x.min()
    maxx = your_mesh.x.max()
    miny = your_mesh.y.min()
    maxy = your_mesh.y.max()
    minz = your_mesh.z.min()
    maxz = your_mesh.z.max()

    x_dim = maxx - minx
    y_dim = maxy - miny
    z_dim = maxz - minz

    # Surface Area Calculation
    def calculate_surface_area(stl_mesh):
        triangles = stl_mesh.vectors
        a = triangles[:, 1] - triangles[:, 0]
        b = triangles[:, 2] - triangles[:, 0]
        cross_product = np.cross(a, b)
        area = np.linalg.norm(cross_product, axis=1) / 2
        return np.sum(area)

    # Volume Calculation
    def calculate_volume(stl_mesh):
        triangles = stl_mesh.vectors
        a = triangles[:, 0]
        b = triangles[:, 1]
        c = triangles[:, 2]
        volume = np.abs(np.einsum('ij,ij->i', a, np.cross(b, c))) / 6
        return np.sum(volume)

    surface_area = calculate_surface_area(your_mesh)
    volume = calculate_volume(your_mesh)

    return render_template('result.html', x_dim=x_dim, y_dim=y_dim, z_dim=z_dim, surface_area=surface_area, volume=volume, filename=filename)


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, port=5001)
