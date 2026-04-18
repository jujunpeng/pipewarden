import pytest
from datetime import datetime
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.checkpoint import Checkpoint, CheckpointStore


def _make_result(name: str, status: CheckStatus, duration: float = 0.1) -> CheckResult:
    return CheckResult(
        check_name=name,
        status=status,
        message="ok",
        duration_ms=duration,
    )


class TestCheckpointStore:
    def setup_method(self):
        self.store = CheckpointStore()

    def test_initial_size_is_zero(self):
        assert self.store.size == 0

    def test_save_passed_result_stores_checkpoint(self):
        r = _make_result("db", CheckStatus.PASSED)
        self.store.save(r)
        assert self.store.has("db")

    def test_save_failed_result_does_not_store(self):
        r = _make_result("db", CheckStatus.FAILED)
        self.store.save(r)
        assert not self.store.has("db")

    def test_save_error_result_does_not_store(self):
        r = _make_result("db", CheckStatus.ERROR)
        self.store.save(r)
        assert not self.store.has("db")

    def test_get_returns_none_when_missing(self):
        assert self.store.get("missing") is None

    def test_get_returns_checkpoint_after_save(self):
        r = _make_result("api", CheckStatus.PASSED)
        self.store.save(r)
        cp = self.store.get("api")
        assert cp is not None
        assert cp.check_name == "api"
        assert cp.result is r

    def test_checkpoint_saved_at_is_datetime(self):
        r = _make_result("api", CheckStatus.PASSED)
        self.store.save(r)
        cp = self.store.get("api")
        assert isinstance(cp.saved_at, datetime)

    def test_overwrite_with_newer_passed_result(self):
        r1 = _make_result("svc", CheckStatus.PASSED, duration=1.0)
        r2 = _make_result("svc", CheckStatus.PASSED, duration=2.0)
        self.store.save(r1)
        self.store.save(r2)
        assert self.store.get("svc").result is r2

    def test_size_increments_per_unique_check(self):
        self.store.save(_make_result("a", CheckStatus.PASSED))
        self.store.save(_make_result("b", CheckStatus.PASSED))
        assert self.store.size == 2

    def test_clear_removes_checkpoint(self):
        self.store.save(_make_result("x", CheckStatus.PASSED))
        self.store.clear("x")
        assert not self.store.has("x")

    def test_clear_nonexistent_does_not_raise(self):
        self.store.clear("ghost")  # should not raise

    def test_all_names_returns_saved_checks(self):
        self.store.save(_make_result("a", CheckStatus.PASSED))
        self.store.save(_make_result("b", CheckStatus.PASSED))
        assert set(self.store.all_names()) == {"a", "b"}

    def test_reset_clears_all(self):
        self.store.save(_make_result("a", CheckStatus.PASSED))
        self.store.reset()
        assert self.store.size == 0

    def test_checkpoint_repr(self):
        r = _make_result("z", CheckStatus.PASSED)
        self.store.save(r)
        cp = self.store.get("z")
        assert "z" in repr(cp)
        assert "passed" in repr(cp)
