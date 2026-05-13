from __future__ import annotations

from lxml import etree

from radimagetovisio.models.diagram import Page

from .connector_builder import build_connector_element
from .rels_builder import RelsBuilder
from .shape_builder import VISIO_NS, build_shape_element, build_text_element

CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def build_pages_xml(pages: list[Page]) -> tuple[str, list[tuple[int, RelsBuilder]]]:
    root = etree.Element("{%s}Pages" % VISIO_NS)

    page_rels_list: list[tuple[int, RelsBuilder]] = []

    for idx, page in enumerate(pages):
        page_id = idx + 1
        rels = RelsBuilder()

        page_elem = etree.SubElement(root, "{%s}Page" % VISIO_NS)
        page_elem.set("ID", str(page_id))
        page_elem.set("Name", page.name)

        page_sheet = etree.SubElement(page_elem, "{%s}PageSheet" % VISIO_NS)
        page_props = etree.SubElement(page_sheet, "{%s}Cell" % VISIO_NS)
        page_props.set("N", "PageWidth")
        page_props.set("V", str(page.width_mm / 25.4))
        page_props = etree.SubElement(page_sheet, "{%s}Cell" % VISIO_NS)
        page_props.set("N", "PageHeight")
        page_props.set("V", str(page.height_mm / 25.4))

        rels.add(
            "http://schemas.microsoft.com/visio/2010/relationships/page",
            f"page{page_id}.xml",
        )

        page_rels_list.append((page_id, rels))

    xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return xml_bytes.decode("utf-8"), page_rels_list


def build_page_xml(page: Page) -> str:
    root = etree.Element("{%s}PageContents" % VISIO_NS)

    page_height_mm = page.height_mm

    shapes_elem = etree.SubElement(root, "{%s}Shapes" % VISIO_NS)

    shape_centers = {shape.id: shape.center for shape in page.shapes}

    for shape in page.shapes:
        shape_elem = build_shape_element(shape, page_height_mm)
        shapes_elem.append(shape_elem)

    for text_box in page.texts:
        text_elem = build_text_element(text_box, page_height_mm)
        shapes_elem.append(text_elem)

    for connector in page.connectors:
        from_point = connector.from_point
        to_point = connector.to_point
        if from_point is None:
            from_point = shape_centers.get(connector.from_shape_id)
        if to_point is None:
            to_point = shape_centers.get(connector.to_shape_id)
        if from_point is not None and to_point is not None:
            conn_elem = build_connector_element(connector, page_height_mm, from_point, to_point)
            shapes_elem.append(conn_elem)

    xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return xml_bytes.decode("utf-8")
