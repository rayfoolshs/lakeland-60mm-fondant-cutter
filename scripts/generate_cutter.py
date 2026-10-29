from __future__ import annotations

import math
import zipfile
from pathlib import Path

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import Circle, PathPatch, Polygon as MplPolygon, Rectangle
from matplotlib.path import Path as MplPath
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from shapely.affinity import scale as shapely_scale, translate
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely.validation import make_valid

DXF_PATH = Path(__file__).resolve().parent.parent / "source" / "Lakeland - Transparent (1).dxf"
OUT_DIR = Path(__file__).resolve().parent.parent

CUT_DIAMETER = 60.0
CUT_RADIUS = CUT_DIAMETER / 2.0
WALL = 1.8
FLANGE_WIDTH = 4.0
HEIGHT = 18.0
FLANGE_TOP = 18.0
FLANGE_BOTTOM = 15.0
PLATE_BOTTOM = 10.0
PLATE_TOP = 12.0
PLATE_RADIUS = CUT_RADIUS + 0.2
FEATURE_TOP = PLATE_BOTTOM + 0.2
FIT_RADIUS = 27.75
BIRD_FACE_Z = 1.5
GREEN_FACE_Z = 2.0
GROOVE_FLOOR_Z = 2.0
LIME_FACE_Z = 2.5
BIRD_BUFFER = 0.25
DETAIL_BUFFER = 0.25
GROOVE_OVERLAP = 0.02
SIMPLIFY = 0.02
MIN_PIECE_AREA = 0.05
SECTIONS = 192


