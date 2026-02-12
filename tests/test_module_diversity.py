import pytest
from src.services.module_usage_tracker import ModuleUsageTracker
from collections import Counter
import tempfile
from pathlib import Path


class TestModuleUsageTracker:
    """Test module usage tracking and diversity scoring."""

    def test_calculate_priority_weights_equal_for_unused(self):
        """Never-used modules should all have equal weight."""
        tracker = ModuleUsageTracker(stats_file=Path(tempfile.mktemp()))
        
        modules = ["module_a", "module_b", "module_c"]
        weights = tracker.calculate_priority_weights(modules)
        
        # All should be 1.0 (equal)
        assert all(w == 1.0 for w in weights.values())
        print("✅ Equal weights for unused modules")

    def test_calculate_priority_weights_favors_less_used(self):
        """Less used modules should get higher weights."""
        tracker = ModuleUsageTracker(stats_file=Path(tempfile.mktemp()))
        
        # Simulate usage
        tracker.record_selection(["module_a"], categories={"module_a": "main"})
        tracker.record_selection(["module_a"], categories={"module_a": "main"})
        tracker.record_selection(["module_a"], categories={"module_a": "main"})
        tracker.record_selection(["module_b"], categories={"module_b": "main"})
        
        modules = ["module_a", "module_b", "module_c"]
        weights = tracker.calculate_priority_weights(modules, category="main")
        
        # module_c (never used) should have highest weight
        # module_a (most used) should have lowest weight
        assert weights["module_c"] > weights["module_b"]
        assert weights["module_b"] > weights["module_a"]
        print(f"✅ Weights favor less used: {weights}")

    def test_get_least_used_modules(self):
        """Should return modules sorted by usage (least first)."""
        tracker = ModuleUsageTracker(stats_file=Path(tempfile.mktemp()))
        
        # Simulate different usage frequencies
        for _ in range(5):
            tracker.record_selection(["popular"], categories={"popular": "main"})
        for _ in range(2):
            tracker.record_selection(["medium"], categories={"medium": "main"})
        # 'rare' never used
        
        available = ["popular", "medium", "rare"]
        least_used = tracker.get_least_used_modules(available, category="main", limit=3)
        
        # Should be ordered: rare, medium, popular
        assert least_used[0] == "rare"
        assert least_used[1] == "medium"
        assert least_used[2] == "popular"
        print(f"✅ Least used order: {least_used}")

    def test_record_selection_increments_count(self):
        """Recording selection should increment usage count."""
        tracker = ModuleUsageTracker(stats_file=Path(tempfile.mktemp()))
        
        initial = tracker.get_module_stats("test_module")["count"]
        tracker.record_selection(["test_module"], categories={"test_module": "main"})
        after = tracker.get_module_stats("test_module")["count"]
        
        assert after == initial + 1
        print("✅ Selection count incremented")

    def test_diversity_over_multiple_selections(self):
        """Multiple selections should show diversity (probabilistic test)."""
        tracker = ModuleUsageTracker(stats_file=Path(tempfile.mktemp()))
        
        # Pre-bias: select module_a many times
        for _ in range(20):
            tracker.record_selection(["module_a"], categories={"module_a": "main"})
        
        # Now module_b and module_c should be preferred
        modules = ["module_a", "module_b", "module_c"]
        weights = tracker.calculate_priority_weights(modules, category="main")
        
        # Weights should be significantly different
        assert weights["module_b"] > 1.5  # High weight for unused
        assert weights["module_a"] < 1.0  # Low weight for overused
        print(f"✅ Diversity weights after bias: {weights}")


class TestWorkoutDiversity:
    """Integration tests for workout diversity."""

    def test_diversity_scenario_simulation(self):
        """Simulate realistic scenario: repeated workout generation."""
        # This is more of a documentation test - shows how it works
        tracker = ModuleUsageTracker(stats_file=Path(tempfile.mktemp()))
        
        # Available modules
        available = ["ss_1", "ss_2", "threshold_1", "vo2max_1"]
        
        # Simulate 10 workout generations
        selections = []
        for i in range(10):
            # Get weights
            weights_dict = tracker.calculate_priority_weights(available, category="main")
            
            # This would normally be done by random.choices in the assembler
            # For testing, just track the weights
            selections.append(weights_dict.copy())
            
            # Simulate selecting the one with highest weight
            selected = max(weights_dict, key=weights_dict.get)
            tracker.record_selection([selected], categories={selected: "main"})
        
        # Check that over time, different modules get selected
        # (weights should shift)
        first_weights = selections[0]
        last_weights = selections[-1]
        
        print(f"\n  First iteration weights: {first_weights}")
        print(f"  Last iteration weights: {last_weights}")
        
        # At least one module's weight should have changed significantly
        changes = [
            abs(last_weights[k] - first_weights[k])
            for k in available
        ]
        assert max(changes) > 0.2, "Weights should shift over time"
        print("✅ Weights adapt to promote diversity")
