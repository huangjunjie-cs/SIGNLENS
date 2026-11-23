"""Deprecated entry point; use :mod:`signlens.cli`."""

from signlens.cli import main
from signlens.cli import main as run_as_command  # noqa: F401

if __name__ == "__main__":
    main()
