"""Utility helpers for UI formatting."""


def format_float(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}"


def format_int_like(value: float) -> str:
    return f"{int(round(value))}"
