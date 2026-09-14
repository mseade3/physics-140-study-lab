"""
Physics 140 verification utilities.

Prefer symbolic algebra first; use these helpers to numerically check
FBDs, net force, and elementary trajectories when asked to verify.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class Force2D:
    """A planar force with optional label for FBD display."""

    fx: float
    fy: float
    label: str = ""

    @property
    def magnitude(self) -> float:
        return float(np.hypot(self.fx, self.fy))

    @property
    def angle_deg(self) -> float:
        return float(np.degrees(np.arctan2(self.fy, self.fx)))


def net_force(forces: Iterable[Force2D]) -> Force2D:
    fx = sum(f.fx for f in forces)
    fy = sum(f.fy for f in forces)
    return Force2D(fx=fx, fy=fy, label="F_net")


def acceleration_from_forces(
    forces: Iterable[Force2D], mass: float
) -> tuple[float, float]:
    """Newton II: a = F_net / m. Raises if mass is non-positive."""
    if mass <= 0:
        raise ValueError("Mass must be positive; check the given constraint.")
    f_net = net_force(forces)
    return f_net.fx / mass, f_net.fy / mass


def force_from_magnitude_angle(magnitude: float, angle_deg: float, label: str = "") -> Force2D:
    theta = np.radians(angle_deg)
    return Force2D(
        fx=float(magnitude * np.cos(theta)),
        fy=float(magnitude * np.sin(theta)),
        label=label,
    )


def projectile_trajectory(
    v0: float,
    angle_deg: float,
    g: float = 9.81,
    n: int = 400,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """
    Ideal projectile (no drag) from the origin on flat ground.

    Returns x, y arrays, time of flight, and range.
    """
    if v0 < 0:
        raise ValueError("Launch speed cannot be negative.")
    if g <= 0:
        raise ValueError("g must be positive in this coordinate convention.")

    theta = np.radians(angle_deg)
    vx = v0 * np.cos(theta)
    vy = v0 * np.sin(theta)

    if abs(vy) < 1e-12:
        # Horizontal launch at ground level: trivial degenerate case
        t_flight = 0.0
        x = np.array([0.0])
        y = np.array([0.0])
        return x, y, t_flight, 0.0

    t_flight = 2.0 * vy / g
    if t_flight <= 0:
        raise ValueError(
            "Time of flight is non-positive for these parameters "
            "(check launch angle and g)."
        )

    t = np.linspace(0.0, t_flight, n)
    x = vx * t
    y = vy * t - 0.5 * g * t**2
    range_x = float(x[-1])
    return x, y, float(t_flight), range_x


def inclined_plane_accel(
    mass: float,
    incline_deg: float,
    mu_k: float = 0.0,
    g: float = 9.81,
    down_the_plane: bool = True,
) -> float:
    """
    Acceleration along an incline with optional kinetic friction.

    Positive result means acceleration down the plane when down_the_plane=True.
    """
    if mass <= 0:
        raise ValueError("Mass must be positive.")
    if mu_k < 0:
        raise ValueError("Coefficient of friction cannot be negative.")

    theta = np.radians(incline_deg)
    # Parallel and normal components
    a_grav = g * np.sin(theta)
    n_force = mass * g * np.cos(theta)
    a_fric = (mu_k * n_force) / mass

    if down_the_plane:
        return float(a_grav - a_fric)
    return float(-a_grav - a_fric)
