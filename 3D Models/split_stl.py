#!/usr/bin/env python3
"""
split_stl.py — Scale a massive STL to a target size, cut it into a 3D grid
of bed-sized pieces, and add cylindrical alignment pins + sockets across
every internal cut face so the pieces key together before gluing.

Approach
--------
1.  Load + repair the mesh so it is a single watertight solid (required for
    both the cutting and the boolean pin/socket operations).
2.  Non-uniformly scale it so its bounding box matches your target X/Y/Z.
3.  Work out the smallest N x N x N grid whose cells are no larger than
    `--max-size` MINUS a safety margin that's reserved for the pins
    themselves (so a piece with a pin sticking out of it still fits the bed).
4.  Cut every grid cell out of the mesh with six axis-aligned half-space
    slices (trimesh's own plane-slice + cap — no external CAD kernel needed
    for this step, so it's fast and robust on non-trivial meshes).
5.  For every pair of grid-adjacent pieces, find the real cross-section of
    material at their shared cut plane (not just the theoretical grid
    square — organic/irregular shapes rarely fill the whole cell), shrink
    it inward for wall thickness, and drop 1-4 cylindrical pins in the
    space that's actually solid on both sides. One piece gets a raised peg,
    its neighbour gets a matching blind socket (radius + clearance).
6.  Boolean-union the pegs on, boolean-difference the sockets in
    (via the `manifold3d` backend — fast, dependency-free, no Blender/OpenSCAD
    install required), re-zero each piece to (0,0,0), and export.
7.  Everything is written into a ZIP: one STL per part, a manifest.csv with
    exact dimensions, and a README with reassembly notes.

Install
-------
    pip install trimesh numpy scipy shapely manifold3d networkx

Usage
-----
    python split_stl.py model.stl \\
        --target 646.68 442.27 1700.0 \\
        --max-size 175 \\
        --pins \\
        --out model_split.zip

Run `python split_stl.py --help` for every knob.
"""

import argparse
import io
import sys
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import trimesh
import trimesh.creation as creation
from shapely.geometry import Polygon
from shapely.ops import unary_union

AXES = (0, 1, 2)
AXIS_NAMES = ("X", "Y", "Z")


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
@dataclass
class Config:
    target: tuple = (646.68, 442.27, 1700.0)   # final assembled size, mm
    max_size: float = 175.0                     # hard limit per axis, mm (bed/gantry)
    pins: bool = True                            # add peg/socket joints
    pin_radius: float = 3.0                      # mm
    pin_protrusion: float = 4.0                  # how far the peg sticks out, mm
    pin_embed: float = 6.0                       # how far the peg is buried in its own piece, mm
    pin_clearance: float = 0.25                  # radial clearance in the socket, mm (printer-dependent)
    pin_wall_margin: float = 3.0                 # keep pins this far from the piece's outer skin, mm
    pin_max_per_face: int = 3                    # cap pins per interface so small faces don't get crowded
    pin_min_spacing: float = 12.0                # minimum distance between pins on the same face, mm
    min_piece_faces: int = 4                     # discard slivers with fewer triangles than this


# --------------------------------------------------------------------------
# Mesh loading / repair / scaling
# --------------------------------------------------------------------------
def load_and_repair(path: str) -> trimesh.Trimesh:
    mesh = trimesh.load(path, process=True, force="mesh")
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(mesh.dump())

    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.merge_vertices()
    trimesh.repair.fix_winding(mesh)
    trimesh.repair.fix_normals(mesh)
    trimesh.repair.fill_holes(mesh)

    if not mesh.is_watertight:
        print(
            "WARNING: mesh is not fully watertight after repair — cuts and "
            "pin booleans may fail on a few cells. Consider repairing the "
            "STL in a tool like Meshmixer/Blender first.",
            file=sys.stderr,
        )
    return mesh


def scale_to_target(mesh: trimesh.Trimesh, target) -> trimesh.Trimesh:
    m = mesh.copy()
    m.apply_translation(-m.bounds[0])
    extents = m.extents
    if np.any(extents <= 0):
        raise ValueError("Model has zero size on at least one axis — check the source file.")
    factors = np.array(target, dtype=float) / extents
    S = np.eye(4)
    S[[0, 1, 2], [0, 1, 2]] = factors
    m.apply_transform(S)
    return m


# --------------------------------------------------------------------------
# Grid + six-plane box slicing
# --------------------------------------------------------------------------
def compute_grid(target, usable_max):
    """Smallest grid whose cells are <= usable_max on every axis."""
    counts = [max(1, int(np.ceil(t / usable_max))) for t in target]
    cell = [t / n for t, n in zip(target, counts)]
    return counts, cell


