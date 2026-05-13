import os
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from radimagetovisio.exporters.vsdx.package import export_vsdx
from radimagetovisio.models.diagram import Connector, Diagram, Page, Shape, TextBox
from radimagetovisio.models.geometry import Point, Rect


class TestVsdxExport:
    def test_vsdx_file_created(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.vsdx")
            export_vsdx(diagram, path)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0

    def test_vsdx_is_valid_zip(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.vsdx")
            export_vsdx(diagram, path)
            assert zipfile.is_zipfile(path)

    def test_required_zip_parts_exist(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                assert "[Content_Types].xml" in names
                assert "_rels/.rels" in names
                assert "visio/document.xml" in names
                assert "visio/_rels/.rels" in names
                assert "visio/pages/pages.xml" in names
                assert "visio/pages/_rels/pages.xml.rels" in names
                assert "visio/pages/page1.xml" in names

    def test_xml_wellformedness(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                for name in zf.namelist():
                    if name.endswith(".xml") or name.endswith(".rels"):
                        data = zf.read(name)
                        ET.fromstring(data)

    def test_document_xml_has_visio_namespace(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                doc = zf.read("visio/document.xml")
                root = ET.fromstring(doc)
                assert "visio" in root.tag

    def test_page_xml_has_shapes(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                page = zf.read("visio/pages/page1.xml")
                root = ET.fromstring(page)
                shapes = root.findall(
                    ".//{http://schemas.microsoft.com/office/visio/2012/main}Shape"
                )
                assert len(shapes) == 2  # rectangle + text box

    def test_pages_xml_has_page_index(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                pages = zf.read("visio/pages/pages.xml")
                root = ET.fromstring(pages)
                ns = {"v": "http://schemas.microsoft.com/office/visio/2012/main"}
                page_elems = root.findall("v:Page", ns)
                assert len(page_elems) == 1
                assert page_elems[0].get("Name") == "Page-1"

    def test_empty_diagram_creates_default_page(self) -> None:
        diagram = Diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "empty.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                assert "visio/pages/page1.xml" in names

    def test_multi_page_diagram(self) -> None:
        diagram = Diagram()
        page1 = Page(name="First")
        page1.add_shape(Shape(bounds=Rect(0, 0, 10, 10)))
        page2 = Page(name="Second")
        page2.add_shape(Shape(bounds=Rect(0, 0, 20, 20)))
        diagram.add_page(page1)
        diagram.add_page(page2)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "multi.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                assert "visio/pages/page1.xml" in names
                assert "visio/pages/page2.xml" in names
                pages = zf.read("visio/pages/pages.xml")
                root = ET.fromstring(pages)
                ns = {"v": "http://schemas.microsoft.com/office/visio/2012/main"}
                page_elems = root.findall("v:Page", ns)
                assert len(page_elems) == 2

    def test_relationships_are_valid(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                rels = zf.read("_rels/.rels")
                root = ET.fromstring(rels)
                rels_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
                assert root.tag == f"{{{rels_ns}}}Relationships"
                rels_elems = root.findall(f"{{{rels_ns}}}Relationship")
                assert len(rels_elems) >= 1
                assert any("visio/document.xml" in r.get("Target", "") for r in rels_elems)

    def test_masters_files_exist(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                assert "visio/masters/masters.xml" in names
                assert "visio/masters/_rels/masters.xml.rels" in names
                assert "visio/masters/master1.xml" in names

    def test_theme_files_exist(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                assert "visio/masters/themecolors.xml" in names
                assert "visio/masters/themeeffects.xml" in names

    def test_connector_exported_with_xform1d(self) -> None:
        page = Page(width_mm=210, height_mm=297)
        s1 = Shape(bounds=Rect(10, 10, 30, 20))
        s2 = Shape(bounds=Rect(60, 10, 30, 20))
        page.add_shape(s1)
        page.add_shape(s2)
        page.add_connector(
            Connector(
                from_shape_id=s1.id,
                to_shape_id=s2.id,
                arrowhead_end=True,
            )
        )
        diagram = Diagram()
        diagram.add_page(page)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "conn.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                page_xml = zf.read("visio/pages/page1.xml")
                root = ET.fromstring(page_xml)
                ns = {"v": "http://schemas.microsoft.com/office/visio/2012/main"}
                shapes = root.findall(".//v:Shape", ns)
                assert len(shapes) == 3  # 2 shapes + 1 connector
                xform1d = root.findall(".//v:XForm1D", ns)
                assert len(xform1d) == 1
                cells = xform1d[0].findall("v:Cell", ns)
                names = {c.get("N") for c in cells}
                assert "BeginX" in names
                assert "BeginY" in names
                assert "EndX" in names
                assert "EndY" in names

    def test_connector_with_explicit_points(self) -> None:
        page = Page(width_mm=210, height_mm=297)
        page.add_connector(
            Connector(
                from_shape_id="a",
                to_shape_id="b",
                from_point=Point(10, 10),
                to_point=Point(100, 100),
                arrowhead_start=True,
            )
        )
        diagram = Diagram()
        diagram.add_page(page)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "conn2.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                page_xml = zf.read("visio/pages/page1.xml")
                root = ET.fromstring(page_xml)
                ns = {"v": "http://schemas.microsoft.com/office/visio/2012/main"}
                xform1d = root.findall(".//v:XForm1D", ns)
                assert len(xform1d) == 1

    def test_connector_arrowheads(self) -> None:
        page = Page(width_mm=210, height_mm=297)
        s1 = Shape(bounds=Rect(10, 10, 30, 20))
        s2 = Shape(bounds=Rect(60, 10, 30, 20))
        page.add_shape(s1)
        page.add_shape(s2)
        page.add_connector(
            Connector(
                from_shape_id=s1.id,
                to_shape_id=s2.id,
                arrowhead_end=True,
                arrowhead_start=True,
            )
        )
        diagram = Diagram()
        diagram.add_page(page)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "arrows.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                page_xml = zf.read("visio/pages/page1.xml")
                root = ET.fromstring(page_xml)
                ns = {"v": "http://schemas.microsoft.com/office/visio/2012/main"}
                line_cells = root.findall(".//v:Shape/v:Line/v:Cell", ns)
                names = {c.get("N") for c in line_cells}
                assert "EndArrow" in names
                assert "BeginArrow" in names

    def test_document_rels_include_masters_and_themes(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                rels = zf.read("visio/_rels/.rels")
                root = ET.fromstring(rels)
                rels_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
                targets = {r.get("Target", "") for r in root.findall(f"{{{rels_ns}}}Relationship")}
                assert "masters/masters.xml" in targets
                assert "masters/themecolors.xml" in targets
                assert "masters/themeeffects.xml" in targets

    def test_content_types_include_masters(self) -> None:
        diagram = _create_sample_diagram()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.vsdx")
            export_vsdx(diagram, path)
            with zipfile.ZipFile(path, "r") as zf:
                ct = zf.read("[Content_Types].xml")
                root = ET.fromstring(ct)
                ct_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
                overrides = root.findall(f"{{{ct_ns}}}Override")
                part_names = {o.get("PartName", "") for o in overrides}
                assert "/visio/masters/masters.xml" in part_names
                assert "/visio/masters/themecolors.xml" in part_names
                assert "/visio/masters/master1.xml" in part_names


def _create_sample_diagram() -> Diagram:
    page = Page(width_mm=210, height_mm=297)
    page.add_shape(Shape(bounds=Rect(10, 10, 30, 20), label="Box"))
    page.add_text(TextBox(text="Hello", bounds=Rect(10, 40, 20, 10)))
    diagram = Diagram(title="Test Diagram")
    diagram.add_page(page)
    return diagram
