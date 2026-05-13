from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass
class ImageLoadResult:
    array: np.ndarray
    path: Path
    width: int
    height: int
    mode: str
    dpi: tuple[float, float]


def load_image(path: str | Path) -> ImageLoadResult:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {p}")

    with Image.open(p) as img:
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        dpi = img.info.get("dpi", (96.0, 96.0))
        if dpi[0] is None or dpi[1] is None:
            dpi = (96.0, 96.0)

    return ImageLoadResult(
        array=arr,
        path=p,
        width=arr.shape[1],
        height=arr.shape[0],
        mode="RGB",
        dpi=dpi,
    )


def save_numpy_as_png(arr: np.ndarray, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if arr.ndim == 2:
        mode = "L"
    elif arr.ndim == 3 and arr.shape[2] == 3:
        mode = "RGB"
    elif arr.ndim == 3 and arr.shape[2] == 4:
        mode = "RGBA"
    else:
        raise ValueError(f"Unsupported array shape for PNG export: {arr.shape}")
    Image.fromarray(arr, mode=mode).save(p, format="PNG")
