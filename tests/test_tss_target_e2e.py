"""E2E tests for Weekly TSS Target, Achievement, and Badge system."""

import json
import pytest

# Import the functions under test
from api.routers.plans import calculate_achievement_status, BADGES


# === Achievement Status Calculation ===

class TestAchievementStatus:
    """Test calculate_achievement_status function."""

    def test_achievement_exceeded(self):
        """actual >= target * 1.1 → 'exceeded'"""
        status, pct = calculate_achievement_status(400, 440)
        assert status == "exceeded"
        assert pct == 110

    def test_achievement_exceeded_high(self):
        """Way over target."""
        status, pct = calculate_achievement_status(300, 450)
        assert status == "exceeded"
        assert pct == 150

    def test_achievement_achieved(self):
        """target * 0.9 <= actual < target * 1.1 → 'achieved'"""
        status, pct = calculate_achievement_status(400, 380)
        assert status == "achieved"
        assert pct == 95

    def test_achievement_achieved_exact(self):
        """Exactly on target."""
        status, pct = calculate_achievement_status(400, 400)
        assert status == "achieved"
        assert pct == 100

    def test_achievement_achieved_lower_bound(self):
        """Exactly at 90%."""
        status, pct = calculate_achievement_status(400, 360)
        assert status == "achieved"
        assert pct == 90

    def test_achievement_partial(self):
        """target * 0.7 <= actual < target * 0.9 → 'partial'"""
        status, pct = calculate_achievement_status(400, 320)
        assert status == "partial"
        assert pct == 80

    def test_achievement_partial_lower_bound(self):
        """Exactly at 70%."""
        status, pct = calculate_achievement_status(400, 280)
        assert status == "partial"
        assert pct == 70

    def test_achievement_missed(self):
        """actual < target * 0.7 → 'missed'"""
        status, pct = calculate_achievement_status(400, 200)
        assert status == "missed"
        assert pct == 50

    def test_achievement_missed_zero(self):
        """Zero actual TSS."""
        status, pct = calculate_achievement_status(400, 0)
        assert status == "missed"
        assert pct == 0

    def test_achievement_no_target_none(self):
        """No target set (None)."""
        status, pct = calculate_achievement_status(None, 300)
        assert status == "no_target"
        assert pct == 0

    def test_achievement_no_target_zero(self):
        """Target is zero."""
        status, pct = calculate_achievement_status(0, 300)
        assert status == "no_target"
        assert pct == 0


# === Warning System ===

class TestWarningSystem:
    """Test TSS target unachievable warning logic (inline, mirrors plans.py logic)."""

    MAX_DAILY_TSS = 150

    def _check_warning(self, weekly_tss_target, accumulated_tss, days_remaining):
        """Replicate the warning logic from plans.py."""
        remaining_tss = (weekly_tss_target or 0) - accumulated_tss
        max_achievable = days_remaining * self.MAX_DAILY_TSS
        target_achievable = remaining_tss <= max_achievable

        achievement_warning = None
        if weekly_tss_target and not target_achievable:
            achievement_pct = int((accumulated_tss / weekly_tss_target) * 100)
            achievement_warning = json.dumps({
                "key": "tss_target_unachievable",
                "days": days_remaining,
                "target": weekly_tss_target,
                "accumulated": accumulated_tss,
                "pct": achievement_pct,
            })
        return achievement_warning, target_achievable

    def test_warning_when_unachievable(self):
        """남은일수 x 150 < 남은TSS → 경고."""
        warning, achievable = self._check_warning(500, 0, 2)
        assert not achievable
        assert warning is not None
        data = json.loads(warning)
        assert data["key"] == "tss_target_unachievable"
        assert data["days"] == 2
        assert data["target"] == 500

    def test_no_warning_when_achievable(self):
        """충분한 시간 → 경고 없음."""
        warning, achievable = self._check_warning(500, 200, 5)
        assert achievable
        assert warning is None

    def test_warning_data_structure(self):
        """Warning contains all required numeric data."""
        warning, _ = self._check_warning(600, 100, 1)
        assert warning is not None
        data = json.loads(warning)
        assert isinstance(data["days"], int)
        assert isinstance(data["target"], int)
        assert isinstance(data["accumulated"], int)
        assert isinstance(data["pct"], int)
        assert data["pct"] == 16


