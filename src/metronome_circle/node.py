"""Definitions related to nodes within the metronome circle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Node:
    """Represents a single node in the circular graph."""

    index: int
    position: Tuple[int, int]
