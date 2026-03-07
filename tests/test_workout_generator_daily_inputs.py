from src.config import UserProfile
from src.services.data_processor import TrainingMetrics, WellnessMetrics
from src.services.fatigue_detector import FatigueSignal
from src.services.workout_generator import WorkoutGenerator


class DummyLLM:
    def generate(self, system_prompt, user_prompt):
        raise AssertionError("LLM.generate should be mocked in these tests")


def make_generator(**profile_overrides):
    profile_data = {
        "ftp": 250,
        "max_hr": 190,
        "lthr": 170,
        "training_goal": "Build FTP",
        "training_style": "auto",
        "training_focus": "maintain",
    }
    profile_data.update(profile_overrides)
    profile = UserProfile(**profile_data)
    return WorkoutGenerator(DummyLLM(), profile, max_duration_minutes=90)


def sample_training_metrics(tsb=2.0):
    return TrainingMetrics(ctl=70.0, atl=68.0, tsb=tsb)


def sample_wellness_metrics():
    return WellnessMetrics(
        hrv=52.0,
        hrv_sdnn=None,
        rhr=48.0,
        sleep_hours=7.5,
        sleep_score=None,
        sleep_quality=None,
        readiness="Ready",
        weight=None,
        body_fat=None,
        vo2max=None,
        soreness=None,
        fatigue=None,
        stress=None,
        mood=None,
        motivation=None,
        spo2=None,
        systolic=None,
        diastolic=None,
        respiration=None,
        readiness_score=None,
    )


def test_generate_enhanced_passes_notes_to_profile_and_module_selection(monkeypatch):
    generator = make_generator()
    captured = {}

    def fake_profile_selector(self, **kwargs):
        captured["profile_notes"] = kwargs["user_notes"]
        return {}

    def fake_module_selector(self, **kwargs):
        captured["module_notes"] = kwargs["user_notes"]
        return {
            "workout_name": "Steady Endurance",
            "design_goal": "Aerobic support",
            "selected_modules": ["ramp_standard", "endurance_20min", "flush_and_fade"],
        }

    monkeypatch.setattr(WorkoutGenerator, "_select_profile_with_llm", fake_profile_selector)
    monkeypatch.setattr(WorkoutGenerator, "_select_modules_with_llm", fake_module_selector)

    generator.generate_enhanced(
        training_metrics=sample_training_metrics(),
        wellness_metrics=sample_wellness_metrics(),
        notes="  hold tempo on climbs  ",
        duration=45,
    )

    assert captured["profile_notes"] == "hold tempo on climbs"
    assert captured["module_notes"] == "hold tempo on climbs"


def test_generate_enhanced_uses_saved_training_style_when_request_is_auto(monkeypatch):
    generator = make_generator(training_style="threshold", training_focus="recovery")
    captured = {}

    def fake_profile_selector(self, **kwargs):
        captured["training_style"] = kwargs["training_style"]
        return {}

    def fake_module_selector(self, **kwargs):
        return {
            "workout_name": "Threshold Touch",
            "design_goal": "Sustain FTP",
            "selected_modules": ["ramp_standard", "threshold_2x8", "flush_and_fade"],
        }

    monkeypatch.setattr(WorkoutGenerator, "_select_profile_with_llm", fake_profile_selector)
    monkeypatch.setattr(WorkoutGenerator, "_select_modules_with_llm", fake_module_selector)

    generator.generate_enhanced(
        training_metrics=sample_training_metrics(tsb=12.0),
        wellness_metrics=sample_wellness_metrics(),
        style="auto",
        duration=40,
    )

    assert captured["training_style"] == "threshold"


def test_generate_enhanced_resolves_auto_style_from_training_focus(monkeypatch):
    generator = make_generator(training_style="auto", training_focus="recovery")
    captured = {}

    def fake_profile_selector(self, **kwargs):
        captured["training_style"] = kwargs["training_style"]
        captured["training_focus"] = kwargs["training_focus"]
        return {}

    def fake_module_selector(self, **kwargs):
        return {
            "workout_name": "Recovery Spin",
            "design_goal": "Absorb load",
            "selected_modules": ["ramp_standard", "endurance_20min", "flush_and_fade"],
        }

    monkeypatch.setattr(WorkoutGenerator, "_select_profile_with_llm", fake_profile_selector)
    monkeypatch.setattr(WorkoutGenerator, "_select_modules_with_llm", fake_module_selector)

    generator.generate_enhanced(
        training_metrics=sample_training_metrics(tsb=8.0),
        wellness_metrics=sample_wellness_metrics(),
        style="auto",
        duration=35,
    )

    assert captured["training_style"] == "endurance"
    assert captured["training_focus"] == "recovery"


