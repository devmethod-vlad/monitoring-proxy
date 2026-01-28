from pathlib import Path

import toml


def find_pyproject(start: Path | str = None) -> Path | None:
    """Идёт вверх по папкам, начиная с start (или текущей папки),
    пока не найдёт pyproject.toml.
    """
    current = Path(start or __file__).resolve()
    for parent in [current] + list(current.parents):
        candidate = parent / "pyproject.toml"
        if candidate.exists():
            return candidate
    return None


def get_app_version() -> str:
    """Получает версию приложения."""
    pyproject_path = find_pyproject()
    if not pyproject_path:
        return "unknown"

    data = toml.load(pyproject_path)
    return data.get("project", {}).get("version", "unknown")
