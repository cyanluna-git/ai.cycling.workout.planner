import { useState } from "react";
import { useTranslation } from "react-i18next";
import { XCircle, Loader2, ChevronDown } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchOAuthUrl } from "@/lib/api";

interface OnboardingPageProps {
    onComplete: () => void;
    accessToken: string;
}

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function OnboardingPage({ onComplete, accessToken }: OnboardingPageProps) {
    const { t } = useTranslation();
    const [showManualKey, setShowManualKey] = useState(false);
    const [athleteId, setAthleteId] = useState("");
    const [apiKey, setApiKey] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isOAuthLoading, setIsOAuthLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleOAuthConnect = async () => {
        setIsOAuthLoading(true);
        setError(null);
        try {
            const data = await fetchOAuthUrl(accessToken);
            // Store state in localStorage for verification on callback
            localStorage.setItem("intervals_oauth_state", data.state);
            // Redirect to Intervals.icu authorize page
            window.location.href = data.authorize_url;
        } catch (e) {
            setError(e instanceof Error ? e.message : t("oauth.error", { message: "Unknown error" }));
            setIsOAuthLoading(false);
        }
    };

    const handleManualSubmit = async () => {
        if (!athleteId || !apiKey) { setError(t("onboarding.bothRequired")); return; }
        setIsLoading(true); setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/settings/api-keys`, {
                method: "PUT",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
                body: JSON.stringify({ athlete_id: athleteId, intervals_api_key: apiKey }),
            });
            if (!res.ok) throw new Error(t("onboarding.saveFailed"));
            onComplete();
        } catch (e) { setError(e instanceof Error ? e.message : t("common.error")); } finally { setIsLoading(false); }
    };

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            <Card className="w-full max-w-2xl">
                <CardHeader>
                    <CardTitle className="text-2xl text-center">{t("onboarding.title")}</CardTitle>
                    <p className="text-center text-muted-foreground">{t("onboarding.subtitle")}</p>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Introduction */}
                    <div className="bg-muted/50 rounded-lg p-4 space-y-3">
                        <p><strong>Intervals.icu</strong> {t("onboarding.step1Desc1")}</p>
                        <p>{t("onboarding.step1Desc2")}</p>
                        <div className="border-l-4 border-blue-500 pl-4 mt-4">
                            <p className="text-sm">{t("onboarding.step1NoAccount")}</p>
                            <a href="https://intervals.icu" target="_blank" rel="noopener noreferrer" className="text-primary underline font-medium">{t("onboarding.step1Signup")}</a>
                        </div>
                    </div>

                    {error && (
                        <div className="bg-destructive/10 text-destructive p-3 rounded-lg text-sm flex items-center gap-1.5">
                            <XCircle className="h-4 w-4 flex-shrink-0" /> {error}
                        </div>
                    )}

                    {/* Primary: OAuth Connect */}
                    <Button
                        className="w-full h-12 text-base"
                        onClick={handleOAuthConnect}
                        disabled={isOAuthLoading}
                    >
                        {isOAuthLoading ? (
                            <><Loader2 className="h-4 w-4 animate-spin mr-2" /> {t("oauth.connecting")}</>
                        ) : (
                            t("oauth.connectButton")
                        )}
                    </Button>

                    {/* Cycling computer tip */}
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                        <h4 className="font-semibold text-blue-600 mb-2">{t("onboarding.step3CyclingTipTitle")}</h4>
                        <p className="text-sm text-muted-foreground mb-2">{t("onboarding.step3CyclingTipDesc")}</p>
                        <ol className="text-sm list-decimal list-inside space-y-1 text-muted-foreground">
                            <li>{t("onboarding.step3CyclingTipStep1")}</li>
                            <li>{t("onboarding.step3CyclingTipStep2")}</li>
                            <li><strong className="text-foreground">{t("onboarding.step3CyclingTipStep3Check")}</strong></li>
                        </ol>
                        <p className="text-xs text-muted-foreground mt-2">{t("onboarding.step3CyclingTipNote")}</p>
                    </div>

                    {/* Secondary: Manual API Key (collapsible) */}
                    <details className="group" open={showManualKey} onToggle={(e) => setShowManualKey((e.target as HTMLDetailsElement).open)}>
                        <summary className="flex items-center gap-2 cursor-pointer select-none text-sm text-muted-foreground hover:text-foreground transition-colors list-none">
                            <ChevronDown className="h-4 w-4 group-open:rotate-180 transition-transform" />
                            {t("oauth.manualApiKey")}
                        </summary>
                        <div className="mt-4 space-y-4 border-t border-border pt-4">
                            <div className="bg-muted/50 rounded-lg p-4 space-y-4">
                                <ol className="list-decimal list-inside space-y-2 text-sm">
                                    <li><a href="https://intervals.icu/settings" target="_blank" rel="noopener noreferrer" className="text-primary underline">Intervals.icu Settings</a> {t("onboarding.step2Inst1")}</li>
                                    <li>{t("onboarding.step2Inst2")}</li>
                                    <li>{t("onboarding.step2Inst3")}</li>
                                    <li>{t("onboarding.step2Inst4")}</li>
                                </ol>
                                <div className="border-l-4 border-yellow-500 pl-4">
                                    <p className="text-sm font-medium">{t("onboarding.step2AthleteIdTitle")}</p>
                                    <p className="text-sm text-muted-foreground">
                                        {t("onboarding.step2AthleteIdDesc")} <code>intervals.icu/athlete/<strong>i12345</strong>/...</code>
                                        <br />{t("onboarding.step2AthleteIdHint")}
                                    </p>
                                </div>
                            </div>
                            <div className="space-y-4">
                                <div><Label htmlFor="athleteId">Athlete ID</Label><Input id="athleteId" placeholder="i12345" value={athleteId} onChange={(e) => setAthleteId(e.target.value)} /></div>
                                <div><Label htmlFor="apiKey">API Key</Label><Input id="apiKey" type="password" placeholder={t("onboarding.step3ApiKeyPlaceholder")} value={apiKey} onChange={(e) => setApiKey(e.target.value)} /></div>
                            </div>
                            <Button className="w-full" onClick={handleManualSubmit} disabled={isLoading}>
                                {isLoading ? t("onboarding.settingUp") : t("onboarding.complete")}
                            </Button>
                        </div>
                    </details>
                </CardContent>
            </Card>
        </div>
    );
}
