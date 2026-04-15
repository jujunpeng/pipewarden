"""Tests for pipewarden.scheduler.CheckScheduler."""

import time
import threading
import pytest
from unittest.mock import MagicMock, patch

from pipewarden.scheduler import CheckScheduler


class TestCheckScheduler:
    def test_raises_on_non_positive_interval(self):
        with pytest.raises(ValueError, match="positive"):
            CheckScheduler(task=lambda: None, interval_seconds=0)

    def test_raises_on_negative_interval(self):
        with pytest.raises(ValueError):
            CheckScheduler(task=lambda: None, interval_seconds=-1)

    def test_is_not_running_before_start(self):
        scheduler = CheckScheduler(task=lambda: None, interval_seconds=1)
        assert not scheduler.is_running

    def test_is_running_after_start(self):
        scheduler = CheckScheduler(task=lambda: None, interval_seconds=60)
        try:
            scheduler.start()
            assert scheduler.is_running
        finally:
            scheduler.stop()

    def test_is_not_running_after_stop(self):
        scheduler = CheckScheduler(task=lambda: None, interval_seconds=60)
        scheduler.start()
        scheduler.stop()
        assert not scheduler.is_running

    def test_raises_if_started_twice(self):
        scheduler = CheckScheduler(task=lambda: None, interval_seconds=60)
        scheduler.start()
        try:
            with pytest.raises(RuntimeError, match="already running"):
                scheduler.start()
        finally:
            scheduler.stop()

    def test_task_is_called(self):
        called = threading.Event()
        task = MagicMock(side_effect=lambda: called.set())
        scheduler = CheckScheduler(task=task, interval_seconds=0.05)
        scheduler.start()
        called.wait(timeout=2)
        scheduler.stop()
        assert task.call_count >= 1

    def test_run_count_increments(self):
        barrier = threading.Barrier(2)
        def task():
            barrier.wait(timeout=2)

        scheduler = CheckScheduler(task=task, interval_seconds=0.05)
        scheduler.start()
        barrier.wait(timeout=2)
        scheduler.stop()
        assert scheduler.run_count >= 1

    def test_exception_in_task_does_not_crash_scheduler(self):
        call_count = [0]
        done = threading.Event()

        def flaky_task():
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("intentional error")
            done.set()

        scheduler = CheckScheduler(task=flaky_task, interval_seconds=0.05)
        scheduler.start()
        done.wait(timeout=2)
        scheduler.stop()
        assert call_count[0] >= 2
        assert scheduler.is_running is False
