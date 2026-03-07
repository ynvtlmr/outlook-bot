"""Tests for the GUI module (import-only, since GUI requires display)."""

import pytest


@pytest.mark.skipif(True, reason="GUI tests require display environment")
class TestOutlookBotGUI:
    def test_placeholder(self):
        pass
