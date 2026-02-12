import { useState, useEffect, useCallback, lazy, Suspense } from "react";
import { useTranslation } from "react-i18next";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { FitnessCard } from "@/components/FitnessCard";
import { TodayWorkoutCard } from "@/components/TodayWorkoutCard";
import { WeeklyCalendarCard } from "@/components/WeeklyCalendarCard";
import { WeeklyPlanCard } from "@/components/WeeklyPlanCard";
import { AchievementBadges } from "@/components/AchievementBadges";
import { FitnessCardSkeleton, WeeklyCalendarSkeleton, WeeklyPlanSkeleton, TodayWorkoutSkeleton } from '@/components/LoadingSkeletons';
import { UpdateAnnouncementModal } from "@/components/UpdateAnnouncementModal";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Button } from "@/components/ui/button";
import { useDashboard } from "@/hooks/useDashboard";

// Lazy load pages for code splitting
const AuthPage = lazy(() => import("@/pages/AuthPage").then(m => ({ default: m.AuthPage })));
const ResetPasswordPage = lazy(() => import("@/pages/ResetPasswordPage").then(m => ({ default: m.ResetPasswordPage })));
const SettingsPage = lazy(() => import("@/pages/SettingsPage").then(m => ({ default: m.SettingsPage })));
const OnboardingPage = lazy(() => import("@/pages/OnboardingPage").then(m => ({ default: m.OnboardingPage })));
const LandingPage = lazy(() => import("@/pages/LandingPage").then(m => ({ default: m.LandingPage })));
const AdminPage = lazy(() => import("@/pages/AdminPage").then(m => ({ default: m.AdminPage })));

const API_BASE = import.meta.env.VITE_API_URL || '';

// Loading fallback component
function PageLoader() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-muted-foreground">{t('common.loading')}</p>
      </div>
    </div>
  );
}

