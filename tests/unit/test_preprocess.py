
import cv2
import numpy as np

from radimagetovisio.vision.preprocess import (
    adaptive_threshold,
    clahe,
    denoise,
    deskew,
    morphological_cleanup,
    otsu_threshold,
    to_grayscale,
)


class TestToGrayscale:
    def test_rgb_to_gray(self) -> None:
        rgb = np.full((10, 10, 3), 128, dtype=np.uint8)
        gray = to_grayscale(rgb)
        assert gray.ndim == 2
        assert gray.shape == (10, 10)

    def test_gray_unchanged(self) -> None:
        gray = np.full((10, 10), 128, dtype=np.uint8)
        result = to_grayscale(gray)
        assert result.ndim == 2
        assert np.array_equal(result, gray)


class TestDenoise:
    def test_denoise_rgb(self) -> None:
        rgb = np.random.randint(0, 255, (20, 20, 3), dtype=np.uint8)
        result = denoise(rgb, strength=5)
        assert result.shape == rgb.shape

    def test_denoise_gray(self) -> None:
        gray = np.random.randint(0, 255, (20, 20), dtype=np.uint8)
        result = denoise(gray, strength=5)
        assert result.shape == gray.shape


class TestDeskew:
    def test_no_skew_returns_copy(self) -> None:
        white = np.full((30, 30, 3), 255, dtype=np.uint8)
        black_box = np.zeros((10, 10, 3), dtype=np.uint8)
        white[10:20, 10:20] = black_box
        result = deskew(white, max_angle=5.0)
        assert result.shape == white.shape

    def test_skewed_image_corrected(self) -> None:
        black = np.zeros((50, 50, 3), dtype=np.uint8)
        angle = 2.0
        center = (25, 25)
        _M = cv2.getRotationMatrix2D(center, angle, 1.0)
        skewed = cv2.warpAffine(black, _M, (50, 50), borderValue=(255, 255, 255))
        result = deskew(skewed, max_angle=5.0)
        assert result.shape == skewed.shape

    def test_too_large_angle_returns_copy(self) -> None:
        white = np.full((30, 30, 3), 255, dtype=np.uint8)
        result = deskew(white, max_angle=0.5)
        assert result.shape == white.shape


class TestAdaptiveThreshold:
    def test_produces_binary(self) -> None:
        gray = np.random.randint(0, 255, (30, 30), dtype=np.uint8)
        binary = adaptive_threshold(gray, block_size=11, c=2.0)
        assert binary.ndim == 2
        assert set(np.unique(binary)) <= {0, 255}

    def test_rgb_input(self) -> None:
        rgb = np.random.randint(0, 255, (30, 30, 3), dtype=np.uint8)
        binary = adaptive_threshold(rgb, block_size=11, c=2.0)
        assert binary.ndim == 2


class TestOtsuThreshold:
    def test_produces_binary(self) -> None:
        gray = np.random.randint(0, 255, (30, 30), dtype=np.uint8)
        binary = otsu_threshold(gray)
        assert binary.ndim == 2
        assert set(np.unique(binary)) <= {0, 255}


class TestMorphologicalCleanup:
    def test_cleans_noise(self) -> None:
        binary = np.zeros((30, 30), dtype=np.uint8)
        binary[5:25, 5:25] = 255
        binary[0, 0] = 255
        result = morphological_cleanup(binary, kernel_size=3, iterations=1)
        assert result.shape == binary.shape
        assert result.ndim == 2


class TestClahe:
    def test_rgb_enhancement(self) -> None:
        rgb = np.random.randint(0, 255, (20, 20, 3), dtype=np.uint8)
        result = clahe(rgb, clip_limit=2.0)
        assert result.shape == rgb.shape
        assert result.ndim == 3

    def test_grayscale_enhancement(self) -> None:
        gray = np.random.randint(0, 255, (20, 20), dtype=np.uint8)
        result = clahe(gray, clip_limit=2.0)
        assert result.shape == gray.shape
        assert result.ndim == 2
