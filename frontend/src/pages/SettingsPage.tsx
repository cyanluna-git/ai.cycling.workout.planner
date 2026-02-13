import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAuth } from '@/contexts/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL || ''

interface Settings {
    ftp: number; max_hr: number; lthr: number; training_goal: string;
    exclude_barcode_workouts?: boolean; training_style?: string;
    preferred_duration?: number; training_focus?: string;
    weekly_tss_target?: number | null;
    weekly_availability?: Record<string, "available" | "unavailable" | "rest">;
}

interface ApiKeysCheck { intervals_configured: boolean; }

export function SettingsPage({ onBack }: { onBack: () => void }) {
    const { t } = useTranslation();
    const { session, signOut } = useAuth()
    const [settings, setSettings] = useState<Settings>({
        ftp: 200, max_hr: 190, lthr: 170, training_goal: '',
        exclude_barcode_workouts: false, training_style: 'auto',
        preferred_duration: 60, training_focus: 'maintain',
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
    })
    const [apiKeys, setApiKeys] = useState({ intervals_api_key: '', athlete_id: '' })
    const [apiKeysCheck, setApiKeysCheck] = useState<ApiKeysCheck | null>(null)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState<string | null>(null)

    useEffect(() => {
        if (session?.access_token) { fetchSettings(); checkApiKeys(); }
    }, [session])

    const fetchSettings = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/settings`, { headers: { Authorization: `Bearer ${session?.access_token}` } });
            if (res.ok) { 
                const data = await res.json(); 
                setSettings({
                    ...data.settings,
                    weekly_availability: data.settings.weekly_availability || {
                        "0": "available",
                        "1": "available",
                        "2": "available",
                        "3": "available",
                        "4": "available",
                        "5": "available",
                        "6": "available",
                    }
                });
            }
        } catch (e) { console.error('Failed to fetch settings', e); }
    }

    const checkApiKeys = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/settings/api-keys/check`, { headers: { Authorization: `Bearer ${session?.access_token}` } });
            if (res.ok) setApiKeysCheck(await res.json());
        } catch (e) { console.error('Failed to check API keys', e); }
    }

    const saveSettings = async () => {
        setSaving(true); setMessage(null);
        try {
            const res = await fetch(`${API_BASE}/api/settings`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session?.access_token}` },
                body: JSON.stringify(settings),
            });
            if (res.ok) setMessage(t('settings.settingsSaved'));
        } catch (e) { setMessage(t('common.saveFailed')); } finally { setSaving(false); }
    }

    const saveApiKeys = async () => {
        setSaving(true); setMessage(null);
        try {
            const res = await fetch(`${API_BASE}/api/settings/api-keys`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session?.access_token}` },
                body: JSON.stringify(apiKeys),
            });
            if (res.ok) { setMessage(t('settings.apiKeySaved')); checkApiKeys(); setApiKeys({ ...apiKeys, intervals_api_key: '' }); }
        } catch (e) { setMessage(t('common.saveFailed')); } finally { setSaving(false); }
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
            } else {
                setMessage(t("settings.weeklyAvailability.saveError"));
            }
        } catch (error) {
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
                    <CardHeader><CardTitle>📅 {t('settings.weeklyAvailability.title')}</CardTitle></CardHeader>
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
                                                🚴 {t("settings.weeklyAvailability.available")}
                                            </SelectItem>
<SelectItem value="rest">
                                                😴 {t("settings.weeklyAvailability.rest")}
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
                        {apiKeysCheck && (
                            <div className="text-sm text-muted-foreground">
                                {t('settings.apiStatus')} {apiKeysCheck.intervals_configured ? t('settings.apiConnected') : t('settings.apiNotConnected')}
                            </div>
                        )}
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {apiKeysCheck?.intervals_configured ? (
                            <div className="text-center py-4">
                                <div className="text-4xl mb-2">🎉</div>
                                <p className="text-sm text-muted-foreground">{t('settings.apiConnectedMessage')}</p>
                                <Button variant="outline" size="sm" className="mt-4" onClick={() => setApiKeysCheck({ intervals_configured: false })}>{t('settings.apiResetKey')}</Button>
                            </div>
                        ) : (
                            <>
                                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                                    <h4 className="font-medium mb-2">{t('settings.apiGuideTitle')}</h4>
                                    <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
                                        <li><a href="https://intervals.icu/settings" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Intervals.icu Settings</a> {t('settings.apiGuideStep1')}</li>
                                        <li>{t('settings.apiGuideStep2')}</li>
                                        <li>{t('settings.apiGuideStep3')}</li>
                                        <li>{t('settings.apiGuideStep4')}</li>
                                    </ol>
                                </div>
                                <div className="space-y-2">
                                    <Label>{t('settings.apiKeyLabel')}</Label>
                                    <Input type="password" placeholder={t('settings.apiKeyPlaceholder')} value={apiKeys.intervals_api_key} onChange={(e) => setApiKeys({ ...apiKeys, intervals_api_key: e.target.value })} />
                                </div>
                                <div className="space-y-2">
                                    <Label>Athlete ID</Label>
                                    <Input placeholder={t('settings.athleteIdPlaceholder')} value={apiKeys.athlete_id} onChange={(e) => setApiKeys({ ...apiKeys, athlete_id: e.target.value })} />
                                </div>
                                <Button onClick={saveApiKeys} disabled={saving}>{saving ? t('common.saving') : t('settings.saveApiKey')}</Button>
                            </>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