function Dashboard() {
  const { t } = useTranslation();
  const { user, session, signOut } = useAuth();
  const [showSettings, setShowSettings] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  const checkAdminStatus = useCallback(async () => {
    if (!session?.access_token) return;
    try {
      const response = await fetch(`${API_BASE}/api/admin/check`, {
        headers: { 'Authorization': `Bearer ${session.access_token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setIsAdmin(data.is_admin || false);
      }
    } catch (error) {
      console.error('Failed to check admin status:', error);
    }
  }, [session?.access_token]);

  useEffect(() => { checkAdminStatus(); }, [checkAdminStatus]);

  const {
    isApiConfigured, fitness, workout, weeklyCalendar, weeklyPlan,
    achievements, isLoadingAchievements,
    currentWeekOffset, isLoadingCalendar, isLoadingPlan, isGeneratingPlan,
    isRegisteringPlanAll, isSyncingPlan, isLoading, isRegistering, error, success,
    handleGenerate, handleRegister, handleSelectDate, handleOnboardingComplete,
    handleGenerateWeeklyPlan, handleDeleteWeeklyPlan, handleRegisterWeeklyPlanAll,
    handleSyncWeeklyPlan, handleWeekNavigation, tssProgress,
  } = useDashboard();

  if (isApiConfigured === null) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-muted-foreground">{t('common.checkingSettings')}</p>
        </div>
      </div>
    );
  }

  if (!isApiConfigured) {
    return (
      <Suspense fallback={<PageLoader />}>
        <OnboardingPage onComplete={handleOnboardingComplete} accessToken={session?.access_token || ""} />
      </Suspense>
    );
  }

  if (showSettings) {
    return (
      <Suspense fallback={<PageLoader />}>
        <SettingsPage onBack={() => setShowSettings(false)} />
      </Suspense>
    );
  }

  if (showAdmin) {
    return (
      <Suspense fallback={<PageLoader />}>
        <AdminPage onBack={() => setShowAdmin(false)} />
      </Suspense>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4">
          {/* Top row: Title + User actions */}
          <div className="flex justify-between items-center">
            <h1 className="text-xl sm:text-2xl font-bold">🚴 AI Cycling Coach</h1>
            <div className="flex items-center gap-1 sm:gap-2">
              <LanguageSwitcher />
              <Button variant="ghost" onClick={signOut} className="h-11 sm:h-9 text-xs sm:text-sm transition-all active:scale-95">
                {t('common.logout')}
              </Button>
            </div>
          </div>
          {/* Bottom row: Navigation buttons */}
          <div className="flex items-center justify-between mt-2">
            <p className="text-muted-foreground text-xs sm:text-sm truncate max-w-[180px] sm:max-w-none">{user?.email}</p>
            <div className="flex items-center gap-1 sm:gap-2">
              <a href="https://docs.google.com/forms/d/e/1FAIpQLSdgOIB6sEsQ-a-vlYpq4DnrnQ_wM7kjO7IILLFQaEe9gLcmhg/viewform" target="_blank" rel="noopener noreferrer" className="text-xs text-muted-foreground hover:text-primary transition-colors hidden sm:inline">
                {t('dashboard.feedback')}
              </a>
              {isAdmin && (
                <Button variant="outline" onClick={() => setShowAdmin(true)} className="h-11 sm:h-9 text-xs sm:text-sm px-2 sm:px-3 transition-all active:scale-95">{t('dashboard.admin')}</Button>
              )}
              <Button variant="outline" onClick={() => setShowSettings(true)} className="h-11 sm:h-9 text-xs sm:text-sm px-2 sm:px-3 transition-all active:scale-95">{t('dashboard.settings')}</Button>
            </div>
          </div>
        </div>
      </header>
      <main className="container mx-auto px-3 sm:px-4 py-4 sm:py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          <div className="space-y-6">
            {fitness ? <FitnessCard training={fitness.training} wellness={fitness.wellness} profile={fitness.profile} /> : <FitnessCardSkeleton />}
            {isLoadingCalendar ? <WeeklyCalendarSkeleton /> : <WeeklyCalendarCard calendar={weeklyCalendar} isLoading={false} onSelectDate={handleSelectDate} />}
            {(!workout && isLoading) ? <TodayWorkoutSkeleton /> : <TodayWorkoutCard workout={workout} onGenerate={handleGenerate} onRegister={handleRegister} isLoading={isLoading} isRegistering={isRegistering} isRegistered={!!success && (success.includes(t('common.registered')) || success.includes("Registered"))} ftp={fitness?.profile?.ftp ?? 250} error={error} success={success} />}
          </div>
          <div className="space-y-4">
            {isLoadingPlan ? <WeeklyPlanSkeleton /> : <WeeklyPlanCard plan={weeklyPlan} isLoading={isLoadingPlan} isGenerating={isGeneratingPlan} isRegisteringAll={isRegisteringPlanAll} isSyncing={isSyncingPlan} currentWeekOffset={currentWeekOffset} tssProgress={tssProgress} onGenerate={handleGenerateWeeklyPlan} onDelete={handleDeleteWeeklyPlan} onRegisterAll={handleRegisterWeeklyPlanAll} onSync={handleSyncWeeklyPlan} onWeekNavigation={handleWeekNavigation} />}
            {weeklyPlan && <AchievementBadges data={achievements} isLoading={isLoadingAchievements} />}
          </div>
        </div>
      </main>
    </div>
  );
}

function AppContent() {
  const { t } = useTranslation();
  const { user, loading } = useAuth();
  const [showLanding, setShowLanding] = useState(true);
  const [showResetPassword, setShowResetPassword] = useState(false);

  useEffect(() => {
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    const type = hashParams.get('type');
    if (type === 'recovery') setShowResetPassword(true);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground">{t('common.loading')}</div>
      </div>
    );
  }

  if (showResetPassword) {
    return (
      <Suspense fallback={<PageLoader />}>
        <ResetPasswordPage onComplete={() => { setShowResetPassword(false); window.location.hash = ''; }} />
      </Suspense>
    );
  }

  if (!user) {
    if (showLanding) {
      return (
        <Suspense fallback={<PageLoader />}>
          <LandingPage onGetStarted={() => setShowLanding(false)} />
        </Suspense>
      );
    }
    return (
      <Suspense fallback={<PageLoader />}>
        <AuthPage />
      </Suspense>
    );
  }

  return <Dashboard />;
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
      <UpdateAnnouncementModal />
    </AuthProvider>
  );
}

export default App;
