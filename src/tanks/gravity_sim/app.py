"""Entry point and UI composition for the gravity simulation."""

from __future__ import annotations

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
                    pygame.draw.lines(surface, point.color, False, point.trail, 2)

        for point in simulation.points:
            pygame.draw.circle(
                surface,
                point.color,
                (int(point.position.x), int(point.position.y)),
                max(1, int(round(settings.point_radius))),
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