# === Streak Tracking ===

class TestStreakTracking:
    """Test streak calculation logic (mirrors get_achievements logic)."""

    @staticmethod
    def _calculate_streak(statuses):
        """Calculate streak from a list of statuses (most recent first)."""
        streak = 0
        for s in statuses:
            if s in ["achieved", "exceeded"]:
                streak += 1
            elif s == "in_progress":
                continue
            else:
                break
        return streak

    @staticmethod
    def _calculate_best_streak(statuses):
        """Calculate best streak from a list of statuses (most recent first)."""
        best = 0
        current = 0
        for s in reversed(statuses):
            if s in ["achieved", "exceeded"]:
                current += 1
                best = max(best, current)
            elif s == "in_progress":
                continue
            else:
                current = 0
        return best

    def test_streak_consecutive(self):
        """3주 연속 achieved → streak = 3."""
        statuses = ["achieved", "exceeded", "achieved"]
        assert self._calculate_streak(statuses) == 3

    def test_streak_broken(self):
        """achieved, achieved, missed, achieved → streak = 1 (most recent first)."""
        statuses = ["achieved", "missed", "achieved", "achieved"]
        assert self._calculate_streak(statuses) == 1

    def test_streak_skips_in_progress(self):
        """in_progress 주는 건너뜀."""
        statuses = ["in_progress", "achieved", "achieved", "exceeded"]
        assert self._calculate_streak(statuses) == 3

    def test_best_streak(self):
        """Best streak across all history."""
        statuses = ["missed", "achieved", "achieved", "achieved", "missed", "achieved"]
        assert self._calculate_best_streak(statuses) == 3


# === Badge System ===

class TestBadgeSystem:
    """Test badge earning logic (mirrors get_achievements logic)."""

    @staticmethod
    def _earn_badges(best_streak, total_exceeded):
        """Calculate earned badges."""
        earned = []
        for badge_id, badge in BADGES.items():
            if badge["type"] == "streak" and best_streak >= badge["requirement"]:
                earned.append(badge_id)
            elif badge["type"] == "exceeded" and total_exceeded >= badge["requirement"]:
                earned.append(badge_id)
        return earned

    @staticmethod
    def _next_badge(current_streak):
        """Calculate next badge."""
        streak_badges = sorted(
            [(k, v) for k, v in BADGES.items() if v["type"] == "streak"],
            key=lambda x: x[1]["requirement"]
        )
        for badge_id, badge in streak_badges:
            if current_streak < badge["requirement"]:
                return badge_id, badge["requirement"] - current_streak
        return None, 0

    def test_badge_first_week(self):
        """1주 달성 → first_week 뱃지."""
        earned = self._earn_badges(best_streak=1, total_exceeded=0)
        assert "first_week" in earned

    def test_badge_consistent_3(self):
        """3주 연속 → consistent_3 뱃지."""
        earned = self._earn_badges(best_streak=3, total_exceeded=0)
        assert "consistent_3" in earned
        assert "first_week" in earned

    def test_badge_overachiever(self):
        """5회 exceeded → overachiever 뱃지."""
        earned = self._earn_badges(best_streak=0, total_exceeded=5)
        assert "overachiever_5" in earned

    def test_badge_not_earned_yet(self):
        """Requirements not met → no badge."""
        earned = self._earn_badges(best_streak=0, total_exceeded=0)
        assert len(earned) == 0

    def test_next_badge_calculation(self):
        """다음 뱃지까지 남은 주 계산."""
        badge_id, remaining = self._next_badge(current_streak=2)
        assert badge_id == "consistent_3"
        assert remaining == 1

    def test_next_badge_after_first(self):
        """After earning first_week, next is consistent_3."""
        badge_id, remaining = self._next_badge(current_streak=1)
        assert badge_id == "consistent_3"
        assert remaining == 2

    def test_next_badge_from_zero(self):
        """Starting fresh, next is first_week."""
        badge_id, remaining = self._next_badge(current_streak=0)
        assert badge_id == "first_week"
        assert remaining == 1


