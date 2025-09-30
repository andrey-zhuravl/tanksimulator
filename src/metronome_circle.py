"""Interactive 16-step rhythm graph metronome.

The module provides a small pygame application that renders a circular
sequencer with 16 nodes.  A running metronome highlights each node in
sequence.  The user can toggle accent nodes with the mouse and start/stop
the metronome with the space bar.  When the metronome reaches an accented
node an audible click is played.
"""

from __future__ import annotations

import math
import time
from array import array
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import pygame


# --- Configuration -----------------------------------------------------------------

WINDOW_SIZE: Tuple[int, int] = (640, 640)
BACKGROUND_COLOR: Tuple[int, int, int] = (20, 20, 30)
CIRCLE_COLOR: Tuple[int, int, int] = (240, 240, 240)
ACCENT_COLOR: Tuple[int, int, int] = (220, 160, 60)
CURRENT_STEP_COLOR: Tuple[int, int, int] = (185, 55, 120)
DEFAULT_NODE_COLOR: Tuple[int, int, int] = (20, 220, 230)
POLYGON_COLOR: Tuple[int, int, int] = (200, 50, 50)
TEXT_COLOR: Tuple[int, int, int] = (210, 210, 220)

NUM_STEPS: int = 17
NODE_RADIUS: int = 19
OUTLINE_WIDTH: int = 5
SEQUENCE_DURATION_SECONDS: float = 2.5  # Default cycle duration (full 16 steps)


@dataclass
class Node:
    """Represents a single node in the circular graph."""

    index: int
    position: Tuple[int, int]


def create_click_sound(
    *,
    frequency: int = 880,
    duration_ms: int = 70,
    volume: float = 0.6,
    sample_rate: int = 44100,
) -> pygame.mixer.Sound:
    """Create a simple click sound using a decaying sine wave."""

    total_samples = int(sample_rate * duration_ms / 1000)
    amplitude = int(32767 * volume)
    samples = array("h")

    for sample_index in range(total_samples):
        t = sample_index / sample_rate
        # Linear decay envelope keeps the click short and percussive.
        envelope = 1.0 - (sample_index / total_samples)
        sample_value = int(
            amplitude * envelope * math.sin(2 * math.pi * frequency * t)
        )
        samples.append(sample_value)

    # Convert to bytes for the pygame mixer.  A mono, signed 16-bit sound is created.
    return pygame.mixer.Sound(buffer=samples.tobytes())


def step_positions(center: Tuple[int, int], radius: int, total_steps: int) -> List[Node]:
    """Calculate cartesian coordinates for equally spaced nodes on a circle."""

    cx, cy = center
    nodes: List[Node] = []
    for i in range(total_steps):
        angle = (math.tau * i / total_steps) - math.pi / 2  # start at top, go clockwise
        x = int(cx + radius * math.cos(angle))
        y = int(cy + radius * math.sin(angle))
        nodes.append(Node(index=i, position=(x, y)))
    return nodes


def draw_nodes(
    surface: pygame.Surface,
    nodes: Sequence[Node],
    active_nodes: Iterable[int],
    current_step: int,
) -> None:
    """Render the circular graph with highlights for active and current nodes."""

    active_set = set(active_nodes)

    for node in nodes:
        node_color = DEFAULT_NODE_COLOR
        outline_color = CIRCLE_COLOR

        if node.index in active_set:
            node_color = ACCENT_COLOR
        if node.index == current_step:
            outline_color = CURRENT_STEP_COLOR

        pygame.draw.circle(surface, outline_color, node.position, NODE_RADIUS + 4)
        pygame.draw.circle(surface, node_color, node.position, NODE_RADIUS)
        pygame.draw.circle(surface, BACKGROUND_COLOR, node.position, NODE_RADIUS, OUTLINE_WIDTH)


def draw_polygon(surface: pygame.Surface, nodes: Sequence[Node], active_nodes: Iterable[int]) -> None:
    """Draw a polygon connecting active nodes in order of the sequence."""

    active_indices = [node for node in sorted(set(active_nodes))]
    if len(active_indices) < 2:
        return

    points = [nodes[index].position for index in active_indices]
    pygame.draw.lines(surface, POLYGON_COLOR, True, points, 3)


def draw_overlay(
    surface: pygame.Surface,
    font: pygame.font.Font,
    speed_font: pygame.font.Font,
    sequence_duration: float,
    is_running: bool,
) -> None:
    """Draw UI text elements such as the centre number and control hints."""

    width, height = surface.get_size()

    number_text = font.render(str(NUM_STEPS), True, (70, 70, 80))
    number_rect = number_text.get_rect(center=(width // 2, height // 2))
    surface.blit(number_text, number_rect)

    status = "Играет" if is_running else "Пауза"
    hints = [
        "Пробел — старт/стоп",
        "Клик — акцент",
        "↑/↓ — скорость",
        f"Цикл: {sequence_duration:.2f} с",
        f"Статус: {status}",
    ]

    for idx, hint in enumerate(hints):
        hint_surface = speed_font.render(hint, True, TEXT_COLOR)
        surface.blit(hint_surface, (20, 20 + idx * 24))




def main() -> None:
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=1)
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("16-Step Rhythm Graph")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 220, bold=True)
    hints_font = pygame.font.SysFont("arial", 20)

    centre = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
    circle_radius = min(WINDOW_SIZE) // 2 - 80
    nodes = step_positions(centre, circle_radius, NUM_STEPS)

    # A simple default groove resembles the figure provided by the user.
    active_nodes = {0, 4, 7, 11}
    current_step = 0
    is_running = False
    sequence_duration = SEQUENCE_DURATION_SECONDS
    time_per_step = sequence_duration / NUM_STEPS
    last_step_time = time.time()

    click_sound = create_click_sound()
    click_sound_first = create_click_sound(frequency = 960, duration_ms = 90, volume = 0.8)

    cicle = 0
    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    is_running = not is_running
                    last_step_time = time.time()
                elif event.key == pygame.K_UP:
                    sequence_duration = max(1.0, sequence_duration - 0.1)
                    time_per_step = sequence_duration / NUM_STEPS
                elif event.key == pygame.K_DOWN:
                    sequence_duration = min(3.0, sequence_duration + 0.1)
                    time_per_step = sequence_duration / NUM_STEPS
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                for node in nodes:
                    if math.dist(mouse_pos, node.position) <= NODE_RADIUS + 4:
                        if node.index in active_nodes:
                            active_nodes.remove(node.index)
                        else:
                            active_nodes.add(node.index)
                        break

        if is_running:
            now = time.time()
            if now - last_step_time >= time_per_step:
                current_step = (current_step + 1) % NUM_STEPS
                last_step_time = now
                if current_step in active_nodes:
                    if(current_step == 0):
                        click_sound_first.play()
                    else:
                        click_sound.play()

        screen.fill(BACKGROUND_COLOR)
        draw_overlay(screen, font, hints_font, sequence_duration, is_running)
        draw_polygon(screen, nodes, active_nodes)
        draw_nodes(screen, nodes, active_nodes, current_step)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

