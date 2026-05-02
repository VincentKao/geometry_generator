#!/usr/bin/env python3
"""
立體幾何題目自動生成器 v1.0
Solid Geometry Auto-Generator for K-12 Math Education

Usage:
    python geometry_generator.py
    → produces geometry_figure.png in the current directory.

Modify the parameters in generate_figure() or call it directly
to produce different problem variants.
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager

# ── CJK font detection ────────────────────────────────────────────────────────
def _setup_font():
    """Pick the first available CJK-compatible font so Chinese labels render."""
    candidates = [
        "PingFang SC", "Heiti SC", "STHeiti", "STSong",   # macOS
        "Microsoft YaHei", "SimHei", "SimSun",             # Windows
        "Noto Sans CJK SC", "WenQuanYi Micro Hei",         # Linux
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for font in candidates:
        if font in available:
            matplotlib.rcParams["font.family"] = [font, "DejaVu Sans"]
            print(f"[font] using '{font}'")
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


_setup_font()


# ── Oblique projection (斜二測畫法) ───────────────────────────────────────────
#   x-axis : horizontal right
#   y-axis : 45° upper-right, scaled by 0.5  (depth)
#   z-axis : vertical up

_PROJ_ANGLE = np.radians(45)
_PROJ_SCALE = 0.5          # y-axis compression ratio

# In the oblique projection, the visual silhouette tangent lines of a cylinder
# are NOT at θ=0/π but shifted by this angle.  Computed from d(px)/dθ = 0.
_SIL_ALPHA = np.arctan(_PROJ_SCALE * np.cos(_PROJ_ANGLE))   # ≈ 0.34 rad ≈ 19.5°


def project(x, y, z):
    """Map a 3-D point to 2-D screen coordinates."""
    px = x + _PROJ_SCALE * y * np.cos(_PROJ_ANGLE)
    py = z + _PROJ_SCALE * y * np.sin(_PROJ_ANGLE)
    return np.array([float(px), float(py)])


# ── Low-level segment helper ──────────────────────────────────────────────────

def _seg(ax, p3a, p3b, ls="-", lw=0.9, color="k"):
    """Project both endpoints and draw a line segment."""
    a, b = project(*p3a), project(*p3b)
    ax.plot(
        [a[0], b[0]], [a[1], b[1]],
        ls, color=color, lw=lw,
        solid_capstyle="round", solid_joinstyle="round",
    )


def shade_cylinder_side(ax, cx, cy, cz, radius, height,
                         light_color="#C5DFF0", dark_color="#5B9DC0",
                         n_strips=80):
    """
    Shade the visible lateral surface of a cylinder with a smooth gradient.

    Uses n_strips thin quadrilateral bands across the front half (θ ∈ [π, 2π]).
    Colour interpolates from dark_color at the tangent edges to light_color at
    the foremost centre point, mimicking a diffuse front-lit surface.
    No visible seam — the entire front side reads as one continuous surface.

    Call BEFORE draw_cylinder() so wireframe edges appear on top.
    """
    def _hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

    lc = np.array(_hex_to_rgb(light_color))
    dc = np.array(_hex_to_rgb(dark_color))

    # Arc runs from the true left silhouette to the true right silhouette,
    # passing through the foremost point.  Both edges are exactly at the
    # projected tangent lines drawn by draw_cylinder().
    a = _SIL_ALPHA
    t_start = np.pi + a          # left  silhouette (projected leftmost x)
    t_end   = 2 * np.pi + a      # right silhouette (projected rightmost x)
    thetas  = np.linspace(t_start, t_end, n_strips + 1)

    for i in range(n_strips):
        t_a, t_b = thetas[i], thetas[i + 1]
        t_mid = (t_a + t_b) / 2

        # sin(t - t_start) goes 0 → 1 → 0 symmetrically over [t_start, t_end]
        factor = float(np.sin(t_mid - t_start))
        color  = tuple(dc + factor * (lc - dc))

        pts = [
            project(cx + radius * np.cos(t_a), cy + radius * np.sin(t_a), cz),
            project(cx + radius * np.cos(t_b), cy + radius * np.sin(t_b), cz),
            project(cx + radius * np.cos(t_b), cy + radius * np.sin(t_b), cz + height),
            project(cx + radius * np.cos(t_a), cy + radius * np.sin(t_a), cz + height),
        ]
        ax.add_patch(plt.Polygon(pts, facecolor=color, edgecolor="none", zorder=1))


def fill_cylinder_top(ax, cx, cy, cz, radius, height, color="#C5DFF0", n=200):
    """
    Fill the top circle of the cylinder with a solid colour (default white).
    This closes the cap visually so the shape reads as a solid cylinder,
    not an open tube.  Draw AFTER side shading but BEFORE wireframe so the
    top-circle outline appears on top.
    """
    theta = np.linspace(0, 2 * np.pi, n)
    xs = cx + radius * np.cos(theta)
    ys = cy + radius * np.sin(theta)
    pts = [project(x, y, cz + height) for x, y in zip(xs, ys)]
    poly = plt.Polygon(pts, facecolor=color, edgecolor="none", zorder=1.5)
    ax.add_patch(poly)


def draw_cylinder_axis(ax, cx, cy, cz, height, lw=0.7):
    """
    Draw the central axis of the cylinder as a thin dashed line.
    Runs from the bottom-circle centre to the top-circle centre.
    Common in Chinese K-12 textbooks to show the axis of rotation.
    """
    p_bot = project(cx, cy, cz)
    p_top = project(cx, cy, cz + height)
    ax.plot(
        [p_bot[0], p_top[0]], [p_bot[1], p_top[1]],
        "--", color="k", lw=lw, zorder=3,
    )


def fill_face_2d(ax, pts_3d, color="#d0d0d0", alpha=0.35, zorder=0):
    """
    Fill a planar polygon face (given as 3-D vertices) with a flat colour.
    Draw BEFORE wireframe so lines appear on top.

    Parameters
    ----------
    pts_3d : list of (x, y, z) tuples, in order around the polygon
    color  : fill colour (default light gray)
    alpha  : opacity  (0 = transparent, 1 = opaque)
    zorder : drawing order (keep 0 so wireframe sits on top)
    """
    pts_2d = [project(*p) for p in pts_3d]
    poly = plt.Polygon(
        pts_2d,
        facecolor=color, edgecolor="none",
        alpha=alpha, zorder=zorder,
    )
    ax.add_patch(poly)


# ═════════════════════════════════════════════════════════════════════════════
#  CORE SHAPE FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def draw_cuboid(ax, length, width, height, ox=0.0, oy=0.0, oz=0.0):
    """
    Draw a wireframe cuboid (長方體) using oblique projection.

    Parameters
    ----------
    ax            : matplotlib Axes
    length, width, height : dimensions along x, y, z
    ox, oy, oz    : 3-D origin of the front-left-bottom corner

    Returns
    -------
    dict of named 3-D vertices  {'A': ..., 'B': ..., ... 'H': ...}
    """
    L, W, H = length, width, height

    # 8 corners  (named for easy reference in the caller)
    A  = (ox,     oy,     oz)       # front-left-bottom
    B  = (ox + L, oy,     oz)       # front-right-bottom
    C  = (ox + L, oy + W, oz)       # back-right-bottom
    D  = (ox,     oy + W, oz)       # back-left-bottom
    E  = (ox,     oy,     oz + H)   # front-left-top
    F  = (ox + L, oy,     oz + H)   # front-right-top
    G  = (ox + L, oy + W, oz + H)   # back-right-top
    Hv = (ox,     oy + W, oz + H)   # back-left-top

    # Visible edges (solid) ──────────────────────────────────────
    #   Front face   : A-B, A-E, B-F, E-F
    #   Top face     : E-F (shared), F-G, G-Hv, E-Hv
    #   Right bottom : B-C
    #   Back-left vert: D-Hv
    visible = [
        (A, B), (A, E), (B, F), (E, F),   # front face
        (F, G), (G, Hv), (E, Hv),          # top face (E-F already above)
        (B, C),                             # right bottom going back
        (D, Hv),                            # back-left vertical
    ]
    for a, b in visible:
        _seg(ax, a, b, ls="-", lw=0.9)

    # Hidden edges (dashed) ──────────────────────────────────────
    #   A-D (left bottom back), D-C (bottom back), C-G (back-right vert)
    hidden = [(A, D), (D, C), (C, G)]
    for a, b in hidden:
        _seg(ax, a, b, ls="--", lw=0.6)

    return dict(A=A, B=B, C=C, D=D, E=E, F=F, G=G, H=Hv)


def draw_cylinder(ax, cx, cy, cz, radius, height, n=300):
    """
    Draw a wireframe cylinder (圓柱體) with vertical axis (along z).

    Parameters
    ----------
    ax            : matplotlib Axes
    cx, cy        : 3-D centre of the bottom circle
    cz            : z-coordinate of the bottom face
    radius, height: dimensions
    n             : number of points used to draw each ellipse

    Returns
    -------
    dict  {'bottom': (cx,cy,cz),  'top': (cx,cy,cz+height)}
    """
    theta = np.linspace(0, 2 * np.pi, n)
    xs = cx + radius * np.cos(theta)
    ys = cy + radius * np.sin(theta)

    def _proj_circle(z_val):
        px = [project(x, y, z_val)[0] for x, y in zip(xs, ys)]
        py = [project(x, y, z_val)[1] for x, y in zip(xs, ys)]
        return px, py

    # Top circle – always fully visible
    tx, ty = _proj_circle(cz + height)
    ax.plot(tx, ty, "-", color="k", lw=0.9)

    # Bottom circle – visible arc solid, hidden arc dashed.
    # Split at the true projected silhouette angles (not simply θ=0/π).
    a = _SIL_ALPHA
    for t_range, ls, lw in [
        (np.linspace(np.pi + a, 2 * np.pi + a, n // 2), "-",  0.9),   # front (visible)
        (np.linspace(2 * np.pi + a, 3 * np.pi + a, n // 2), "--", 0.6),  # back (hidden)
    ]:
        xs_r = cx + radius * np.cos(t_range)
        ys_r = cy + radius * np.sin(t_range)
        px_r = [project(x, y, cz)[0] for x, y in zip(xs_r, ys_r)]
        py_r = [project(x, y, cz)[1] for x, y in zip(xs_r, ys_r)]
        ax.plot(px_r, py_r, ls, color="k", lw=lw)

    # Tangent lines at the true projected silhouette positions
    xl = cx + radius * np.cos(np.pi + a)
    yl = cy + radius * np.sin(np.pi + a)
    xr = cx + radius * np.cos(a)
    yr = cy + radius * np.sin(a)
    _seg(ax, (xl, yl, cz), (xl, yl, cz + height))
    _seg(ax, (xr, yr, cz), (xr, yr, cz + height))

    return dict(bottom=(cx, cy, cz), top=(cx, cy, cz + height))


# ═════════════════════════════════════════════════════════════════════════════
#  ANNOTATION FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def draw_dimension_line(ax, p1_2d, p2_2d, text,
                        perp, gap=1.5, ext=0.5, fontsize=9):
    """
    Draw a double-headed dimension arrow with a label.

    Parameters
    ----------
    p1_2d, p2_2d : 2-D endpoints (already projected)
    text         : label string
    perp         : direction away from the geometry (need not be normalised)
    gap          : perpendicular offset from the geometry
    ext          : extension-line overshoot beyond the dimension line
    fontsize     : text size
    """
    perp = np.asarray(perp, dtype=float)
    perp /= np.linalg.norm(perp)             # normalise

    p1, p2 = np.asarray(p1_2d), np.asarray(p2_2d)
    q1 = p1 + perp * gap
    q2 = p2 + perp * gap

    # Extension lines (from geometry to just past the dimension line)
    for p, q in [(p1, q1), (p2, q2)]:
        tip = q + perp * ext
        ax.plot([p[0], tip[0]], [p[1], tip[1]], "-", color="k", lw=0.5)

    # Double-headed arrow along the offset line
    ax.annotate(
        "", xy=tuple(q2), xytext=tuple(q1),
        arrowprops=dict(arrowstyle="<->", color="k", lw=0.8,
                        mutation_scale=10),
    )

    # Label centred on the dimension line, offset outward a little
    mid = (q1 + q2) / 2
    ax.text(
        *(mid + perp * 1.0), text,
        ha="center", va="center", fontsize=fontsize,
        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"),
    )


def draw_radius_line(ax, center_3d, radius, angle_deg=0,
                     label="r", center_label="O", fontsize=9):
    """
    Draw a radius line on a horizontal circle and label the centre.

    Parameters
    ----------
    center_3d   : 3-D centre of the circle  (x, y, z)
    radius      : circle radius
    angle_deg   : direction of the radius in the real xy-plane
    label       : text placed at the midpoint of the radius line
    center_label: text placed at the centre point
    fontsize    : text size
    """
    cx, cy, cz = center_3d
    ang = np.radians(angle_deg)
    ex = cx + radius * np.cos(ang)
    ey = cy + radius * np.sin(ang)

    pc = project(cx, cy, cz)
    pe = project(ex, ey, cz)

    # Radius line
    ax.plot([pc[0], pe[0]], [pc[1], pe[1]], "-", color="k", lw=0.9)

    # Centre dot and label
    ax.plot(pc[0], pc[1], "o", color="k", ms=3)
    ax.text(pc[0] - 0.5, pc[1] - 0.4, center_label,
            ha="right", va="top", fontsize=fontsize, fontweight="bold")

    # Radius label at midpoint, shifted slightly above
    mid = (pc + pe) / 2
    ax.text(mid[0], mid[1] + 0.8, label,
            ha="center", va="bottom", fontsize=fontsize, style="italic")


# ═════════════════════════════════════════════════════════════════════════════
#  FUTURE SHAPE STUBS  (ready to extend)
# ═════════════════════════════════════════════════════════════════════════════

def draw_triangular_prism(ax, base_a, base_b, base_c, height,
                          ox=0.0, oy=0.0, oz=0.0):
    """Stub – draw a triangular prism (三角柱). Not yet implemented."""
    raise NotImplementedError("draw_triangular_prism: coming soon")


def draw_cone(ax, cx, cy, cz, radius, height):
    """Stub – draw a cone (圓錐). Not yet implemented."""
    raise NotImplementedError("draw_cone: coming soon")


def draw_pyramid(ax, base_length, base_width, height,
                 ox=0.0, oy=0.0, oz=0.0):
    """Stub – draw a rectangular pyramid (四角錐). Not yet implemented."""
    raise NotImplementedError("draw_pyramid: coming soon")


# ═════════════════════════════════════════════════════════════════════════════
#  MULTI-OBJECT HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _validate_object(obj, box_length, box_width):
    """Warn if an object's footprint exceeds the box top-face boundary."""
    t = obj.get("type", "?")
    if t == "cylinder":
        cx, cy, r = obj["cx"], obj["cy"], obj["radius"]
        outside = (cx - r < 0 or cx + r > box_length or
                   cy - r < 0 or cy + r > box_width)
    elif t == "cuboid":
        ox, oy = obj["ox"], obj["oy"]
        outside = (ox < 0 or ox + obj["length"] > box_length or
                   oy < 0 or oy + obj["width"]  > box_width)
    else:
        print(f"[warning] unknown object type '{t}'")
        return
    if outside:
        print(f"[warning] {t} {obj} extends outside the box top face")


