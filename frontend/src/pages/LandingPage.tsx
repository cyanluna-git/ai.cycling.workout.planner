import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface LandingPageProps {
    onGetStarted: () => void;
}

export function LandingPage({ onGetStarted }: LandingPageProps) {
    return (
        <div className="min-h-screen bg-gradient-to-b from-background to-muted">
            {/* Hero Section */}
            <div className="container mx-auto px-4 py-16">
                <div className="text-center max-w-3xl mx-auto">
                    <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
                        🚴 AI Cycling Coach
                    </h1>
                    <p className="text-xl text-muted-foreground mb-8">
                        매일 당신에게 <span className="text-primary font-semibold">최적화된 워크아웃</span>을
                        <br />AI가 자동으로 생성하고 사이클링 컴퓨터에 전송합니다
                    </p>
                    <Button size="lg" className="text-lg px-8 py-6" onClick={onGetStarted}>
                        🚀 무료로 시작하기
                    </Button>
                </div>
            </div>

            {/* Problem Statement */}
            <div className="container mx-auto px-4 py-12">
                <div className="max-w-4xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-8">혹시 이런 고민 있으신가요?</h2>
                    <div className="grid md:grid-cols-3 gap-6">
                        <Card className="bg-red-500/5 border-red-500/20">
                            <CardContent className="p-6 text-center">
                                <div className="text-4xl mb-4">😓</div>
                                <p className="text-muted-foreground">
                                    "오늘 뭘 타야 하지?"<br />
                                    매일 고민하는 시간 낭비
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="bg-red-500/5 border-red-500/20">
                            <CardContent className="p-6 text-center">
                                <div className="text-4xl mb-4">📊</div>
                                <p className="text-muted-foreground">
                                    CTL, ATL, TSB...<br />
                                    데이터는 있는데 활용을 못함
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="bg-red-500/5 border-red-500/20">
                            <CardContent className="p-6 text-center">
                                <div className="text-4xl mb-4">💻</div>
                                <p className="text-muted-foreground">
                                    태블릿/노트북 없이<br />
                                    로라만 타고 싶은데...
                                </p>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>

            {/* Solution */}
            <div className="container mx-auto px-4 py-12 bg-primary/5">
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="text-3xl font-bold mb-4">AI가 매일 최적의 워크아웃을 추천합니다</h2>
                    <p className="text-lg text-muted-foreground mb-8">
                        Intervals.icu의 훈련 데이터와 웰니스 정보를 분석하여<br />
                        <span className="text-primary font-semibold">당신의 현재 상태에 딱 맞는</span> 워크아웃을 생성합니다
                    </p>
                </div>
            </div>

            {/* Features */}
            <div className="container mx-auto px-4 py-16">
                <div className="max-w-5xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-12">이렇게 동작합니다</h2>
                    <div className="grid md:grid-cols-3 gap-8">
                        <div className="text-center">
                            <div className="w-16 h-16 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                <span className="text-3xl">📡</span>
                            </div>
                            <h3 className="font-bold mb-2">1. 데이터 분석</h3>
                            <p className="text-sm text-muted-foreground">
                                Intervals.icu에서 CTL/ATL/TSB,<br />
                                HRV, 수면 데이터 등을 가져와<br />
                                현재 컨디션을 파악합니다
                            </p>
                        </div>
                        <div className="text-center">
                            <div className="w-16 h-16 bg-purple-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                <span className="text-3xl">🤖</span>
                            </div>
                            <h3 className="font-bold mb-2">2. AI 워크아웃 생성</h3>
                            <p className="text-sm text-muted-foreground">
                                AI가 당신의 상태와 목표에 맞는<br />
                                오늘의 최적 워크아웃을<br />
                                자동으로 설계합니다
                            </p>
                        </div>
                        <div className="text-center">
                            <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                <span className="text-3xl">📲</span>
                            </div>
                            <h3 className="font-bold mb-2">3. 자동 전송</h3>
                            <p className="text-sm text-muted-foreground">
                                Wahoo, Garmin 사이클링 컴퓨터에<br />
                                워크아웃이 자동 동기화!<br />
                                바로 훈련 시작하세요
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Key Benefits */}
            <div className="container mx-auto px-4 py-12">
                <div className="max-w-4xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-8">왜 AI Cycling Coach인가요?</h2>
                    <div className="grid md:grid-cols-2 gap-6">
                        <Card className="bg-gradient-to-br from-green-500/5 to-green-500/10 border-green-500/20">
                            <CardContent className="p-6">
                                <div className="flex items-start gap-4">
                                    <span className="text-3xl">⚡</span>
                                    <div>
                                        <h3 className="font-bold mb-2">즉시 실행 가능</h3>
                                        <p className="text-sm text-muted-foreground">
                                            생성된 워크아웃이 바로 기기에 전송됩니다.
                                            태블릿이나 노트북 없이 사이클링 컴퓨터만으로 훈련 가능!
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-blue-500/5 to-blue-500/10 border-blue-500/20">
                            <CardContent className="p-6">
                                <div className="flex items-start gap-4">
                                    <span className="text-3xl">🎯</span>
                                    <div>
                                        <h3 className="font-bold mb-2">개인 맞춤형 훈련</h3>
                                        <p className="text-sm text-muted-foreground">
                                            당신의 FTP, 훈련 부하, 피로도, HRV 등을 종합 분석하여
                                            매일 최적의 강도와 볼륨을 추천합니다.
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-purple-500/5 to-purple-500/10 border-purple-500/20">
                            <CardContent className="p-6">
                                <div className="flex items-start gap-4">
                                    <span className="text-3xl">🔗</span>
                                    <div>
                                        <h3 className="font-bold mb-2">완벽한 연동</h3>
                                        <p className="text-sm text-muted-foreground">
                                            Intervals.icu + Wahoo/Garmin과 자동 연동.
                                            스마트 트레이너와 바로 연결하여 훈련하세요.
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-orange-500/5 to-orange-500/10 border-orange-500/20">
                            <CardContent className="p-6">
                                <div className="flex items-start gap-4">
                                    <span className="text-3xl">🆓</span>
                                    <div>
                                        <h3 className="font-bold mb-2">무료 사용</h3>
                                        <p className="text-sm text-muted-foreground">
                                            Intervals.icu는 무료! AI Cycling Coach도 무료!
                                            추가 비용 없이 스마트한 훈련을 시작하세요.
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>

            {/* Target Users */}
            <div className="container mx-auto px-4 py-12 bg-muted/50">
                <div className="max-w-3xl mx-auto text-center">
                    <h2 className="text-2xl font-bold mb-6">이런 분들께 추천합니다</h2>
                    <div className="flex flex-wrap justify-center gap-3">
                        <span className="px-4 py-2 bg-background rounded-full text-sm">🏠 실내 트레이너로 훈련하는 분</span>
                        <span className="px-4 py-2 bg-background rounded-full text-sm">📊 Intervals.icu 사용자</span>
                        <span className="px-4 py-2 bg-background rounded-full text-sm">⌚ Wahoo / Garmin 유저</span>
                        <span className="px-4 py-2 bg-background rounded-full text-sm">🎮 Zwift/MyWoosh 없이 타는 분</span>
                        <span className="px-4 py-2 bg-background rounded-full text-sm">🤔 매일 훈련 계획 고민하는 분</span>
                    </div>
                </div>
            </div>

            {/* CTA */}
            <div className="container mx-auto px-4 py-16">
                <div className="max-w-2xl mx-auto text-center">
                    <h2 className="text-3xl font-bold mb-4">오늘부터 스마트하게 훈련하세요</h2>
                    <p className="text-muted-foreground mb-8">
                        Intervals.icu 계정만 있으면 바로 시작할 수 있습니다
                    </p>
                    <Button size="lg" className="text-lg px-8 py-6" onClick={onGetStarted}>
                        🚴 시작하기
                    </Button>
                </div>
            </div>

            {/* Footer */}
            <footer className="border-t py-8">
                <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
                    <p>AI Cycling Coach • Powered by Intervals.icu Integration</p>
                </div>
            </footer>
        </div>
    );
}
