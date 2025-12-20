import { useState, useEffect } from "react";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { AuthPage } from "@/pages/AuthPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { FitnessCard } from "@/components/FitnessCard";
import { WorkoutForm } from "@/components/WorkoutForm";
import { WorkoutPreview } from "@/components/WorkoutPreview";
import { WeeklyCalendarCard } from "@/components/WeeklyCalendarCard";
import { Button } from "@/components/ui/button";
import {
  fetchFitness,
  generateWorkout,
  createWorkout,
  fetchWeeklyCalendar,
  type FitnessData,
  type GeneratedWorkout,
  type WorkoutGenerateRequest,
  type WeeklyCalendarData,
} from "@/lib/api";

function Dashboard() {
  const { user, session, signOut } = useAuth();
  const [showSettings, setShowSettings] = useState(false);
  const [fitness, setFitness] = useState<FitnessData | null>(null);
  const [workout, setWorkout] = useState<GeneratedWorkout | null>(null);
  const [weeklyCalendar, setWeeklyCalendar] = useState<WeeklyCalendarData | null>(null);
  const [isLoadingCalendar, setIsLoadingCalendar] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (session?.access_token) {
      fetchFitness(session.access_token)
        .then(setFitness)
        .catch((e) => setError(`데이터 로딩 실패: ${e.message}`));

      setIsLoadingCalendar(true);
      fetchWeeklyCalendar(session.access_token)
        .then(setWeeklyCalendar)
        .catch(console.error)
        .finally(() => setIsLoadingCalendar(false));
    }
  }, [session]);

  const handleGenerate = async (request: WorkoutGenerateRequest) => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    setWorkout(null);

    try {
      if (!session?.access_token) {
        setError("인증 토큰이 없습니다. 다시 로그인해주세요.");
        return;
      }
      const result = await generateWorkout(request, session.access_token);
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
      if (!session?.access_token) {
        setError("인증 토큰이 없습니다.");
        return;
      }
      const today = new Date().toISOString().split("T")[0];
      const result = await createWorkout(
        {
          target_date: today,
          name: workout.name,
          workout_text: workout.workout_text,
          duration_minutes: workout.estimated_duration_minutes,
          estimated_tss: workout.estimated_tss,
          force: true,
        },
        session.access_token
      );

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

  if (showSettings) {
    return <SettingsPage onBack={() => setShowSettings(false)} />;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">🚴 AI Cycling Coach</h1>
            <p className="text-muted-foreground text-sm">AI 기반 워크아웃 추천</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">{user?.email}</span>
            <Button variant="outline" size="sm" onClick={() => setShowSettings(true)}>
              ⚙️ 설정
            </Button>
            <Button variant="ghost" size="sm" onClick={signOut}>
              로그아웃
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {fitness && (
              <FitnessCard training={fitness.training} wellness={fitness.wellness} profile={fitness.profile} />
            )}
            <WorkoutForm onGenerate={handleGenerate} isLoading={isLoading} />
          </div>

          {/* Right Column */}
          <div className="space-y-4">
            <WeeklyCalendarCard calendar={weeklyCalendar} isLoading={isLoadingCalendar} />

            {error && (
              <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
                ❌ {error}
              </div>
            )}

            {success && (
              <div className="bg-green-500/10 text-green-600 p-4 rounded-lg">
                {success}
              </div>
            )}

            {workout && (
              <WorkoutPreview
                workout={workout}
                onRegister={handleRegister}
                isRegistering={isRegistering}
                ftp={fitness?.profile?.ftp ?? 250}
              />
            )}

            {!workout && !error && !success && (
              <div className="border-2 border-dashed rounded-lg p-8 text-center text-muted-foreground">
                <p className="text-lg">🎯 워크아웃을 생성해보세요!</p>
                <p className="text-sm mt-2">
                  왼쪽 폼에서 옵션을 선택 후 생성 버튼을 클릭하세요
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function AppContent() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground">로딩 중...</div>
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return <Dashboard />;
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
