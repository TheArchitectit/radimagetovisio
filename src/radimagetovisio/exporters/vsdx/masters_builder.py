from __future__ import annotations

from lxml import etree

from radimagetovisio.assets.stencils import BASIC_FLOWCHART_MASTERS
from radimagetovisio.models.diagram import ShapeType

from .rels_builder import RelsBuilder
from .shape_builder import VISIO_NS

MASTER_SHAPES = BASIC_FLOWCHART_MASTERS


def _master_shape_type_to_icon(master: object) -> str:
    return master.shape_type


def build_masters_xml() -> str:
    root = etree.Element("{%s}Masters" % VISIO_NS)

    for master in MASTER_SHAPES:
        master_elem = etree.SubElement(root, "{%s}Master" % VISIO_NS)
        master_elem.set("ID", str(master.master_id))
        master_elem.set("Name", master.name)
        master_elem.set("NameU", master.name_u)

    xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return xml_bytes.decode("utf-8")


def build_master_xml(master_id: int, name: str) -> str:
    root = etree.Element("{%s}MasterContents" % VISIO_NS)

    shapes = etree.SubElement(root, "{%s}Shapes" % VISIO_NS)
    shape = etree.SubElement(shapes, "{%s}Shape" % VISIO_NS)
    shape.set("ID", str(master_id))
    shape.set("Type", "Shape")

    xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return xml_bytes.decode("utf-8")


def build_masters_rels() -> str:
    rels = RelsBuilder()
    for master in MASTER_SHAPES:
        rels.add(
            "http://schemas.microsoft.com/visio/2010/relationships/master",
            f"master{master.master_id}.xml",
        )
    return rels.to_xml()


def get_master_id_for_shape(shape_type: ShapeType) -> str | None:
    from radimagetovisio.assets.stencils import get_master_id_for_shape_type

    mid = get_master_id_for_shape_type(shape_type)
    return str(mid) if mid is not None else None
