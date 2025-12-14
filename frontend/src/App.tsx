import { useState, useEffect } from "react";
import { FitnessCard } from "@/components/FitnessCard";
import { WorkoutForm } from "@/components/WorkoutForm";
import { WorkoutPreview } from "@/components/WorkoutPreview";
import {
  fetchFitness,
  generateWorkout,
  createWorkout,
  type FitnessData,
  type GeneratedWorkout,
  type WorkoutGenerateRequest
} from "@/lib/api";

function App() {
  const [fitness, setFitness] = useState<FitnessData | null>(null);
  const [workout, setWorkout] = useState<GeneratedWorkout | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Fetch fitness data on mount
  useEffect(() => {
    fetchFitness()
      .then(setFitness)
      .catch((e) => setError(`데이터 로딩 실패: ${e.message}`));
  }, []);

  const handleGenerate = async (request: WorkoutGenerateRequest) => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    setWorkout(null);

    try {
      const result = await generateWorkout(request);
      if (result.success && result.workout) {
        setWorkout(result.workout);
      } else {
        setError(result.error || "워크아웃 생성 실패");
      }
    } catch (e) {
      setError(`생성 오류: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!workout) return;

    setIsRegistering(true);
    setError(null);

    try {
      const today = new Date().toISOString().split("T")[0];
      const result = await createWorkout({
        target_date: today,
        name: workout.name,
        workout_text: workout.workout_text,
        duration_minutes: workout.estimated_duration_minutes,
        estimated_tss: workout.estimated_tss,
        force: true,
      });

      if (result.success) {
        setSuccess(`✅ 등록 완료! (Event ID: ${result.event_id})`);
        setWorkout(null);
      } else {
        setError(result.error || "등록 실패");
      }
    } catch (e) {
      setError(`등록 오류: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIsRegistering(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">🚴 AI Cycling Coach</h1>
          <p className="text-muted-foreground text-sm">AI 기반 워크아웃 추천</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Fitness Card */}
            {fitness && <FitnessCard training={fitness.training} wellness={fitness.wellness} />}

            {/* Workout Form */}
            <WorkoutForm onGenerate={handleGenerate} isLoading={isLoading} />
          </div>

          {/* Right Column */}
          <div className="space-y-4">
            {/* Error Message */}
            {error && (
              <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
                ❌ {error}
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="bg-green-500/10 text-green-600 p-4 rounded-lg">
                {success}
              </div>
            )}

            {/* Workout Preview */}
            {workout && (
              <WorkoutPreview
                workout={workout}
                onRegister={handleRegister}
                isRegistering={isRegistering}
              />
            )}

            {/* Empty State */}
            {!workout && !error && !success && (
              <div className="border-2 border-dashed rounded-lg p-8 text-center text-muted-foreground">
                <p className="text-lg">🎯 워크아웃을 생성해보세요!</p>
                <p className="text-sm mt-2">왼쪽 폼에서 옵션을 선택 후 생성 버튼을 클릭하세요</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
