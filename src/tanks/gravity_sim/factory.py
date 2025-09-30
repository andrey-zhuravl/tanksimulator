"""Helpers for creating and maintaining simulation points."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from .constants import GROUP_COLORS, SCREEN_HEIGHT, SIMULATION_WIDTH
from .point import GravityPoint
from .settings import SimulationSettings

if TYPE_CHECKING:
    from .simulation import GravitySimulation


def create_default_points(settings: SimulationSettings, rng: random.Random) -> list[GravityPoint]:
    points: list[GravityPoint] = []
    desired = max(1, int(round(settings.num_points)))
    group_count = max(1, len(settings.group_masses))

    for index in range(desired):
        group_index = index % group_count
        points.append(create_random_point(settings, rng, group_index))

    return points


def create_random_point(
    settings: SimulationSettings, rng: random.Random, group_index: int
) -> GravityPoint:
    half_depth = max(0.0, settings.volume_depth / 2 - settings.boundary_padding - 10)
    position = pygame.Vector3(
        rng.uniform(
            settings.point_radius + settings.boundary_padding + 10,
            SIMULATION_WIDTH - settings.point_radius - settings.boundary_padding - 10,
        ),
        rng.uniform(
            settings.point_radius + settings.boundary_padding + 10,
            SCREEN_HEIGHT - settings.point_radius - settings.boundary_padding - 10,
        ),
        rng.uniform(
            -half_depth,
            half_depth,
        ),
    )
    max_initial_speed = settings.get_group_max_speed(group_index)
    spread = min(120.0, max_initial_speed * 0.25)
    velocity = pygame.Vector3(
        rng.uniform(-spread, spread),
        rng.uniform(-spread, spread),
        rng.uniform(-spread, spread),
    )
    mass = settings.get_group_mass(group_index)
    color = _color_for_group(group_index, rng)
    return GravityPoint(
        position=position,
        velocity=velocity,
        mass=mass,
        color=color,
        group_index=group_index,
    )


def ensure_point_count(
    simulation: "GravitySimulation", settings: SimulationSettings, rng: random.Random
) -> None:
    desired = max(1, int(round(settings.num_points)))
    current = len(simulation.points)

    if desired > current:
        group_count = max(1, len(settings.group_masses))
        for offset in range(desired - current):
            group_index = (current + offset) % group_count
            simulation.points.append(create_random_point(settings, rng, group_index))
    elif desired < current:
        del simulation.points[desired:]


def _color_for_group(group_index: int, rng: random.Random) -> tuple[int, int, int]:
    base = GROUP_COLORS[group_index % len(GROUP_COLORS)]
    variation = []
    for channel in base:
        jitter = rng.randint(-24, 24)
        variation.append(max(0, min(255, channel + jitter)))
    return tuple(variation)
