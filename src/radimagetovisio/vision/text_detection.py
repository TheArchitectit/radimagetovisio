from __future__ import annotations

from collections.abc import Callable

import numpy as np
from PIL import Image

from radimagetovisio.models.diagram import TextBox
from radimagetovisio.models.geometry import Rect, px_to_mm

try:
    import pytesseract

    _TESSERACT_AVAILABLE = True
except Exception:
    _TESSERACT_AVAILABLE = False

ProgressCallback = Callable[[str, int], None]


def _default_progress(step: str, percent: int) -> None:
    pass


def _extract_words_from_data(data: dict) -> list[dict]:
    words = []
    n_boxes = len(data.get("text", []))
    for i in range(n_boxes):
        text = str(data["text"][i]).strip()
        try:
            conf = int(data["conf"][i])
        except (ValueError, TypeError):
            conf = 0
        if not text or conf < 0:
            continue
        words.append(
            {
                "text": text,
                "left": int(data["left"][i]),
                "top": int(data["top"][i]),
                "width": int(data["width"][i]),
                "height": int(data["height"][i]),
                "conf": conf,
                "line_num": int(data.get("line_num", [0] * n_boxes)[i]),
                "block_num": int(data.get("block_num", [0] * n_boxes)[i]),
                "par_num": int(data.get("par_num", [0] * n_boxes)[i]),
            }
        )
    return words


def _words_to_textboxes(words: list[dict]) -> list[TextBox]:
    textboxes = []
    for w in words:
        bounds_px = Rect(w["left"], w["top"], w["width"], w["height"])
        bounds_mm = Rect(
            px_to_mm(bounds_px.x),
            px_to_mm(bounds_px.y),
            px_to_mm(bounds_px.width),
            px_to_mm(bounds_px.height),
        )
        textboxes.append(
            TextBox(
                text=w["text"],
                bounds=bounds_mm,
                font_size_pt=max(1.0, px_to_mm(w["height"]) * 2.83),
            )
        )
    return textboxes


def _merge_words_on_same_line(
    words: list[dict],
    max_vertical_gap_factor: float = 0.6,
    max_horizontal_gap_factor: float = 2.5,
) -> list[dict]:
    if not words:
        return []

    words = sorted(words, key=lambda w: (w["top"], w["left"]))
    lines: list[list[dict]] = []

    for w in words:
        placed = False
        for line in lines:
            line_avg_height = sum(x["height"] for x in line) / len(line)
            line_top = min(x["top"] for x in line)
            line_bottom = max(x["top"] + x["height"] for x in line)
            vertical_overlap = w["top"] < line_bottom and w["top"] + w["height"] > line_top
            vertical_proximity = (
                abs((w["top"] + w["height"] / 2) - (line_top + (line_bottom - line_top) / 2))
                <= max_vertical_gap_factor * line_avg_height
            )

            if vertical_overlap or vertical_proximity:
                last_in_line = max(line, key=lambda x: x["left"])
                gap = w["left"] - (last_in_line["left"] + last_in_line["width"])
                avg_width = sum(x["width"] for x in line) / len(line)
                if gap <= max_horizontal_gap_factor * avg_width:
                    line.append(w)
                    placed = True
                    break

        if not placed:
            lines.append([w])

    merged = []
    for line in lines:
        line = sorted(line, key=lambda w: w["left"])
        left = line[0]["left"]
        top = min(w["top"] for w in line)
        right = max(w["left"] + w["width"] for w in line)
        bottom = max(w["top"] + w["height"] for w in line)
        text = " ".join(w["text"] for w in line)
        avg_conf = sum(w["conf"] for w in line) / len(line)
        merged.append(
            {
                "text": text,
                "left": left,
                "top": top,
                "width": right - left,
                "height": bottom - top,
                "conf": avg_conf,
            }
        )

    return merged


def detect_text(
    image: np.ndarray,
    merge_into_lines: bool = True,
    progress: ProgressCallback = _default_progress,
) -> list[TextBox]:
    progress("Detecting text", 0)

    if not _TESSERACT_AVAILABLE:
        progress("Tesseract unavailable", 100)
        return []

    if image.ndim == 2:
        pil_image = Image.fromarray(image, mode="L")
    else:
        pil_image = Image.fromarray(image, mode="RGB")

    progress("Running OCR", 30)

    data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
    words = _extract_words_from_data(data)

    progress("Post-processing OCR", 60)

    merged = _merge_words_on_same_line(words) if merge_into_lines else words

    result = _words_to_textboxes(merged)
    progress("Done", 100)
    return result


def detect_text_words_only(
    image: np.ndarray,
    progress: ProgressCallback = _default_progress,
) -> list[TextBox]:
    return detect_text(image, merge_into_lines=False, progress=progress)
