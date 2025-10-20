#!/usr/bin/env python3
"""
Build the standalone NukeWorks executable using PyInstaller.

This script wraps PyInstaller with the flags and data includes required
to package the Flask application into a Windows-friendly ``onedir`` bundle.

Usage (from repository root):
    python installer/build_executable.py

By default the script assumes you are running inside an environment that
already has the project dependencies (and PyInstaller) installed. It will
create/refresh ``build/`` and ``dist/NukeWorks/`` outputs.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILD_DIR = PROJECT_ROOT / "build"
DEFAULT_DIST_DIR = PROJECT_ROOT / "dist"


def ensure_supported_python() -> None:
    """Validate that the active interpreter is supported for packaging."""
    if sys.version_info >= (3, 13):
        raise SystemExit(
            "PyInstaller packaging must run under Python 3.12 or earlier. "
            "The pinned SQLAlchemy==2.0.23 release is not yet compatible with "
            "Python 3.13+, which causes runtime import failures during the build."
        )


def ensure_pyinstaller() -> None:
    """Ensure PyInstaller is importable before continuing."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError as exc:  # pragma: no cover - runtime guard
        raise SystemExit(
            "PyInstaller is not installed for this Python interpreter. "
            "Install project dependencies (including the 'pyinstaller' extra) "
            "before running this script.\n\n"
            "Example:\n"
            "    python -m pip install -r requirements.txt\n"
            "    python -m pip install pyinstaller"
        ) from exc


def build_executable(
    clean: bool,
    build_dir: Path,
    dist_dir: Path,
) -> None:
    """Invoke PyInstaller with the desired arguments."""
    ensure_supported_python()
    ensure_pyinstaller()

    if clean:
        shutil.rmtree(build_dir, ignore_errors=True)
        shutil.rmtree(dist_dir / "NukeWorks", ignore_errors=True)

    import PyInstaller.__main__  # Local import so guard above runs first

    spec_path = PROJECT_ROOT / "installer" / "nukeworks.spec"
    pyinstaller_args = [
        "--noconfirm",
        "--clean",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        str(spec_path),
    ]

    PyInstaller.__main__.run(pyinstaller_args)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build NukeWorks PyInstaller bundle")
    parser.add_argument(
        "--no-clean",
        dest="clean",
        action="store_false",
        help="Skip removing previous build/dist outputs before running PyInstaller",
    )
    parser.add_argument(
        "--dist-dir",
        default=str(DEFAULT_DIST_DIR),
        help="Directory to place the PyInstaller dist output (default: %(default)s)",
    )
    parser.add_argument(
        "--build-dir",
        default=str(DEFAULT_BUILD_DIR),
        help="Directory to place the PyInstaller build artifacts (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    build_executable(
        clean=args.clean,
        build_dir=Path(args.build_dir).resolve(),
        dist_dir=Path(args.dist_dir).resolve(),
    )


if __name__ == "__main__":
    main()
