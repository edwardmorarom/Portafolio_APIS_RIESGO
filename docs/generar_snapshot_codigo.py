from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess
import re


ROOT = Path(".").resolve()
OUTPUT = ROOT / "docs" / "00_snapshot_codigo_actual.md"

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
}

PY_TARGETS = [
    ROOT / "backend" / "app",
    ROOT / "frontend",
    ROOT / "tests",
]


def run_cmd(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return (result.stdout + result.stderr).strip()
    except Exception as exc:
        return f"ERROR ejecutando {' '.join(command)}: {exc}"


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def project_tree() -> list[str]:
    lines = []
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if should_skip(rel):
            continue

        if path.is_dir():
            continue

        if rel.parts and rel.parts[0] in {".venv", ".git"}:
            continue

        if path.suffix.lower() in {".py", ".md", ".txt", ".yml", ".yaml", ".json", ".toml", ".env", ".example"}:
            lines.append(str(rel).replace("\\", "/"))

    return lines


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"ERROR leyendo {path}: {exc}"


def python_files() -> list[Path]:
    files = []
    for target in PY_TARGETS:
        if not target.exists():
            continue
        for path in sorted(target.rglob("*.py")):
            rel = path.relative_to(ROOT)
            if not should_skip(rel):
                files.append(path)
    return files


def extract_imports(text: str) -> list[str]:
    imports = []
    for line in text.splitlines():
        clean = line.strip()
        if clean.startswith("from app.") or clean.startswith("import app."):
            imports.append(clean)
    return imports


def extract_decorators(text: str) -> list[str]:
    patterns = [
        r"^\s*@router\.(get|post|put|delete|patch)\(.*",
        r"^\s*@app\.(get|post|put|delete|patch|exception_handler)\(.*",
        r"^\s*@field_validator\(.*",
        r"^\s*@model_validator\(.*",
        r"^\s*@asynccontextmanager\s*$",
        r"^\s*@classmethod\s*$",
    ]

    out = []
    for line in text.splitlines():
        if any(re.match(pattern, line) for pattern in patterns):
            out.append(line.strip())
    return out


def extract_defs(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        if re.match(r"^\s*class\s+\w+", line):
            out.append(line.strip())
        elif re.match(r"^\s*def\s+\w+", line):
            out.append(line.strip())
        elif re.match(r"^\s*async\s+def\s+\w+", line):
            out.append(line.strip())
    return out


def extract_depends(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        if "Depends(" in line or "get_db" in line or "get_" in line and "_service" in line:
            out.append(line.strip())
    return out


def main() -> None:
    lines = []

    lines.append("# Snapshot técnico actual del Proyecto Portafolio Riesgo USTA")
    lines.append("")
    lines.append(f"Generado: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Git")
    lines.append("")
    lines.append("```text")
    lines.append(run_cmd(["git", "status"]))
    lines.append("```")
    lines.append("")
    lines.append("## Estructura detectada")
    lines.append("")
    lines.append("```text")
    lines.extend(project_tree())
    lines.append("```")
    lines.append("")

    readme = ROOT / "README.md"
    if readme.exists():
        lines.append("## README actual")
        lines.append("")
        lines.append("```markdown")
        lines.append(read_file(readme))
        lines.append("```")
        lines.append("")

    lines.append("## Archivos Python analizados")
    lines.append("")

    for path in python_files():
        rel = path.relative_to(ROOT)
        text = read_file(path)

        imports = extract_imports(text)
        decorators = extract_decorators(text)
        defs = extract_defs(text)
        depends = extract_depends(text)

        lines.append(f"### `{str(rel).replace('\\', '/')}`")
        lines.append("")

        if imports:
            lines.append("**Imports internos:**")
            lines.append("")
            for item in imports:
                lines.append(f"- `{item}`")
            lines.append("")

        if decorators:
            lines.append("**Decoradores detectados:**")
            lines.append("")
            for item in decorators:
                lines.append(f"- `{item}`")
            lines.append("")

        if defs:
            lines.append("**Clases y funciones:**")
            lines.append("")
            for item in defs:
                lines.append(f"- `{item}`")
            lines.append("")

        if depends:
            lines.append("**Dependencias / inyección detectada:**")
            lines.append("")
            for item in depends:
                lines.append(f"- `{item}`")
            lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK: snapshot generado en {OUTPUT}")


if __name__ == "__main__":
    main()
