"""Entry point and UI composition for the gravity simulation."""

from __future__ import annotations

import math
import random

import pygame

from .constants import (
    BACKGROUND_COLOR,
    CONTROL_PANEL_WIDTH,
    PANEL_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SIMULATION_WIDTH,
    TEXT_COLOR,
)
from .factory import create_default_points, ensure_point_count
from .feedback import DensityFeedbackController
from .settings import SimulationSettings
from .simulation import GravitySimulation
from .slider import Slider
from .utils import format_float, format_int_like


def run() -> None:
    """Launch the gravity simulation window."""

    pygame.init()
    pygame.font.init()
    clock = pygame.time.Clock()
    surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Gravity point simulation")

    font = pygame.font.SysFont("arial", 16)
    info_font = pygame.font.SysFont("arial", 18)

    rng = random.Random()
    settings = SimulationSettings()
    simulation = GravitySimulation(settings, create_default_points(settings, rng))
    feedback = DensityFeedbackController(settings, simulation)
    sliders = _build_sliders(settings)
    trails_enabled = True

    running = True
    while running:
        dt_real = clock.tick(240) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                trails_enabled = not trails_enabled

            for slider in sliders:
                slider.handle_event(event)

        ensure_point_count(simulation, settings, rng)
        simulation.step(settings.time_step)
        feedback.update(dt_real)

        surface.fill(BACKGROUND_COLOR)
        pygame.draw.rect(
            surface,
            PANEL_COLOR,
            pygame.Rect(SIMULATION_WIDTH, 0, CONTROL_PANEL_WIDTH, SCREEN_HEIGHT),
        )

        if trails_enabled:
            for point in simulation.points:
                if len(point.trail) > 1:
                    trail_points: list[tuple[int, int]] = []
                    for position in point.trail:
                        projection = _project_point(position, settings)
                        if projection is None:
                            continue
                        (tx, ty), _, _ = projection
                        if not math.isfinite(tx) or not math.isfinite(ty):
                            continue
                        if tx < 0 or tx >= SIMULATION_WIDTH or ty < 0 or ty >= SCREEN_HEIGHT:
                            continue
                        trail_points.append((int(tx), int(ty)))
                    if len(trail_points) > 1:
                        pygame.draw.lines(surface, point.color, False, trail_points, 2)

        drawable_points: list[tuple[float, float, float, int, tuple[int, int, int]]] = []
        for point in simulation.points:
            projection = _project_point(point.position, settings)
            if projection is None:
                continue
            (px, py), scale, depth = projection
            if not math.isfinite(px) or not math.isfinite(py) or scale <= 0:
                continue
            if px < 0 or px >= SIMULATION_WIDTH or py < 0 or py >= SCREEN_HEIGHT:
                continue
            radius = max(1, min(60, int(round(settings.point_radius * scale))))
            drawable_points.append((depth, px, py, radius, point.color))

        drawable_points.sort(key=lambda item: item[0], reverse=True)

        for _, px, py, radius, color in drawable_points:
            pygame.draw.circle(
                surface,
                color,
                (int(px), int(py)),
                radius,
            )

        title_surface = info_font.render("Controls", True, TEXT_COLOR)
        surface.blit(title_surface, (SIMULATION_WIDTH + 24, 24))

        trails_text = "Trails: ON" if trails_enabled else "Trails: OFF"
        trails_surface = font.render(f"{trails_text} (press T)", True, TEXT_COLOR)
        surface.blit(trails_surface, (SIMULATION_WIDTH + 24, 50))

        density_surface = font.render(
            f"Density: {simulation.last_density_metric:.2f}", True, TEXT_COLOR
        )
        surface.blit(density_surface, (SIMULATION_WIDTH + 24, 74))

        pulse_surface = font.render(
            f"Pulse: {feedback.current_frequency:.2f} Hz", True, TEXT_COLOR
        )
        surface.blit(pulse_surface, (SIMULATION_WIDTH + 24, 92))

        mode_surface = font.render(
            f"Mode: {feedback.current_mode.capitalize()}", True, TEXT_COLOR
        )
        surface.blit(mode_surface, (SIMULATION_WIDTH + 24, 110))

        for slider in sliders:
            slider.draw(surface, font)

        pygame.display.flip()

    pygame.quit()


