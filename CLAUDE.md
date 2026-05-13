# radimagetovisio — Agent Guidelines

## Guardrails

This project adopts the **Four Laws of Agent Safety** and all mandatory guardrails from `agent-guardrails-template`. Every agent operation must comply with:

1. **Read Before Editing** — Never modify a file without reading it first.
2. **Stay in Scope** — Only touch files within the authorized task. No "while I'm here" fixes.
3. **Verify Before Committing** — Run tests and checks before any commit.
4. **Halt When Uncertain** — Ask the user instead of guessing.

Additional mandatory rules:
- **Three Strikes Rule**: Max 3 attempts per task; halt and escalate on the 3rd failure.
- **Production-First**: Production code is created before test or infrastructure code.
- **Test/Prod Separation**: Test infrastructure is separate from production logic.
- **No Feature Creep**: Do not add features, refactor, or improve unrelated code without approval.
- **500-Line Max**: No source file may exceed 500 lines; refactor when approaching this limit.
- **Single Focused Commits**: One commit per milestone or task.
- **No Skip Hooks**: Never use `--no-verify` to bypass safety checks.

## Stack

- **Language**: Python 3.10+
- **GUI**: PyQt6
- **Image Processing**: OpenCV + Pillow + NumPy
- **OCR**: pytesseract (requires Tesseract system package)
- **SVG Export**: svgwrite
- **VSDX Export**: Manual OOXML ZIP via `zipfile` + `lxml`
- **Testing**: pytest + pytest-qt
- **Lint/Format**: black, ruff, mypy
- **Packaging**: pyproject.toml (hatchling) + PyInstaller

## Project Structure

- `src/radimagetovisio/` — Application code
  - `gui/` — Qt widgets and dialogs
  - `models/` — Diagram data model (pure dataclasses)
  - `vision/` — Image processing, OCR, and diagram inference
  - `exporters/` — SVG and VSDX export logic
  - `utils/` — Image I/O helpers
- `tests/unit/` — Unit tests
- `tests/integration/` — Integration tests
- `assets/stencils/` — Minimal built-in Visio master shape XML

## Workflow

1. **Read** the target file(s) before editing.
2. **Scope check** — confirm the file is within the current task.
3. **Edit** — small, single-file changes preferred.
4. **Test** — run relevant tests (`pytest`, `pytest-qt`).
5. **Lint** — run `black`, `ruff`, `mypy`.
6. **Commit** — single focused commit per task (only when user requests).

## Halt Conditions

Stop and ask the user when:
- Requirements are ambiguous or have multiple interpretations.
- A file exceeds 500 lines and needs refactoring.
- The .vsdx exporter fails 3 times on a milestone.
- A change would break existing functionality.
- Scope boundaries are unclear.

## References

- `../agent-guardrails-template/docs/AGENT_GUARDRAILS.md` — Core safety protocols
- `../agent-guardrails-template/skills/four-laws/SKILL.md` — Four Laws canonical definition
- `../agent-guardrails-template/skills/halt-conditions/SKILL.md` — Full halt conditions
- `../agent-guardrails-template/skills/scope-validator/SKILL.md` — Scope rules
