"""Core integration logic for the gravity simulation."""

from __future__ import annotations

import math
from typing import Iterable, List

import pygame

from .constants import SCREEN_HEIGHT, SIMULATION_WIDTH, TRAIL_MAX_LENGTH
from .point import GravityPoint
from .settings import SimulationSettings


class GravitySimulation:
    """Manage the interaction between multiple gravity points."""

    def __init__(self, settings: SimulationSettings, points: Iterable[GravityPoint]):
        self.settings = settings
        self.points: List[GravityPoint] = list(points)
        self.last_average_acceleration: float = 0.0
        self.last_average_acceleration_vector: pygame.Vector3 = pygame.Vector3()
        self.last_average_mass: float = 0.0
        self.last_center_of_mass: pygame.Vector3 = pygame.Vector3(
            SIMULATION_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            0.0,
        )
        self.last_density_metric: float = 0.0
        diagonal_sq = (
            SIMULATION_WIDTH * SIMULATION_WIDTH
            + SCREEN_HEIGHT * SCREEN_HEIGHT
            + self.settings.volume_depth * self.settings.volume_depth
        )
        self._max_density_radius = math.sqrt(diagonal_sq) / 2.0
        self._update_density_stats()

    def step(self, dt: float) -> None:
        for point in self.points:
            point.mass = self.settings.get_group_mass(point.group_index)

        forces = [pygame.Vector3() for _ in self.points]
        softening_sq = self.settings.softening_distance * self.settings.softening_distance

        for i in range(len(self.points)):
            for j in range(i + 1, len(self.points)):
                pi = self.points[i]
                pj = self.points[j]
                offset = pj.position - pi.position
                distance_sq = offset.length_squared()
                if distance_sq < 1e-6:
                    continue

                softened_distance_sq = distance_sq + softening_sq
                force_magnitude = (
                    self.settings.gravitational_constant * pi.mass * pj.mass / softened_distance_sq
                )
                force_magnitude = min(force_magnitude, self.settings.max_force)
                force_direction = offset.normalize()
                force = force_direction * force_magnitude
                forces[i] += force
                forces[j] -= force

        total_acceleration = pygame.Vector3()
        total_magnitude = 0.0

        for point, force in zip(self.points, forces):
            acceleration = force / point.mass
            total_acceleration += acceleration
            total_magnitude += acceleration.length()
            point.velocity += acceleration * dt
            group_speed_limit = min(
                self.settings.max_speed,
                self.settings.get_group_max_speed(point.group_index),
            )
            point.limit_speed(group_speed_limit)
            point.position += point.velocity * dt
            self._keep_inside(point)
            point.limit_speed(group_speed_limit)
            if TRAIL_MAX_LENGTH > 0:
                point.trail.append(point.position.copy())
                if len(point.trail) > TRAIL_MAX_LENGTH:
                    del point.trail[: len(point.trail) - TRAIL_MAX_LENGTH]

        count = len(self.points)
        if count > 0:
            self.last_average_acceleration_vector = total_acceleration / count
            self.last_average_acceleration = total_magnitude / count
        else:
            self.last_average_acceleration_vector = pygame.Vector3()
            self.last_average_acceleration = 0.0

        self._update_density_stats()

    def _keep_inside(self, point: GravityPoint) -> None:
        radius = self.settings.point_radius
        padding = self.settings.boundary_padding

        limit_x = SIMULATION_WIDTH - radius - padding
        limit_y = SCREEN_HEIGHT - radius - padding
        half_depth = max(0.0, self.settings.volume_depth / 2 - radius - padding)
        min_x = radius + padding
        min_y = radius + padding
        max_z = half_depth
        min_z = -half_depth

        if point.position.x < min_x:
            point.position.x = min_x
            if point.velocity.x < 0:
                point.velocity.x *= -self.settings.bounce_damping
        elif point.position.x > limit_x:
            point.position.x = limit_x
            if point.velocity.x > 0:
                point.velocity.x *= -self.settings.bounce_damping

        if point.position.y < min_y:
            point.position.y = min_y
            if point.velocity.y < 0:
                point.velocity.y *= -self.settings.bounce_damping
        elif point.position.y > limit_y:
            point.position.y = limit_y
            if point.velocity.y > 0:
                point.velocity.y *= -self.settings.bounce_damping

        if point.position.z < min_z:
            point.position.z = min_z
            if point.velocity.z < 0:
                point.velocity.z *= -self.settings.bounce_damping
        elif point.position.z > max_z:
            point.position.z = max_z
            if point.velocity.z > 0:
                point.velocity.z *= -self.settings.bounce_damping

    def _update_density_stats(self) -> None:
        if not self.points:
            self.last_density_metric = 0.0
            self.last_average_mass = 0.0
            self.last_center_of_mass = pygame.Vector3(
                SIMULATION_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                0.0,
            )
            return

        total_mass = sum(point.mass for point in self.points)
        if total_mass <= 0:
            self.last_density_metric = 0.0
            self.last_average_mass = 0.0
            self.last_center_of_mass = pygame.Vector3(
                SIMULATION_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                0.0,
            )
            return

        weighted_position = pygame.Vector3()
        for point in self.points:
            weighted_position += point.position * point.mass

        center = weighted_position / total_mass
        self.last_center_of_mass = center
        self.last_average_mass = total_mass / len(self.points)

        average_distance = 0.0
        for point in self.points:
            average_distance += (point.position - center).length()

        average_distance /= len(self.points)

        if self._max_density_radius > 0:
            normalized = min(1.0, average_distance / self._max_density_radius)
            self.last_density_metric = 1.0 - normalized
        else:
            self.last_density_metric = 0.0