def test_generate_enhanced_keeps_explicit_style_and_intensity_over_focus(monkeypatch):
    generator = make_generator(training_style="auto", training_focus="recovery")
    captured = {}

    def fake_profile_selector(self, **kwargs):
        captured["training_style"] = kwargs["training_style"]
        captured["intensity"] = kwargs["intensity"]
        return {}

    def fake_module_selector(self, **kwargs):
        return {
            "workout_name": "Hard Threshold",
            "design_goal": "Raise FTP",
            "selected_modules": ["ramp_standard", "threshold_2x8", "flush_and_fade"],
        }

    monkeypatch.setattr(WorkoutGenerator, "_select_profile_with_llm", fake_profile_selector)
    monkeypatch.setattr(WorkoutGenerator, "_select_modules_with_llm", fake_module_selector)

    generator.generate_enhanced(
        training_metrics=sample_training_metrics(tsb=6.0),
        wellness_metrics=sample_wellness_metrics(),
        style="threshold",
        intensity="hard",
        duration=40,
    )

    assert captured["training_style"] == "threshold"
    assert captured["intensity"] == "hard"


def test_generate_enhanced_recovery_focus_downgrades_auto_intensity(monkeypatch):
    generator = make_generator(training_style="auto", training_focus="recovery")
    captured = {}

    def fake_profile_selector(self, **kwargs):
        captured["intensity"] = kwargs["intensity"]
        return {}

    def fake_module_selector(self, **kwargs):
        return {
            "workout_name": "Recovery Spin",
            "design_goal": "Absorb fatigue",
            "selected_modules": ["ramp_standard", "endurance_20min", "flush_and_fade"],
        }

    monkeypatch.setattr(WorkoutGenerator, "_select_profile_with_llm", fake_profile_selector)
    monkeypatch.setattr(WorkoutGenerator, "_select_modules_with_llm", fake_module_selector)

    generator.generate_enhanced(
        training_metrics=sample_training_metrics(tsb=12.0),
        wellness_metrics=sample_wellness_metrics(),
        intensity="auto",
        duration=35,
    )

    assert captured["intensity"] == "easy"


def test_generate_enhanced_fatigue_override_still_forces_easy(monkeypatch):
    generator = make_generator(training_style="auto", training_focus="build")
    captured = {}

    def fake_profile_selector(self, **kwargs):
        captured["intensity"] = kwargs["intensity"]
        return {}

    def fake_module_selector(self, **kwargs):
        return {
            "workout_name": "Reset Spin",
            "design_goal": "Recover",
            "selected_modules": ["ramp_standard", "endurance_20min", "flush_and_fade"],
        }

    monkeypatch.setattr(WorkoutGenerator, "_select_profile_with_llm", fake_profile_selector)
    monkeypatch.setattr(WorkoutGenerator, "_select_modules_with_llm", fake_module_selector)

    generator.generate_enhanced(
        training_metrics=sample_training_metrics(tsb=15.0),
        wellness_metrics=sample_wellness_metrics(),
        intensity="hard",
        fatigue_override=FatigueSignal(is_fatigued=True, hrv_drop_pct=0.25),
        duration=35,
    )

    assert captured["intensity"] == "easy"


def test_generate_enhanced_retries_recent_profile_exclusions_then_falls_back(monkeypatch):
    from api.services import workout_profile_service

    generator = make_generator()
    candidate_calls = []

    def fake_candidates(**kwargs):
        candidate_calls.append(kwargs["exclude_profile_ids"])
        return "(No profiles available)", []

    def fake_module_selector(self, **kwargs):
        return {
            "workout_name": "Fallback Endurance",
            "design_goal": "Keep moving",
            "selected_modules": ["ramp_standard", "endurance_20min", "flush_and_fade"],
        }

    monkeypatch.setattr(workout_profile_service, "get_profile_candidates_for_llm", fake_candidates)
    monkeypatch.setattr(WorkoutGenerator, "_select_modules_with_llm", fake_module_selector)

    workout = generator.generate_enhanced(
        training_metrics=sample_training_metrics(),
        wellness_metrics=sample_wellness_metrics(),
        duration=40,
        recent_profile_ids=[26, 65],
    )

    assert candidate_calls == [[26, 65], None]
    assert workout.source == "module_assembly"
