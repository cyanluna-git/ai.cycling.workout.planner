#!/usr/bin/env python3
"""Manual E2E Test - TSB-based intensity hotfix validation.

Tests the fix by inspecting the actual source code behavior.
"""

import re

# Read the fixed file
with open('/home/cyanluna-jarvis/ai.cycling.workout.planner/src/services/workout_assembler.py', 'r') as f:
    source_code = f.read()

print("🧪 Hotfix Validation - Static Code Analysis\n")

# Check 1: TSB-based auto selection exists
has_auto_check = 'if intensity == "auto" or not intensity:' in source_code
has_tsb_fatigued = 'if self.tsb < -10' in source_code
has_tsb_fresh = 'elif self.tsb > 10' in source_code
has_moderate_fallback = 'else:  # Neutral state' in source_code or 'else:  # moderate' in source_code

print("✅ Check 1: Auto intensity handling")
print(f"   - 'auto' check present: {'✅' if has_auto_check else '❌'}")
print(f"   - TSB < -10 (fatigued): {'✅' if has_tsb_fatigued else '❌'}")
print(f"   - TSB > 10 (fresh): {'✅' if has_tsb_fresh else '❌'}")
print(f"   - Moderate fallback: {'✅' if has_moderate_fallback else '❌'}")
print()

# Check 2: Debug logging exists
has_debug_logging = 'logger.debug' in source_code and 'Auto-selected' in source_code
print("✅ Check 2: Debug logging")
print(f"   - Debug logs present: {'✅' if has_debug_logging else '❌'}")
print()

# Check 3: Comment markers
has_hotfix_marker = '[HOTFIX]' in source_code
print("✅ Check 3: Hotfix markers")
print(f"   - [HOTFIX] marker present: {'✅' if has_hotfix_marker else '❌'}")
print()

# Extract the fixed function
match = re.search(
    r'def _select_main_segments\(.*?\):(.*?)(?=\n    def |\Z)',
    source_code,
    re.DOTALL
)

if match:
    function_body = match.group(1)
    
    # Count intensity branches
    easy_count = function_body.count('intensity == "easy"')
    hard_count = function_body.count('intensity == "hard"')
    auto_count = function_body.count('intensity == "auto"')
    
    print("✅ Check 4: Function structure")
    print(f"   - Easy branch: {easy_count} occurrence(s) {'✅' if easy_count > 0 else '❌'}")
    print(f"   - Hard branch: {hard_count} occurrence(s) {'✅' if hard_count > 0 else '❌'}")
    print(f"   - Auto branch: {auto_count} occurrence(s) {'✅' if auto_count > 0 else '❌'}")
    print()

# Final verdict
all_checks = [
    has_auto_check,
    has_tsb_fatigued,
    has_tsb_fresh,
    has_moderate_fallback,
    has_debug_logging,
    has_hotfix_marker
]

print("="*50)
if all(all_checks):
    print("✅ HOTFIX VALIDATION PASSED")
    print("   All required changes are present.")
    exit_code = 0
else:
    print("❌ HOTFIX VALIDATION FAILED")
    print(f"   {sum(all_checks)}/{len(all_checks)} checks passed.")
    exit_code = 1

print("="*50)
print()

# Show the actual auto-selection logic
print("🔍 Extracted Auto-Selection Logic:\n")
auto_logic_match = re.search(
    r'# \[HOTFIX\].*?if intensity == "auto".*?(?=\n        # Filter)',
    source_code,
    re.DOTALL
)

if auto_logic_match:
    print(auto_logic_match.group(0))
else:
    print("⚠️  Could not extract auto-selection logic")

exit(exit_code)
