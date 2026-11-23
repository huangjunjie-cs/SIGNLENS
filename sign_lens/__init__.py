"""Backward-compatible API of the 2021 ``sign_lens`` package.

New code should use :mod:`signlens`; these classes delegate to it.
"""

from signlens import __version__

from .sign_lens import SignBipartiteLens, SignLens
from .utils import (
    SignedBipartiteFeaExtra,
    SignedBipartiteFeaExtraByMatrace,
    SignedTriadFeaExtra,
    SignedTriadFeaExtraByMatrace,
)

__all__ = [
    "SignBipartiteLens",
    "SignLens",
    "SignedBipartiteFeaExtra",
    "SignedBipartiteFeaExtraByMatrace",
    "SignedTriadFeaExtra",
    "SignedTriadFeaExtraByMatrace",
    "__version__",
]
