"""Tests for pipewarden.context."""

import pytest

from pipewarden.context import CheckContext, make_context


class TestCheckContext:
    def _make(self, **kwargs) -> CheckContext:
        defaults = {"run_id": "run-001"}
        defaults.update(kwargs)
        return make_context(**defaults)

    # --- construction ---

    def test_run_id_stored(self):
        ctx = self._make(run_id="abc")
        assert ctx.run_id == "abc"

    def test_default_tags_empty(self):
        ctx = self._make()
        assert ctx.tags == {}

    def test_default_metadata_empty(self):
        ctx = self._make()
        assert ctx.metadata == {}

    def test_default_timeout_is_none(self):
        ctx = self._make()
        assert ctx.timeout_seconds is None

    def test_custom_tags(self):
        ctx = self._make(tags={"env": "prod"})
        assert ctx.tags["env"] == "prod"

    def test_custom_metadata(self):
        ctx = self._make(metadata={"owner": "data-team"})
        assert ctx.metadata["owner"] == "data-team"

    def test_custom_timeout(self):
        ctx = self._make(timeout_seconds=30.0)
        assert ctx.timeout_seconds == 30.0

    # --- with_tag ---

    def test_with_tag_returns_new_context(self):
        ctx = self._make()
        new_ctx = ctx.with_tag("region", "us-east")
        assert new_ctx is not ctx

    def test_with_tag_adds_tag(self):
        ctx = self._make()
        new_ctx = ctx.with_tag("region", "us-east")
        assert new_ctx.tags["region"] == "us-east"

    def test_with_tag_does_not_mutate_original(self):
        ctx = self._make(tags={"env": "prod"})
        ctx.with_tag("region", "us-east")
        assert "region" not in ctx.tags

    def test_with_tag_preserves_existing_tags(self):
        ctx = self._make(tags={"env": "prod"})
        new_ctx = ctx.with_tag("region", "us-east")
        assert new_ctx.tags["env"] == "prod"

    # --- with_metadata ---

    def test_with_metadata_returns_new_context(self):
        ctx = self._make()
        new_ctx = ctx.with_metadata("key", 42)
        assert new_ctx is not ctx

    def test_with_metadata_adds_entry(self):
        ctx = self._make()
        new_ctx = ctx.with_metadata("threshold", 0.95)
        assert new_ctx.metadata["threshold"] == 0.95

    def test_with_metadata_does_not_mutate_original(self):
        ctx = self._make(metadata={"x": 1})
        ctx.with_metadata("y", 2)
        assert "y" not in ctx.metadata

    # --- has_tag ---

    def test_has_tag_true_when_present(self):
        ctx = self._make(tags={"env": "staging"})
        assert ctx.has_tag("env") is True

    def test_has_tag_false_when_absent(self):
        ctx = self._make()
        assert ctx.has_tag("missing") is False

    # --- make_context ---

    def test_make_context_none_tags_defaults_to_empty(self):
        ctx = make_context(run_id="x", tags=None)
        assert ctx.tags == {}

    def test_make_context_none_metadata_defaults_to_empty(self):
        ctx = make_context(run_id="x", metadata=None)
        assert ctx.metadata == {}