def _depth_key(obj):
    """Painter's-algorithm sort key: back objects (higher y) drawn first."""
    if obj["type"] == "cylinder":
        return -(obj["cy"] + obj["radius"])
    return -(obj["oy"] + obj["width"])


def _draw_object(ax, obj, base_z):
    """Draw shading + wireframe + contact mark for one object on the box top."""
    if obj["type"] == "cylinder":
        cx, cy = obj["cx"], obj["cy"]
        r,  h  = obj["radius"], obj["height"]
        cz     = base_z

        # Shading (must come before wireframe)
        shade_cylinder_side(ax, cx, cy, cz, r, h)
        fill_cylinder_top(ax, cx, cy, cz, r, h)

        # Wireframe + centre axis
        draw_cylinder(ax, cx, cy, cz, r, h)
        draw_cylinder_axis(ax, cx, cy, cz, h)

        # Contact ellipse – redraw thicker to mark the joint
        a = _SIL_ALPHA
        n = 200
        for t_range, ls in [
            (np.linspace(np.pi + a, 2*np.pi + a, n // 2), "-"),
            (np.linspace(2*np.pi + a, 3*np.pi + a, n // 2), "--"),
        ]:
            xs_r = cx + r * np.cos(t_range)
            ys_r = cy + r * np.sin(t_range)
            ax.plot(
                [project(x, y, cz)[0] for x, y in zip(xs_r, ys_r)],
                [project(x, y, cz)[1] for x, y in zip(xs_r, ys_r)],
                ls, color="k", lw=1.6,
            )

    elif obj["type"] == "cuboid":
        ox, oy = obj["ox"], obj["oy"]
        L, W, H = obj["length"], obj["width"], obj["height"]
        cz = base_z

        # Shade top face and front face before wireframe
        fill_face_2d(ax, [                          # top face
            (ox,     oy,     cz + H),
            (ox + L, oy,     cz + H),
            (ox + L, oy + W, cz + H),
            (ox,     oy + W, cz + H),
        ], color="#c0c0c0", alpha=0.55, zorder=1)
        fill_face_2d(ax, [                          # front face
            (ox,     oy, cz),
            (ox + L, oy, cz),
            (ox + L, oy, cz + H),
            (ox,     oy, cz + H),
        ], color="#d8d8d8", alpha=0.45, zorder=1)

        draw_cuboid(ax, L, W, H, ox=ox, oy=oy, oz=cz)


def _draw_object_labels(ax, obj, base_z, fontsize=14):
    """Draw dimension annotations for one object."""
    if obj["type"] == "cylinder":
        cx, cy = obj["cx"], obj["cy"]
        r,  h  = obj["radius"], obj["height"]
        cz     = base_z

        # Height: along the true right silhouette tangent
        xr = cx + r * np.cos(_SIL_ALPHA)
        yr = cy + r * np.sin(_SIL_ALPHA)
        draw_dimension_line(
            ax,
            project(xr, yr, cz), project(xr, yr, cz + h),
            f"高 = {h}",
            perp=(1, 0), gap=2.5, fontsize=fontsize,
        )
        # Radius on the top circle
        draw_radius_line(
            ax,
            center_3d=(cx, cy, cz + h),
            radius=r,
            angle_deg=obj.get("label_angle", 0),
            label=f"r = {r}",
            center_label="O",
            fontsize=fontsize,
        )

    elif obj["type"] == "cuboid":
        ox, oy = obj["ox"], obj["oy"]
        L, W, H = obj["length"], obj["width"], obj["height"]
        cz = base_z
        A = (ox,     oy,     cz)
        B = (ox + L, oy,     cz)
        C = (ox + L, oy + W, cz)
        E = (ox,     oy,     cz + H)
        draw_dimension_line(ax, project(*A), project(*B),
                            f"長 = {L}", perp=(0, -1), gap=2.0, fontsize=fontsize)
        draw_dimension_line(ax, project(*B), project(*C),
                            f"寬 = {W}", perp=(1, -1), gap=1.5, fontsize=fontsize)
        draw_dimension_line(ax, project(*A), project(*E),
                            f"高 = {H}", perp=(-1, 0), gap=2.0, fontsize=fontsize)


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN SCENE BUILDER
# ═════════════════════════════════════════════════════════════════════════════

def generate_figure(
    box_length = 20,
    box_width  = 12,
    box_height =  6,
    objects    = None,   # list of shape dicts placed on the box top face
    filename   = "geometry_figure.png",
    dpi        = 150,
    show       = True,
):
    """
    Generate a geometry diagram: a cuboid base with one or more shapes on top.

    objects
    -------
    List of dicts.  Each dict must include a ``'type'`` key.

    Cylinder::

        {'type': 'cylinder',
         'cx': x, 'cy': y,          # centre on the box top face
         'radius': r, 'height': h,
         'show_labels': True,        # optional, default True
         'label_angle': 0}           # radius-line direction (degrees)

    Small cuboid::

        {'type': 'cuboid',
         'ox': x, 'oy': y,           # front-left corner on the box top face
         'length': L, 'width': W, 'height': H,
         'show_labels': True}         # optional

    If *objects* is ``None``, defaults to a single centred cylinder (r=5, h=8).

    Examples
    --------
    Two cylinders of different sizes::

        generate_figure(
            box_length=20, box_width=12, box_height=6,
            objects=[
                {'type': 'cylinder', 'cx': 6,  'cy': 6, 'radius': 3, 'height': 10},
                {'type': 'cylinder', 'cx': 15, 'cy': 6, 'radius': 2, 'height': 6,
                 'label_angle': 45},
            ],
            filename="multi_cylinder.png",
        )

    One cylinder + one small cuboid::

        generate_figure(
            box_length=20, box_width=12, box_height=6,
            objects=[
                {'type': 'cylinder', 'cx': 5,  'cy': 6, 'radius': 3, 'height': 8},
                {'type': 'cuboid',   'ox': 11, 'oy': 3,
                 'length': 6, 'width': 5, 'height': 5},
            ],
            filename="mixed.png",
        )
    """
    # ── Defaults ──────────────────────────────────────────────────
    if objects is None:
        objects = [dict(type="cylinder",
                        cx=box_length / 2, cy=box_width / 2,
                        radius=5, height=8)]

    for obj in objects:
        _validate_object(obj, box_length, box_width)

    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_aspect("equal")
    ax.axis("off")

    cz = box_height   # z-level of the box top face

    # ── 0. Box top-face shading ───────────────────────────────────
    fill_face_2d(ax, [
        (0,          0,         cz),
        (box_length, 0,         cz),
        (box_length, box_width, cz),
        (0,          box_width, cz),
    ], color="#c8c8c8", alpha=0.40)

    # ── 1. Cuboid base wireframe ──────────────────────────────────
    v = draw_cuboid(ax, box_length, box_width, box_height)

    # ── 2. Objects – back to front (painter's algorithm) ─────────
    for obj in sorted(objects, key=_depth_key):
        _draw_object(ax, obj, cz)

    # ── 3. Base cuboid dimension lines ────────────────────────────
    DIM_FS = 14
    draw_dimension_line(ax, project(*v["A"]), project(*v["B"]),
                        f"長 = {box_length}", perp=(0, -1), gap=2.5, fontsize=DIM_FS)
    draw_dimension_line(ax, project(*v["B"]), project(*v["C"]),
                        f"寬 = {box_width}",  perp=(1, -1), gap=2.0, fontsize=DIM_FS)
    draw_dimension_line(ax, project(*v["A"]), project(*v["E"]),
                        f"高 = {box_height}", perp=(-1, 0), gap=2.5, fontsize=DIM_FS)

    # ── 4. Per-object dimension lines ─────────────────────────────
    for obj in objects:
        if obj.get("show_labels", True):
            _draw_object_labels(ax, obj, cz, fontsize=DIM_FS)

    # ── 5. Title ──────────────────────────────────────────────────
    _name = {"cylinder": "圓柱體", "cuboid": "長方體"}
    top_shapes = "、".join(
        dict.fromkeys(_name.get(o["type"], o["type"]) for o in objects)
    )
    ax.set_title(
        f"複合立體幾何示意圖　（長方體底座 ＋ {top_shapes}）",
        fontsize=13, pad=22,
    )

    # ── 6. Save / show ────────────────────────────────────────────
    plt.tight_layout()
    fig.savefig(filename, dpi=dpi, bbox_inches="tight", facecolor="white")
    print(f"✓ 圖形已儲存為 {filename}")
    if show:
        plt.show()
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # ── Example 1: single centred cylinder (original problem) ─────
    generate_figure(
        box_length=20, box_width=12, box_height=6,
        objects=[
            {"type": "cylinder", "cx": 10, "cy": 6, "radius": 5, "height": 8},
        ],
        filename="geometry_figure.png",
        show=False,
    )

    # ── Example 2: two cylinders of different sizes ───────────────
    generate_figure(
        box_length=20, box_width=12, box_height=6,
        objects=[
            {"type": "cylinder", "cx": 6,  "cy": 6, "radius": 3, "height": 10,
             "label_angle": 170},
            {"type": "cylinder", "cx": 15, "cy": 6, "radius": 2, "height": 6,
             "label_angle": 0},
        ],
        filename="geometry_figure_multi_cyl.png",
        show=False,
    )

    # ── Example 3: cylinder + small cuboid ───────────────────────
    generate_figure(
        box_length=20, box_width=12, box_height=6,
        objects=[
            {"type": "cylinder", "cx": 5,  "cy": 6, "radius": 3, "height": 8,
             "label_angle": 180},
            {"type": "cuboid",   "ox": 10, "oy": 3,
             "length": 7, "width": 5, "height": 5},
        ],
        filename="geometry_figure_mixed.png",
        show=False,
    )

    print("全部圖形已產生完畢。")
