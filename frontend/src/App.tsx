import { useState, useEffect } from "react";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { AuthPage } from "@/pages/AuthPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { OnboardingPage } from "@/pages/OnboardingPage";
import { LandingPage } from "@/pages/LandingPage";
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
  fetchTodaysWorkout,
  checkApiConfigured,
  type FitnessData,
  type GeneratedWorkout,
  type WorkoutGenerateRequest,
  type WeeklyCalendarData,
} from "@/lib/api";

function Dashboard() {
  const { user, session, signOut } = useAuth();
  const [showSettings, setShowSettings] = useState(false);
  const [isApiConfigured, setIsApiConfigured] = useState<boolean | null>(null);
  const [fitness, setFitness] = useState<FitnessData | null>(null);
  const [workout, setWorkout] = useState<GeneratedWorkout | null>(null);
  const [weeklyCalendar, setWeeklyCalendar] = useState<WeeklyCalendarData | null>(null);
  const [isLoadingCalendar, setIsLoadingCalendar] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Check if API is configured
  useEffect(() => {
    if (session?.access_token) {
      checkApiConfigured(session.access_token)
        .then(setIsApiConfigured);
    }
  }, [session]);

  // Fetch data only if API is configured
  useEffect(() => {
    if (session?.access_token && isApiConfigured) {
      fetchFitness(session.access_token)
        .then(setFitness)
        .catch((e) => setError(`데이터 로딩 실패: ${e.message}`));

      setIsLoadingCalendar(true);
      fetchWeeklyCalendar(session.access_token)
        .then((data) => {
          setWeeklyCalendar(data);
          // Load today's workout AFTER calendar sync removes race condition
          return fetchTodaysWorkout(session.access_token);
        })
        .then((result) => {
          if (result && result.success && result.workout) {
            setWorkout(result.workout);
            setSuccess("📅 오늘의 워크아웃을 불러왔습니다.");
          }
        })
        .catch(console.error)
        .finally(() => setIsLoadingCalendar(false));
    }
  }, [session, isApiConfigured]);

  const handleOnboardingComplete = () => {
    setIsApiConfigured(true);
  };

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
          design_goal: workout.design_goal,
          workout_type: workout.workout_type,
          force: true,
          steps: workout.steps, // Pass structured steps to API
        },
        session.access_token
      );

      if (result.success) {
        setSuccess(`✅ 등록 완료! (Event ID: ${result.event_id})`);
        // Keep the workout visible!
        // setWorkout(null); 
      } else {
        setError(result.error || "등록 실패");
      }
    } catch (e) {
      setError(`등록 오류: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIsRegistering(false);
    }
  };

  const handleSelectDate = async (date: string) => {
    if (!session?.access_token) return;

    // Optional: Only allow clicking days with events (if desired)
    // For now, let's allow trying to load any day, maybe user wants to see if there is one

    setIsLoading(true); // Reuse loading state or add specific one? Reusing is fine for now
    setError(null);
    setSuccess(null);
    setWorkout(null); // Clear current view

    try {
      const result = await fetchTodaysWorkout(session.access_token, date);
      if (result.success && result.workout) {
        setWorkout(result.workout);
        setSuccess(`📅 ${date} 워크아웃을 불러왔습니다.`);
      } else {
        // No workout found for this date
        setError(`${date}에는 저장된 워크아웃이 없습니다.`);
      }
    } catch (e) {
      setError(`불러오기 실패: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Show loading while checking API config
  if (isApiConfigured === null) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-muted-foreground">설정 확인 중...</p>
        </div>
      </div>
    );
  }

  // Show onboarding if API not configured
  if (!isApiConfigured) {
    return (
      <OnboardingPage
        onComplete={handleOnboardingComplete}
        accessToken={session?.access_token || ""}
      />
    );
  }

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
            <a
              href="https://docs.google.com/forms/d/e/1FAIpQLSdgOIB6sEsQ-a-vlYpq4DnrnQ_wM7kjO7IILLFQaEe9gLcmhg/viewform"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-muted-foreground hover:text-primary transition-colors"
            >
              💬 피드백
            </a>
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
            <WeeklyCalendarCard
              calendar={weeklyCalendar}
              isLoading={isLoadingCalendar}
              onSelectDate={handleSelectDate}
            />

            {error && (
              <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
                ❌ {error}
              </div>
            )}

            {/* Show success message only if NOT viewing the workout preview (which now has its own indicator) 
                OR keep it for extra clarity? User said "removing button and showing Complete".
                Let's keep the banner for now, it's consistent with other actions. 
            */}
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
                isRegistered={!!success && success.includes("등록 완료")} // Pass registered state
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
  const [showLanding, setShowLanding] = useState(true);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground">로딩 중...</div>
      </div>
    );
  }

  if (!user) {
    if (showLanding) {
      return <LandingPage onGetStarted={() => setShowLanding(false)} />;
    }
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
