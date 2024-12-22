from __future__ import annotations

import logging
import sys

from build123d import (
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Circle,
    FilletPolyline,
    Location,
    Locations,
    Mode,
    Plane,
    Polyline,
    RectangleRounded,
    Sketch,
    Vector,
    add,
    chamfer,
    extrude,
    fillet,
    make_face,
    mirror,
)

from . import LabelBase

logger = logging.getLogger(__name__)


def _outer_edge(width_u: int) -> Sketch:
    """Generate the outer edge profile of a therick-label"""
    # Width of straight bit in label is:
    #   Bin width (u * 42) (23mm for therick bins)
    # - label margins (4.2mm) (2.2mm for therick bins)
    # - label end size (1.9mm per end)
    #straight_width = width_u * 42 - 4.2 - (1.9 * 2)
    straight_width = width_u * 25 - 2.2 - (1.9 * 2)
    with BuildSketch() as sketch:
        with BuildLine() as line:
            # Where the sketch is placed in X. 2.1 is the therick label offset
            # on one edge; 1.9 is the extra distance to our "zero" point
            # x = 2.1 + 1.9
            x = -straight_width / 2
            #l1 = Polyline([(x - 1.9, 0), (x - 1.9, 2.85), (x - 0.9, 2.85)])
            #l1 = Polyline([(x - 1.9, 0), (x - 1.9, 4.85), (x - 0.9, 4.85)])
            l1 = Polyline([(x - 1.9, 0), (x - 1.9, 5.45), (x - 0.9, 5.45)])
            FilletPolyline(
                [
                    l1 @ 1,
                    #(x - 0.9, 5.75),
                    #(0, 5.75),
                    (x - 0.9, 6.5),
                    (0, 6.5),
                ],
                radius=0.9,
            )
            mirror(line.line, Plane.XZ)
            mirror(line.line, Plane.YZ)

        make_face()

        with Locations([(x - 0.4, 0, 0.4), (x + straight_width + 0.4, 0, 0.4)]):
            Circle(0.75, mode=Mode.SUBTRACT)

    return sketch.sketch


def _inner_edge(width_u: int) -> Sketch:
    #straight_width = width_u * 42 - 4.2 - (1.9 * 2)
    straight_width = width_u * 25 - 2.2 - (1.9 * 2)
    x = -straight_width / 2
    with BuildSketch() as sketch:
        with BuildLine() as line:
            a1 = CenterArc((x - 0.4, 0), 1.25, 0, 90)
            FilletPolyline([a1 @ 1, (x - 0.4, 5.25), (0, 5.25)], radius=0.4)
            # Fillet the vertex between the arc and polyline
            fillet([line.vertices().sort_by_distance(a1 @ 1)[0]], radius=1)
            mirror(line.line, Plane.XZ)
            mirror(line.line, Plane.YZ)
        make_face()

    return sketch.sketch


def body(width_u: int, recessed: bool = False) -> LabelBase:
    """
    Generate a therick-label body.

    Origin is positioned at the center of the label, with the label
    surface at z=0.

    Args:
        width_u: The width of the label, in gridfinity bin units.
        recessed:
            Whether the label surface is resecced into the label (used
            for embossing) or just flat, for cutting away.

    Returns:
        A LabelBase tuple consisting of:
            part: The actual label body.
            label_area: A vector describing the width, height of the usable area.
    """

    with BuildPart() as part:
        add(_outer_edge(width_u=width_u))
        # Extrude the base up
        extrude(amount=0.3, both=True)

        # PDS don't want to cut into top face:
        #if recessed:
        #    add(_inner_edge(width_u=width_u))
        #    # Cut the indent out of the top face
        #    extrude(amount=0.3, mode=Mode.SUBTRACT)

        # 0.2 mm fillet all top edges
        fillet_edges = [
            *part.edges().group_by(Axis.Z)[-1],
            *part.edges().group_by(Axis.Z)[0],
        ]
        fillet(fillet_edges, radius=0.2)

    #area = Vector(width_u * 42 - 4.2 - 5.5, 10.5)
    #area = Vector(width_u * 25 - 2.2 - 5.5, 10.5)
    # 1.0mm margin for label on top and sides
    area = Vector(width_u * 25 - 1.0 - 5.5, 13 - 1.0)
    #if recessed:
    #    return LabelBase(part.part, area)

    # We want the sketch at z=0 to cut in
    return LabelBase(part.part.locate(Location((0, 0, -0.4))), area)

