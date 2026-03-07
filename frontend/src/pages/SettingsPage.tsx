import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { CalendarDays, Bike, Moon, PartyPopper, Watch, Zap, Activity, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAuth } from '@/contexts/AuthContext'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/queryClient'
import { removeCachedData } from '@/lib/queryCache'
import { disconnectOAuth, fetchOAuthUrl, fetchSettingsBootstrap, type IntervalsConnectionStatus, type UserSettingsData } from '@/lib/api'

const API_BASE = import.meta.env.VITE_API_URL || ''

const DEFAULT_SETTINGS: UserSettingsData = {
    ftp: 200,
    max_hr: 190,
    lthr: 170,
    training_goal: '',
    exclude_barcode_workouts: false,
    training_style: 'auto',
    preferred_duration: 60,
    training_focus: 'maintain',
    weekly_tss_target: null,
    weekly_availability: {
        "0": "available",
        "1": "available",
        "2": "available",
        "3": "available",
        "4": "available",
        "5": "available",
        "6": "available",
    },
}

export function SettingsPage({ onBack }: { onBack: () => void }) {
    const { t } = useTranslation();
    const { session, signOut } = useAuth()
    const queryClient = useQueryClient()
    const [settings, setSettings] = useState<UserSettingsData>(DEFAULT_SETTINGS)
    const [isOAuthLoading, setIsOAuthLoading] = useState(false)
    const [isDisconnecting, setIsDisconnecting] = useState(false)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState<string | null>(null)

    const { data: settingsBootstrap, isLoading: isLoadingSettingsBootstrap } = useQuery({
        queryKey: queryKeys.settingsBootstrap(),
        queryFn: () => fetchSettingsBootstrap(session?.access_token || ''),
        enabled: !!session?.access_token,
        staleTime: 5 * 60 * 1000,
        refetchOnWindowFocus: false,
    })

    useEffect(() => {
        if (!settingsBootstrap?.settings) return
        setSettings({
            ...DEFAULT_SETTINGS,
            ...settingsBootstrap.settings,
            weekly_availability: settingsBootstrap.settings.weekly_availability || DEFAULT_SETTINGS.weekly_availability,
        })
    }, [settingsBootstrap])

    const connectionStatus = settingsBootstrap?.intervals_connection ?? null
    const isConnectionLoading = isLoadingSettingsBootstrap && !connectionStatus
    const handleOAuthConnect = async () => {
        if (!session?.access_token) return;
        setIsOAuthLoading(true);
        try {
            const data = await fetchOAuthUrl(session.access_token);
            localStorage.setItem('intervals_oauth_state', data.state);
            window.location.href = data.authorize_url;
        } catch {
            setMessage(t('oauth.error', { message: 'Failed to start OAuth' }));
            setIsOAuthLoading(false);
        }
    };

    const handleDisconnect = async () => {
        if (!session?.access_token) return;
        setIsDisconnecting(true);
        try {
            await disconnectOAuth(session.access_token);
            queryClient.setQueryData(queryKeys.settingsBootstrap(), (current: {
                settings: UserSettingsData;
                api_keys_configured: boolean;
                intervals_connection: IntervalsConnectionStatus;
            } | undefined) => {
                if (!current) return current;
                return {
                    ...current,
                    api_keys_configured: false,
                    intervals_connection: {
                        connected: false,
                        method: 'none',
                        athlete_id: null,
                    },
                };
            });
            queryClient.setQueryData(queryKeys.apiConfigured(), false);
            setMessage(t('oauth.disconnected'));
        } catch {
            setMessage(t('common.error'));
        } finally { setIsDisconnecting(false); }
    };

    const saveSettings = async () => {
        setSaving(true); setMessage(null);
        try {
            const res = await fetch(`${API_BASE}/api/settings`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session?.access_token}` },
                body: JSON.stringify(settings),
            });
            if (res.ok) {
                setMessage(t('settings.settingsSaved'));
                removeCachedData('todayPlan');
                queryClient.invalidateQueries({ queryKey: queryKeys.todayPlan() });
                queryClient.invalidateQueries({ queryKey: queryKeys.weeklyCalendar() });
            }
        } catch { setMessage(t('common.saveFailed')); } finally { setSaving(false); }
    }

    // Weekly Availability handlers
    const dayKeys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];

    const handleAvailabilityChange = (dayIndex: number, value: string) => {
        setSettings(prev => ({
            ...prev,
            weekly_availability: {
                ...prev.weekly_availability,
                [dayIndex.toString()]: value as "available" | "unavailable" | "rest"
            }
        }));
    };

    const validateAvailability = (availability: Record<string, string>) => {
        const hasAvailable = Object.values(availability).some(v => v === "available");
        if (!hasAvailable) {
            setMessage(t("settings.weeklyAvailability.validation.atLeastOne"));
            return false;
        }
        return true;
    };

    const handleSaveAvailability = async () => {
        if (!validateAvailability(settings.weekly_availability || {})) return;
        
        setSaving(true); setMessage(null);
        try {
            const res = await fetch(`${API_BASE}/api/settings`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session?.access_token}` },
                body: JSON.stringify(settings),
            });
            if (res.ok) {
                setMessage(t("settings.weeklyAvailability.saveSuccess"));
                removeCachedData('todayPlan');
                queryClient.invalidateQueries({ queryKey: queryKeys.todayPlan() });
            } else {
                setMessage(t("settings.weeklyAvailability.saveError"));
            }
        } catch {
            setMessage(t("settings.weeklyAvailability.saveError"));
        } finally { setSaving(false); }
    };

    return (
        <div className="min-h-screen bg-background p-4">
            <div className="container mx-auto max-w-2xl space-y-6">
                <div className="flex justify-between items-center">
                    <Button variant="ghost" onClick={onBack}>{t('common.back')}</Button>
                    <Button variant="outline" onClick={signOut}>{t('common.logout')}</Button>
                </div>
                {message && <div className="p-3 rounded bg-muted text-center">{message}</div>}
                <Card>
                    <CardHeader><CardTitle>{t('settings.trainingTitle')}</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-sm text-muted-foreground">{t('settings.trainingAutoSync')}</p>
                        <div className="space-y-2">
                            <Label>{t('settings.weeklyGoal')}</Label>
                            <div className="grid grid-cols-3 gap-2">
                                <button type="button" onClick={() => setSettings({ ...settings, training_focus: 'recovery' })} className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${settings.training_focus === 'recovery' ? 'bg-green-500 text-white' : 'bg-muted hover:bg-muted/80'}`}>{t('settings.recovery')}</button>
                                <button type="button" onClick={() => setSettings({ ...settings, training_focus: 'maintain' })} className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${settings.training_focus === 'maintain' ? 'bg-blue-500 text-white' : 'bg-muted hover:bg-muted/80'}`}>{t('settings.maintain')}</button>
                                <button type="button" onClick={() => setSettings({ ...settings, training_focus: 'build' })} className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${settings.training_focus === 'build' ? 'bg-orange-500 text-white' : 'bg-muted hover:bg-muted/80'}`}>{t('settings.build')}</button>
                            </div>
                            <p className="text-xs text-muted-foreground">{t('settings.focusDescription')}</p>
                        </div>
                        <div className="space-y-2">
                            <Label>{t('settings.weeklyTssTarget')}</Label>
                            <div className="flex items-center gap-4">
                                <div className="flex-1">
                                    <Slider
                                        min={200}
                                        max={800}
                                        step={25}
                                        value={[settings.weekly_tss_target || 0]}
                                        onValueChange={([v]) => setSettings({ ...settings, weekly_tss_target: v === 0 ? null : v })}
                                    />
                                </div>
                                <span className="text-sm font-medium w-24 text-right">
                                    {settings.weekly_tss_target ? `${settings.weekly_tss_target} TSS` : t('settings.tssAuto')}
                                </span>
                            </div>
                            <p className="text-xs text-muted-foreground">{t('settings.weeklyTssHint')}</p>
                            {settings.weekly_tss_target && (
                                <button type="button" onClick={() => setSettings({ ...settings, weekly_tss_target: null })} className="text-xs text-primary hover:underline">{t('settings.tssReset')}</button>
                            )}
                        </div>
                        <div className="space-y-2">
                            <Label>{t('settings.trainingStyle')}</Label>
                            <select value={settings.training_style || 'auto'} onChange={(e) => setSettings({ ...settings, training_style: e.target.value })} className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
                                <option value="auto">{t('settings.styleAuto')}</option>
                                <option value="polarized">{t('settings.stylePolarized')}</option>
                                <option value="norwegian">{t('settings.styleNorwegian')}</option>
                                <option value="sweetspot">{t('settings.styleSweetspot')}</option>
                                <option value="threshold">{t('settings.styleThreshold')}</option>
                                <option value="endurance">{t('settings.styleEndurance')}</option>
                            </select>
                        </div>
                        <div className="flex items-center space-x-2">
                            <input type="checkbox" id="exclude_barcode" checked={settings.exclude_barcode_workouts ?? false} onChange={(e) => setSettings({ ...settings, exclude_barcode_workouts: e.target.checked })} className="h-4 w-4 rounded border-gray-300" />
                            <div>
                                <label htmlFor="exclude_barcode" className="text-sm font-medium cursor-pointer">{t('settings.excludeBarcode')}</label>
                                <p className="text-xs text-muted-foreground">{t('settings.excludeBarcodeHint')}</p>
                            </div>
                        </div>
                        <Button onClick={saveSettings} disabled={saving}>{saving ? t('common.saving') : t('settings.saveSettings')}</Button>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader><CardTitle className="flex items-center gap-2"><CalendarDays className="h-5 w-5" /> {t('settings.weeklyAvailability.title')}</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-sm text-muted-foreground">{t('settings.weeklyAvailability.description')}</p>
                        <div className="space-y-3">
                            {dayKeys.map((dayKey, index) => (
                                <div key={index} className="flex items-center gap-4">
                                    <span className="w-24 text-sm font-medium">
                                        {t(`settings.weeklyAvailability.days.${dayKey}`)}
                                    </span>
                                    <Select
                                        value={settings.weekly_availability?.[index.toString()] || "available"}
                                        onValueChange={(value) => handleAvailabilityChange(index, value)}
                                    >
                                        <SelectTrigger className="w-56">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="available">
                                                <span className="inline-flex items-center gap-1.5"><Bike className="h-3.5 w-3.5" /> {t("settings.weeklyAvailability.available")}</span>
                                            </SelectItem>
                                            <SelectItem value="rest">
                                                <span className="inline-flex items-center gap-1.5"><Moon className="h-3.5 w-3.5" /> {t("settings.weeklyAvailability.rest")}</span>
                                            </SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            ))}
                        </div>
                        <Button onClick={handleSaveAvailability} disabled={saving} className="mt-4">
                            {saving ? t('common.saving') : t('common.confirm')}
                        </Button>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader>
                        <CardTitle>{t('settings.apiTitle')}</CardTitle>
                        {isConnectionLoading ? (
                            <div className="text-sm text-muted-foreground">{t('common.loading')}</div>
                        ) : connectionStatus && (
                            <div className="text-sm text-muted-foreground">
                                {t('settings.apiStatus')}{' '}
                                {connectionStatus.connected ? t('settings.apiConnected') : t('settings.apiNotConnected')}
                            </div>
                        )}
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {isConnectionLoading && (
                            <div className="flex items-center justify-center py-4 text-sm text-muted-foreground">
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                {t('common.loading')}
                            </div>
                        )}
                        {/* Connected (any method) */}
                        {!isConnectionLoading && connectionStatus?.connected && (
                            <div className="text-center py-4">
                                <div className="mb-2 flex justify-center"><PartyPopper className="h-10 w-10 text-primary" /></div>
                                <p className="text-sm text-muted-foreground">{t('settings.apiConnectedMessage')}</p>
                                <p className="text-xs text-muted-foreground mt-1">
                                    {t('oauth.connectedVia', { method: 'OAuth' })} &middot; {connectionStatus.athlete_id}
                                </p>
                                <span className="inline-block mt-2 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
                                    OAuth
                                </span>
                                <div className="mt-4">
                                    <Button variant="outline" size="sm" onClick={handleDisconnect} disabled={isDisconnecting}>
                                        {isDisconnecting ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
                                        {t('oauth.disconnect')}
                                    </Button>
                                </div>
                            </div>
                        )}

                        {/* Not connected */}
                        {!isConnectionLoading && !connectionStatus?.connected && (
                            <Button className="w-full h-11" onClick={handleOAuthConnect} disabled={isOAuthLoading}>
                                {isOAuthLoading ? (
                                    <><Loader2 className="h-4 w-4 animate-spin mr-2" /> {t('oauth.connecting')}</>
                                ) : (
                                    t('oauth.connectButton')
                                )}
                            </Button>
                        )}
                    </CardContent>
                </Card>
                {/* ── Device & App Connection Guide ── */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Activity className="h-5 w-5" />
                            {t('settings.connectionGuideTitle')}
                        </CardTitle>
                        <p className="text-sm text-muted-foreground">{t('settings.connectionGuideDesc')}</p>
                    </CardHeader>
                    <CardContent className="space-y-2">

                        {/* Garmin */}
                        <details className="group rounded-lg border border-border overflow-hidden">
                            <summary className="flex items-center justify-between gap-2 px-4 py-3 cursor-pointer select-none hover:bg-muted/40 transition-colors list-none">
                                <span className="flex items-center gap-2 font-medium text-sm">
                                    <Watch className="h-4 w-4 text-blue-500" />
                                    Garmin Connect
                                </span>
                                <span className="text-muted-foreground text-xs group-open:rotate-180 transition-transform">▾</span>
                            </summary>
                            <div className="px-4 pb-4 pt-2 space-y-3 text-sm text-muted-foreground border-t border-border">
                                <ol className="space-y-1.5 list-decimal list-inside">
                                    <li>Intervals.icu → <span className="text-foreground font-medium">Settings → Health → Garmin Connect</span></li>
                                    <li><span className="text-foreground font-medium">Connect Garmin</span> {t('settings.guideGarminStep2After')}</li>
                                    <li>{t('settings.guideGarminStep3Before')} <span className="text-foreground font-medium">{t('settings.guideGarminStep3AllowAll')}</span> {t('settings.guideGarminStep3After')}</li>
                                    <li>{t('settings.guideGarminStep4')}</li>
                                </ol>
                                <img src="/guide/garmin-02-connect.png" alt="Garmin Connect" className="rounded-lg border max-w-[200px] w-full mx-auto block mt-2" />
                            </div>
                        </details>

                        {/* Wahoo + Hammerhead */}
                        <details className="group rounded-lg border border-border overflow-hidden">
                            <summary className="flex items-center justify-between gap-2 px-4 py-3 cursor-pointer select-none hover:bg-muted/40 transition-colors list-none">
                                <span className="flex items-center gap-2 font-medium text-sm">
                                    <Zap className="h-4 w-4 text-red-500" />
                                    Wahoo · Hammerhead
                                </span>
                                <span className="text-muted-foreground text-xs group-open:rotate-180 transition-transform">▾</span>
                            </summary>
                            <div className="px-4 pb-4 pt-2 space-y-3 text-sm text-muted-foreground border-t border-border">
                                <ol className="space-y-1.5 list-decimal list-inside">
                                    <li>Intervals.icu → <span className="text-foreground font-medium">Settings → Health → Wahoo</span></li>
                                    <li><span className="text-foreground font-medium">Connect Wahoo</span> {t('settings.guideWahooStep2After')}</li>
                                    <li>{t('settings.guideWahooStep3')}</li>
                                </ol>
                                <p className="text-xs bg-muted/60 rounded px-3 py-2">
                                    💡 <span className="font-medium">Hammerhead Karoo</span> {t('settings.guideWahooHammerheadTip')}
                                </p>
                                <img src="/guide/wahoo-01-connect.png" alt="Wahoo" className="rounded-lg border max-w-[200px] w-full mx-auto block mt-2" />
                            </div>
                        </details>

                        {/* Apple Watch */}
                        <details className="group rounded-lg border border-border overflow-hidden">
                            <summary className="flex items-center justify-between gap-2 px-4 py-3 cursor-pointer select-none hover:bg-muted/40 transition-colors list-none">
                                <span className="flex items-center gap-2 font-medium text-sm">
                                    <Watch className="h-4 w-4 text-gray-500" />
                                    Apple Watch
                                </span>
                                <span className="text-muted-foreground text-xs group-open:rotate-180 transition-transform">▾</span>
                            </summary>
                            <div className="px-4 pb-4 pt-2 space-y-3 text-sm text-muted-foreground border-t border-border">
                                <p>{t('settings.guideAppleWatchIntroBefore')} <span className="text-foreground font-medium">HealthFit</span> {t('settings.guideAppleWatchIntroAfter')}</p>
                                <ol className="space-y-1.5 list-decimal list-inside">
                                    <li>{t('settings.guideAppleWatchStep1Before')} <span className="text-foreground font-medium">HealthFit</span> {t('settings.guideAppleWatchStep1After')}</li>
                                    <li>HealthFit → <span className="text-foreground font-medium">Settings → Upload → Intervals.icu</span></li>
                                    <li>{t('settings.guideAppleWatchStep3')}</li>
                                    <li>{t('settings.guideAppleWatchStep4Before')} <span className="text-foreground font-medium">Activities · Wellness Data · Calendar — Read + Update</span> → OK</li>
                                    <li>{t('settings.guideAppleWatchStep5')}</li>
                                </ol>
                                <img src="/guide/healthfit-connect.png" alt="HealthFit" className="rounded-lg border max-w-[200px] w-full mx-auto block mt-2" />
                            </div>
                        </details>

                        {/* Zwift */}
                        <details className="group rounded-lg border border-border overflow-hidden">
                            <summary className="flex items-center justify-between gap-2 px-4 py-3 cursor-pointer select-none hover:bg-muted/40 transition-colors list-none">
                                <span className="flex items-center gap-2 font-medium text-sm">
                                    <Bike className="h-4 w-4 text-orange-500" />
                                    {t('settings.guideZwiftTitle')}
                                </span>
                                <span className="text-muted-foreground text-xs group-open:rotate-180 transition-transform">▾</span>
                            </summary>
                            <div className="px-4 pb-4 pt-2 space-y-3 text-sm text-muted-foreground border-t border-border">
                                <p>{t('settings.guideZwiftIntroBefore')} <span className="text-foreground font-medium">{t('settings.guideZwiftUploadLabel')}</span> {t('settings.guideZwiftIntroAfter')}</p>
                                <ol className="space-y-1.5 list-decimal list-inside">
                                    <li>Intervals.icu → <span className="text-foreground font-medium">Settings → Integrations → Zwift</span> {t('settings.guideZwiftStep1Suffix')}</li>
                                    <li>{t('settings.guideZwiftStep2Before')} <span className="text-foreground font-medium">"{t('settings.guideZwiftUploadLabel')}"</span> {t('settings.guideZwiftStep2Check')}</li>
                                    <li>{t('settings.guideZwiftStep3Before')} <span className="text-foreground font-medium">{t('settings.guideZwiftTodaysWorkout')}</span> {t('settings.guideZwiftStep3Suffix')}</li>
                                </ol>
                                <img src="/guide/zwift-01-connect.png" alt="Zwift" className="rounded-lg border max-w-[200px] w-full h-40 object-cover object-top mx-auto block mt-2" />
                            </div>
                        </details>

                    </CardContent>
                </Card>

            </div>
        </div>
    )
}
