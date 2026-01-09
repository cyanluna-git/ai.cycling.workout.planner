#!/usr/bin/env python3
"""View workout module usage statistics.

This script displays usage statistics for workout modules,
showing which modules are selected most/least frequently.

Usage:
    python scripts/view_module_stats.py
    python scripts/view_module_stats.py --category main
    python scripts/view_module_stats.py --export stats.json
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.module_usage_tracker import get_tracker


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='View workout module usage statistics')
    parser.add_argument('--category', type=str, choices=['warmup', 'main', 'rest', 'cooldown'],
                        help='Filter by category')
    parser.add_argument('--limit', type=int, default=10, help='Number of top modules to show')
    parser.add_argument('--export', type=str, help='Export statistics to JSON file')

    args = parser.parse_args()

    # Get tracker
    tracker = get_tracker()

    # Export to JSON if requested
    if args.export:
        data = {
            "summary": tracker.get_summary(),
            "all_modules": dict(tracker.stats["modules"]),
            "by_category": {
                cat: dict(mods)
                for cat, mods in tracker.stats["by_category"].items()
            }
        }

        with open(args.export, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Statistics exported to {args.export}")
        return

    # Print report
    if args.category:
        print(f"\n{'='*60}")
        print(f"MODULE USAGE STATISTICS - {args.category.upper()}")
        print('='*60)

        stats = tracker.get_category_stats(args.category)
        total = sum(stats.values())

        print(f"\nTotal selections in {args.category}: {total}")
        print(f"Unique modules used: {len(stats)}")

        top_modules = tracker.get_top_modules(category=args.category, limit=args.limit)
        print(f"\nTop {args.limit} Most Used Modules:")
        for i, (module, count) in enumerate(top_modules, 1):
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {i:2}. {module:35} {count:>5} times ({percentage:>5.1f}%)")

        print("\n" + "="*60 + "\n")
    else:
        # Print full report
        tracker.print_report()


if __name__ == '__main__':
    main()
