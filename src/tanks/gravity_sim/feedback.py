"""Feedback controller that modulates settings based on density."""

from __future__ import annotations

from .settings import SimulationSettings
from .simulation import GravitySimulation


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
