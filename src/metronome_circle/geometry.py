"""Geometric helpers for the metronome circle application."""

from __future__ import annotations

import math
from typing import List, Tuple

from .node import Node


def step_positions(center: Tuple[int, int], radius: int, total_steps: int) -> List[Node]:
    """Calculate cartesian coordinates for equally spaced nodes on a circle."""

    cx, cy = center
    nodes: List[Node] = []
    for index in range(total_steps):
        angle = (math.tau * index / total_steps) - math.pi / 2
        x = int(cx + radius * math.cos(angle))
        y = int(cy + radius * math.sin(angle))
        nodes.append(Node(index=index, position=(x, y)))
    return nodes
