import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface OnboardingPageProps {
    onComplete: () => void;
    accessToken: string;
}

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function OnboardingPage({ onComplete, accessToken }: OnboardingPageProps) {
    const [step, setStep] = useState(1);
    const [athleteId, setAthleteId] = useState("");
    const [apiKey, setApiKey] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async () => {
        if (!athleteId || !apiKey) {
            setError("Athlete ID와 API Key를 모두 입력해주세요.");
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const res = await fetch(`${API_BASE}/api/settings`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${accessToken}`,
                },
                body: JSON.stringify({
                    intervals_athlete_id: athleteId,
                    intervals_api_key: apiKey,
                }),
            });

            if (!res.ok) {
                throw new Error("설정 저장에 실패했습니다.");
            }

            onComplete();
        } catch (e) {
            setError(e instanceof Error ? e.message : "오류가 발생했습니다.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            <Card className="w-full max-w-2xl">
                <CardHeader>
                    <CardTitle className="text-2xl text-center">
                        🚴 AI Cycling Workout Planner 설정
                    </CardTitle>
                    <p className="text-center text-muted-foreground">
                        서비스 이용을 위해 Intervals.icu 연동이 필요합니다
                    </p>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Progress Indicator */}
                    <div className="flex justify-center gap-2 mb-6">
                        {[1, 2, 3].map((s) => (
                            <div
                                key={s}
                                className={`w-3 h-3 rounded-full ${s === step ? "bg-primary" : s < step ? "bg-primary/50" : "bg-muted"
                                    }`}
                            />
                        ))}
                    </div>

                    {/* Step 1: Intervals.icu 소개 */}
                    {step === 1 && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">1단계: Intervals.icu 연동 준비</h3>
                            <div className="bg-muted/50 rounded-lg p-4 space-y-3">
                                <p>
                                    <strong>Intervals.icu</strong>는 무료로 사용할 수 있는 강력한 훈련 분석 플랫폼입니다.
                                </p>
                                <p>
                                    이 서비스는 Intervals.icu의 데이터를 기반으로 AI 워크아웃을 생성하고
                                    직접 캘린더에 등록합니다.
                                </p>
                                <div className="border-l-4 border-blue-500 pl-4 mt-4">
                                    <p className="text-sm">
                                        아직 Intervals.icu 계정이 없으시다면:
                                    </p>
                                    <a
                                        href="https://intervals.icu"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-primary underline font-medium"
                                    >
                                        intervals.icu에서 무료 가입하기 →
                                    </a>
                                </div>
                            </div>
                            <Button className="w-full" onClick={() => setStep(2)}>
                                다음: API 키 발급하기
                            </Button>
                        </div>
                    )}

                    {/* Step 2: API Key 발급 가이드 */}
                    {step === 2 && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">2단계: API 키 발급</h3>
                            <div className="bg-muted/50 rounded-lg p-4 space-y-4">
                                <ol className="list-decimal list-inside space-y-2 text-sm">
                                    <li>
                                        <a
                                            href="https://intervals.icu/settings"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-primary underline"
                                        >
                                            Intervals.icu Settings
                                        </a>
                                        에 접속하세요
                                    </li>
                                    <li>왼쪽 메뉴에서 <strong>Developer</strong>를 클릭</li>
                                    <li><strong>Create API Key</strong> 버튼 클릭</li>
                                    <li>생성된 API Key를 복사하세요</li>
                                </ol>
                                <div className="border-l-4 border-yellow-500 pl-4">
                                    <p className="text-sm font-medium">Athlete ID 확인 방법:</p>
                                    <p className="text-sm text-muted-foreground">
                                        Intervals.icu URL을 확인하세요: <code>intervals.icu/athlete/<strong>i12345</strong>/...</code>
                                        <br />
                                        여기서 <strong>i12345</strong>가 Athlete ID입니다.
                                    </p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <Button variant="outline" onClick={() => setStep(1)}>
                                    이전
                                </Button>
                                <Button className="flex-1" onClick={() => setStep(3)}>
                                    다음: API 정보 입력
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* Step 3: API 정보 입력 */}
                    {step === 3 && (
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold">3단계: API 정보 입력</h3>

                            {error && (
                                <div className="bg-destructive/10 text-destructive p-3 rounded-lg text-sm">
                                    ❌ {error}
                                </div>
                            )}

                            <div className="space-y-4">
                                <div>
                                    <Label htmlFor="athleteId">Athlete ID</Label>
                                    <Input
                                        id="athleteId"
                                        placeholder="i12345"
                                        value={athleteId}
                                        onChange={(e) => setAthleteId(e.target.value)}
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="apiKey">API Key</Label>
                                    <Input
                                        id="apiKey"
                                        type="password"
                                        placeholder="Intervals.icu에서 발급받은 API Key"
                                        value={apiKey}
                                        onChange={(e) => setApiKey(e.target.value)}
                                    />
                                </div>
                            </div>

                            {/* 사이클링 컴퓨터 동기화 안내 */}
                            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mt-4">
                                <h4 className="font-semibold text-blue-600 mb-2">
                                    💡 사이클링 컴퓨터 연동 팁
                                </h4>
                                <p className="text-sm text-muted-foreground mb-2">
                                    생성된 워크아웃을 Wahoo, Garmin 등의 사이클링 컴퓨터에서 사용하려면:
                                </p>
                                <ol className="text-sm list-decimal list-inside space-y-1 text-muted-foreground">
                                    <li>Intervals.icu Settings → Connections로 이동</li>
                                    <li>Wahoo 또는 Garmin Connect 연결</li>
                                    <li><strong className="text-foreground">"Upload planned workouts"</strong> 옵션을 반드시 체크하세요!</li>
                                </ol>
                                <p className="text-xs text-muted-foreground mt-2">
                                    이 옵션을 활성화해야 AI가 생성한 워크아웃이 자동으로 기기에 동기화됩니다.
                                </p>
                            </div>

                            <div className="flex gap-2">
                                <Button variant="outline" onClick={() => setStep(2)}>
                                    이전
                                </Button>
                                <Button className="flex-1" onClick={handleSubmit} disabled={isLoading}>
                                    {isLoading ? "설정 중..." : "🚀 설정 완료"}
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
