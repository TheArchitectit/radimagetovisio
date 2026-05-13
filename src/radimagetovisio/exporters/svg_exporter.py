from __future__ import annotations

import svgwrite

from radimagetovisio.models.diagram import (
    Connector,
    ConnectorType,
    Diagram,
    Page,
    Shape,
    ShapeType,
    TextBox,
)
from radimagetovisio.models.geometry import Point

ARROW_MARKER_SIZE = 6
ARROW_MARKER_ID_END = "arrow-end"
ARROW_MARKER_ID_START = "arrow-start"


def _polygon_points(shape: Shape) -> list[tuple[float, float]]:
    b = shape.bounds
    if shape.shape_type == ShapeType.DIAMOND:
        return [
            (b.x + b.width / 2, b.y),
            (b.x + b.width, b.y + b.height / 2),
            (b.x + b.width / 2, b.y + b.height),
            (b.x, b.y + b.height / 2),
        ]
    if shape.shape_type == ShapeType.PARALLELOGRAM:
        offset = b.width * 0.2
        return [
            (b.x + offset, b.y),
            (b.x + b.width, b.y),
            (b.x + b.width - offset, b.y + b.height),
            (b.x, b.y + b.height),
        ]
    if shape.shape_type == ShapeType.TRIANGLE:
        return [
            (b.x + b.width / 2, b.y),
            (b.x + b.width, b.y + b.height),
            (b.x, b.y + b.height),
        ]
    return []


def _add_arrowhead_marker(
    dwg: svgwrite.Drawing,
    marker_id: str,
    color: str,
    stroke_width: float,
) -> None:
    existing = [e for e in dwg.defs.elements if getattr(e, "attribs", {}).get("id") == marker_id]
    if existing:
        return
    size = ARROW_MARKER_SIZE + stroke_width
    marker = dwg.marker(
        insert=(0, size / 2),
        size=(size, size),
        orient="auto",
        markerUnits="strokeWidth",
        id=marker_id,
    )
    marker.add(
        dwg.polygon(
            points=[(size, 0), (0, size / 2), (size, size)],
            fill=color,
        )
    )
    dwg.defs.add(marker)


def _resolve_connector_points(
    page: Page,
    connector: Connector,
) -> tuple[Point, Point]:
    from_pt = connector.from_point
    to_pt = connector.to_point
    if from_pt is None:
        shape = page.get_shape_by_id(connector.from_shape_id)
        from_pt = shape.center if shape else Point(0, 0)
    if to_pt is None:
        shape = page.get_shape_by_id(connector.to_shape_id)
        to_pt = shape.center if shape else Point(0, 0)
    return from_pt, to_pt


def _draw_shape(dwg: svgwrite.Drawing, shape: Shape) -> None:
    b = shape.bounds
    fill = shape.fill_color
    stroke = shape.stroke_color
    stroke_w = shape.stroke_width
    opacity = shape.opacity

    if shape.shape_type == ShapeType.RECTANGLE:
        element = dwg.rect(
            insert=(b.x, b.y),
            size=(b.width, b.height),
            fill=fill,
            stroke=stroke,
            stroke_width=stroke_w,
            opacity=opacity,
        )
    elif shape.shape_type == ShapeType.ELLIPSE:
        rx = b.width / 2
        ry = b.height / 2
        cx = b.x + rx
        cy = b.y + ry
        element = dwg.ellipse(
            center=(cx, cy),
            r=(rx, ry),
            fill=fill,
            stroke=stroke,
            stroke_width=stroke_w,
            opacity=opacity,
        )
    elif shape.shape_type in (
        ShapeType.DIAMOND,
        ShapeType.PARALLELOGRAM,
        ShapeType.TRIANGLE,
    ):
        pts = _polygon_points(shape)
        element = dwg.polygon(
            points=pts,
            fill=fill,
            stroke=stroke,
            stroke_width=stroke_w,
            opacity=opacity,
        )
    else:
        element = dwg.rect(
            insert=(b.x, b.y),
            size=(b.width, b.height),
            fill=fill,
            stroke=stroke,
            stroke_width=stroke_w,
            opacity=opacity,
        )

    element.attribs["id"] = shape.id
    dwg.add(element)


