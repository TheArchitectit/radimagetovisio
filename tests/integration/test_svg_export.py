import os
import tempfile
import xml.etree.ElementTree as ET

from radimagetovisio.exporters.svg_exporter import export_diagram_to_svg
from radimagetovisio.models.diagram import (
    Connector,
    ConnectorType,
    Diagram,
    Page,
    Shape,
    ShapeType,
    TextBox,
)
from radimagetovisio.models.geometry import Rect

SVG_NS = "http://www.w3.org/2000/svg"


def _count_elements(root: ET.Element, tag_name: str) -> int:
    return len(root.findall(f".//{{{SVG_NS}}}{tag_name}"))


def _create_sample_diagram() -> Diagram:
    page = Page(width_mm=210, height_mm=297)

    page.add_shape(
        Shape(
            bounds=Rect(10, 10, 30, 20),
            shape_type=ShapeType.RECTANGLE,
            label="Box",
            fill_color="#ffcccc",
        )
    )
    page.add_shape(
        Shape(bounds=Rect(60, 10, 30, 20), shape_type=ShapeType.ELLIPSE, fill_color="#ccffcc")
    )
    page.add_shape(
        Shape(bounds=Rect(10, 50, 30, 20), shape_type=ShapeType.DIAMOND, fill_color="#ccccff")
    )
    page.add_shape(
        Shape(bounds=Rect(60, 50, 30, 20), shape_type=ShapeType.PARALLELOGRAM, fill_color="#ffffcc")
    )
    page.add_shape(
        Shape(bounds=Rect(110, 50, 30, 20), shape_type=ShapeType.TRIANGLE, fill_color="#ffccff")
    )

    shapes = page.shapes
    page.add_connector(
        Connector(
            from_shape_id=shapes[0].id,
            to_shape_id=shapes[1].id,
            connector_type=ConnectorType.STRAIGHT,
            arrowhead_end=True,
        )
    )
    page.add_connector(
        Connector(
            from_shape_id=shapes[0].id,
            to_shape_id=shapes[2].id,
            connector_type=ConnectorType.ELBOW,
            arrowhead_end=True,
            arrowhead_start=True,
        )
    )

    page.add_text(TextBox(text="Hello SVG", bounds=Rect(10, 90, 40, 10), font_size_pt=14))

    diagram = Diagram(title="Test Diagram")
    diagram.add_page(page)
    return diagram


class TestSvgExport:
    def test_svg_file_created(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.svg")
            export_diagram_to_svg(diagram, path)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0

    def test_svg_xml_wellformed(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.svg")
            export_diagram_to_svg(diagram, path)
            tree = ET.parse(path)
            root = tree.getroot()
            assert root.tag == f"{{{SVG_NS}}}svg"

    def test_svg_viewbox_matches_page(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.svg")
            export_diagram_to_svg(diagram, path)
            tree = ET.parse(path)
            root = tree.getroot()
            assert root.get("viewBox") == "0 0 210 297"

    def test_shape_element_counts(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.svg")
            export_diagram_to_svg(diagram, path)
            tree = ET.parse(path)
            root = tree.getroot()

            rects = _count_elements(root, "rect")
            ellipses = _count_elements(root, "ellipse")
            polygons = _count_elements(root, "polygon")
            paths = _count_elements(root, "path")
            texts = _count_elements(root, "text")

            assert rects == 1
            assert ellipses == 1
            # 3 shape polygons + 2 arrowhead markers (arrow-end + arrow-start)
            assert polygons == 5
            assert paths == 2  # two connectors
            assert texts == 2  # shape label + text box

    def test_connector_arrowheads(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.svg")
            export_diagram_to_svg(diagram, path)
            tree = ET.parse(path)
            root = tree.getroot()

            paths = root.findall(f".//{{{SVG_NS}}}path")
            assert len(paths) == 2

            elbow = next(
                p for p in paths if "L" in p.get("d", "") and p.get("d", "").count("L") > 1
            )
            straight = next(p for p in paths if p != elbow)

            assert "url(#arrow-end)" in straight.get("marker-end", "")
            assert "url(#arrow-end)" in elbow.get("marker-end", "")
            assert "url(#arrow-start)" in elbow.get("marker-start", "")

    def test_text_styling(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.svg")
            export_diagram_to_svg(diagram, path)
            tree = ET.parse(path)
            root = tree.getroot()

            text_elements = root.findall(f".//{{{SVG_NS}}}text")
            assert any("Hello SVG" in (t.text or "") for t in text_elements)

            hello_text = next(t for t in text_elements if (t.text or "") == "Hello SVG")
            style = hello_text.get("style", "")
            assert "font-size:14pt" in style

    def test_empty_diagram_creates_single_page(self) -> None:
        diagram = Diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "empty.svg")
            export_diagram_to_svg(diagram, path)
            assert os.path.exists(path)
            tree = ET.parse(path)
            root = tree.getroot()
            assert root.tag == f"{{{SVG_NS}}}svg"

    def test_multi_page_diagram(self) -> None:
        diagram = Diagram()
        diagram.add_page(Page(name="Page 1", width_mm=100, height_mm=100))
        diagram.add_page(Page(name="Page 2", width_mm=200, height_mm=200))
        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.join(tmpdir, "multi")
            export_diagram_to_svg(diagram, base + ".svg")
            assert os.path.exists(base + "_page1.svg")
            assert os.path.exists(base + "_page2.svg")
