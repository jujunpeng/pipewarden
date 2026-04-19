"""Tests for ProfilerReport."""
import pytest
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.profiler import CheckProfiler
from pipewarden.profiler_report import ProfilerReport


def _make_result(name: str, duration_ms: float) -> CheckResult:
    return CheckResult(check_name=name, status=CheckStatus.PASSED, message="ok", duration_ms=duration_ms)


class TestProfilerReport:
    def setup_method(self):
        self.profiler = CheckProfiler(threshold_ms=200.0)
        self.report = ProfilerReport(self.profiler)

    def test_raises_on_non_profiler(self):
        with pytest.raises(TypeError):
            ProfilerReport("not a profiler")  # type: ignore

    def test_render_empty_message(self):
        result = self.report.render()
        assert "No profiling data" in result

    def test_render_contains_check_name(self):
        self.profiler.observe(_make_result("my_check", 50.0))
        assert "my_check" in self.report.render()

    def test_render_flags_slow(self):
        self.profiler.observe(_make_result("slow_check", 500.0))
        assert "SLOW" in self.report.render()

    def test_render_no_slow_flag_for_fast(self):
        self.profiler.observe(_make_result("fast_check", 10.0))
        rendered = self.report.render()
        assert "SLOW" not in rendered

    def test_render_contains_totals(self):
        self.profiler.observe(_make_result("a", 10.0))
        self.profiler.observe(_make_result("b", 300.0))
        rendered = self.report.render()
        assert "Total: 2" in rendered
        assert "Slow: 1" in rendered

    def test_str_equals_render(self):
        self.profiler.observe(_make_result("x", 100.0))
        assert str(self.report) == self.report.render()

    def test_render_contains_threshold(self):
        rendered = self.report.render()
        # empty case won't show threshold, observe first
        self.profiler.observe(_make_result("a", 10.0))
        assert "200" in self.report.render()
