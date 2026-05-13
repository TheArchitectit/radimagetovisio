from __future__ import annotations

from lxml import etree

VISIO_NS = "http://schemas.microsoft.com/office/visio/2012/main"


def build_theme_colors_xml() -> str:
    root = etree.Element("{%s}Colors" % VISIO_NS)
    root.set("ID", "0")
    root.set("Name", "Office")
    root.set("NameU", "Office")

    scheme = [
        ("1", "Text", "RGB(0,0,0)"),
        ("2", "Background", "RGB(255,255,255)"),
        ("3", "Accent1", "RGB(68,114,196)"),
        ("4", "Accent2", "RGB(237,125,49)"),
        ("5", "Accent3", "RGB(165,165,165)"),
        ("6", "Accent4", "RGB(255,192,0)"),
        ("7", "Accent5", "RGB(91,155,213)"),
        ("8", "Accent6", "RGB(112,173,71)"),
    ]

    for ix, name, val in scheme:
        color = etree.SubElement(root, "{%s}Color" % VISIO_NS)
        color.set("IX", ix)
        color.set("Name", name)
        color.set("Value", val)

    xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return xml_bytes.decode("utf-8")


def build_theme_effects_xml() -> str:
    root = etree.Element("{%s}Effects" % VISIO_NS)
    root.set("ID", "0")
    root.set("Name", "Office")
    root.set("NameU", "Office")

    xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return xml_bytes.decode("utf-8")
