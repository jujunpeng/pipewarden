"""Tests for pipewarden.sampler."""
import pytest

from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.sampler import ResultSampler


def _make_result(name: str = "check", status: CheckStatus = CheckStatus.PASSED) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="ok")


class TestResultSampler:
    def setup_method(self):
        self.sampler = ResultSampler(max_size=5, seed=42)

    def test_raises_on_zero_max_size(self):
        with pytest.raises(ValueError):
            ResultSampler(max_size=0)

    def test_raises_on_negative_max_size(self):
        with pytest.raises(ValueError):
            ResultSampler(max_size=-1)

    def test_max_size_stored(self):
        assert self.sampler.max_size == 5

    def test_initial_len_is_zero(self):
        assert len(self.sampler) == 0

    def test_total_seen_starts_at_zero(self):
        assert self.sampler.total_seen == 0

    def test_record_increments_total_seen(self):
        self.sampler.record(_make_result())
        assert self.sampler.total_seen == 1

    def test_record_adds_to_samples_below_capacity(self):
        for i in range(3):
            self.sampler.record(_make_result(f"c{i}"))
        assert len(self.sampler) == 3

    def test_samples_do_not_exceed_max_size(self):
        for i in range(20):
            self.sampler.record(_make_result(f"c{i}"))
        assert len(self.sampler) <= self.sampler.max_size

    def test_total_seen_reflects_all_records(self):
        for i in range(20):
            self.sampler.record(_make_result(f"c{i}"))
        assert self.sampler.total_seen == 20

    def test_samples_returns_copy(self):
        self.sampler.record(_make_result())
        s1 = self.sampler.samples()
        s1.clear()
        assert len(self.sampler) == 1

    def test_clear_resets_state(self):
        for i in range(5):
            self.sampler.record(_make_result(f"c{i}"))
        self.sampler.clear()
        assert len(self.sampler) == 0
        assert self.sampler.total_seen == 0

    def test_repr_contains_class_name(self):
        assert "ResultSampler" in repr(self.sampler)

    def test_repr_contains_max_size(self):
        assert "max_size=5" in repr(self.sampler)

    def test_deterministic_with_seed(self):
        s1 = ResultSampler(max_size=3, seed=0)
        s2 = ResultSampler(max_size=3, seed=0)
        results = [_make_result(f"c{i}") for i in range(10)]
        for r in results:
            s1.record(r)
            s2.record(r)
        names1 = [r.check_name for r in s1.samples()]
        names2 = [r.check_name for r in s2.samples()]
        assert names1 == names2