def slice_box(mesh: trimesh.Trimesh, bmin, bmax):
    """Cut the portion of `mesh` inside the axis-aligned box [bmin, bmax]."""
    m = mesh
    for axis in AXES:
        normal = np.zeros(3)
        normal[axis] = 1.0

        origin_max = np.zeros(3)
        origin_max[axis] = bmax[axis]
        m = m.slice_plane(plane_origin=origin_max, plane_normal=-normal, cap=True)
        if m is None or len(m.faces) == 0:
            return None

        origin_min = np.zeros(3)
        origin_min[axis] = bmin[axis]
        m = m.slice_plane(plane_origin=origin_min, plane_normal=normal, cap=True)
        if m is None or len(m.faces) == 0:
            return None
    return m


# --------------------------------------------------------------------------
# Cap cross-section extraction (for placing pins only where there's material)
# --------------------------------------------------------------------------
def cap_polygon(mesh: trimesh.Trimesh, axis: int, value: float, tol: float = 1e-3):
    """Union of the flat triangles trimesh added when it capped the cut at
    `axis == value`, returned as a shapely polygon in the plane's 2D coords."""
    other = [a for a in AXES if a != axis]
    v = mesh.vertices
    on_plane = np.abs(v[:, axis] - value) < tol
    if not on_plane.any():
        return None
    face_mask = on_plane[mesh.faces].all(axis=1)
    faces = mesh.faces[face_mask]
    if len(faces) == 0:
        return None

    polys = []
    for f in faces:
        pts = v[f][:, other]
        poly = Polygon(pts)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.area > 1e-9:
            polys.append(poly)
    if not polys:
        return None
    merged = unary_union(polys)
    return merged


def pick_pin_points(poly, cfg: Config):
    """Farthest-point-sample candidate pin centers inside a safe, eroded
    region of the shared cut-face polygon."""
    if poly is None or poly.is_empty:
        return []
    safe = poly.buffer(-(cfg.pin_radius + cfg.pin_wall_margin))
    if safe.is_empty:
        return []

    geoms = list(safe.geoms) if safe.geom_type == "MultiPolygon" else [safe]
    geoms.sort(key=lambda g: g.area, reverse=True)

    points = []
    for g in geoms:
        if g.area < 4.0:
            continue
        minx, miny, maxx, maxy = g.bounds
        step = max(cfg.pin_min_spacing / 2.0, 2.0)
        xs = np.arange(minx, maxx + step, step)
        ys = np.arange(miny, maxy + step, step)
        candidates = [
            (x, y) for x in xs for y in ys if g.contains(Polygon.from_bounds(x - 0.01, y - 0.01, x + 0.01, y + 0.01).centroid)
        ]
        # cheap point-in-polygon via shapely Point instead of the bbox hack above
        from shapely.geometry import Point
        candidates = [(x, y) for x in xs for y in ys if g.contains(Point(x, y))]
        if not candidates:
            rp = g.representative_point()
            candidates = [(rp.x, rp.y)]

        chosen = [candidates[0]]
        for _ in range(cfg.pin_max_per_face - 1):
            best, best_d = None, -1
            for c in candidates:
                d = min((c[0] - s[0]) ** 2 + (c[1] - s[1]) ** 2 for s in chosen)
                if d > best_d:
                    best_d, best = d, c
            if best is None or best_d < cfg.pin_min_spacing ** 2:
                break
            chosen.append(best)
        points.extend(chosen)
        if len(points) >= cfg.pin_max_per_face:
            break

    return points[: cfg.pin_max_per_face]


# --------------------------------------------------------------------------
# Peg / socket geometry
# --------------------------------------------------------------------------
def axis_cylinder(radius, length, center, axis):
    cyl = creation.cylinder(radius=radius, height=length, sections=20)
    if axis == 0:
        R = trimesh.geometry.align_vectors([0, 0, 1], [1, 0, 0])
    elif axis == 1:
        R = trimesh.geometry.align_vectors([0, 0, 1], [0, 1, 0])
    else:
        R = np.eye(4)
    cyl.apply_transform(R)
    cyl.apply_translation(center)
    return cyl


def point_3d(u, v, axis, value):
    p = [0.0, 0.0, 0.0]
    other = [a for a in AXES if a != axis]
    p[other[0]] = u
    p[other[1]] = v
    p[axis] = value
    return np.array(p)


