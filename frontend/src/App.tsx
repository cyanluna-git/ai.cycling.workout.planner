import { useState, useEffect, useCallback } from "react";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { AuthPage } from "@/pages/AuthPage";
import { ResetPasswordPage } from "@/pages/ResetPasswordPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { OnboardingPage } from "@/pages/OnboardingPage";
import { LandingPage } from "@/pages/LandingPage";
import { AdminPage } from "@/pages/AdminPage";
import { FitnessCard } from "@/components/FitnessCard";
import { WorkoutForm } from "@/components/WorkoutForm";
import { WorkoutPreview } from "@/components/WorkoutPreview";
import { WeeklyCalendarCard } from "@/components/WeeklyCalendarCard";
import { WeeklyPlanCard } from "@/components/WeeklyPlanCard";
import { Button } from "@/components/ui/button";
import { useDashboard } from "@/hooks/useDashboard";

const API_BASE = import.meta.env.VITE_API_URL || '';

function Dashboard() {
  const { user, session, signOut } = useAuth();
  const [showSettings, setShowSettings] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  // Check admin status on mount
  const checkAdminStatus = useCallback(async () => {
    if (!session?.access_token) return;

    try {
      const response = await fetch(`${API_BASE}/api/admin/check`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setIsAdmin(data.is_admin || false);
      }
    } catch (error) {
      console.error('Failed to check admin status:', error);
    }
  }, [session?.access_token]);

  useEffect(() => {
    checkAdminStatus();
  }, [checkAdminStatus]);

  // Use custom hook for all dashboard state and logic
  const {
    isApiConfigured,
    fitness,
    workout,
    weeklyCalendar,
    weeklyPlan,
    currentWeekOffset,
    isLoadingCalendar,
    isLoadingPlan,
    isGeneratingPlan,
    isLoading,
    isRegistering,
    error,
    success,
    handleGenerate,
    handleRegister,
    handleSelectDate,
    handleOnboardingComplete,
    handleGenerateWeeklyPlan,
    handleDeleteWeeklyPlan,
    handleWeekNavigation,
  } = useDashboard();

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

  if (showAdmin) {
    return <AdminPage onBack={() => setShowAdmin(false)} />;
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
            {isAdmin && (
              <Button variant="outline" size="sm" onClick={() => setShowAdmin(true)}>
                🔧 관리자
              </Button>
            )}
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {fitness && (
              <FitnessCard training={fitness.training} wellness={fitness.wellness} profile={fitness.profile} />
            )}
            <WorkoutForm onGenerate={handleGenerate} isLoading={isLoading} />

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
                isRegistered={!!success && success.includes("등록 완료")}
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

          {/* Right Column - Weekly Plan */}
          <div className="space-y-4">
            <WeeklyPlanCard
              plan={weeklyPlan}
              isLoading={isLoadingPlan}
              isGenerating={isGeneratingPlan}
              currentWeekOffset={currentWeekOffset}
              onGenerate={handleGenerateWeeklyPlan}
              onDelete={handleDeleteWeeklyPlan}
              onWeekNavigation={handleWeekNavigation}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

function AppContent() {
  const { user, loading } = useAuth();
  const [showLanding, setShowLanding] = useState(true);
  const [showResetPassword, setShowResetPassword] = useState(false);

  // Check URL for password reset flow (Supabase redirects with #type=recovery)
  useEffect(() => {
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    const type = hashParams.get('type');
    if (type === 'recovery') {
      setShowResetPassword(true);
    }
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground">로딩 중...</div>
      </div>
    );
  }

  // Show reset password page if in recovery mode
  if (showResetPassword) {
    return <ResetPasswordPage onComplete={() => {
      setShowResetPassword(false);
      window.location.hash = '';
    }} />;
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
