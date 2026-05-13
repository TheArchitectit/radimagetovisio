#!/usr/bin/env python3
"""Cross-platform PyInstaller build script for radimagetovisio."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPECFILE = PROJECT_ROOT / "radimagetovisio.spec"
SRC = PROJECT_ROOT / "src"


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def clean() -> None:
    for name in ("build", "dist"):
        path = PROJECT_ROOT / name
        if path.exists():
            print(f"Removing {path}")
            shutil.rmtree(path)


def build(windowed: bool = False) -> None:
    python = sys.executable
    cmd = [python, "-m", "PyInstaller", str(SPECFILE), "--noconfirm"]

    if windowed:
        cmd.append("--windowed")

    _run(cmd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build radimagetovisio executable")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove previous build/dist directories before building",
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Hide console window (Windows only)",
    )
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Create a one-directory bundle instead of a single executable",
    )
    args = parser.parse_args(argv)

    if args.clean:
        clean()

    build(windowed=args.windowed)

    exe_name = "radimagetovisio.exe" if sys.platform.startswith("win") else "radimagetovisio"
    exe_path = PROJECT_ROOT / "dist" / exe_name
    if exe_path.exists():
        print(f"\nBuild complete: {exe_path}")
        return 0

    print("\nBuild finished but executable not found at expected path.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
