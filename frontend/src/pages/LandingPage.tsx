import { useTranslation } from "react-i18next";
import {
    Bike, Radio, Bot, Smartphone, Crosshair,
    FileCode, ChevronRight, CalendarDays,
} from "lucide-react";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Button } from "@/components/ui/button";

interface LandingPageProps {
    onGetStarted: () => void;
}

export function LandingPage({ onGetStarted }: LandingPageProps) {
    const { t } = useTranslation();

    return (
        <div className="min-h-screen bg-gradient-to-b from-background to-muted">
            <div className="absolute top-4 right-4"><LanguageSwitcher /></div>

            {/* HERO */}
            <div className="container mx-auto px-4 pt-20 pb-16">
                <div className="text-center max-w-3xl mx-auto">
                    <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">
                        AI Cycling Coach
                    </h1>
                    <p className="text-xl md:text-2xl font-medium mb-3">
                        {t('landing.heroSubtitle')}
                    </p>
                    <p className="text-sm text-muted-foreground mb-8">
                        {t('landing.heroTagline')}
                    </p>

                    {/* Power Zone Bar */}
                    <div
                        className="h-1.5 w-full max-w-md mx-auto rounded-full mb-10"
                        style={{
                            background: "linear-gradient(90deg, #3b82f6, #22c55e, #eab308, #f97316, #ef4444, #3b82f6, #22c55e, #eab308, #f97316, #ef4444)",
                            backgroundSize: "200% 100%",
                            animation: "shimmer 8s linear infinite",
                        }}
                    />

                    <Button size="lg" className="text-lg px-8 py-6" onClick={onGetStarted}>
                        {t('landing.getStarted')}
                    </Button>
                </div>
            </div>

            {/* PIPELINE STRIP */}
            <div className="bg-muted/50 border-y">
                <div className="container mx-auto px-4 py-8">
                    <div className="hidden md:flex items-center justify-center gap-4">
                        {[
                            { icon: Radio, label: t('landing.pipeline1') },
                            { icon: Bot, label: t('landing.pipeline2') },
                            { icon: FileCode, label: t('landing.pipeline3') },
                            { icon: Smartphone, label: t('landing.pipeline4') },
                        ].map((item, i, arr) => (
                            <div key={i} className="flex items-center gap-4">
                                <div className="flex flex-col items-center gap-2">
                                    <item.icon className="h-6 w-6 text-muted-foreground" />
                                    <span className="text-sm font-medium">{item.label}</span>
                                </div>
                                {i < arr.length - 1 && (
                                    <ChevronRight className="h-4 w-4 text-muted-foreground/50" />
                                )}
                            </div>
                        ))}
                    </div>
                    <div className="grid grid-cols-2 gap-6 md:hidden">
                        {[
                            { icon: Radio, label: t('landing.pipeline1') },
                            { icon: Bot, label: t('landing.pipeline2') },
                            { icon: FileCode, label: t('landing.pipeline3') },
                            { icon: Smartphone, label: t('landing.pipeline4') },
                        ].map((item, i) => (
                            <div key={i} className="flex flex-col items-center gap-2">
                                <item.icon className="h-6 w-6 text-muted-foreground" />
                                <span className="text-sm font-medium">{item.label}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* HOW IT WORKS */}
            <div className="container mx-auto px-4 py-16">
                <div className="max-w-4xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-12">{t('landing.howItWorksTitle')}</h2>
                    <div className="grid md:grid-cols-3 gap-10">
                        {[
                            { num: "01", title: t('landing.step1Title'), desc: t('landing.step1Desc') },
                            { num: "02", title: t('landing.step2Title'), desc: t('landing.step2Desc') },
                            { num: "03", title: t('landing.step3Title'), desc: t('landing.step3Desc') },
                        ].map((step) => (
                            <div key={step.num} className="relative">
                                <span className="text-6xl font-bold text-muted-foreground/10 absolute -top-4 -left-2 select-none">
                                    {step.num}
                                </span>
                                <div className="pt-8">
                                    <div className="w-12 h-0.5 bg-primary mb-4" />
                                    <h3 className="font-bold mb-2">{step.title}</h3>
                                    <p className="text-sm text-muted-foreground">{step.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* FEATURES */}
            <div className="container mx-auto px-4 py-12">
                <div className="max-w-5xl mx-auto">
                    <div className="grid md:grid-cols-3 md:divide-x divide-border">
                        {[
                            { icon: Crosshair, title: t('landing.feat1Title'), desc: t('landing.feat1Desc') },
                            { icon: Smartphone, title: t('landing.feat2Title'), desc: t('landing.feat2Desc') },
                            { icon: CalendarDays, title: t('landing.feat3Title'), desc: t('landing.feat3Desc') },
                        ].map((feat, i) => (
                            <div key={i} className="px-6 py-4 md:py-0">
                                <feat.icon className="h-6 w-6 text-primary mb-3" />
                                <h3 className="font-bold mb-2">{feat.title}</h3>
                                <p className="text-sm text-muted-foreground">{feat.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* FAQ */}
            <div className="container mx-auto px-4 py-12 bg-muted/30">
                <div className="max-w-3xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-8">{t('landing.faqTitle')}</h2>
                    <div className="space-y-4">
                        {[1, 2, 3].map((i) => (
                            <details key={i} className="group p-4 bg-background rounded-lg border">
                                <summary className="font-semibold cursor-pointer list-none flex items-center justify-between">
                                    <span>{t(`landing.faq${i}Q`)}</span>
                                    <span className="transition group-open:rotate-180">&#9660;</span>
                                </summary>
                                <p className="mt-3 text-sm text-muted-foreground">{t(`landing.faq${i}A`)}</p>
                            </details>
                        ))}
                    </div>
                </div>
            </div>

            {/* CTA + FOOTER */}
            <div className="container mx-auto px-4 py-16">
                <div className="max-w-2xl mx-auto text-center">
                    <p className="text-3xl font-bold mb-2">{t('landing.freeStatement')}</p>
                    <p className="text-muted-foreground mb-8">{t('landing.freeDesc')}</p>
                    <Button size="lg" className="text-lg px-8 py-6" onClick={onGetStarted}>
                        {t('landing.ctaButton')}
                    </Button>
                </div>
            </div>

            <footer className="border-t py-8">
                <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
                    <div className="inline-flex items-center gap-1.5">
                        <Bike className="h-4 w-4" />
                        <span>AI Cycling Coach</span>
                    </div>
                </div>
            </footer>
        </div>
    );
}
