from __future__ import annotations

from lxml import etree

from radimagetovisio.models.diagram import Shape, ShapeType, TextBox

VISIO_NS = "http://schemas.microsoft.com/office/visio/2012/main"


def _mm_to_in(mm: float) -> float:
    return mm / 25.4


def _hex_to_visio_color(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    elif len(hex_color) == 3:
        r = int(hex_color[0] * 2, 16)
        g = int(hex_color[1] * 2, 16)
        b = int(hex_color[2] * 2, 16)
    else:
        return "0"
    return f"RGB({r},{g},{b})"


def _make_cell(name: str, value: str) -> etree.Element:
    cell = etree.Element("{%s}Cell" % VISIO_NS)
    cell.set("N", name)
    cell.set("V", value)
    return cell


def _make_sub(name: str, value: str) -> etree.Element:
    sub = etree.Element("{%s}Cell" % VISIO_NS)
    sub.set("N", name)
    sub.set("V", value)
    return sub


def _add_xform(parent: etree.Element, shape: Shape, page_height_mm: float) -> None:
    b = shape.bounds
    w_in = _mm_to_in(b.width)
    h_in = _mm_to_in(b.height)
    pin_x = _mm_to_in(b.x + b.width / 2)
    pin_y = _mm_to_in(page_height_mm - (b.y + b.height / 2))

    xform = etree.SubElement(parent, "{%s}XForm" % VISIO_NS)
    xform.append(_make_cell("PinX", str(pin_x)))
    xform.append(_make_cell("PinY", str(pin_y)))
    xform.append(_make_cell("Width", str(w_in)))
    xform.append(_make_cell("Height", str(h_in)))
    xform.append(_make_cell("LocPinX", str(w_in / 2)))
    xform.append(_make_cell("LocPinY", str(h_in / 2)))


def _add_text_xform(parent: etree.Element, text_box: TextBox, page_height_mm: float) -> None:
    b = text_box.bounds
    w_in = _mm_to_in(b.width)
    h_in = _mm_to_in(b.height)
    pin_x = _mm_to_in(b.x + b.width / 2)
    pin_y = _mm_to_in(page_height_mm - (b.y + b.height / 2))

    xform = etree.SubElement(parent, "{%s}XForm" % VISIO_NS)
    xform.append(_make_cell("PinX", str(pin_x)))
    xform.append(_make_cell("PinY", str(pin_y)))
    xform.append(_make_cell("Width", str(w_in)))
    xform.append(_make_cell("Height", str(h_in)))
    xform.append(_make_cell("LocPinX", str(w_in / 2)))
    xform.append(_make_cell("LocPinY", str(h_in / 2)))


def _add_geom_rectangle(parent: etree.Element, width: float, height: float) -> None:
    geom = etree.SubElement(parent, "{%s}Geom" % VISIO_NS)
    geom.set("IX", "0")
    path = etree.SubElement(geom, "{%s}Path" % VISIO_NS)

    move = etree.SubElement(path, "{%s}MoveTo" % VISIO_NS)
    move.set("IX", "1")
    move.append(_make_sub("X", "0"))
    move.append(_make_sub("Y", "0"))

    for ix, (x, y) in enumerate([(width, 0), (width, height), (0, height), (0, 0)], start=2):
        line = etree.SubElement(path, "{%s}LineTo" % VISIO_NS)
        line.set("IX", str(ix))
        line.append(_make_sub("X", str(x)))
        line.append(_make_sub("Y", str(y)))


def _add_geom_ellipse(parent: etree.Element, width: float, height: float) -> None:
    w = width
    h = height
    cx = w / 2
    cy = h / 2

    geom = etree.SubElement(parent, "{%s}Geom" % VISIO_NS)
    geom.set("IX", "0")
    path = etree.SubElement(geom, "{%s}Path" % VISIO_NS)

    move = etree.SubElement(path, "{%s}MoveTo" % VISIO_NS)
    move.set("IX", "1")
    move.append(_make_sub("X", str(w)))
    move.append(_make_sub("Y", str(cy)))

    arcs = [
        (cx, h, w, h, "0", "0.5"),
        (0, cy, 0, h, "0", "0.5"),
        (cx, 0, 0, 0, "0", "0.5"),
        (w, cy, w, 0, "0", "0.5"),
    ]
    for ix, (ex, ey, ax, ay, c, d) in enumerate(arcs, start=2):
        arc = etree.SubElement(path, "{%s}EllipticalArcTo" % VISIO_NS)
        arc.set("IX", str(ix))
        arc.append(_make_sub("X", str(ex)))
        arc.append(_make_sub("Y", str(ey)))
        arc.append(_make_sub("A", str(ax)))
        arc.append(_make_sub("B", str(ay)))
        arc.append(_make_sub("C", c))
        arc.append(_make_sub("D", d))


def _add_geom_polygon(parent: etree.Element, points: list[tuple[float, float]]) -> None:
    geom = etree.SubElement(parent, "{%s}Geom" % VISIO_NS)
    geom.set("IX", "0")
    path = etree.SubElement(geom, "{%s}Path" % VISIO_NS)

    move = etree.SubElement(path, "{%s}MoveTo" % VISIO_NS)
    move.set("IX", "1")
    move.append(_make_sub("X", str(points[0][0])))
    move.append(_make_sub("Y", str(points[0][1])))

    for ix, (x, y) in enumerate(points[1:], start=2):
        line = etree.SubElement(path, "{%s}LineTo" % VISIO_NS)
        line.set("IX", str(ix))
        line.append(_make_sub("X", str(x)))
        line.append(_make_sub("Y", str(y)))

    close = etree.SubElement(path, "{%s}LineTo" % VISIO_NS)
    close.set("IX", str(len(points) + 1))
    close.append(_make_sub("X", str(points[0][0])))
    close.append(_make_sub("Y", str(points[0][1])))


def _polygon_points_mm(shape: Shape) -> list[tuple[float, float]]:
    b = shape.bounds
    if shape.shape_type == ShapeType.DIAMOND:
        return [
            (b.width / 2, 0),
            (b.width, b.height / 2),
            (b.width / 2, b.height),
            (0, b.height / 2),
        ]
    if shape.shape_type == ShapeType.PARALLELOGRAM:
        offset = b.width * 0.2
        return [
            (offset, 0),
            (b.width, 0),
            (b.width - offset, b.height),
            (0, b.height),
        ]
    if shape.shape_type == ShapeType.TRIANGLE:
        return [
            (b.width / 2, 0),
            (b.width, b.height),
            (0, b.height),
        ]
    return []


def _add_geom(parent: etree.Element, shape: Shape) -> None:
    b = shape.bounds
    if shape.shape_type == ShapeType.RECTANGLE:
        _add_geom_rectangle(parent, b.width, b.height)
    elif shape.shape_type == ShapeType.ELLIPSE:
        _add_geom_ellipse(parent, b.width, b.height)
    elif shape.shape_type in (
        ShapeType.DIAMOND,
        ShapeType.PARALLELOGRAM,
        ShapeType.TRIANGLE,
    ):
        pts = _polygon_points_mm(shape)
        _add_geom_polygon(parent, pts)
    else:
        _add_geom_rectangle(parent, b.width, b.height)


def _add_fill_line(parent: etree.Element, shape: Shape) -> None:
    fill = etree.SubElement(parent, "{%s}Fill" % VISIO_NS)
    fill.append(_make_cell("FillForegnd", _hex_to_visio_color(shape.fill_color)))

    line = etree.SubElement(parent, "{%s}Line" % VISIO_NS)
    line.append(_make_cell("LineColor", _hex_to_visio_color(shape.stroke_color)))
    line.append(_make_cell("LineWeight", str(_mm_to_in(shape.stroke_width))))


def build_shape_element(shape: Shape, page_height_mm: float) -> etree.Element:
    element = etree.Element("{%s}Shape" % VISIO_NS)
    element.set("ID", shape.id)
    element.set("Type", "Shape")

    _add_xform(element, shape, page_height_mm)
    _add_geom(element, shape)
    _add_fill_line(element, shape)

    if shape.label:
        text = etree.SubElement(element, "{%s}Text" % VISIO_NS)
        text.text = shape.label

    return element


def build_text_element(text_box: TextBox, page_height_mm: float) -> etree.Element:
    element = etree.Element("{%s}Shape" % VISIO_NS)
    element.set("ID", text_box.id)
    element.set("Type", "Shape")

    _add_text_xform(element, text_box, page_height_mm)

    geom = etree.SubElement(element, "{%s}Geom" % VISIO_NS)
    geom.set("IX", "0")
    geom.set("NoShow", "1")
    path = etree.SubElement(geom, "{%s}Path" % VISIO_NS)
    move = etree.SubElement(path, "{%s}MoveTo" % VISIO_NS)
    move.set("IX", "1")
    move.append(_make_sub("X", "0"))
    move.append(_make_sub("Y", "0"))

    fill = etree.SubElement(element, "{%s}Fill" % VISIO_NS)
    fill.append(_make_cell("FillForegnd", "0"))
    fill.append(_make_cell("FillPattern", "0"))

    line = etree.SubElement(element, "{%s}Line" % VISIO_NS)
    line.append(_make_cell("LineColor", "0"))
    line.append(_make_cell("LinePattern", "0"))

    text = etree.SubElement(element, "{%s}Text" % VISIO_NS)
    text.text = text_box.text

    return element