def add_peg(mesh, axis, boundary, uv_point, cfg: Config):
    center_val = boundary + (cfg.pin_protrusion - cfg.pin_embed) / 2.0
    length = cfg.pin_protrusion + cfg.pin_embed
    center = point_3d(uv_point[0], uv_point[1], axis, center_val)
    cyl = axis_cylinder(cfg.pin_radius, length, center, axis)
    return trimesh.boolean.union([mesh, cyl])


def cut_socket(mesh, axis, boundary, uv_point, cfg: Config):
    depth = cfg.pin_protrusion + cfg.pin_clearance + 1.0   # +1mm so it starts inside solid material
    center_val = boundary - 0.5 + depth / 2.0
    center = point_3d(uv_point[0], uv_point[1], axis, center_val)
    cyl = axis_cylinder(cfg.pin_radius + cfg.pin_clearance, depth, center, axis)
    return trimesh.boolean.difference([mesh, cyl])


# --------------------------------------------------------------------------
# Main pipeline
# --------------------------------------------------------------------------
@dataclass
class Piece:
    idx: tuple
    mesh: trimesh.Trimesh
    bounds: np.ndarray  # pre-pin bounds, used for cap-plane lookups


def run(input_path: str, output_zip: str, cfg: Config):
    t_start = time.time()
    name = Path(input_path).stem

    print(f"[1/5] loading + repairing '{input_path}' ...")
    mesh = load_and_repair(input_path)
    print(f"      {len(mesh.faces):,} triangles, watertight={mesh.is_watertight}")

    print(f"[2/5] scaling to {cfg.target[0]} x {cfg.target[1]} x {cfg.target[2]} mm ...")
    mesh = scale_to_target(mesh, cfg.target)

    usable_max = cfg.max_size - (cfg.pin_protrusion if cfg.pins else 0.0)
    counts, cell = compute_grid(cfg.target, usable_max)
    nx, ny, nz = counts
    total_cells = nx * ny * nz
    print(
        f"[3/5] cutting into a {nx} x {ny} x {nz} grid "
        f"({total_cells} cells, each up to {cell[0]:.2f} x {cell[1]:.2f} x {cell[2]:.2f} mm) ..."
    )

    pieces = {}
    done = 0
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                bmin = [i * cell[0], j * cell[1], k * cell[2]]
                bmax = [(i + 1) * cell[0], (j + 1) * cell[1], (k + 1) * cell[2]]
                piece_mesh = slice_box(mesh, bmin, bmax)
                done += 1
                if piece_mesh is None or len(piece_mesh.faces) < cfg.min_piece_faces:
                    continue
                pieces[(i, j, k)] = Piece(
                    idx=(i, j, k), mesh=piece_mesh, bounds=piece_mesh.bounds.copy()
                )
        print(f"      row {i+1}/{nx} done ({done}/{total_cells} cells scanned, {len(pieces)} non-empty)")

    if not pieces:
        raise RuntimeError("No material found in any grid cell — check --target / the source model.")

    if cfg.pins:
        print(f"[4/5] adding alignment pins across {len(pieces)} pieces ...")
        pin_log = []
        for axis in AXES:
            for (i, j, k), piece in list(pieces.items()):
                nb_idx = list((i, j, k))
                nb_idx[axis] += 1
                nb_idx = tuple(nb_idx)
                if nb_idx not in pieces:
                    continue
                neighbour = pieces[nb_idx]

                boundary = (piece.idx[axis] + 1) * cell[axis]
                poly_a = cap_polygon(piece.mesh, axis, boundary)
                poly_b = cap_polygon(neighbour.mesh, axis, boundary)
                if poly_a is None or poly_b is None:
                    continue
                shared = poly_a.intersection(poly_b)
                pts = pick_pin_points(shared, cfg)
                if not pts:
                    continue

                for uv in pts:
                    try:
                        piece.mesh = add_peg(piece.mesh, axis, boundary, uv, cfg)
                        neighbour.mesh = cut_socket(neighbour.mesh, axis, boundary, uv, cfg)
                        pin_log.append((piece.idx, nb_idx, AXIS_NAMES[axis]))
                    except Exception as e:  # noqa: BLE001 — boolean backends can fail on edge cases
                        print(f"      ! pin skipped between {piece.idx} and {nb_idx}: {e}", file=sys.stderr)
        print(f"      {len(pin_log)} pins placed")
    else:
        print("[4/5] --no-pins set, skipping pin/socket generation")

    print(f"[5/5] exporting {len(pieces)} parts to '{output_zip}' ...")
    manifest = ["part,grid_x,grid_y,grid_z,size_x_mm,size_y_mm,size_z_mm,faces,file"]
    oversize_warnings = []
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for (i, j, k), piece in sorted(pieces.items()):
            m = piece.mesh
            m.apply_translation(-m.bounds[0])
            size = m.extents
            if np.any(size > cfg.max_size + 1e-6):
                oversize_warnings.append((i, j, k, size))

            label = f"x{i+1}_y{j+1}_z{k+1}"
            fname = f"{name}_part_{label}.stl"
            stl_bytes = trimesh.exchange.stl.export_stl(m)
            zf.writestr(fname, stl_bytes)
            manifest.append(
                f"{label},{i+1},{j+1},{k+1},{size[0]:.2f},{size[1]:.2f},{size[2]:.2f},{len(m.faces)},{fname}"
            )

        zf.writestr("manifest.csv", "\n".join(manifest))
        zf.writestr(
            "README.txt",
            f"""split_stl.py output — {name}

Final assembled size : {cfg.target[0]} x {cfg.target[1]} x {cfg.target[2]} mm
Bed / gantry limit    : {cfg.max_size} x {cfg.max_size} x {cfg.max_size} mm
Grid                  : {nx} (X) x {ny} (Y) x {nz} (Z)
Parts produced        : {len(pieces)}
Alignment pins        : {'yes, r=' + str(cfg.pin_radius) + 'mm, protrusion=' + str(cfg.pin_protrusion) + 'mm' if cfg.pins else 'no'}

Each STL is re-zeroed so its own bounding-box minimum sits at (0,0,0) —
they drop straight into a slicer with no repositioning.

File names encode grid position: part_x{{col}}_y{{row}}_z{{layer}}.
Where two pieces are grid-adjacent, the lower-index piece carries a
raised cylindrical peg and the higher-index neighbour carries a matching
blind socket ({cfg.pin_clearance}mm radial clearance) — press them together
to self-align before gluing. Faces with no usable solid cross-section
(edges of thin/organic shapes) are left as plain glue joints.

See manifest.csv for exact per-part dimensions.
""",
        )

    Path(output_zip).write_bytes(buf.getvalue())

    if oversize_warnings:
        print("WARNING: the following parts exceed --max-size after pins were added:", file=sys.stderr)
        for i, j, k, size in oversize_warnings:
            print(f"  x{i+1}_y{j+1}_z{k+1}: {size}", file=sys.stderr)
        print(
            "Reduce --pin-protrusion, increase the safety margin, or lower --max-size and re-run.",
            file=sys.stderr,
        )

    dt = time.time() - t_start
    print(f"done in {dt:.1f}s — {len(pieces)} parts written to {output_zip}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", help="source STL file")
    p.add_argument("--target", nargs=3, type=float, default=[646.68, 442.27, 1700.0],
                    metavar=("X", "Y", "Z"), help="final assembled size in mm (default: %(default)s)")
    p.add_argument("--max-size", type=float, default=175.0,
                    help="max size per part per axis in mm (default: %(default)s)")
    p.add_argument("--out", default=None, help="output .zip path (default: <input>_split.zip)")
    p.add_argument("--pins", dest="pins", action="store_true", default=True,
                    help="add alignment peg/socket joints (default: on)")
    p.add_argument("--no-pins", dest="pins", action="store_false",
                    help="disable pins, cut only")
    p.add_argument("--pin-radius", type=float, default=3.0, help="peg radius in mm (default: %(default)s)")
    p.add_argument("--pin-protrusion", type=float, default=4.0,
                    help="how far the peg sticks out past the cut face, mm (default: %(default)s)")
    p.add_argument("--pin-embed", type=float, default=6.0,
                    help="how far the peg is buried into its own piece, mm (default: %(default)s)")
    p.add_argument("--pin-clearance", type=float, default=0.25,
                    help="radial clearance in the socket, mm — tune per printer (default: %(default)s)")
    p.add_argument("--pin-max-per-face", type=int, default=3,
                    help="max pins per shared cut face (default: %(default)s)")
    args = p.parse_args()

    cfg = Config(
        target=tuple(args.target),
        max_size=args.max_size,
        pins=args.pins,
        pin_radius=args.pin_radius,
        pin_protrusion=args.pin_protrusion,
        pin_embed=args.pin_embed,
        pin_clearance=args.pin_clearance,
        pin_max_per_face=args.pin_max_per_face,
    )
    out = args.out or str(Path(args.input).with_suffix("").as_posix()) + "_split.zip"
    run(args.input, out, cfg)


if __name__ == "__main__":
    main()
