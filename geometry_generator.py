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

    # Bottom circle – front half solid (y < cy → θ ∈ [π, 2π]),
    #                 back half dashed  (y > cy → θ ∈ [0, π])
    for t_range, ls, lw in [
        (np.linspace(np.pi, 2 * np.pi, n // 2), "-",  0.9),   # front
        (np.linspace(0,      np.pi,     n // 2), "--", 0.6),   # back
    ]:
        xs_r = cx + radius * np.cos(t_range)
        ys_r = cy + radius * np.sin(t_range)
        px_r = [project(x, y, cz)[0] for x, y in zip(xs_r, ys_r)]
        py_r = [project(x, y, cz)[1] for x, y in zip(xs_r, ys_r)]
        ax.plot(px_r, py_r, ls, color="k", lw=lw)

    # Left and right tangent lines
    _seg(ax, (cx - radius, cy, cz), (cx - radius, cy, cz + height))
    _seg(ax, (cx + radius, cy, cz), (cx + radius, cy, cz + height))

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
#  MAIN SCENE BUILDER
# ═════════════════════════════════════════════════════════════════════════════

def generate_figure(
    box_length  = 20,
    box_width   = 12,
    box_height  =  6,
    cyl_radius  =  5,
    cyl_height  =  8,
    filename    = "geometry_figure.png",
    dpi         = 150,
    show        = True,
):
    """
    Generate a composite long-cuboid + cylinder diagram.

    All parameters are independent so you can pass different values
    to auto-generate different exam-question variants:

        generate_figure(box_length=24, box_width=10, box_height=8,
                        cyl_radius=4, cyl_height=10,
                        filename="variant2.png")
    """
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_aspect("equal")
    ax.axis("off")

    cx = box_length / 2
    cy = box_width  / 2
    cz = box_height

    # ── 0. Shading: fill top face BEFORE wireframe (stays behind lines) ──
    #   Top face corners in 3-D order: E → F → G → H
    top_face = [
        (0,            0,           cz),   # E  front-left
        (box_length,   0,           cz),   # F  front-right
        (box_length,   box_width,   cz),   # G  back-right
        (0,            box_width,   cz),   # Hv back-left
    ]
    fill_face_2d(ax, top_face, color="#c8c8c8", alpha=0.40)

    # ── 1. Draw the cuboid wireframe ──────────────────────────────
    v = draw_cuboid(ax, box_length, box_width, box_height)

    # ── 2. Draw the cylinder, centred on the cuboid's top face ────
    draw_cylinder(ax, cx, cy, cz, cyl_radius, cyl_height)

    # ── 2b. Re-draw the contact ellipse thicker to show the joint ─
    #   Full bottom circle at z = cz (both visible and hidden arcs)
    n = 300
    theta = np.linspace(0, 2 * np.pi, n)
    xs = cx + cyl_radius * np.cos(theta)
    ys = cy + cyl_radius * np.sin(theta)
    for t_range, ls in [
        (np.linspace(np.pi, 2 * np.pi, n // 2), "-"),    # front (visible)
        (np.linspace(0,      np.pi,     n // 2), "--"),   # back  (hidden)
    ]:
        xs_r = cx + cyl_radius * np.cos(t_range)
        ys_r = cy + cyl_radius * np.sin(t_range)
        px_r = [project(x, y, cz)[0] for x, y in zip(xs_r, ys_r)]
        py_r = [project(x, y, cz)[1] for x, y in zip(xs_r, ys_r)]
        ax.plot(px_r, py_r, ls, color="k", lw=1.6)   # thicker = emphasis

    # ── 3. Dimension lines ────────────────────────────────────────

    # Cuboid: length (front-bottom edge  A → B)
    draw_dimension_line(
        ax,
        project(*v["A"]), project(*v["B"]),
        f"長 = {box_length}",
        perp=(0, -1), gap=1.8,
    )

    # Cuboid: width (right-bottom edge  B → C, goes oblique)
    draw_dimension_line(
        ax,
        project(*v["B"]), project(*v["C"]),
        f"寬 = {box_width}",
        perp=(1, -1), gap=1.4,
    )

    # Cuboid: height (front-left vertical  A → E)
    draw_dimension_line(
        ax,
        project(*v["A"]), project(*v["E"]),
        f"高 = {box_height}",
        perp=(-1, 0), gap=1.8,
    )

    # Cylinder: height (right tangent of cylinder, vertical)
    p_cyl_bot = project(cx + cyl_radius, cy, cz)
    p_cyl_top = project(cx + cyl_radius, cy, cz + cyl_height)
    draw_dimension_line(
        ax,
        p_cyl_bot, p_cyl_top,
        f"高 = {cyl_height}",
        perp=(1, 0), gap=1.8,
    )

    # Cylinder: radius on the top circle (fully visible), going rightward
    draw_radius_line(
        ax,
        center_3d=(cx, cy, cz + cyl_height),
        radius=cyl_radius,
        angle_deg=0,
        label=f"r = {cyl_radius}",
        center_label="O",
    )

    # ── 4. Title ──────────────────────────────────────────────────
    ax.set_title(
        "複合立體幾何示意圖　（長方體 + 圓柱體）",
        fontsize=13, pad=22,
    )

    # ── 5. Save / show ────────────────────────────────────────────
    plt.tight_layout()
    fig.savefig(filename, dpi=dpi, bbox_inches="tight", facecolor="white")
    print(f"✓ 圖形已儲存為 {filename}")
    if show:
        plt.show()
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # ── Default parameters (matches the problem statement) ────────
    generate_figure(
        box_length = 20,
        box_width  = 12,
        box_height =  6,
        cyl_radius =  5,
        cyl_height =  8,
        filename   = "geometry_figure.png",
        dpi        = 150,
        show       = True,
    )

    # ── Uncomment to produce a different variant ──────────────────
    # generate_figure(
    #     box_length=30, box_width=15, box_height=8,
    #     cyl_radius=6, cyl_height=10,
    #     filename="variant_large.png",
    # )
