from dataclasses import dataclass

from radimagetovisio.models.diagram import ShapeType


@dataclass(frozen=True)
class MasterShape:
    master_id: int
    name: str
    name_u: str
    shape_type: str


BASIC_FLOWCHART_MASTERS = [
    MasterShape(1, "Process", "Process", "Shape"),
    MasterShape(2, "Decision", "Decision", "Shape"),
    MasterShape(3, "Start/End", "Start/End", "Shape"),
    MasterShape(4, "Connector", "Connector", "Shape"),
]


MASTER_MAP: dict[ShapeType, int] = {
    ShapeType.RECTANGLE: 1,
    ShapeType.CONTAINER: 1,
    ShapeType.DIAMOND: 2,
    ShapeType.ELLIPSE: 3,
    ShapeType.TRIANGLE: 1,
    ShapeType.PARALLELOGRAM: 1,
    ShapeType.FREEHAND: 1,
}

CONNECTOR_MASTER_ID = 4


def get_master_id_for_shape_type(shape_type: ShapeType) -> int | None:
    return MASTER_MAP.get(shape_type)
