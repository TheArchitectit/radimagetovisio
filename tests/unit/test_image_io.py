import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from radimagetovisio.utils.image_io import ImageLoadResult, load_image, save_numpy_as_png


class TestLoadImage:
    def test_loads_rgb_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.png"
            arr = np.full((50, 60, 3), 128, dtype=np.uint8)
            Image.fromarray(arr, mode="RGB").save(path)

            result = load_image(path)
            assert isinstance(result, ImageLoadResult)
            assert result.width == 60
            assert result.height == 50
            assert result.mode == "RGB"
            assert result.array.shape == (50, 60, 3)
            assert result.dpi == (96.0, 96.0)

    def test_loads_rgba_as_rgb(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.png"
            rgba = np.full((10, 10, 4), 255, dtype=np.uint8)
            rgba[:, :, 3] = 128
            Image.fromarray(rgba, mode="RGBA").save(path)

            result = load_image(path)
            assert result.mode == "RGB"
            assert result.array.shape == (10, 10, 3)

    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_image("/nonexistent/path/image.png")

    def test_loads_grayscale_as_rgb(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.png"
            gray = np.full((20, 30), 64, dtype=np.uint8)
            Image.fromarray(gray, mode="L").save(path)

            result = load_image(path)
            assert result.mode == "RGB"
            assert result.array.shape == (20, 30, 3)


class TestSaveNumpyAsPng:
    def test_save_grayscale(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "out.png"
            arr = np.full((15, 15), 200, dtype=np.uint8)
            save_numpy_as_png(arr, path)
            assert path.exists()
            loaded = Image.open(path)
            assert loaded.mode == "L"

    def test_save_rgb(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "out.png"
            arr = np.full((10, 10, 3), 100, dtype=np.uint8)
            save_numpy_as_png(arr, path)
            assert path.exists()
            loaded = Image.open(path)
            assert loaded.mode == "RGB"

    def test_save_rgba(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "out.png"
            arr = np.full((10, 10, 4), 255, dtype=np.uint8)
            save_numpy_as_png(arr, path)
            assert path.exists()
            loaded = Image.open(path)
            assert loaded.mode == "RGBA"

    def test_unsupported_shape_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "out.png"
            arr = np.full((10, 10, 5), 255, dtype=np.uint8)
            with pytest.raises(ValueError):
                save_numpy_as_png(arr, path)