# === TSS Target Priority ===

class TestTSSTargetPriority:
    """Test TSS target resolution priority: parameter > settings > auto."""

    @staticmethod
    def _resolve_tss_target(param_target, settings_target, ctl, training_focus="maintain"):
        """Replicate TSS target priority logic from WeeklyPlanGenerator."""
        if param_target is not None:
            return param_target, "parameter"
        elif settings_target:
            return int(settings_target), "settings"
        else:
            base_tss = int(ctl * 7)
            multipliers = {"recovery": 0.7, "maintain": 1.0, "build": 1.1}
            multiplier = multipliers.get(training_focus, 1.0)
            return int(base_tss * multiplier), "auto"

    def test_tss_target_parameter_priority(self):
        """파라미터 > settings > auto."""
        target, source = self._resolve_tss_target(500, 400, 60)
        assert target == 500
        assert source == "parameter"

    def test_tss_target_from_settings(self):
        """user_settings에서 가져오기."""
        target, source = self._resolve_tss_target(None, 450, 60)
        assert target == 450
        assert source == "settings"

    def test_tss_target_auto_calculation(self):
        """CTL 기반 자동 계산."""
        target, source = self._resolve_tss_target(None, None, 60)
        assert target == 420
        assert source == "auto"

    def test_tss_target_auto_build(self):
        """CTL 기반 자동 계산 (build focus)."""
        target, source = self._resolve_tss_target(None, None, 60, "build")
        assert target == 462
        assert source == "auto"

    def test_tss_target_auto_recovery(self):
        """CTL 기반 자동 계산 (recovery focus)."""
        target, source = self._resolve_tss_target(None, None, 60, "recovery")
        assert target == 294
        assert source == "auto"


# === Full Integration Flow ===

class TestFullFlow:
    """Test the complete flow: target → achievement → streak → badges."""

    def test_full_flow(self):
        """목표 설정 → 달성 판정 → streak → 뱃지 획득."""
        s1, p1 = calculate_achievement_status(400, 420)
        assert s1 == "achieved"

        s2, p2 = calculate_achievement_status(400, 450)
        assert s2 == "exceeded"

        s3, p3 = calculate_achievement_status(400, 380)
        assert s3 == "achieved"

        statuses = [s3, s2, s1]
        streak = 0
        for s in statuses:
            if s in ["achieved", "exceeded"]:
                streak += 1
            else:
                break
        assert streak == 3

        earned = []
        total_exceeded = sum(1 for s in statuses if s == "exceeded")
        for badge_id, badge in BADGES.items():
            if badge["type"] == "streak" and streak >= badge["requirement"]:
                earned.append(badge_id)
            elif badge["type"] == "exceeded" and total_exceeded >= badge["requirement"]:
                earned.append(badge_id)

        assert "first_week" in earned
        assert "consistent_3" in earned
        assert "overachiever_5" not in earned

    def test_full_flow_with_miss(self):
        """달성 → 실패 → 달성 → streak 리셋."""
        s1, _ = calculate_achievement_status(400, 400)
        s2, _ = calculate_achievement_status(400, 100)
        s3, _ = calculate_achievement_status(400, 420)

        statuses = [s3, s2, s1]
        streak = 0
        for s in statuses:
            if s in ["achieved", "exceeded"]:
                streak += 1
            else:
                break
        assert streak == 1
