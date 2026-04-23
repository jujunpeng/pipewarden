"""Registry that manages one CheckForecaster per check name."""
from __future__ import annotations

from typing import Dict, List

from pipewarden.checks import CheckResult
from pipewarden.forecast import CheckForecaster, ForecastPoint


class ForecastRegistry:
    """Maintains a pool of :class:`CheckForecaster` instances, creating them
    on demand with shared default parameters.

    Args:
        default_alpha:   Smoothing factor applied to newly created forecasters.
        default_horizon: Forecast horizon applied to newly created forecasters.
    """

    def __init__(
        self,
        default_alpha: float = 0.3,
        default_horizon: int = 3,
    ) -> None:
        if not (0.0 < default_alpha <= 1.0):
            raise ValueError("default_alpha must be in (0, 1]")
        if default_horizon < 1:
            raise ValueError("default_horizon must be >= 1")
        self._default_alpha = default_alpha
        self._default_horizon = default_horizon
        self._forecasters: Dict[str, CheckForecaster] = {}

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def default_alpha(self) -> float:
        return self._default_alpha

    @property
    def default_horizon(self) -> int:
        return self._default_horizon

    @property
    def check_names(self) -> List[str]:
        return list(self._forecasters.keys())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def observe(self, result: CheckResult) -> None:
        """Feed *result* to the appropriate forecaster, creating it if needed."""
        forecaster = self._get_or_create(result.check_name)
        forecaster.observe(result)

    def forecast(self, check_name: str) -> List[ForecastPoint]:
        """Return forecast points for *check_name*.

        Returns an all-zero forecast if no observations exist yet.
        """
        forecaster = self._get_or_create(check_name)
        return forecaster.forecast()

    def get(self, check_name: str) -> CheckForecaster:
        """Return the forecaster for *check_name*, creating it if needed."""
        return self._get_or_create(check_name)

    def reset(self, check_name: str) -> None:
        """Reset the forecaster for *check_name* without removing it."""
        self._get_or_create(check_name).reset()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_or_create(self, check_name: str) -> CheckForecaster:
        if check_name not in self._forecasters:
            self._forecasters[check_name] = CheckForecaster(
                check_name=check_name,
                alpha=self._default_alpha,
                horizon=self._default_horizon,
            )
        return self._forecasters[check_name]
