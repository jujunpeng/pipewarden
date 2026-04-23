"""Scheduler module for running pipeline health checks on a defined interval."""

import time
import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class CheckScheduler:
    """Runs a callable (e.g. a pipeline runner) on a fixed interval in a background thread."""

    def __init__(self, task: Callable[[], None], interval_seconds: float):
        """
        Args:
            task: A zero-argument callable to execute on each tick.
            interval_seconds: How often (in seconds) to run the task.
        """
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be a positive number.")
        self._task = task
        self._interval = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._run_count = 0
        self._last_run_time: Optional[float] = None

    @property
    def is_running(self) -> bool:
        """Return True if the scheduler background thread is active."""
        return self._thread is not None and self._thread.is_alive()

    @property
    def run_count(self) -> int:
        """Total number of times the task has been executed."""
        return self._run_count

    @property
    def last_run_time(self) -> Optional[float]:
        """Unix timestamp of the most recent task execution, or None if never run."""
        return self._last_run_time

    def start(self) -> None:
        """Start the scheduler in a daemon background thread."""
        if self.is_running:
            raise RuntimeError("Scheduler is already running.")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("CheckScheduler started with interval=%.2fs.", self._interval)

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the scheduler to stop and wait for the thread to finish."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        logger.info("CheckScheduler stopped after %d run(s).", self._run_count)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._task()
                self._run_count += 1
                self._last_run_time = time.time()
            except Exception:
                logger.exception("CheckScheduler task raised an unhandled exception.")
            self._stop_event.wait(timeout=self._interval)
