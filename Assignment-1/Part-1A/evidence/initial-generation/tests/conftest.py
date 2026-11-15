"""Deterministic Hypothesis profile (Constitution III)."""

from hypothesis import HealthCheck, settings

settings.register_profile(
    "slotfinder",
    derandomize=True,
    database=None,
    deadline=None,
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("slotfinder")
