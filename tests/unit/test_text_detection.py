import numpy as np
from PIL import Image, ImageDraw, ImageFont

from radimagetovisio.vision.text_detection import (
    _extract_words_from_data,
    _merge_words_on_same_line,
    _words_to_textboxes,
    detect_text,
    detect_text_words_only,
)


class TestExtractWordsFromData:
    def test_extracts_words(self) -> None:
        data = {
            "text": ["Hello", "world"],
            "left": [10, 50],
            "top": [20, 20],
            "width": [30, 35],
            "height": [10, 10],
            "conf": [95, 90],
            "line_num": [1, 1],
            "block_num": [1, 1],
            "par_num": [1, 1],
        }
        words = _extract_words_from_data(data)
        assert len(words) == 2
        assert words[0]["text"] == "Hello"
        assert words[1]["text"] == "world"

    def test_skips_empty_and_negative_conf(self) -> None:
        data = {
            "text": ["", "ok", "bad"],
            "left": [0, 10, 20],
            "top": [0, 10, 20],
            "width": [10, 10, 10],
            "height": [10, 10, 10],
            "conf": [0, 80, -1],
            "line_num": [1, 1, 1],
            "block_num": [1, 1, 1],
            "par_num": [1, 1, 1],
        }
        words = _extract_words_from_data(data)
        assert len(words) == 1
        assert words[0]["text"] == "ok"


class TestMergeWordsOnSameLine:
    def test_merges_nearby_words(self) -> None:
        words = [
            {"text": "Hello", "left": 10, "top": 20, "width": 30, "height": 10, "conf": 95},
            {"text": "world", "left": 45, "top": 20, "width": 35, "height": 10, "conf": 90},
        ]
        merged = _merge_words_on_same_line(words)
        assert len(merged) == 1
        assert merged[0]["text"] == "Hello world"
        assert merged[0]["left"] == 10
        assert merged[0]["width"] == 70

    def test_keeps_separate_lines(self) -> None:
        words = [
            {"text": "Line1", "left": 10, "top": 20, "width": 30, "height": 10, "conf": 95},
            {"text": "Line2", "left": 10, "top": 50, "width": 30, "height": 10, "conf": 90},
        ]
        merged = _merge_words_on_same_line(words)
        assert len(merged) == 2

    def test_empty_input(self) -> None:
        assert _merge_words_on_same_line([]) == []


class TestWordsToTextboxes:
    def test_conversion(self) -> None:
        words = [
            {"text": "Hello", "left": 10, "top": 20, "width": 30, "height": 10, "conf": 95},
        ]
        boxes = _words_to_textboxes(words)
        assert len(boxes) == 1
        assert boxes[0].text == "Hello"
        assert boxes[0].bounds.width > 0
        assert boxes[0].bounds.height > 0


class TestDetectText:
    def _make_text_image(self, text: str, size: tuple = (300, 100)) -> np.ndarray:
        img = Image.new("RGB", size, color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except Exception:
            font = ImageFont.load_default()
        draw.text((20, 30), text, fill=(0, 0, 0), font=font)
        return np.array(img)

    def test_detects_text(self) -> None:
        img = self._make_text_image("TEST")
        result = detect_text(img, merge_into_lines=False)
        assert len(result) > 0
        texts = [t.text.upper() for t in result]
        assert any("TEST" in t for t in texts)

    def test_merges_words(self) -> None:
        img = self._make_text_image("Hello World", size=(400, 100))
        result = detect_text(img, merge_into_lines=True)
        combined = " ".join(t.text for t in result)
        assert "Hello" in combined or "World" in combined

    def test_grayscale_input(self) -> None:
        img = self._make_text_image("OK")
        gray = np.array(Image.fromarray(img).convert("L"))
        result = detect_text(gray, merge_into_lines=False)
        assert len(result) > 0

    def test_progress_callback(self) -> None:
        calls = []

        def cb(step: str, pct: int) -> None:
            calls.append((step, pct))

        img = self._make_text_image("A")
        detect_text(img, progress=cb)
        assert len(calls) >= 2
        assert calls[0][1] <= calls[-1][1]

    def test_words_only(self) -> None:
        img = self._make_text_image("Hello World", size=(400, 100))
        result = detect_text_words_only(img)
        assert len(result) > 0


class TestGuardedImport:
    def test_module_imports_without_tesseract(self) -> None:
        import radimagetovisio.vision.text_detection as td

        assert hasattr(td, "_TESSERACT_AVAILABLE")
