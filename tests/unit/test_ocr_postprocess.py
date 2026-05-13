import pytest

from radimagetovisio.models.diagram import Shape, TextBox
from radimagetovisio.models.geometry import Rect
from radimagetovisio.vision.ocr_postprocess import (
    associate_text_with_shapes,
    estimate_font_sizes,
    filter_noise,
)


class TestEstimateFontSizes:
    def test_estimates_from_height(self) -> None:
        texts = [
            TextBox(text="hello", bounds=Rect(0, 0, 10, 3.53)),
            TextBox(text="world", bounds=Rect(0, 0, 10, 7.06)),
        ]
        result = estimate_font_sizes(texts)
        assert result[0].font_size_pt == pytest.approx(10.0, abs=1.0)
        assert result[1].font_size_pt == pytest.approx(20.0, abs=1.0)

    def test_clamps_extreme_sizes(self) -> None:
        texts = [
            TextBox(text="tiny", bounds=Rect(0, 0, 5, 0.5)),
            TextBox(text="normal", bounds=Rect(0, 0, 5, 3.53)),
            TextBox(text="huge", bounds=Rect(0, 0, 5, 50.0)),
        ]
        result = estimate_font_sizes(texts)
        tiny = next(t for t in result if t.text == "tiny")
        huge = next(t for t in result if t.text == "huge")
        assert tiny.font_size_pt >= 6.0
        assert huge.font_size_pt <= 72.0

    def test_empty_list(self) -> None:
        assert estimate_font_sizes([]) == []

    def test_preserves_id_and_other_fields(self) -> None:
        t = TextBox(text="x", bounds=Rect(0, 0, 10, 3.53), font_family="Times", color="#ff0000")
        result = estimate_font_sizes([t])
        assert result[0].id == t.id
        assert result[0].font_family == "Times"
        assert result[0].color == "#ff0000"


class TestFilterNoise:
    def test_filters_tiny_boxes(self) -> None:
        texts = [
            TextBox(text="ok", bounds=Rect(0, 0, 10, 10)),
            TextBox(text="", bounds=Rect(0, 0, 0.1, 0.1)),
        ]
        result = filter_noise(texts, min_area_mm2=1.0)
        assert len(result) == 1
        assert result[0].text == "ok"

    def test_filters_extreme_fonts(self) -> None:
        texts = [
            TextBox(text="ok", bounds=Rect(0, 0, 10, 3.53)),
            TextBox(text="tiny", bounds=Rect(0, 0, 10, 0.5), font_size_pt=2.0),
        ]
        result = filter_noise(texts, min_font_size_pt=4.0)
        assert len(result) == 1
        assert result[0].text == "ok"

    def test_filters_extreme_aspect(self) -> None:
        texts = [
            TextBox(text="ok", bounds=Rect(0, 0, 10, 3.53)),
            TextBox(text="long", bounds=Rect(0, 0, 100, 1.0)),
        ]
        result = filter_noise(texts, max_aspect_ratio=20.0)
        assert len(result) == 1
        assert result[0].text == "ok"

    def test_filters_short_text(self) -> None:
        texts = [
            TextBox(text="a", bounds=Rect(0, 0, 10, 3.53)),
            TextBox(text="ab", bounds=Rect(0, 0, 10, 3.53)),
        ]
        result = filter_noise(texts, min_text_length=2)
        assert len(result) == 1
        assert result[0].text == "ab"

    def test_empty_list(self) -> None:
        assert filter_noise([]) == []

    def test_progress_callback(self) -> None:
        calls = []

        def cb(step: str, pct: int) -> None:
            calls.append((step, pct))

        filter_noise([TextBox(text="x", bounds=Rect(0, 0, 10, 3.53))], progress=cb)
        assert len(calls) >= 2


class TestAssociateTextWithShapes:
    def test_associates_when_centroid_inside(self) -> None:
        shape = Shape(bounds=Rect(0, 0, 100, 100))
        text = TextBox(text="label", bounds=Rect(40, 40, 20, 20))
        texts, shapes = associate_text_with_shapes([text], [shape])
        assert texts[0].associated_shape_id == shape.id
        assert shapes[0].label == "label"

    def test_no_association_when_far(self) -> None:
        shape = Shape(bounds=Rect(0, 0, 10, 10))
        text = TextBox(text="far", bounds=Rect(100, 100, 10, 10))
        texts, shapes = associate_text_with_shapes([text], [shape])
        assert texts[0].associated_shape_id is None
        assert shapes[0].label == ""

    def test_associates_with_margin(self) -> None:
        shape = Shape(bounds=Rect(0, 0, 100, 100))
        text = TextBox(text="edge", bounds=Rect(105, 50, 10, 10))
        texts, shapes = associate_text_with_shapes([text], [shape], margin_factor=0.2)
        assert texts[0].associated_shape_id == shape.id

    def test_multiple_texts_one_shape(self) -> None:
        shape = Shape(bounds=Rect(0, 0, 100, 100))
        t1 = TextBox(text="a", bounds=Rect(10, 10, 20, 20))
        t2 = TextBox(text="b", bounds=Rect(70, 70, 20, 20))
        texts, shapes = associate_text_with_shapes([t1, t2], [shape])
        assert texts[0].associated_shape_id == shape.id
        assert texts[1].associated_shape_id == shape.id
        # The last associated text wins for label
        assert shapes[0].label == "b"

    def test_empty_inputs(self) -> None:
        texts, shapes = associate_text_with_shapes([], [])
        assert texts == []
        assert shapes == []

    def test_progress_callback(self) -> None:
        calls = []

        def cb(step: str, pct: int) -> None:
            calls.append((step, pct))

        shape = Shape(bounds=Rect(0, 0, 10, 10))
        text = TextBox(text="x", bounds=Rect(5, 5, 2, 2))
        associate_text_with_shapes([text], [shape], progress=cb)
        assert len(calls) >= 2
