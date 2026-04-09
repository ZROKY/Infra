"""Tests for Consistency Engine analyzers."""

from __future__ import annotations

import pytest

from engine_consistency.analyzers.benchmark import BenchmarkAnalyzer
from engine_consistency.analyzers.drift import DriftAnalyzer
from engine_consistency.analyzers.fingerprint import FingerprintAnalyzer
from engine_consistency.analyzers.regression import RegressionAnalyzer
from engine_consistency.analyzers.version_tracker import VersionTracker
from engine_consistency.models import AnalysisType

# ── Benchmark Analyzer ─────────────────────────────────────────────────


class TestBenchmarkAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return BenchmarkAnalyzer(redis_client=None)

    @pytest.mark.asyncio
    async def test_quality_score_good_response(self, analyzer):
        response = "The Python programming language is widely used for data science. It provides excellent libraries such as pandas and numpy. These tools enable efficient data manipulation and numerical computing."
        result = await analyzer.analyze(response, "c1", "a1")
        assert result.analysis_type == AnalysisType.benchmark
        assert result.score >= 70

    @pytest.mark.asyncio
    async def test_quality_score_empty_response(self, analyzer):
        result = await analyzer.analyze("", "c1", "a1")
        assert result.score == 0.0

    @pytest.mark.asyncio
    async def test_quality_score_short_response(self, analyzer):
        result = await analyzer.analyze("Yes", "c1", "a1")
        assert result.score < 70

    @pytest.mark.asyncio
    async def test_no_baseline_gives_moderate_confidence(self, analyzer):
        result = await analyzer.analyze("A reasonably long response with details.", "c1", "a1")
        assert result.confidence < 0.8


# ── Drift Analyzer ─────────────────────────────────────────────────────


class TestDriftAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return DriftAnalyzer(redis_client=None)

    @pytest.mark.asyncio
    async def test_insufficient_data(self, analyzer):
        results, metrics = await analyzer.analyze("test response", "c1", "a1")
        assert len(results) == 1
        assert results[0].score == 90.0
        assert results[0].details["reason"] == "insufficient_baseline_data"

    def test_extract_features(self):
        features = DriftAnalyzer._extract_features("Hello world how are you today")
        assert features["response_length"] == 29
        assert features["word_count"] == 6
        assert features["avg_word_length"] > 3

    def test_psi_identical_distributions(self):
        data = [100, 200, 300, 400, 500, 150, 250, 350, 450, 550]
        from engine_consistency.analyzers.drift import RESPONSE_LENGTH_BINS
        psi = DriftAnalyzer._compute_psi(data, data, RESPONSE_LENGTH_BINS)
        assert psi < 0.01

    def test_psi_different_distributions(self):
        base = [100, 150, 200, 250, 300, 100, 150, 200, 250, 300]
        shifted = [5000, 6000, 7000, 8000, 9000, 5000, 6000, 7000, 8000, 9000]
        from engine_consistency.analyzers.drift import RESPONSE_LENGTH_BINS
        psi = DriftAnalyzer._compute_psi(base, shifted, RESPONSE_LENGTH_BINS)
        assert psi > 0.1


# ── Regression Analyzer ────────────────────────────────────────────────


class TestRegressionAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return RegressionAnalyzer(redis_client=None)

    @pytest.mark.asyncio
    async def test_no_baseline(self, analyzer):
        result = await analyzer.analyze("What is Python?", "Python is a programming language.", "c1", "a1")
        assert result.analysis_type == AnalysisType.regression
        assert result.score == 85.0
        assert result.details["reason"] == "no_baseline_response"

    def test_similarity_identical(self):
        sim = RegressionAnalyzer._compute_similarity("Hello world", "Hello world")
        assert sim == 1.0

    def test_similarity_different(self):
        sim = RegressionAnalyzer._compute_similarity("The sun is hot", "Bananas are yellow fruits")
        assert sim < 0.3

    def test_structural_similarity(self):
        a = "First sentence. Second sentence. Third sentence."
        b = "One sentence. Two sentences. Three sentences."
        sim = RegressionAnalyzer._structural_similarity(a, b)
        assert sim > 0.7


# ── Fingerprint Analyzer ──────────────────────────────────────────────


class TestFingerprintAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return FingerprintAnalyzer(redis_client=None)

    @pytest.mark.asyncio
    async def test_no_previous(self, analyzer):
        result = await analyzer.analyze("test response", "c1", "a1")
        assert result.analysis_type == AnalysisType.fingerprint
        assert result.score == 90.0

    def test_fingerprint_generates_vector(self):
        fp = FingerprintAnalyzer._generate_fingerprint("Hello world. This is a test response with some content.")
        assert len(fp) == 12
        assert all(0 <= v <= 1 for v in fp)

    def test_delta_identical(self):
        fp = FingerprintAnalyzer._generate_fingerprint("Same response text here.")
        delta = FingerprintAnalyzer._compute_delta(fp, fp)
        assert delta < 0.001

    def test_delta_different(self):
        fp1 = FingerprintAnalyzer._generate_fingerprint("Short.")
        fp2 = FingerprintAnalyzer._generate_fingerprint("A very very very very very very very very long response with lots of words and sentences. " * 10)
        delta = FingerprintAnalyzer._compute_delta(fp1, fp2)
        assert delta > 0.01


# ── Version Tracker ────────────────────────────────────────────────────


class TestVersionTracker:
    @pytest.fixture
    def tracker(self):
        return VersionTracker(redis_client=None)

    @pytest.mark.asyncio
    async def test_first_version(self, tracker):
        result = await tracker.analyze("gpt-4", "gpt-4-0125", "c1", "a1")
        assert result.analysis_type == AnalysisType.version_tracking
        assert result.score == 90.0
        assert result.details["model_version"] == "gpt-4-0125"

    @pytest.mark.asyncio
    async def test_no_version_string_uses_model_name(self, tracker):
        result = await tracker.analyze("gpt-4", "", "c1", "a1")
        assert result.details["model_version"] == "gpt-4"
