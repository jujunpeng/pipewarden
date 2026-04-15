"""pipewarden — lightweight ETL pipeline health-check library."""

from pipewarden.checks import CheckResult, CheckStatus, HealthCheck
from pipewarden.alerts import AlertHandler, LogAlertHandler, ThresholdAlertHandler
from pipewarden.pipeline import Pipeline, PipelineReport
from pipewarden.registry import CheckRegistry
from pipewarden.runner import CheckRunner
from pipewarden.scheduler import CheckScheduler
from pipewarden.history import CheckHistory

__all__ = [
    # checks
    "CheckResult",
    "CheckStatus",
    "HealthCheck",
    # alerts
    "AlertHandler",
    "LogAlertHandler",
    "ThresholdAlertHandler",
    # pipeline
    "Pipeline",
    "PipelineReport",
    # registry
    "CheckRegistry",
    # runner
    "CheckRunner",
    # scheduler
    "CheckScheduler",
    # history
    "CheckHistory",
]

__version__ = "0.1.0"
