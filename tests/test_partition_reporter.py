"""Tests for PartitionReport and PartitionRegistry."""
import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.partition import ResultPartitioner
from pipewarden.partition_reporter import PartitionReport
from pipewarden.partition_registry import PartitionRegistry


def _make_result(name: str, status: CheckStatus) -> CheckResult:
    return CheckResult(check_name=name, status=status, message="", duration_ms=5.0)


class TestPartitionReport:
    def setup_method(self):
        self.partitioner = ResultPartitioner()
        self.partitioner.add_partition("passed", lambda r: r.status == CheckStatus.PASSED)
        self.partitioner.add_partition("failed", lambda r: r.status == CheckStatus.FAILED)
        self.report = PartitionReport(self.partitioner)

    def test_raises_on_non_partitioner(self):
        with pytest.raises(TypeError):
            PartitionReport("not a partitioner")

    def test_render_contains_partition_names(self):
        rendered = self.report.render()
        assert "[passed]" in rendered
        assert "[failed]" in rendered

    def test_render_contains_unmatched(self):
        rendered = self.report.render()
        assert "[unmatched]" in rendered

    def test_render_counts_correctly(self):
        self.partitioner.route(_make_result("c1", CheckStatus.PASSED))
        self.partitioner.route(_make_result("c2", CheckStatus.PASSED))
        self.partitioner.route(_make_result("c3", CheckStatus.FAILED))
        rendered = self.report.render()
        assert "total=2" in rendered
        assert "total=1" in rendered

    def test_str_equals_render(self):
        assert str(self.report) == self.report.render()

    def test_render_shows_header(self):
        assert "Partition Report" in self.report.render()


class TestPartitionRegistry:
    def setup_method(self):
        self.registry = PartitionRegistry()

    def test_initial_len_zero(self):
        assert len(self.registry) == 0

    def test_register_and_get(self):
        p = ResultPartitioner()
        self.registry.register("main", p)
        assert self.registry.get("main") is p

    def test_register_duplicate_raises(self):
        p = ResultPartitioner()
        self.registry.register("main", p)
        with pytest.raises(ValueError, match="already registered"):
            self.registry.register("main", ResultPartitioner())

    def test_register_non_partitioner_raises(self):
        with pytest.raises(TypeError):
            self.registry.register("x", object())

    def test_get_unknown_raises(self):
        with pytest.raises(KeyError):
            self.registry.get("nope")

    def test_unregister(self):
        p = ResultPartitioner()
        self.registry.register("main", p)
        self.registry.unregister("main")
        assert len(self.registry) == 0

    def test_unregister_unknown_raises(self):
        with pytest.raises(KeyError):
            self.registry.unregister("ghost")

    def test_names(self):
        self.registry.register("a", ResultPartitioner())
        self.registry.register("b", ResultPartitioner())
        assert set(self.registry.names()) == {"a", "b"}
