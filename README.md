# RadImageToVisio

[![Sponsor](https://img.shields.io/badge/Sponsor-TheArchitectit-FF69B4?style=flat&logo=github-sponsors)](https://github.com/sponsors/TheArchitectit)

Cross-platform desktop application that converts images into Visio-compatible diagrams using computer vision and OCR.

## Features

- **Image import**: Load PNG, JPG, BMP, TIFF images
- **Shape detection**: Automatically detect rectangles, ellipses, diamonds, parallelograms, triangles, and connectors
- **Text recognition**: OCR for labels and text boxes via Tesseract
- **Diagram export**: Export to SVG or VSDX (Visio) formats
- **Interactive editor**: PyQt6-based canvas with zoom, pan, drag-to-arrange, and shape palette
- **Batch CLI**: Convert images directly from the command line without launching the GUI

## System Requirements

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (external binary dependency)

### Installing Tesseract

**Windows**
1. Download the installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install to `C:\Program Files\Tesseract-OCR`
3. Add `C:\Program Files\Tesseract-OCR` to your system `PATH`

**Linux / Arch**
```bash
# Debian / Ubuntu
sudo apt install tesseract-ocr

# Fedora
sudo dnf install tesseract

# Arch Linux
sudo pacman -S tesseract tesseract-data-eng
```

**macOS**
```bash
brew install tesseract
```

## Running from Source

```bash
# Clone the repository
git clone <repo-url>
cd radimagetovisio

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -e ".[dev]"

# Run the GUI
python -m radimagetovisio

# Or batch convert from the command line
python -m radimagetovisio input.png output.vsdx
python -m radimagetovisio input.jpg output.svg
```

## Quick Convert (GUI)

Open the GUI and use **File → Quick Convert** (Ctrl+Q) to pick an image and export a diagram in a single step.

## Running Tests

```bash
# All tests
PYTHONPATH=src python -m pytest tests/ -v

# Export integration tests only
PYTHONPATH=src python -m pytest tests/integration/ -v
```

## Building Distributable Artifacts

### Linux / Arch

```bash
source .venv/bin/activate
python scripts/build.py --clean
```

The executable will be created at `dist/radimagetovisio`.

### Windows

```powershell
.venv\Scripts\Activate.ps1
python scripts/build.py --clean --windowed
```

The executable will be created at `dist\radimagetovisio.exe`.

### Build Options

| Flag | Description |
|------|-------------|
| `--clean` | Remove previous `build/` and `dist/` directories |
| `--windowed` | Hide console window (Windows only) |
| `--onedir` | Create a folder bundle instead of a single executable |

## Project Structure

```
src/radimagetovisio/
  app.py              # GUI application entry point
  cli.py              # Command-line batch converter
  __main__.py         # Auto-detects CLI vs GUI mode
  gui/                # PyQt6 widgets (main window, canvas, image view)
  models/             # Data models (Diagram, Page, Shape, Connector, TextBox)
  vision/             # Computer vision pipeline (detection, OCR, inference)
  exporters/          # SVG and VSDX export writers
  utils/              # Image I/O utilities

tests/
  unit/               # Unit tests for models and vision modules
  integration/        # End-to-end exporter tests

scripts/
  build.py            # PyInstaller build script
```

## License

BSD 3-Clause License. See [LICENSE](LICENSE).

---

---

### ☕ Support This Project

Help keep this project going — use a referral link below and both of us get credits!

| Service | Your Bonus | Details | Referral Code |
| --------- | ----------- | --------- | --------------- |
| [**Neuralwatt**](https://portal.neuralwatt.com/auth/register?ref=NW-ROGER-ET3Y) | $10 in credits | Spend $10+ → you get $10, we get $20 | `NW-ROGER-ET3Y` |
| [**Synthetic**](https://synthetic.new/?referral=UAWqkKQQLFkzMkY) | $10 in credits | Subscribe → both get $10 credit | `UAWqkKQQLFkzMkY` |

## ☁️ Cloud Credits

Power your AI projects with [Ozore.com](https://ozore.com/?ref=cwe4kdx0) — use code **lundrog50** for 50% off your first month.

## ☕ Support

If this project helped you, consider buying me a coffee:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-TheArchitectit-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/TheArchitectit)

If this project helps you, consider sponsoring on GitHub: [github.com/sponsors/TheArchitectit](https://github.com/sponsors/TheArchitectit)
