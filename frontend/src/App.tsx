import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { AuthPage } from "@/pages/AuthPage";
import { ResetPasswordPage } from "@/pages/ResetPasswordPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { OnboardingPage } from "@/pages/OnboardingPage";
import { LandingPage } from "@/pages/LandingPage";
import { AdminPage } from "@/pages/AdminPage";
import { FitnessCard } from "@/components/FitnessCard";
import { TodayWorkoutCard } from "@/components/TodayWorkoutCard";
import { WeeklyCalendarCard } from "@/components/WeeklyCalendarCard";
import { WeeklyPlanCard } from "@/components/WeeklyPlanCard";
import { FitnessCardSkeleton, WeeklyCalendarSkeleton, WeeklyPlanSkeleton, TodayWorkoutSkeleton } from '@/components/LoadingSkeletons';
import { UpdateAnnouncementModal } from "@/components/UpdateAnnouncementModal";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Button } from "@/components/ui/button";
import { useDashboard } from "@/hooks/useDashboard";

const API_BASE = import.meta.env.VITE_API_URL || '';

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
    currentWeekOffset, isLoadingCalendar, isLoadingPlan, isGeneratingPlan,
    isRegisteringPlanAll, isSyncingPlan, isLoading, isRegistering, error, success,
    handleGenerate, handleRegister, handleSelectDate, handleOnboardingComplete,
    handleGenerateWeeklyPlan, handleDeleteWeeklyPlan, handleRegisterWeeklyPlanAll,
    handleSyncWeeklyPlan, handleWeekNavigation,
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
    return <OnboardingPage onComplete={handleOnboardingComplete} accessToken={session?.access_token || ""} />;
  }

  if (showSettings) return <SettingsPage onBack={() => setShowSettings(false)} />;
  if (showAdmin) return <AdminPage onBack={() => setShowAdmin(false)} />;

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
            {isLoadingPlan ? <WeeklyPlanSkeleton /> : <WeeklyPlanCard plan={weeklyPlan} isLoading={isLoadingPlan} isGenerating={isGeneratingPlan} isRegisteringAll={isRegisteringPlanAll} isSyncing={isSyncingPlan} currentWeekOffset={currentWeekOffset} onGenerate={handleGenerateWeeklyPlan} onDelete={handleDeleteWeeklyPlan} onRegisterAll={handleRegisterWeeklyPlanAll} onSync={handleSyncWeeklyPlan} onWeekNavigation={handleWeekNavigation} />}
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
    return <ResetPasswordPage onComplete={() => { setShowResetPassword(false); window.location.hash = ''; }} />;
  }

  if (!user) {
    if (showLanding) return <LandingPage onGetStarted={() => setShowLanding(false)} />;
    return <AuthPage />;
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