def largest_polygon(geom):
    if geom.is_empty:
        return geom
    if geom.geom_type == "Polygon":
        return geom
    if geom.geom_type == "MultiPolygon":
        return max(geom.geoms, key=lambda g: g.area)
    if geom.geom_type == "GeometryCollection":
        polys = [g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        if not polys:
            return Polygon()
        merged = unary_union(polys)
        return largest_polygon(merged)
    return Polygon()


def clean(geom):
    if geom.is_empty:
        return geom
    if not geom.is_valid:
        geom = make_valid(geom)
    return geom


def filter_pieces(geom, min_area=MIN_PIECE_AREA):
    geom = clean(geom)
    if geom.is_empty:
        return geom
    if geom.geom_type == "Polygon":
        return geom if geom.area >= min_area else Polygon()
    if geom.geom_type == "MultiPolygon":
        pieces = [g for g in geom.geoms if g.area >= min_area]
        if not pieces:
            return Polygon()
        return unary_union(pieces)
    if geom.geom_type == "GeometryCollection":
        pieces = []
        for g in geom.geoms:
            if g.geom_type == "Polygon" and g.area >= min_area:
                pieces.append(g)
            elif g.geom_type == "MultiPolygon":
                pieces.extend([p for p in g.geoms if p.area >= min_area])
        if not pieces:
            return Polygon()
        return unary_union(pieces)
    return Polygon()


def load_regions(dxf_path: Path):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    raw = []
    for entity in msp.query("LWPOLYLINE"):
        pts = [(float(x), float(y)) for x, y in entity.get_points("xy")]
        if len(pts) < 3:
            continue
        poly = largest_polygon(clean(Polygon(pts)))
        if poly.is_empty or poly.area <= 0:
            continue
        raw.append({"layer": entity.dxf.layer.strip(), "poly": poly, "pts": pts})

    emblem = [p for p in raw if max(y for x, y in p["pts"]) > 60.0]
    navy = [p for p in emblem if p["layer"] == "NAVY"]
    bird = max(navy, key=lambda p: p["poly"].area)
    details = unary_union([p["poly"] for p in navy if p is not bird])
    green = unary_union([p["poly"] for p in emblem if p["layer"] == "GREEN"])
    lime = unary_union([p["poly"] for p in emblem if p["layer"] == "LIME"])

    xs = [x for p in emblem for x, y in p["pts"]]
    ys = [y for p in emblem for x, y in p["pts"]]
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0
    max_radius = max(math.hypot(x - cx, y - cy) for x, y in zip(xs, ys))
    scale = FIT_RADIUS / max_radius

    def transform(geom):
        return translate(
            shapely_scale(geom, xfact=scale, yfact=scale, origin=(0, 0)),
            xoff=-cx * scale,
            yoff=-cy * scale,
        )

    bird_s = transform(bird["poly"])
    details_s = transform(details)
    green_s = transform(green)
    lime_s = transform(lime)

    bird_b = clean(bird_s.buffer(BIRD_BUFFER, join_style=2, mitre_limit=3)).simplify(
        SIMPLIFY, preserve_topology=True
    )
    details_b = clean(
        details_s.buffer(DETAIL_BUFFER, join_style=2, mitre_limit=3).intersection(bird_b)
    ).simplify(SIMPLIFY, preserve_topology=True)
    bird_face = clean(bird_b.difference(details_b)).simplify(SIMPLIFY, preserve_topology=True)
    green_clean = filter_pieces(green_s.difference(bird_b).simplify(SIMPLIFY, preserve_topology=True))
    lime_clean = filter_pieces(
        lime_s.difference(green_s).difference(bird_b).simplify(SIMPLIFY, preserve_topology=True)
    )

    region_info = {
        "emblem_polylines": len(emblem),
        "bird_area_dxf": bird["poly"].area,
        "details_area_dxf": details.area,
        "green_area_dxf": green.area,
        "lime_area_dxf": lime.area,
        "dxf_bbox_mm": [min(xs), min(ys), max(xs), max(ys)],
        "fit_scale": scale,
        "scaled_bbox_mm": [
            (max(xs) - min(xs)) * scale,
            (max(ys) - min(ys)) * scale,
        ],
        "bird_face_area_mm2": bird_face.area,
        "groove_area_mm2": details_b.area,
        "green_area_mm2": green_clean.area,
        "lime_area_mm2": lime_clean.area,
        "bird_bounds_mm": bird_b.bounds,
        "bird_max_radius_mm": max(math.hypot(x, y) for x, y in bird_b.exterior.coords),
        "ring_clearance_mm": CUT_RADIUS - max(math.hypot(x, y) for x, y in bird_b.exterior.coords),
    }
    return {
        "bird_face": bird_face,
        "groove": details_b,
        "green": green_clean,
        "lime": lime_clean,
        "bird_b": bird_b,
        "info": region_info,
    }


def extrude_geometry(geom, z0, z1):
    if geom.is_empty:
        return []
    if geom.geom_type == "GeometryCollection":
        pieces = []
        for g in geom.geoms:
            pieces.extend(extrude_geometry(g, z0, z1))
        return pieces
    if geom.geom_type == "MultiPolygon":
        pieces = []
        for g in geom.geoms:
            pieces.extend(extrude_geometry(g, z0, z1))
        return pieces
    if geom.geom_type != "Polygon":
        return []
    g = orient(clean(geom), sign=1.0)
    if g.is_empty or g.area < 1e-6:
        return []
    mesh = trimesh.creation.extrude_polygon(g, height=z1 - z0)
    mesh.apply_translation([0.0, 0.0, z0])
    return [mesh]


def build_mesh(regions):
    profile = np.array(
        [
            (CUT_RADIUS, 0.0),
            (CUT_RADIUS + 0.4, 0.0),
            (CUT_RADIUS + WALL, 1.4),
            (CUT_RADIUS + WALL, FLANGE_BOTTOM),
            (CUT_RADIUS + WALL + FLANGE_WIDTH, FLANGE_BOTTOM),
            (CUT_RADIUS + WALL + FLANGE_WIDTH, FLANGE_TOP),
            (CUT_RADIUS, FLANGE_TOP),
            (CUT_RADIUS, 0.0),
        ],
        dtype=float,
    )
    ring = trimesh.creation.revolve(profile, sections=SECTIONS)
    plate = trimesh.creation.cylinder(
        radius=PLATE_RADIUS,
        height=PLATE_TOP - PLATE_BOTTOM,
        sections=SECTIONS,
    )
    plate.apply_translation([0.0, 0.0, (PLATE_BOTTOM + PLATE_TOP) / 2.0])

    bird_meshes = extrude_geometry(regions["bird_face"], BIRD_FACE_Z, FEATURE_TOP)
    groove_meshes = extrude_geometry(
        regions["groove"].buffer(GROOVE_OVERLAP, join_style=2), GROOVE_FLOOR_Z, FEATURE_TOP
    )
    green_meshes = extrude_geometry(regions["green"], GREEN_FACE_Z, FEATURE_TOP)
    lime_meshes = extrude_geometry(regions["lime"], LIME_FACE_Z, FEATURE_TOP)

    parts = [ring, plate] + bird_meshes + groove_meshes + green_meshes + lime_meshes
    mesh = trimesh.boolean.union(parts, engine="manifold")
    vents = []
    for angle_deg in (45.0, 225.0):
        angle = math.radians(angle_deg)
        vent = trimesh.creation.cylinder(radius=0.4, height=4.0, sections=32)
        vent.apply_translation([29.0 * math.cos(angle), 29.0 * math.sin(angle), 11.0])
        vents.append(vent)
    mesh = trimesh.boolean.difference([mesh] + vents, engine="manifold")
    mesh.merge_vertices()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals()
    return mesh


def transform_to_print(mesh):
    transform = trimesh.transformations.rotation_matrix(math.pi, [1.0, 0.0, 0.0])
    printed = mesh.copy()
    printed.apply_transform(transform)
    printed.apply_translation([0.0, 0.0, -printed.bounds[0][2]])
    return printed


def write_3mf(mesh, path: Path):
    vertices = mesh.vertices
    faces = mesh.faces
    vertex_lines = []
    for x, y, z in vertices:
        vertex_lines.append(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>')
    face_lines = []
    for a, b, c in faces:
        face_lines.append(f'<triangle v1="{int(a)}" v2="{int(b)}" v3="{int(c)}"/>')
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
        '  <metadata name="Title">Lakeland 60 mm Fondant Cutter</metadata>\n'
        '  <metadata name="Designer">OpenCode</metadata>\n'
        '  <resources>\n'
        '    <object id="1" type="model">\n'
        '      <mesh>\n'
        '        <vertices>\n          '
        + "\n          ".join(vertex_lines)
        + "\n        </vertices>\n"
        '        <triangles>\n          '
        + "\n          ".join(face_lines)
        + "\n        </triangles>\n"
        '      </mesh>\n'
        '    </object>\n'
        '  </resources>\n'
        '  <build>\n'
        '    <item objectid="1"/>\n'
        '  </build>\n'
        '</model>\n'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '  <Default Extension="model" '
        'ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
        '</Types>\n'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '  <Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
        '</Relationships>\n'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("3D/3dmodel.model", model)


def draw_geometry(ax, geom, color, alpha=1.0, zorder=1):
    if geom.is_empty:
        return
    if geom.geom_type == "GeometryCollection":
        for g in geom.geoms:
            draw_geometry(ax, g, color, alpha, zorder)
        return
    if geom.geom_type == "MultiPolygon":
        for g in geom.geoms:
            draw_geometry(ax, g, color, alpha, zorder)
        return
    if geom.geom_type != "Polygon":
        return
    verts = list(geom.exterior.coords)
    codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(verts) - 2) + [MplPath.CLOSEPOLY]
    for interior in geom.interiors:
        iv = list(interior.coords)
        verts += iv
        codes += [MplPath.MOVETO] + [MplPath.LINETO] * (len(iv) - 2) + [MplPath.CLOSEPOLY]
    ax.add_patch(
        PathPatch(
            MplPath(verts, codes),
            facecolor=color,
            edgecolor="none",
            alpha=alpha,
            zorder=zorder,
        )
    )


def draw_cross_section(ax):
    ring_profile = [
        (CUT_RADIUS, 0.0),
        (CUT_RADIUS + 0.4, 0.0),
        (CUT_RADIUS + WALL, 1.4),
        (CUT_RADIUS + WALL, FLANGE_BOTTOM),
        (CUT_RADIUS + WALL + FLANGE_WIDTH, FLANGE_BOTTOM),
        (CUT_RADIUS + WALL + FLANGE_WIDTH, FLANGE_TOP),
        (CUT_RADIUS, FLANGE_TOP),
    ]
    material_color = "#9bb7c9"
    feature_color = "#27346b"
    green_color = "#2b8a4b"
    lime_color = "#b9d84a"
    for side in (-1.0, 1.0):
        pts = [(side * r, z) for r, z in ring_profile]
        pts += [(side * CUT_RADIUS, 0.0)]
        ax.add_patch(MplPolygon(pts, closed=True, facecolor=material_color, edgecolor="#40515c", linewidth=0.8, zorder=3))
    ax.add_patch(
        Rectangle(
            (-PLATE_RADIUS, PLATE_BOTTOM),
            2 * PLATE_RADIUS,
            PLATE_TOP - PLATE_BOTTOM,
            facecolor=material_color,
            edgecolor="#40515c",
            linewidth=0.8,
            zorder=3,
        )
    )
    ax.add_patch(
        Rectangle(
            (-CUT_RADIUS, 0.0),
            2 * CUT_RADIUS,
            3.0,
            facecolor="#e8c98f",
            edgecolor="none",
            alpha=0.55,
            zorder=1,
        )
    )
    ax.add_patch(Rectangle((-10.0, BIRD_FACE_Z), 20.0, FEATURE_TOP - BIRD_FACE_Z, facecolor=feature_color, edgecolor="none", zorder=4))
    ax.add_patch(Rectangle((-22.0, GREEN_FACE_Z), 12.0, FEATURE_TOP - GREEN_FACE_Z, facecolor=green_color, edgecolor="none", zorder=4))
    ax.add_patch(Rectangle((10.0, GREEN_FACE_Z), 12.0, FEATURE_TOP - GREEN_FACE_Z, facecolor=green_color, edgecolor="none", zorder=4))
    ax.add_patch(Rectangle((-28.0, LIME_FACE_Z), 6.0, FEATURE_TOP - LIME_FACE_Z, facecolor=lime_color, edgecolor="none", zorder=4))
    ax.add_patch(Rectangle((22.0, LIME_FACE_Z), 6.0, FEATURE_TOP - LIME_FACE_Z, facecolor=lime_color, edgecolor="none", zorder=4))

    ax.annotate(
        "",
        xy=(-CUT_RADIUS, -2.2),
        xytext=(CUT_RADIUS, -2.2),
        arrowprops={"arrowstyle": "<->", "color": "#222", "lw": 1.0},
        zorder=5,
    )
    ax.text(0.0, -3.2, "60 mm cut diameter", ha="center", va="top", fontsize=8)
    ax.annotate(
        "",
        xy=(CUT_RADIUS + WALL + 1.5, 0.0),
        xytext=(CUT_RADIUS + WALL + 1.5, HEIGHT),
        arrowprops={"arrowstyle": "<->", "color": "#222", "lw": 1.0},
        zorder=5,
    )
    ax.text(CUT_RADIUS + WALL + 2.0, HEIGHT / 2.0, "18 mm", va="center", fontsize=8, rotation=90)
    ax.annotate(
        "1.5 mm emboss",
        xy=(5.0, BIRD_FACE_Z),
        xytext=(-17.0, 4.9),
        arrowprops={"arrowstyle": "->", "color": "#8a2d1f", "lw": 1.0},
        fontsize=7,
        color="#8a2d1f",
        va="center",
        zorder=6,
        bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "none", "alpha": 0.85},
    )
    ax.text(
        -27.0,
        1.5,
        "3 mm fondant",
        ha="center",
        va="center",
        fontsize=7,
        color="#6b4f1d",
        zorder=6,
        bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "none", "alpha": 0.85},
    )
    ax.set_xlim(-38.0, 42.0)
    ax.set_ylim(-4.0, 20.0)
    ax.set_aspect("equal")
    ax.set_title("Schematic cross-section (not to scale)", fontsize=9)
    ax.set_xlabel("radius (mm)")
    ax.set_ylabel("height (mm)")
    ax.grid(True, alpha=0.2)


