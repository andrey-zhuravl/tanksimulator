"""Entry point for the metronome circle application."""

from __future__ import annotations

from metronome_circle import MetronomeApp


def main() -> None:
    """Launch the metronome application."""

    app = MetronomeApp()
    app.run()


if __name__ == "__main__":
    main()
