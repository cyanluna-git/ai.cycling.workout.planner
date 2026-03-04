import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { submitOAuthCallback } from "@/lib/api";

interface OAuthCallbackPageProps {
    accessToken: string;
    onComplete: () => void;
}

export function OAuthCallbackPage({ accessToken, onComplete }: OAuthCallbackPageProps) {
    const { t } = useTranslation();
    const [status, setStatus] = useState<"processing" | "success" | "error">("processing");
    const [errorMessage, setErrorMessage] = useState<string>("");

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const code = params.get("code");
        const state = params.get("state");
        const error = params.get("error");

        if (error) {
            setStatus("error");
            setErrorMessage(t("oauth.denied"));
            // Redirect to dashboard after delay
            setTimeout(() => {
                window.history.replaceState({}, "", "/");
                onComplete();
            }, 3000);
            return;
        }

        if (!code || !state) {
            setStatus("error");
            setErrorMessage(t("oauth.error", { message: "Missing code or state" }));
            setTimeout(() => {
                window.history.replaceState({}, "", "/");
                onComplete();
            }, 3000);
            return;
        }

        // Client-side state check: if localStorage has a stored state, it must match.
        // If localStorage is empty (e.g. different device/browser), the server will verify.
        const storedState = localStorage.getItem("intervals_oauth_state");
        if (storedState && storedState !== state) {
            setStatus("error");
            setErrorMessage(t("oauth.error", { message: "State mismatch" }));
            setTimeout(() => {
                window.history.replaceState({}, "", "/");
                onComplete();
            }, 3000);
            return;
        }

        // Exchange code for token
        (async () => {
            try {
                await submitOAuthCallback(accessToken, code, state);
                localStorage.removeItem("intervals_oauth_state");
                setStatus("success");
                // Redirect to dashboard after brief success display
                setTimeout(() => {
                    window.history.replaceState({}, "", "/");
                    onComplete();
                }, 2000);
            } catch (err) {
                setStatus("error");
                setErrorMessage(
                    t("oauth.error", {
                        message: err instanceof Error ? err.message : "Unknown error",
                    })
                );
                setTimeout(() => {
                    window.history.replaceState({}, "", "/");
                    onComplete();
                }, 3000);
            }
        })();
    }, [accessToken, onComplete, t]);

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            <Card className="w-full max-w-md">
                <CardContent className="pt-6 text-center space-y-4">
                    {status === "processing" && (
                        <>
                            <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
                            <p className="text-lg font-medium">{t("oauth.processing")}</p>
                        </>
                    )}
                    {status === "success" && (
                        <>
                            <CheckCircle className="h-12 w-12 text-green-500 mx-auto" />
                            <p className="text-lg font-medium text-green-600">{t("oauth.success")}</p>
                        </>
                    )}
                    {status === "error" && (
                        <>
                            <XCircle className="h-12 w-12 text-destructive mx-auto" />
                            <p className="text-lg font-medium text-destructive">{errorMessage}</p>
                            <Button
                                variant="outline"
                                onClick={() => {
                                    window.history.replaceState({}, "", "/");
                                    onComplete();
                                }}
                            >
                                {t("common.back")}
                            </Button>
                        </>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