def _build_sliders(settings: SimulationSettings) -> list[Slider]:
    sliders: list[Slider] = []
    start_x = SIMULATION_WIDTH + 24
    start_y = 150
    length = CONTROL_PANEL_WIDTH - 80
    vertical_spacing = 60

    specs = [
        (
            "Point count",
            "num_points",
            2.0,
            25.0,
            lambda v: max(1, int(round(v))),
            lambda v: format_int_like(v),
        ),
        (
            "Point radius",
            "point_radius",
            1.0,
            16.0,
            lambda v: round(v, 1),
            lambda v: f"{v:.1f} px",
        ),
        (
            "Gravity",
            "gravitational_constant",
            100.0,
            1200000.0,
            lambda v: v,
            lambda v: f"{v:,.0f}",
        ),
        (
            "Max speed",
            "max_speed",
            100.0,
            15000.0,
            lambda v: v,
            lambda v: f"{v:,.0f}",
        ),
        (
            "Time step",
            "time_step",
            1.0 / 240.0,
            1.0 / 30.0,
            lambda v: v,
            lambda v: f"{v*1000:.2f} ms",
        ),
        (
            "Boundary pad",
            "boundary_padding",
            0.0,
            40.0,
            lambda v: round(v, 1),
            lambda v: f"{v:.1f} px",
        ),
        (
            "Bounce",
            "bounce_damping",
            0.5,
            1.0,
            lambda v: round(v, 2),
            lambda v: format_float(v, 2),
        ),
        (
            "Softening",
            "softening_distance",
            0.0,
            60.0,
            lambda v: round(v, 2),
            lambda v: f"{v:.2f}",
        ),
        (
            "Max force",
            "max_force",
            1000.0,
            80000.0,
            lambda v: v,
            lambda v: f"{v:,.0f}",
        ),
        (
            "Camera distance",
            "projection_distance",
            200.0,
            4000.0,
            lambda v: round(max(50.0, v), 1),
            lambda v: f"{v:.0f}",
        ),
        (
            "Perspective",
            "perspective_angle",
            10.0,
            140.0,
            lambda v: round(max(5.0, min(175.0, v)), 1),
            lambda v: f"{v:.1f}°",
        ),
        (
            "Rotate X",
            "rotation_x",
            -180.0,
            180.0,
            lambda v: round(v, 1),
            lambda v: f"{v:.1f}°",
        ),
        (
            "Rotate Y",
            "rotation_y",
            -180.0,
            180.0,
            lambda v: round(v, 1),
            lambda v: f"{v:.1f}°",
        ),
        (
            "Rotate Z",
            "rotation_z",
            -180.0,
            180.0,
            lambda v: round(v, 1),
            lambda v: f"{v:.1f}°",
        ),
    ]

    for index, (label, attr, min_v, max_v, postprocess, formatter) in enumerate(specs):
        position = (start_x, start_y + index * vertical_spacing)
        sliders.append(
            Slider(
                label=label,
                attr=attr,
                settings=settings,
                min_value=min_v,
                max_value=max_v,
                position=position,
                length=length,
                postprocess=postprocess,
                formatter=formatter,
            )
        )

    group_start_y = start_y + len(specs) * vertical_spacing + 40
    group_labels = [f"Group {index + 1}" for index in range(len(settings.group_masses))]

    for group_index, label in enumerate(group_labels):
        mass_position = (start_x, group_start_y + (group_index * 2) * vertical_spacing)
        sliders.append(
            Slider(
                label=f"{label} mass",
                attr=None,
                settings=settings,
                min_value=20.0,
                max_value=800.0,
                position=mass_position,
                length=length,
                postprocess=lambda v: round(max(1.0, v), 1),
                formatter=lambda v: f"{v:.1f}",
                getter=lambda idx=group_index: settings.get_group_mass(idx),
                setter=lambda value, idx=group_index: settings.set_group_mass(idx, value),
            )
        )

        speed_position = (
            start_x,
            group_start_y + (group_index * 2 + 1) * vertical_spacing,
        )
        sliders.append(
            Slider(
                label=f"{label} max speed",
                attr=None,
                settings=settings,
                min_value=100.0,
                max_value=15000.0,
                position=speed_position,
                length=length,
                postprocess=lambda v: max(100.0, v),
                formatter=lambda v: f"{v:,.0f}",
                getter=lambda idx=group_index: settings.get_group_max_speed(idx),
                setter=lambda value, idx=group_index: settings.set_group_max_speed(idx, value),
            )
        )

    return sliders


def _project_point(
    position: pygame.Vector3, settings: SimulationSettings
) -> tuple[tuple[float, float], float, float] | None:
    center = pygame.Vector3(SIMULATION_WIDTH / 2, SCREEN_HEIGHT / 2, 0.0)
    relative = position - center
    rotated = _rotate_vector(relative, settings)

    distance = max(10.0, settings.projection_distance)
    z = rotated.z + distance
    if z <= 1.0:
        return None

    angle = max(5.0, min(175.0, settings.perspective_angle))
    fov_rad = math.radians(angle)
    tan_half = math.tan(fov_rad / 2.0)
    if tan_half <= 0.0:
        return None

    focal_length_x = 0.5 * SIMULATION_WIDTH / tan_half
    focal_length_y = 0.5 * SCREEN_HEIGHT / tan_half
    projected_x = (rotated.x * focal_length_x) / z + SIMULATION_WIDTH / 2
    projected_y = (rotated.y * focal_length_y) / z + SCREEN_HEIGHT / 2
    scale = focal_length_y / z
    return (projected_x, projected_y), scale, z


def _rotate_vector(vector: pygame.Vector3, settings: SimulationSettings) -> pygame.Vector3:
    rotated = pygame.Vector3(vector)

    rx = math.radians(settings.rotation_x)
    ry = math.radians(settings.rotation_y)
    rz = math.radians(settings.rotation_z)

    cos_x, sin_x = math.cos(rx), math.sin(rx)
    y = rotated.y * cos_x - rotated.z * sin_x
    z = rotated.y * sin_x + rotated.z * cos_x
    rotated.y, rotated.z = y, z

    cos_y, sin_y = math.cos(ry), math.sin(ry)
    x = rotated.x * cos_y + rotated.z * sin_y
    z = -rotated.x * sin_y + rotated.z * cos_y
    rotated.x, rotated.z = x, z

    cos_z, sin_z = math.cos(rz), math.sin(rz)
    x = rotated.x * cos_z - rotated.y * sin_z
    y = rotated.x * sin_z + rotated.y * cos_z
    rotated.x, rotated.y = x, y

    return rotated

