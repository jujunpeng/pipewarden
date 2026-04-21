"""Renders a text summary of a CheckHeatmap."""
from __future__ import annotations

from pipewarden.heatmap import CheckHeatmap


class HeatmapReporter:
    """Produces a human-readable report from a CheckHeatmap."""

    def __init__(self, heatmap: CheckHeatmap) -> None:
        if not isinstance(heatmap, CheckHeatmap):
            raise TypeError("heatmap must be a CheckHeatmap instance")
        self._heatmap = heatmap

    def render(self) -> str:
        """Return a formatted string report of failure rates per check/bucket."""
        lines: list[str] = ["=== Check Failure Heatmap ==="]
        names = self._heatmap.check_names()
        if not names:
            lines.append("  (no data recorded)")
            return "\n".join(lines)

        for name in names:
            lines.append(f"  {name}")
            for bucket in self._heatmap.buckets_for(name):
                cell = self._heatmap.get(name, bucket)
                if cell is None:
                    continue
                bar = self._bar(cell.failure_rate)
                lines.append(
                    f"    {bucket}  {bar}  "
                    f"{cell.failure_count}/{cell.total_count} failures "
                    f"({cell.failure_rate * 100:.1f}%)"
                )
        return "\n".join(lines)

    @staticmethod
    def _bar(rate: float, width: int = 10) -> str:
        filled = round(rate * width)
        return "[" + "#" * filled + "." * (width - filled) + "]"

    def __str__(self) -> str:  # pragma: no cover
        return self.render()
