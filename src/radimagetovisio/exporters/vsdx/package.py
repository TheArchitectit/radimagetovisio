from __future__ import annotations

import zipfile
from io import BytesIO

from radimagetovisio.models.diagram import Diagram

from .masters_builder import (
    MASTER_SHAPES,
    build_master_xml,
    build_masters_rels,
    build_masters_xml,
)
from .page_builder import build_page_xml, build_pages_xml
from .rels_builder import RelsBuilder
from .theme_builder import build_theme_colors_xml, build_theme_effects_xml

PACKAGE_RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
VISIO_REL = "http://schemas.microsoft.com/visio/2010/relationships"


def _content_types_xml() -> str:
    overrides = (
        '<Override PartName="/visio/document.xml" '
        'ContentType="application/vnd.ms-visio.drawing.main+xml"/>'
        '<Override PartName="/visio/pages/pages.xml" '
        'ContentType="application/vnd.ms-visio.pages+xml"/>'
        '<Override PartName="/visio/masters/masters.xml" '
        'ContentType="application/vnd.ms-visio.masters+xml"/>'
        '<Override PartName="/visio/masters/themecolors.xml" '
        'ContentType="application/vnd.ms-visio.themecolors+xml"/>'
        '<Override PartName="/visio/masters/themeeffects.xml" '
        'ContentType="application/vnd.ms-visio.themeeffects+xml"/>'
    )
    for master in MASTER_SHAPES:
        overrides += (
            f'<Override PartName="/visio/masters/master{master.master_id}.xml" '
            'ContentType="application/vnd.ms-visio.master+xml"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f"{overrides}"
        "</Types>\n"
    )


def _package_rels_xml() -> str:
    rels = RelsBuilder()
    rels.add(f"{VISIO_REL}/document", "visio/document.xml")
    return rels.to_xml()


def _document_xml(diagram: Diagram) -> str:
    from lxml import etree

    VISIO_NS = "http://schemas.microsoft.com/office/visio/2012/main"
    root = etree.Element("{%s}VisioDocument" % VISIO_NS)

    doc_props = etree.SubElement(root, "{%s}DocumentProperties" % VISIO_NS)
    creator = etree.SubElement(doc_props, "{%s}Creator" % VISIO_NS)
    creator.text = diagram.author or "radimagetovisio"
    title = etree.SubElement(doc_props, "{%s}Title" % VISIO_NS)
    title.text = diagram.title

    xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return xml_bytes.decode("utf-8")


def _document_rels_xml() -> str:
    rels = RelsBuilder()
    rels.add(f"{VISIO_REL}/pages", "pages/pages.xml")
    rels.add(f"{VISIO_REL}/masters", "masters/masters.xml")
    rels.add(f"{VISIO_REL}/themecolors", "masters/themecolors.xml")
    rels.add(f"{VISIO_REL}/themeeffects", "masters/themeeffects.xml")
    return rels.to_xml()


def _pages_rels_xml(page_rels_list: list[tuple[int, RelsBuilder]]) -> str:
    rels = RelsBuilder()
    for page_id, _ in page_rels_list:
        rels.add(f"{VISIO_REL}/page", f"page{page_id}.xml")
    return rels.to_xml()


def export_vsdx(diagram: Diagram, output_path: str) -> None:
    if not diagram.pages:
        from radimagetovisio.models.diagram import Page

        diagram.add_page(Page())

    pages = diagram.pages

    pages_xml_str, page_rels_list = build_pages_xml(pages)

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _content_types_xml())
        zf.writestr("_rels/.rels", _package_rels_xml())
        zf.writestr("visio/document.xml", _document_xml(diagram))
        zf.writestr("visio/_rels/.rels", _document_rels_xml())
        zf.writestr("visio/pages/pages.xml", pages_xml_str)
        zf.writestr("visio/pages/_rels/pages.xml.rels", _pages_rels_xml(page_rels_list))

        for idx, page in enumerate(pages):
            page_id = idx + 1
            page_xml = build_page_xml(page)
            zf.writestr(f"visio/pages/page{page_id}.xml", page_xml)

        zf.writestr("visio/masters/masters.xml", build_masters_xml())
        zf.writestr("visio/masters/_rels/masters.xml.rels", build_masters_rels())
        for master in MASTER_SHAPES:
            zf.writestr(
                f"visio/masters/master{master.master_id}.xml",
                build_master_xml(master.master_id, master.name),
            )

        zf.writestr("visio/masters/themecolors.xml", build_theme_colors_xml())
        zf.writestr("visio/masters/themeeffects.xml", build_theme_effects_xml())

    with open(output_path, "wb") as f:
        f.write(buffer.getvalue())