def _draw_connector(dwg: svgwrite.Drawing, page: Page, connector: Connector) -> None:
    from_pt, to_pt = _resolve_connector_points(page, connector)
    color = connector.stroke_color
    stroke_w = connector.stroke_width

    if connector.arrowhead_end:
        _add_arrowhead_marker(dwg, ARROW_MARKER_ID_END, color, stroke_w)
    if connector.arrowhead_start:
        _add_arrowhead_marker(dwg, ARROW_MARKER_ID_START, color, stroke_w)

    if connector.connector_type == ConnectorType.STRAIGHT:
        path_data = f"M {from_pt.x} {from_pt.y} L {to_pt.x} {to_pt.y}"
    elif connector.connector_type == ConnectorType.ELBOW:
        mid_x = (from_pt.x + to_pt.x) / 2
        path_data = (
            f"M {from_pt.x} {from_pt.y} "
            f"L {mid_x} {from_pt.y} "
            f"L {mid_x} {to_pt.y} "
            f"L {to_pt.x} {to_pt.y}"
        )
    else:
        path_data = f"M {from_pt.x} {from_pt.y} L {to_pt.x} {to_pt.y}"

    extra = {}
    if connector.arrowhead_end:
        extra["marker-end"] = f"url(#{ARROW_MARKER_ID_END})"
    if connector.arrowhead_start:
        extra["marker-start"] = f"url(#{ARROW_MARKER_ID_START})"

    path = dwg.path(
        d=path_data,
        fill="none",
        stroke=color,
        stroke_width=stroke_w,
        **extra,
    )
    path.attribs["id"] = connector.id
    dwg.add(path)


def _draw_text(dwg: svgwrite.Drawing, text_box: TextBox) -> None:
    b = text_box.bounds
    style = f"font-family:{text_box.font_family};font-size:{text_box.font_size_pt}pt;"
    if text_box.bold:
        style += "font-weight:bold;"
    if text_box.italic:
        style += "font-style:italic;"

    text = dwg.text(
        text_box.text,
        insert=(b.x, b.y + b.height * 0.6),
        fill=text_box.color,
        style=style,
    )
    text.attribs["id"] = text_box.id
    dwg.add(text)


def _draw_label(dwg: svgwrite.Drawing, shape: Shape) -> None:
    if not shape.label:
        return
    b = shape.bounds
    style = "font-family:Arial;font-size:10pt;"
    text = dwg.text(
        shape.label,
        insert=(b.x + b.width / 2, b.y + b.height / 2),
        fill="#000000",
        style=style,
        text_anchor="middle",
        dominant_baseline="middle",
    )
    dwg.add(text)


def export_page_to_svg(page: Page, output_path: str) -> None:
    dwg = svgwrite.Drawing(
        filename=output_path,
        size=(f"{page.width_mm}mm", f"{page.height_mm}mm"),
        viewBox=f"0 0 {page.width_mm} {page.height_mm}",
    )

    for shape in sorted(page.shapes, key=lambda s: s.z_order):
        _draw_shape(dwg, shape)
        _draw_label(dwg, shape)

    for text_box in page.texts:
        _draw_text(dwg, text_box)

    for connector in page.connectors:
        _draw_connector(dwg, page, connector)

    dwg.save()


def export_diagram_to_svg(diagram: Diagram, output_path: str) -> None:
    if not diagram.pages:
        page = Page()
        diagram.add_page(page)
    if len(diagram.pages) == 1:
        export_page_to_svg(diagram.pages[0], output_path)
    else:
        import os

        base, ext = os.path.splitext(output_path)
        for idx, page in enumerate(diagram.pages):
            page_path = f"{base}_page{idx + 1}{ext}"
            export_page_to_svg(page, page_path)


# Backwards-compatible alias used by GUI code
export_svg = export_diagram_to_svg
