"""Workout Module Usage Tracker.

Tracks how often each workout module is selected by the AI.
Provides statistics for understanding module selection patterns.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Usage stats file location
USAGE_STATS_FILE = Path(__file__).parent.parent.parent / "data" / "module_usage_stats.json"


class ModuleUsageTracker:
    """Tracks workout module selection frequency."""

    def __init__(self, stats_file: Optional[Path] = None):
        """Initialize tracker.

        Args:
            stats_file: Path to JSON file for storing stats (default: data/module_usage_stats.json)
        """
        self.stats_file = stats_file or USAGE_STATS_FILE
        self.stats = self._load_stats()

    def _load_stats(self) -> Dict:
        """Load usage statistics from file."""
        if not self.stats_file.exists():
            return {
                "total_selections": 0,
                "modules": defaultdict(lambda: {"count": 0, "last_used": None}),
                "by_category": {
                    "warmup": defaultdict(int),
                    "main": defaultdict(int),
                    "rest": defaultdict(int),
                    "cooldown": defaultdict(int),
                },
            }

        try:
            with open(self.stats_file, 'r') as f:
                data = json.load(f)

            # Convert to defaultdict for easier access
            if "modules" in data:
                data["modules"] = defaultdict(
                    lambda: {"count": 0, "last_used": None},
                    data["modules"]
                )

            if "by_category" in data:
                for category in data["by_category"]:
                    data["by_category"][category] = defaultdict(int, data["by_category"][category])

            return data

        except Exception as e:
            logger.error(f"Failed to load usage stats: {e}")
            return {
                "total_selections": 0,
                "modules": defaultdict(lambda: {"count": 0, "last_used": None}),
                "by_category": {
                    "warmup": defaultdict(int),
                    "main": defaultdict(int),
                    "rest": defaultdict(int),
                    "cooldown": defaultdict(int),
                },
            }

    def _save_stats(self):
        """Save usage statistics to file."""
        try:
            # Ensure directory exists
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert defaultdict to regular dict for JSON serialization
            data = {
                "total_selections": self.stats["total_selections"],
                "modules": dict(self.stats["modules"]),
                "by_category": {
                    category: dict(modules)
                    for category, modules in self.stats["by_category"].items()
                },
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.stats_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save usage stats: {e}")

    def record_selection(self, module_keys: List[str], categories: Optional[Dict[str, str]] = None):
        """Record module selection.

        Args:
            module_keys: List of selected module keys
            categories: Optional dict mapping module_key -> category (warmup/main/rest/cooldown)
        """
        timestamp = datetime.now().isoformat()

        for module_key in module_keys:
            # Update module stats
            if module_key not in self.stats["modules"]:
                self.stats["modules"][module_key] = {"count": 0, "last_used": None}

            self.stats["modules"][module_key]["count"] += 1
            self.stats["modules"][module_key]["last_used"] = timestamp

            # Update category stats
            if categories and module_key in categories:
                category = categories[module_key]
                if category in self.stats["by_category"]:
                    self.stats["by_category"][category][module_key] += 1

        # Update total
        self.stats["total_selections"] += 1

        # Save to disk
        self._save_stats()

        logger.info(f"Recorded selection of {len(module_keys)} modules (total: {self.stats['total_selections']})")

    def get_module_stats(self, module_key: str) -> Dict:
        """Get statistics for a specific module.

        Args:
            module_key: Module key to look up

        Returns:
            Dict with count and last_used timestamp
        """
        return self.stats["modules"].get(module_key, {"count": 0, "last_used": None})

    def get_category_stats(self, category: str) -> Dict[str, int]:
        """Get usage statistics for a category.

        Args:
            category: Category name (warmup/main/rest/cooldown)

        Returns:
            Dict mapping module_key -> count
        """
        return dict(self.stats["by_category"].get(category, {}))

    def get_top_modules(self, category: Optional[str] = None, limit: int = 10) -> List[tuple]:
        """Get most frequently used modules.

        Args:
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of (module_key, count) tuples sorted by count descending
        """
        if category:
            stats = self.stats["by_category"].get(category, {})
        else:
            stats = {k: v["count"] for k, v in self.stats["modules"].items()}

        sorted_modules = sorted(stats.items(), key=lambda x: x[1], reverse=True)
        return sorted_modules[:limit]

    def get_least_used_modules(
        self,
        available_modules: List[str],
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[str]:
        """Get least frequently used modules from available list.

        Useful for ensuring variety in workout generation.

        Args:
            available_modules: List of module keys to consider
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of module keys sorted by usage (least used first)
        """
        if category:
            stats = self.stats["by_category"].get(category, {})
        else:
            stats = {k: v["count"] for k, v in self.stats["modules"].items()}

        # Get counts for available modules (default to 0 if never used)
        module_counts = [(key, stats.get(key, 0)) for key in available_modules]

        # Sort by count ascending (least used first)
        sorted_modules = sorted(module_counts, key=lambda x: x[1])

        return [key for key, _ in sorted_modules[:limit]]

    def get_summary(self) -> Dict:
        """Get summary statistics.

        Returns:
            Dict with total selections, module count, and category breakdown
        """
        return {
            "total_selections": self.stats["total_selections"],
            "unique_modules_used": len(self.stats["modules"]),
            "category_totals": {
                category: sum(modules.values())
                for category, modules in self.stats["by_category"].items()
            },
            "top_modules": self.get_top_modules(limit=5),
        }

    def print_report(self):
        """Print a human-readable usage report."""
        summary = self.get_summary()

        print("\n" + "="*60)
        print("WORKOUT MODULE USAGE REPORT")
        print("="*60)
        print(f"\nTotal Selections: {summary['total_selections']}")
        print(f"Unique Modules Used: {summary['unique_modules_used']}")

        print("\nCategory Totals:")
        for category, total in summary['category_totals'].items():
            print(f"  {category.capitalize():12} {total:>5}")

        print("\nTop 10 Most Used Modules (Overall):")
        top_overall = self.get_top_modules(limit=10)
        for i, (module, count) in enumerate(top_overall, 1):
            print(f"  {i:2}. {module:30} {count:>5} times")

        for category in ["warmup", "main", "rest", "cooldown"]:
            print(f"\nTop 5 Most Used {category.capitalize()} Modules:")
            top_category = self.get_top_modules(category=category, limit=5)
            for i, (module, count) in enumerate(top_category, 1):
                print(f"  {i}. {module:30} {count:>5} times")

        print("\n" + "="*60 + "\n")


# Global tracker instance
_global_tracker: Optional[ModuleUsageTracker] = None


def get_tracker() -> ModuleUsageTracker:
    """Get global tracker instance (singleton pattern)."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ModuleUsageTracker()
    return _global_tracker
