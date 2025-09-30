"""Gravity point simulation module.

This module can be executed as a script to display a simple
five-body gravity simulation. The total kinetic energy of the
points is kept under control so that they cannot leave the screen
bounds.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable, List

import pygame


SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
BACKGROUND_COLOR = (15, 15, 30)
POINT_COLORS = [
    (240, 98, 146),
    (129, 212, 250),
    (244, 143, 177),
    (165, 214, 167),
    (255, 224, 130),
]
POINT_RADIUS = 10
GRAVITATIONAL_CONSTANT = 5000.0
MAX_SPEED = 220.0
TIME_STEP = 1.0 / 60.0
BOUNDARY_PADDING = 4
BOUNCE_DAMPING = 0.9


@dataclass
class GravityPoint:
    """A simple body affected by gravity."""

    position: pygame.Vector2
    velocity: pygame.Vector2
    mass: float
    color: tuple[int, int, int]

    def kinetic_energy(self) -> float:
        return 0.5 * self.mass * self.velocity.length_squared()

    @property
    def max_kinetic_energy(self) -> float:
        return 0.5 * self.mass * MAX_SPEED * MAX_SPEED

    def limit_energy(self) -> None:
        energy = self.kinetic_energy()
        if energy > self.max_kinetic_energy:
            scale = math.sqrt(self.max_kinetic_energy / energy)
            self.velocity *= scale


class GravitySimulation:
    """Manage the interaction between multiple gravity points."""

    def __init__(self, points: Iterable[GravityPoint]):
        self.points: List[GravityPoint] = list(points)

    def step(self, dt: float) -> None:
        forces = [pygame.Vector2() for _ in self.points]

        for i in range(len(self.points)):
            for j in range(i + 1, len(self.points)):
                pi = self.points[i]
                pj = self.points[j]
                offset = pj.position - pi.position
                distance_sq = offset.length_squared()
                if distance_sq < 1e-4:
                    continue
                clamped_distance_sq = max(distance_sq, 25.0)
                force_magnitude = (
                    GRAVITATIONAL_CONSTANT * pi.mass * pj.mass / clamped_distance_sq
                )
                force_direction = offset.normalize()
                force = force_direction * force_magnitude
                forces[i] += force
                forces[j] -= force

        for point, force in zip(self.points, forces):
            acceleration = force / point.mass
            point.velocity += acceleration * dt
            point.limit_energy()
            point.position += point.velocity * dt
            self._keep_inside(point)

    def _keep_inside(self, point: GravityPoint) -> None:
        limit_x = SCREEN_WIDTH - POINT_RADIUS - BOUNDARY_PADDING
        limit_y = SCREEN_HEIGHT - POINT_RADIUS - BOUNDARY_PADDING
        min_x = POINT_RADIUS + BOUNDARY_PADDING
        min_y = POINT_RADIUS + BOUNDARY_PADDING

        if point.position.x < min_x:
            point.position.x = min_x
            if point.velocity.x < 0:
                point.velocity.x *= -BOUNCE_DAMPING
        elif point.position.x > limit_x:
            point.position.x = limit_x
            if point.velocity.x > 0:
                point.velocity.x *= -BOUNCE_DAMPING

        if point.position.y < min_y:
            point.position.y = min_y
            if point.velocity.y < 0:
                point.velocity.y *= -BOUNCE_DAMPING
        elif point.position.y > limit_y:
            point.position.y = limit_y
            if point.velocity.y > 0:
                point.velocity.y *= -BOUNCE_DAMPING

        point.limit_energy()


def _create_default_points() -> List[GravityPoint]:
    rng = random.Random()
    points: List[GravityPoint] = []
    for index in range(5):
        position = pygame.Vector2(
            rng.uniform(POINT_RADIUS + 80, SCREEN_WIDTH - POINT_RADIUS - 80),
            rng.uniform(POINT_RADIUS + 80, SCREEN_HEIGHT - POINT_RADIUS - 80),
        )
        velocity = pygame.Vector2(
            rng.uniform(-80.0, 80.0),
            rng.uniform(-80.0, 80.0),
        )
        mass = rng.uniform(1.0, 3.0)
        points.append(
            GravityPoint(
                position=position,
                velocity=velocity,
                mass=mass,
                color=POINT_COLORS[index % len(POINT_COLORS)],
            )
        )
    return points


def run() -> None:
    """Launch the gravity simulation window."""

    pygame.init()
    clock = pygame.time.Clock()
    surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Gravity point simulation")

    simulation = GravitySimulation(_create_default_points())

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        surface.fill(BACKGROUND_COLOR)
        simulation.step(TIME_STEP)

        for point in simulation.points:
            pygame.draw.circle(
                surface,
                point.color,
                (int(point.position.x), int(point.position.y)),
                POINT_RADIUS,
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    run()
