from __future__ import annotations

from collections.abc import Callable

from radimagetovisio.models.diagram import Shape, TextBox
from radimagetovisio.models.geometry import Rect

ProgressCallback = Callable[[str, int], None]


def _default_progress(step: str, percent: int) -> None:
    pass


def estimate_font_sizes(
    texts: list[TextBox],
    pt_to_mm_factor: float = 0.353,
) -> list[TextBox]:
    if not texts:
        return []

    heights = [t.bounds.height for t in texts]
    median_height = sorted(heights)[len(heights) // 2]

    result = []
    for t in texts:
        estimated = t.bounds.height / pt_to_mm_factor
        if median_height > 0:
            ratio = t.bounds.height / median_height
            if ratio < 0.5:
                estimated = max(6.0, estimated)
            elif ratio > 2.0:
                estimated = min(72.0, estimated)
        result.append(
            TextBox(
                text=t.text,
                bounds=t.bounds,
                id=t.id,
                font_family=t.font_family,
                font_size_pt=round(estimated, 1),
                color=t.color,
                bold=t.bold,
                italic=t.italic,
                associated_shape_id=t.associated_shape_id,
            )
        )
    return result


def filter_noise(
    texts: list[TextBox],
    min_area_mm2: float = 1.0,
    min_font_size_pt: float = 4.0,
    max_font_size_pt: float = 120.0,
    max_aspect_ratio: float = 20.0,
    min_text_length: int = 1,
    progress: ProgressCallback = _default_progress,
) -> list[TextBox]:
    progress("Filtering noise", 0)
    result = []
    for t in texts:
        area = t.bounds.area
        if area < min_area_mm2:
            continue
        if t.font_size_pt < min_font_size_pt or t.font_size_pt > max_font_size_pt:
            continue
        aspect = t.bounds.width / t.bounds.height if t.bounds.height > 0 else float("inf")
        if aspect > max_aspect_ratio or (aspect < 1.0 / max_aspect_ratio and aspect > 0):
            continue
        if len(t.text.strip()) < min_text_length:
            continue
        result.append(t)
    progress("Done", 100)
    return result


def associate_text_with_shapes(
    texts: list[TextBox],
    shapes: list[Shape],
    margin_factor: float = 0.2,
    progress: ProgressCallback = _default_progress,
) -> tuple[list[TextBox], list[Shape]]:
    progress("Associating text", 0)

    updated_texts = []
    updated_shapes = list(shapes)

    for idx, t in enumerate(texts):
        center = t.bounds.center
        associated_id: str | None = None
        best_overlap = -1.0
        best_distance = float("inf")

        for s in shapes:
            margin_x = s.bounds.width * margin_factor
            margin_y = s.bounds.height * margin_factor
            expanded = Rect(
                s.bounds.x - margin_x,
                s.bounds.y - margin_y,
                s.bounds.width + 2 * margin_x,
                s.bounds.height + 2 * margin_y,
            )
            if expanded.contains(center):
                overlap = t.bounds.intersection_area(s.bounds)
                distance = center.distance_to(s.bounds.center)
                if overlap > best_overlap or (overlap == best_overlap and distance < best_distance):
                    best_overlap = overlap
                    best_distance = distance
                    associated_id = s.id

        new_text = TextBox(
            text=t.text,
            bounds=t.bounds,
            id=t.id,
            font_family=t.font_family,
            font_size_pt=t.font_size_pt,
            color=t.color,
            bold=t.bold,
            italic=t.italic,
            associated_shape_id=associated_id,
        )
        updated_texts.append(new_text)

        if associated_id:
            for i, s in enumerate(updated_shapes):
                if s.id == associated_id:
                    updated_shapes[i] = Shape(
                        bounds=s.bounds,
                        shape_type=s.shape_type,
                        id=s.id,
                        fill_color=s.fill_color,
                        stroke_color=s.stroke_color,
                        stroke_width=s.stroke_width,
                        z_order=s.z_order,
                        opacity=s.opacity,
                        label=new_text.text,
                    )
                    break

        progress(
            f"Associating text {idx + 1}/{len(texts)}", int(100 * (idx + 1) / max(len(texts), 1))
        )

    progress("Done", 100)
    return updated_texts, updated_shapes
