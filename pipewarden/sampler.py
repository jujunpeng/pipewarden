"""Result sampler — keeps a random reservoir sample of CheckResults."""
from __future__ import annotations

import random
from typing import List

from pipewarden.checks import CheckResult


class ResultSampler:
    """Reservoir sampler that keeps at most *max_size* results."""

    def __init__(self, max_size: int = 100, seed: int | None = None) -> None:
        if max_size < 1:
            raise ValueError("max_size must be at least 1")
        self._max_size = max_size
        self._samples: List[CheckResult] = []
        self._total = 0
        self._rng = random.Random(seed)

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def total_seen(self) -> int:
        return self._total

    def record(self, result: CheckResult) -> None:
        """Add *result* to the reservoir using Algorithm R."""
        self._total += 1
        if len(self._samples) < self._max_size:
            self._samples.append(result)
        else:
            idx = self._rng.randint(0, self._total - 1)
            if idx < self._max_size:
                self._samples[idx] = result

    def samples(self) -> List[CheckResult]:
        """Return a copy of the current reservoir."""
        return list(self._samples)

    def clear(self) -> None:
        self._samples.clear()
        self._total = 0

    def __len__(self) -> int:
        return len(self._samples)

    def __repr__(self) -> str:
        return (
            f"ResultSampler(max_size={self._max_size}, "
            f"total_seen={self._total}, samples={len(self._samples)})"
        )
