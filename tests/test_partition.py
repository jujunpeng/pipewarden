"""Tests for pipewarden.partition."""
import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.partition import Partition, ResultPartitioner


def _make_result(name: str, status: CheckStatus, duration_ms: float = 10.0) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="ok", duration_ms=duration_ms)


class TestPartition:
    def test_repr_contains_name(self):
        p = Partition(name="fast", predicate=lambda r: True)
        assert "fast" in repr(p)

    def test_matches_true(self):
        p = Partition(name="x", predicate=lambda r: r.status == CheckStatus.PASSED)
        r = _make_result("c", CheckStatus.PASSED)
        assert p.matches(r) is True

    def test_matches_false(self):
        p = Partition(name="x", predicate=lambda r: r.status == CheckStatus.PASSED)
        r = _make_result("c", CheckStatus.FAILED)
        assert p.matches(r) is False

    def test_matches_exception_returns_false(self):
        p = Partition(name="x", predicate=lambda r: 1 / 0)
        r = _make_result("c", CheckStatus.PASSED)
        assert p.matches(r) is False

    def test_add_and_results(self):
        p = Partition(name="x", predicate=lambda r: True)
        r = _make_result("c", CheckStatus.PASSED)
        p.add(r)
        assert len(p) == 1
        assert p.results() == [r]

    def test_results_returns_copy(self):
        p = Partition(name="x", predicate=lambda r: True)
        r = _make_result("c", CheckStatus.PASSED)
        p.add(r)
        copy = p.results()
        copy.clear()
        assert len(p) == 1


class TestResultPartitioner:
    def setup_method(self):
        self.partitioner = ResultPartitioner()
        self.partitioner.add_partition("passed", lambda r: r.status == CheckStatus.PASSED)
        self.partitioner.add_partition("failed", lambda r: r.status == CheckStatus.FAILED)

    def test_len_reflects_partition_count(self):
        assert len(self.partitioner) == 2

    def test_partition_names(self):
        assert set(self.partitioner.partition_names()) == {"passed", "failed"}

    def test_duplicate_partition_raises(self):
        with pytest.raises(ValueError, match="already registered"):
            self.partitioner.add_partition("passed", lambda r: True)

    def test_get_unknown_raises(self):
        with pytest.raises(KeyError):
            self.partitioner.get("unknown")

    def test_route_passed_result(self):
        r = _make_result("c", CheckStatus.PASSED)
        self.partitioner.route(r)
        assert len(self.partitioner.get("passed")) == 1
        assert len(self.partitioner.get("failed")) == 0

    def test_route_failed_result(self):
        r = _make_result("c", CheckStatus.FAILED)
        self.partitioner.route(r)
        assert len(self.partitioner.get("failed")) == 1

    def test_unmatched_when_no_partition_matches(self):
        r = _make_result("c", CheckStatus.ERROR)
        self.partitioner.route(r)
        assert len(self.partitioner.unmatched()) == 1

    def test_unmatched_returns_copy(self):
        r = _make_result("c", CheckStatus.ERROR)
        self.partitioner.route(r)
        copy = self.partitioner.unmatched()
        copy.clear()
        assert len(self.partitioner.unmatched()) == 1

    def test_result_can_match_multiple_partitions(self):
        self.partitioner.add_partition("all", lambda r: True)
        r = _make_result("c", CheckStatus.PASSED)
        self.partitioner.route(r)
        assert len(self.partitioner.get("passed")) == 1
        assert len(self.partitioner.get("all")) == 1
        assert len(self.partitioner.unmatched()) == 0
