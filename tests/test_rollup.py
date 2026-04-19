"""Tests for pipewarden.rollup."""
import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.rollup import PipelineRollup, RollupBucket


def _make_result(status: CheckStatus) -> CheckResult:
    return CheckResult(check_name="demo", status=status, message="ok")


class TestRollupBucket:
    def test_pass_rate_zero_when_empty(self):
        b = RollupBucket(label="week1")
        assert b.pass_rate == 0.0

    def test_pass_rate_calculation(self):
        b = RollupBucket(label="week1", total=4, passed=3, failed=1)
        assert b.pass_rate == pytest.approx(0.75)

    def test_repr_contains_label(self):
        b = RollupBucket(label="week1")
        assert "week1" in repr(b)


class TestPipelineRollup:
    def setup_method(self):
        self.rollup = PipelineRollup()

    def test_initial_len_is_zero(self):
        assert len(self.rollup) == 0

    def test_bucket_names_empty_initially(self):
        assert self.rollup.bucket_names == []

    def test_record_creates_bucket(self):
        self.rollup.record("week1", _make_result(CheckStatus.PASSED))
        assert "week1" in self.rollup.bucket_names

    def test_record_increments_total(self):
        self.rollup.record("week1", _make_result(CheckStatus.PASSED))
        self.rollup.record("week1", _make_result(CheckStatus.FAILED))
        assert self.rollup.get("week1").total == 2

    def test_record_counts_passed(self):
        self.rollup.record("w", _make_result(CheckStatus.PASSED))
        self.rollup.record("w", _make_result(CheckStatus.PASSED))
        assert self.rollup.get("w").passed == 2

    def test_record_counts_failed(self):
        self.rollup.record("w", _make_result(CheckStatus.FAILED))
        assert self.rollup.get("w").failed == 1

    def test_record_counts_errors(self):
        self.rollup.record("w", _make_result(CheckStatus.ERROR))
        assert self.rollup.get("w").errors == 1

    def test_multiple_buckets(self):
        self.rollup.record("week1", _make_result(CheckStatus.PASSED))
        self.rollup.record("week2", _make_result(CheckStatus.FAILED))
        assert len(self.rollup) == 2

    def test_get_raises_on_missing_bucket(self):
        with pytest.raises(KeyError):
            self.rollup.get("nonexistent")

    def test_record_raises_on_empty_label(self):
        with pytest.raises(ValueError):
            self.rollup.record("", _make_result(CheckStatus.PASSED))

    def test_record_raises_on_blank_label(self):
        with pytest.raises(ValueError):
            self.rollup.record("   ", _make_result(CheckStatus.PASSED))

    def test_record_raises_on_non_result(self):
        with pytest.raises(TypeError):
            self.rollup.record("week1", "not-a-result")  # type: ignore

    def test_all_buckets_returns_list(self):
        self.rollup.record("a", _make_result(CheckStatus.PASSED))
        self.rollup.record("b", _make_result(CheckStatus.PASSED))
        buckets = self.rollup.all_buckets()
        assert len(buckets) == 2
        assert all(isinstance(b, RollupBucket) for b in buckets)

    def test_recorded_at_is_set(self):
        from datetime import timezone
        assert self.rollup.recorded_at.tzinfo == timezone.utc
