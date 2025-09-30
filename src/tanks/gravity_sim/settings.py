"""Simulation configuration dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class SimulationSettings:
    """Parameters that can be tuned during the simulation."""

    num_points: int = 150
    point_radius: float = 2.0
    gravitational_constant: float = 600000.0
    max_speed: float = 1720.0
    time_step: float = 1.0 / 120.0
    boundary_padding: float = 4.0
    bounce_damping: float = 0.9
    softening_distance: float = 0.01
    max_force: float = 15000.0
    group_masses: List[float] = field(default_factory=lambda: [140.0, 220.0, 320.0, 140.0, 220.0])
    group_max_speeds: List[float] = field(default_factory=lambda: [1200.0, 1600.0, 2000.0,1200.0, 1600.0])

    def get_group_mass(self, index: int) -> float:
        if not self.group_masses:
            return 1.0
        safe_index = max(0, min(index, len(self.group_masses) - 1))
        return max(1e-3, self.group_masses[safe_index])

    def set_group_mass(self, index: int, value: float) -> None:
        if not self.group_masses:
            self.group_masses = [max(1e-3, value)]
            return
        safe_index = max(0, min(index, len(self.group_masses) - 1))
        self.group_masses[safe_index] = max(1e-3, value)

    def get_group_max_speed(self, index: int) -> float:
        if not self.group_max_speeds:
            return self.max_speed
        safe_index = max(0, min(index, len(self.group_max_speeds) - 1))
        return max(1.0, self.group_max_speeds[safe_index])

    def set_group_max_speed(self, index: int, value: float) -> None:
        if not self.group_max_speeds:
            self.group_max_speeds = [max(1.0, value)]
            return
        safe_index = max(0, min(index, len(self.group_max_speeds) - 1))
        self.group_max_speeds[safe_index] = max(1.0, value)
