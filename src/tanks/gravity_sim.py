"""Interactive gravity point simulation with adjustable parameters."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Iterable, List

import pygame


SCREEN_WIDTH = 2200
SCREEN_HEIGHT = 1240
CONTROL_PANEL_WIDTH = 260
SIMULATION_WIDTH = SCREEN_WIDTH - CONTROL_PANEL_WIDTH
BACKGROUND_COLOR = (15, 15, 30)
PANEL_COLOR = (28, 28, 48)
TEXT_COLOR = (220, 220, 230)
SLIDER_TRACK_COLOR = (80, 80, 110)
SLIDER_HANDLE_COLOR = (210, 210, 230)
TRAIL_MAX_LENGTH = 1


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


@dataclass
class GravityPoint:
    """A simple body affected by gravity."""

    position: pygame.Vector2
    velocity: pygame.Vector2
    mass: float
    color: tuple[int, int, int]
    trail: List[tuple[float, float]] = field(default_factory=list)

    def limit_speed(self, max_speed: float) -> None:
        max_speed_sq = max_speed * max_speed
        velocity_sq = self.velocity.length_squared()
        if velocity_sq > max_speed_sq and velocity_sq > 0:
            scale = math.sqrt(max_speed_sq / velocity_sq)
            self.velocity *= scale


class GravitySimulation:
    """Manage the interaction between multiple gravity points."""

    def __init__(self, settings: SimulationSettings, points: Iterable[GravityPoint]):
        self.settings = settings
        self.points: List[GravityPoint] = list(points)
        self.last_average_acceleration: float = 0.0
        self.last_average_acceleration_vector: pygame.Vector2 = pygame.Vector2()
        self.last_average_mass: float = 0.0
        self.last_center_of_mass: pygame.Vector2 = pygame.Vector2(
            SIMULATION_WIDTH / 2, SCREEN_HEIGHT / 2
        )
        self.last_density_metric: float = 0.0
        self._max_density_radius = math.hypot(SIMULATION_WIDTH, SCREEN_HEIGHT) / 2.0
        self._update_density_stats()

    def step(self, dt: float) -> None:
        forces = [pygame.Vector2() for _ in self.points]
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

        total_acceleration = pygame.Vector2()
        total_magnitude = 0.0

        for point, force in zip(self.points, forces):
            acceleration = force / point.mass
            total_acceleration += acceleration
            total_magnitude += acceleration.length()
            point.velocity += acceleration * dt
            point.limit_speed(self.settings.max_speed)
            point.position += point.velocity * dt
            self._keep_inside(point)
            point.limit_speed(self.settings.max_speed)

        count = len(self.points)
        if count > 0:
            self.last_average_acceleration_vector = total_acceleration / count
            self.last_average_acceleration = total_magnitude / count
        else:
            self.last_average_acceleration_vector = pygame.Vector2()
            self.last_average_acceleration = 0.0

        self._update_density_stats()

    def _keep_inside(self, point: GravityPoint) -> None:
        radius = self.settings.point_radius
        padding = self.settings.boundary_padding

        limit_x = SIMULATION_WIDTH - radius - padding
        limit_y = SCREEN_HEIGHT - radius - padding
        min_x = radius + padding
        min_y = radius + padding

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


    def _update_density_stats(self) -> None:
        if not self.points:
            self.last_density_metric = 0.0
            self.last_average_mass = 0.0
            self.last_center_of_mass = pygame.Vector2(
                SIMULATION_WIDTH / 2, SCREEN_HEIGHT / 2
            )
            return

        total_mass = sum(point.mass for point in self.points)
        if total_mass <= 0:
            self.last_density_metric = 0.0
            self.last_average_mass = 0.0
            self.last_center_of_mass = pygame.Vector2(
                SIMULATION_WIDTH / 2, SCREEN_HEIGHT / 2
            )
            return

        weighted_position = pygame.Vector2()
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


class Slider:
    """A horizontal slider UI component."""

    def __init__(
        self,
        label: str,
        attr: str,
        settings: SimulationSettings,
        min_value: float,
        max_value: float,
        position: tuple[int, int],
        length: int,
        postprocess: Callable[[float], float],
        formatter: Callable[[float], str],
    ) -> None:
        self.label = label
        self.attr = attr
        self.settings = settings
        self.min_value = min_value
        self.max_value = max_value
        self.position = position
        self.length = length
        self.postprocess = postprocess
        self.formatter = formatter
        self.dragging = False
        self.handle_radius = 8

    @property
    def value(self) -> float:
        return getattr(self.settings, self.attr)

    def set_value(self, raw_value: float) -> None:
        clamped = max(self.min_value, min(self.max_value, raw_value))
        value = self.postprocess(clamped)
        setattr(self.settings, self.attr, value)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._handle_rect().collidepoint(event.pos) or self._track_rect().collidepoint(event.pos):
                self.dragging = True
                self._update_from_x(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_from_x(event.pos[0])

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        label_surface = font.render(self.label, True, TEXT_COLOR)
        surface.blit(label_surface, (self.position[0], self.position[1] - 18))

        track_rect = self._track_rect()
        pygame.draw.rect(surface, SLIDER_TRACK_COLOR, track_rect, border_radius=4)

        handle_rect = self._handle_rect()
        pygame.draw.circle(surface, SLIDER_HANDLE_COLOR, handle_rect.center, self.handle_radius)

        value_surface = font.render(self.formatter(self.value), True, TEXT_COLOR)
        surface.blit(value_surface, (self.position[0] + self.length + 16, self.position[1] - 10))

    def _track_rect(self) -> pygame.Rect:
        return pygame.Rect(self.position[0], self.position[1], self.length, 6)

    def _handle_rect(self) -> pygame.Rect:
        ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
        center_x = self.position[0] + ratio * self.length
        center_y = self.position[1] + 3
        return pygame.Rect(int(center_x) - self.handle_radius, int(center_y) - self.handle_radius, self.handle_radius * 2, self.handle_radius * 2)

    def _update_from_x(self, x: int) -> None:
        ratio = (x - self.position[0]) / self.length
        ratio = max(0.0, min(1.0, ratio))
        raw_value = self.min_value + ratio * (self.max_value - self.min_value)
        self.set_value(raw_value)


class DensityFeedbackController:
    """Feedback loop that modulates gravity parameters based on density."""

    def __init__(self, settings: SimulationSettings, simulation: GravitySimulation) -> None:
        self.settings = settings
        self.simulation = simulation
        self.base_values = {
            "gravitational_constant": settings.gravitational_constant,
            "max_force": settings.max_force,
            "max_speed": settings.max_speed,
        }
        self.current_mode: str = "contract"
        self.pending_mode: str | None = None
        self.time_since_toggle: float = 0.0
        self.desired_period: float = 1.0 / 0.08
        self.current_frequency: float = 0.08
        self.transition_delay: float = 0.5
        self.delay_timer: float = 0.0
        self.response_rate: float = 1.5
        self.high_density_threshold: float = 0.62
        self.low_density_threshold: float = 0.38
        initial_density = simulation.last_density_metric
        self._last_factors = self._mode_factors(self.current_mode, initial_density)
        self.tolerance: float = 1e-3

    def update(self, dt: float) -> None:
        if dt <= 0:
            return

        self._capture_user_adjustments()

        density = max(0.0, min(1.0, self.simulation.last_density_metric))
        frequency = 0.01 + 0.29 * density
        period = 1.0 / frequency
        min_period = 1.0 / 0.3
        max_period = 1.0 / 0.01
        period = max(min_period, min(max_period, period))
        self.desired_period = period
        self.current_frequency = 1.0 / period
        self.time_since_toggle += dt

        cooldown = max(min_period, 0.5 * period)

        if self.pending_mode is None and self.delay_timer <= 0.0:
            if (
                density > self.high_density_threshold
                and self.current_mode != "expand"
                and self.time_since_toggle >= cooldown
            ):
                self._schedule_mode("expand")
            elif (
                density < self.low_density_threshold
                and self.current_mode != "contract"
                and self.time_since_toggle >= cooldown
            ):
                self._schedule_mode("contract")
            elif self.time_since_toggle >= period:
                self._schedule_mode("expand" if self.current_mode == "contract" else "contract")

        if self.delay_timer > 0.0:
            self.delay_timer -= dt
            if self.delay_timer <= 0.0 and self.pending_mode is not None:
                self._activate_pending_mode()

        self._apply_targets(dt)

    def _schedule_mode(self, mode: str) -> None:
        self.pending_mode = mode
        self.delay_timer = self.transition_delay

    def _activate_pending_mode(self) -> None:
        if self.pending_mode is None:
            return
        self.current_mode = self.pending_mode
        self.pending_mode = None
        self.time_since_toggle = 0.0

    def _capture_user_adjustments(self) -> None:
        density = max(0.0, min(1.0, self.simulation.last_density_metric))
        current_factors = self._mode_factors(self.current_mode, density)

        for attr, base_value in self.base_values.items():
            actual = getattr(self.settings, attr)
            expected = base_value * self._last_factors.get(attr, 1.0)
            if abs(actual - expected) > self.tolerance:
                factor = current_factors.get(attr, 1.0)
                if abs(factor) < 1e-6:
                    self.base_values[attr] = actual
                else:
                    self.base_values[attr] = actual / factor
                self._last_factors[attr] = factor

    def _apply_targets(self, dt: float) -> None:
        density = max(0.0, min(1.0, self.simulation.last_density_metric))
        factors = self._mode_factors(self.current_mode, density)
        alpha = max(0.0, min(1.0, dt * self.response_rate))

        for attr, base_value in self.base_values.items():
            target = base_value * factors.get(attr, 1.0)
            current = getattr(self.settings, attr)
            new_value = current + (target - current) * alpha
            setattr(self.settings, attr, new_value)
            self._last_factors[attr] = factors.get(attr, 1.0)

    def _mode_factors(self, mode: str, density: float) -> dict[str, float]:
        density = max(0.0, min(1.0, density))
        if mode == "contract":
            return {
                "gravitational_constant": 1.15 + 0.35 * density,
                "max_force": 1.1 + 0.3 * density,
                "max_speed": 1.05 + 0.2 * density,
            }

        inverse_density = 1.0 - density
        return {
            "gravitational_constant": 0.55 + 0.35 * inverse_density,
            "max_force": 0.65 + 0.25 * inverse_density,
            "max_speed": 0.8 + 0.15 * inverse_density,
        }


def _format_float(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}"


def _format_int_like(value: float) -> str:
    return f"{int(round(value))}"


def _create_default_points(
    settings: SimulationSettings, rng: random.Random
) -> List[GravityPoint]:
    return [_create_random_point(settings, rng) for _ in range(settings.num_points)]


def _create_random_point(settings: SimulationSettings, rng: random.Random) -> GravityPoint:
    position = pygame.Vector2(
        rng.uniform(
            settings.point_radius + settings.boundary_padding + 10,
            SIMULATION_WIDTH - settings.point_radius - settings.boundary_padding - 10,
        ),
        rng.uniform(
            settings.point_radius + settings.boundary_padding + 10,
            SCREEN_HEIGHT - settings.point_radius - settings.boundary_padding - 10,
        ),
    )
    velocity = pygame.Vector2(
        rng.uniform(-80.0, 80.0),
        rng.uniform(-80.0, 80.0),
    )
    mass = rng.uniform(1.0, 300.0)
    color = _random_color(rng)
    return GravityPoint(position=position, velocity=velocity, mass=mass, color=color)


def _random_color(rng: random.Random) -> tuple[int, int, int]:
    return (rng.randint(64, 255), rng.randint(64, 255), rng.randint(64, 255))


def _ensure_point_count(
    simulation: GravitySimulation, settings: SimulationSettings, rng: random.Random
) -> None:
    desired = max(1, int(round(settings.num_points)))
    current = len(simulation.points)

    if desired > current:
        for _ in range(desired - current):
            simulation.points.append(_create_random_point(settings, rng))
    elif desired < current:
        del simulation.points[desired:]


def _build_sliders(settings: SimulationSettings) -> List[Slider]:
    sliders: List[Slider] = []
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
            lambda v: _format_int_like(v),
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
            lambda v: _format_float(v, 2),
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

    return sliders


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
    simulation = GravitySimulation(settings, _create_default_points(settings, rng))
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

        _ensure_point_count(simulation, settings, rng)
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


if __name__ == "__main__":
    run()
