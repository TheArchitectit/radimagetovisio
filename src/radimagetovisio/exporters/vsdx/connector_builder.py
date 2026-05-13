from __future__ import annotations

from lxml import etree

from radimagetovisio.models.diagram import Connector
from radimagetovisio.models.geometry import Point

from .shape_builder import VISIO_NS, _make_cell, _make_sub, _mm_to_in


def build_connector_element(
    connector: Connector,
    page_height_mm: float,
    from_point: Point,
    to_point: Point,
) -> etree.Element:
    element = etree.Element("{%s}Shape" % VISIO_NS)
    element.set("ID", connector.id)
    element.set("Type", "Shape")

    begin_x = _mm_to_in(from_point.x)
    begin_y = _mm_to_in(page_height_mm - from_point.y)
    end_x = _mm_to_in(to_point.x)
    end_y = _mm_to_in(page_height_mm - to_point.y)

    xform1d = etree.SubElement(element, "{%s}XForm1D" % VISIO_NS)
    xform1d.append(_make_cell("BeginX", str(begin_x)))
    xform1d.append(_make_cell("BeginY", str(begin_y)))
    xform1d.append(_make_cell("EndX", str(end_x)))
    xform1d.append(_make_cell("EndY", str(end_y)))

    geom = etree.SubElement(element, "{%s}Geom" % VISIO_NS)
    geom.set("IX", "0")
    path = etree.SubElement(geom, "{%s}Path" % VISIO_NS)

    move = etree.SubElement(path, "{%s}MoveTo" % VISIO_NS)
    move.set("IX", "1")
    move.append(_make_sub("X", "0"))
    move.append(_make_sub("Y", "0"))

    line_to = etree.SubElement(path, "{%s}LineTo" % VISIO_NS)
    line_to.set("IX", "2")
    line_to.append(_make_sub("X", "1"))
    line_to.append(_make_sub("Y", "0"))

    line_section = etree.SubElement(element, "{%s}Line" % VISIO_NS)
    line_section.append(_make_cell("LineColor", "RGB(0,0,0)"))
    line_section.append(_make_cell("LineWeight", str(_mm_to_in(connector.stroke_width))))
    if connector.arrowhead_end:
        line_section.append(_make_cell("EndArrow", "13"))
    if connector.arrowhead_start:
        line_section.append(_make_cell("BeginArrow", "13"))

    return element
