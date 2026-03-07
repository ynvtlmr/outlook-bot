"""Tests for the main CLI entry point."""

from unittest.mock import patch

from shorting_intel.main import (
    build_parser,
    run_category_filter,
    run_counter_intel_only,
    run_scores_only,
    run_single_ticker,
)


class TestCLIParser:
    def test_default_args(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert not args.signals_only
        assert not args.scores_only
        assert not args.counter_intel
        assert args.ticker is None
        assert args.days == 30
        assert not args.json
        assert not args.verbose

    def test_signals_only(self):
        parser = build_parser()
        args = parser.parse_args(["--signals-only"])
        assert args.signals_only

    def test_ticker_arg(self):
        parser = build_parser()
        args = parser.parse_args(["--ticker", "CHGG"])
        assert args.ticker == "CHGG"

    def test_days_arg(self):
        parser = build_parser()
        args = parser.parse_args(["--days", "7"])
        assert args.days == 7

    def test_verbose_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-v"])
        assert args.verbose


class TestScoresOnly:
    def test_generates_output(self):
        output = run_scores_only()
        assert "DISRUPTION SCORES" in output
        assert "CHGG" in output

    def test_contains_all_targets(self):
        output = run_scores_only()
        assert "Chegg" in output
        assert "Five9" in output


class TestCounterIntelOnly:
    def test_generates_output(self):
        output = run_counter_intel_only()
        assert "COUNTER-INTELLIGENCE ANALYSIS" in output
        assert "Defense:" in output
        assert "Deception:" in output


class TestSingleTicker:
    def test_valid_ticker(self):
        output = run_single_ticker("CHGG")
        assert "DEEP DIVE" in output
        assert "Chegg" in output
        assert "DISRUPTION THESIS" in output
        assert "COUNTER-INTELLIGENCE" in output

    def test_invalid_ticker(self):
        output = run_single_ticker("ZZZZZ")
        assert "not found" in output

    def test_case_insensitive(self):
        output = run_single_ticker("chgg")
        assert "Chegg" in output


class TestCategoryFilter:
    def test_valid_category(self):
        output = run_category_filter("education_tutoring")
        assert "EDUCATION" in output
        assert "CHGG" in output

    def test_invalid_category(self):
        output = run_category_filter("nonexistent_category")
        assert "Unknown category" in output