def render_preview(regions, print_mesh, path: Path):
    fig = plt.figure(figsize=(16, 10))
    grid = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.8], hspace=0.25, wspace=0.15)

    ax_logo = fig.add_subplot(grid[0, 0])
    ax_logo.set_aspect("equal")
    ax_logo.add_patch(Circle((0.0, 0.0), CUT_RADIUS, fill=False, edgecolor="#222", linewidth=1.1, linestyle="--", zorder=10))
    ax_logo.add_patch(Circle((0.0, 0.0), FIT_RADIUS, fill=False, edgecolor="#888", linewidth=0.6, linestyle=":", zorder=10))
    draw_geometry(ax_logo, regions["bird_b"], "#27346b", 1.0, 2)
    draw_geometry(ax_logo, regions["groove"], "#5d6fae", 1.0, 3)
    draw_geometry(ax_logo, regions["green"], "#2b8a4b", 1.0, 4)
    draw_geometry(ax_logo, regions["lime"], "#b9d84a", 1.0, 5)
    ax_logo.set_xlim(-34.0, 34.0)
    ax_logo.set_ylim(-34.0, 34.0)
    ax_logo.grid(True, alpha=0.2)
    ax_logo.set_title("Emblem regions and 60 mm cutting circle", fontsize=9)

    ax_3d = fig.add_subplot(grid[0, 1], projection="3d")
    vertices = print_mesh.vertices
    faces = print_mesh.faces
    triangles = vertices[faces]
    edge_a = triangles[:, 1] - triangles[:, 0]
    edge_b = triangles[:, 2] - triangles[:, 0]
    normals = np.cross(edge_a, edge_b)
    normals = np.nan_to_num(normals, nan=0.0, posinf=0.0, neginf=0.0)
    norms = np.linalg.norm(normals, axis=1)
    valid_normals = norms > 1e-12
    normals[valid_normals] /= norms[valid_normals, None]
    centroids = triangles.mean(axis=1)
    radii = np.linalg.norm(centroids[:, :2], axis=1)
    logo_faces = (radii < 28.6) & (centroids[:, 2] > 8.1) & (centroids[:, 2] < 17.5)
    light = np.array([0.35, -0.45, 0.82])
    light = light / np.linalg.norm(light)
    dot = normals[:, 0] * light[0] + normals[:, 1] * light[1] + normals[:, 2] * light[2]
    dot = np.nan_to_num(dot, nan=0.0, posinf=0.0, neginf=0.0)
    shade = 0.38 + 0.62 * np.clip(np.abs(dot), 0.0, 1.0)
    base = np.tile(np.array([0.50, 0.68, 0.79]), (len(faces), 1))
    base[logo_faces] = np.array([0.12, 0.26, 0.46])
    colors = np.clip(base * shade[:, None], 0.0, 1.0)
    collection = Poly3DCollection(triangles, facecolors=colors, linewidths=0.0, alpha=1.0)
    ax_3d.add_collection3d(collection)
    ax_3d.set_xlim(-37.0, 37.0)
    ax_3d.set_ylim(-37.0, 37.0)
    ax_3d.set_zlim(0.0, 20.0)
    ax_3d.set_box_aspect((1.0, 1.0, 0.5))
    ax_3d.view_init(elev=52.0, azim=-58.0)
    ax_3d.set_axis_off()
    ax_3d.set_title("Print orientation: flange on bed, logo faces up", fontsize=9)

    ax_section = fig.add_subplot(grid[1, :])
    draw_cross_section(ax_section)

    fig.suptitle("Lakeland 60 mm fondant cutter / embosser", fontsize=13)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    regions = load_regions(DXF_PATH)
    mesh = build_mesh(regions)
    print_mesh = transform_to_print(mesh)

    stl_design = OUT_DIR / "lakeland_60mm_fondant_cutter.stl"
    stl_print = OUT_DIR / "lakeland_60mm_fondant_cutter_print.stl"
    threemf_print = OUT_DIR / "lakeland_60mm_fondant_cutter_print.3mf"
    preview_path = OUT_DIR / "preview.png"

    mesh.export(stl_design, file_type="stl")
    print_mesh.export(stl_print, file_type="stl")
    write_3mf(print_mesh, threemf_print)

    report = {
        "dxf": str(DXF_PATH),
        "cut_diameter_mm": CUT_DIAMETER,
        "outer_diameter_mm": 2.0 * (CUT_RADIUS + WALL + FLANGE_WIDTH),
        "height_mm": HEIGHT,
        "wall_mm": WALL,
        "flange_width_mm": FLANGE_WIDTH,
        "plate_bottom_mm": PLATE_BOTTOM,
        "plate_top_mm": PLATE_TOP,
        "feature_top_mm": FEATURE_TOP,
        "emboss_bird_mm": 3.0 - BIRD_FACE_Z,
        "emboss_green_mm": 3.0 - GREEN_FACE_Z,
        "emboss_lime_mm": 3.0 - LIME_FACE_Z,
        "watertight_design": bool(mesh.is_watertight),
        "watertight_print": bool(print_mesh.is_watertight),
        "winding_consistent_design": bool(mesh.is_winding_consistent),
        "winding_consistent_print": bool(print_mesh.is_winding_consistent),
        "volume_mm3": float(mesh.volume),
        "bounds_design_mm": mesh.bounds.tolist(),
        "bounds_print_mm": print_mesh.bounds.tolist(),
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "regions": regions["info"],
        "files": {
            "stl_design": str(stl_design),
            "stl_print": str(stl_print),
            "3mf_print": str(threemf_print),
            "preview": str(preview_path),
        },
    }

    report_path = OUT_DIR / "generation_report.txt"
    lines = []
    for key, value in report.items():
        if key == "regions":
            lines.append("regions:")
            for rk, rv in value.items():
                lines.append(f"  {rk}: {rv}")
        elif key == "files":
            lines.append("files:")
            for fk, fv in value.items():
                lines.append(f"  {fk}: {fv}")
        elif key in ("bounds_design_mm", "bounds_print_mm"):
            lines.append(f"{key}:")
            for row in value:
                lines.append(f"  {row}")
        else:
            lines.append(f"{key}: {value}")
    report_path.write_text("\n".join(lines) + "\n")

    render_preview(regions, print_mesh, preview_path)

    for path in (stl_design, stl_print, threemf_print, preview_path, report_path):
        print(f"{path}  {path.stat().st_size / 1024.0:.1f} KiB")
    print(f"watertight design: {mesh.is_watertight}")
    print(f"watertight print: {print_mesh.is_watertight}")
    print(f"volume: {mesh.volume:.1f} mm3")
    print(f"design bounds: {mesh.bounds.tolist()}")
    print(f"print bounds: {print_mesh.bounds.tolist()}")
    print(f"bird max radius: {regions['info']['bird_max_radius_mm']:.3f} mm")
    print(f"ring clearance: {regions['info']['ring_clearance_mm']:.3f} mm")


if __name__ == "__main__":
    main()
