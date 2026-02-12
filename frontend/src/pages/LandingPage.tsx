import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface LandingPageProps {
    onGetStarted: () => void;
}

export function LandingPage({ onGetStarted }: LandingPageProps) {
    const { t } = useTranslation();

    return (
        <div className="min-h-screen bg-gradient-to-b from-background to-muted">
            <div className="absolute top-4 right-4"><LanguageSwitcher /></div>
            <div className="container mx-auto px-4 py-16">
                <div className="text-center max-w-3xl mx-auto">
                    <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
                        \ud83d\udeb4 AI Cycling Coach
                    </h1>
                    <p className="text-xl text-muted-foreground mb-8">
                        {t('landing.heroSubtitle1')} <span className="text-primary font-semibold">{t('landing.heroSubtitle2')}</span>{t('landing.heroSubtitle3')}
                        <br />{t('landing.heroSubtitle4')}
                    </p>
                    <Button size="lg" className="text-lg px-8 py-6" onClick={onGetStarted}>{t('landing.getStarted')}</Button>
                </div>
            </div>

            <div className="container mx-auto px-4 py-12">
                <div className="max-w-4xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-8">{t('landing.problemTitle')}</h2>
                    <div className="grid md:grid-cols-3 gap-6">
                        <Card className="bg-red-500/5 border-red-500/20"><CardContent className="p-6 text-center"><div className="text-4xl mb-4">\ud83d\ude13</div><p className="text-muted-foreground whitespace-pre-line">{t('landing.problem1')}</p></CardContent></Card>
                        <Card className="bg-red-500/5 border-red-500/20"><CardContent className="p-6 text-center"><div className="text-4xl mb-4">\ud83d\udcca</div><p className="text-muted-foreground whitespace-pre-line">{t('landing.problem2')}</p></CardContent></Card>
                        <Card className="bg-red-500/5 border-red-500/20"><CardContent className="p-6 text-center"><div className="text-4xl mb-4">\ud83d\udcbb</div><p className="text-muted-foreground whitespace-pre-line">{t('landing.problem3')}</p></CardContent></Card>
                    </div>
                </div>
            </div>

            <div className="container mx-auto px-4 py-12 bg-primary/5">
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="text-3xl font-bold mb-4">{t('landing.solutionTitle')}</h2>
                    <p className="text-lg text-muted-foreground mb-8">
                        {t('landing.solutionDesc1')}<br />
                        <span className="text-primary font-semibold">{t('landing.solutionDesc2')}</span> {t('landing.solutionDesc3')}
                    </p>
                </div>
            </div>

            <div className="container mx-auto px-4 py-16">
                <div className="max-w-5xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-12">{t('landing.howItWorksTitle')}</h2>
                    <div className="grid md:grid-cols-3 gap-8">
                        <div className="text-center">
                            <div className="w-16 h-16 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-4"><span className="text-3xl">\ud83d\udce1</span></div>
                            <h3 className="font-bold mb-2">{t('landing.step1Title')}</h3>
                            <p className="text-sm text-muted-foreground whitespace-pre-line">{t('landing.step1Desc')}</p>
                        </div>
                        <div className="text-center">
                            <div className="w-16 h-16 bg-purple-500/10 rounded-full flex items-center justify-center mx-auto mb-4"><span className="text-3xl">\ud83e\udd16</span></div>
                            <h3 className="font-bold mb-2">{t('landing.step2Title')}</h3>
                            <p className="text-sm text-muted-foreground whitespace-pre-line">{t('landing.step2Desc')}</p>
                        </div>
                        <div className="text-center">
                            <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-4"><span className="text-3xl">\ud83d\udcf2</span></div>
                            <h3 className="font-bold mb-2">{t('landing.step3Title')}</h3>
                            <p className="text-sm text-muted-foreground whitespace-pre-line">{t('landing.step3Desc')}</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="container mx-auto px-4 py-12">
                <div className="max-w-4xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-8">{t('landing.whyTitle')}</h2>
                    <div className="grid md:grid-cols-2 gap-6">
                        <Card className="bg-gradient-to-br from-green-500/5 to-green-500/10 border-green-500/20"><CardContent className="p-6"><div className="flex items-start gap-4"><span className="text-3xl">\u26a1</span><div><h3 className="font-bold mb-2">{t('landing.benefit1Title')}</h3><p className="text-sm text-muted-foreground">{t('landing.benefit1Desc')}</p></div></div></CardContent></Card>
                        <Card className="bg-gradient-to-br from-blue-500/5 to-blue-500/10 border-blue-500/20"><CardContent className="p-6"><div className="flex items-start gap-4"><span className="text-3xl">\ud83c\udfaf</span><div><h3 className="font-bold mb-2">{t('landing.benefit2Title')}</h3><p className="text-sm text-muted-foreground">{t('landing.benefit2Desc')}</p></div></div></CardContent></Card>
                        <Card className="bg-gradient-to-br from-purple-500/5 to-purple-500/10 border-purple-500/20"><CardContent className="p-6"><div className="flex items-start gap-4"><span className="text-3xl">\ud83d\udd17</span><div><h3 className="font-bold mb-2">{t('landing.benefit3Title')}</h3><p className="text-sm text-muted-foreground">{t('landing.benefit3Desc')}</p></div></div></CardContent></Card>
                        <Card className="bg-gradient-to-br from-orange-500/5 to-orange-500/10 border-orange-500/20"><CardContent className="p-6"><div className="flex items-start gap-4"><span className="text-3xl">\ud83c\udd93</span><div><h3 className="font-bold mb-2">{t('landing.benefit4Title')}</h3><p className="text-sm text-muted-foreground">{t('landing.benefit4Desc')}</p></div></div></CardContent></Card>
                    </div>
                </div>
            </div>


            {/* Testimonials Section */}
            <div className="container mx-auto px-4 py-12 bg-muted/30">
                <div className="max-w-4xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-2">{t('landing.testimonialsTitle')}</h2>
                    <p className="text-center text-sm text-muted-foreground mb-8">{t('landing.testimonialsNote')}</p>
                    
                    <div className="grid md:grid-cols-3 gap-6">
                        {/* Testimonial Card 1 */}
                        <Card className="bg-gradient-to-br from-blue-500/5 to-blue-500/10">
                            <CardContent className="p-6">
                                <div className="text-4xl mb-3">💬</div>
                                <p className="text-sm mb-4 italic">"{t('landing.testimonial1')}"</p>
                                <p className="text-xs text-muted-foreground">- {t('landing.testimonial1Author')}</p>
                            </CardContent>
                        </Card>
                        
                        {/* Testimonial Card 2 */}
                        <Card className="bg-gradient-to-br from-green-500/5 to-green-500/10">
                            <CardContent className="p-6">
                                <div className="text-4xl mb-3">💬</div>
                                <p className="text-sm mb-4 italic">"{t('landing.testimonial2')}"</p>
                                <p className="text-xs text-muted-foreground">- {t('landing.testimonial2Author')}</p>
                            </CardContent>
                        </Card>
                        
                        {/* Testimonial Card 3 */}
                        <Card className="bg-gradient-to-br from-purple-500/5 to-purple-500/10">
                            <CardContent className="p-6">
                                <div className="text-4xl mb-3">💬</div>
                                <p className="text-sm mb-4 italic">"{t('landing.testimonial3')}"</p>
                                <p className="text-xs text-muted-foreground">- {t('landing.testimonial3Author')}</p>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>

            {/* Before/After Comparison Section */}
            <div className="container mx-auto px-4 py-12">
                <div className="max-w-4xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-8">{t('landing.beforeAfterTitle')}</h2>
                    
                    <div className="grid md:grid-cols-2 gap-6">
                        {/* Before Card */}
                        <Card className="border-red-200 bg-red-50/50 dark:bg-red-950/20">
                            <CardContent className="p-6">
                                <h3 className="font-bold mb-4 text-lg">{t('landing.beforeTitle')}</h3>
                                <div className="space-y-3">
                                    <div className="flex items-start gap-2">
                                        <span className="text-red-500 mt-1">❌</span>
                                        <p className="text-sm">{t('landing.before1')}</p>
                                    </div>
                                    <div className="flex items-start gap-2">
                                        <span className="text-red-500 mt-1">❌</span>
                                        <p className="text-sm">{t('landing.before2')}</p>
                                    </div>
                                    <div className="flex items-start gap-2">
                                        <span className="text-red-500 mt-1">❌</span>
                                        <p className="text-sm">{t('landing.before3')}</p>
                                    </div>
                                    <div className="flex items-start gap-2">
                                        <span className="text-red-500 mt-1">❌</span>
                                        <p className="text-sm">{t('landing.before4')}</p>
                                    </div>
                                    <div className="flex items-start gap-2">
                                        <span className="text-red-500 mt-1">❌</span>
                                        <p className="text-sm">{t('landing.before5')}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        
                        {/* After Card */}
                        <Card className="border-green-200 bg-green-50/50 dark:bg-green-950/20">
                            <CardContent className="p-6">
                                <h3 className="font-bold mb-4 text-lg">{t('landing.afterTitle')}</h3>
                                <div className="space-y-3">
                                    <div className="flex items-start gap-2">
                                        <span className="text-green-500 mt-1">✅</span>
                                        <p className="text-sm">{t('landing.after1')}</p>
                                    </div>
                                    <div className="flex items-start gap-2">
                                        <span className="text-green-500 mt-1">✅</span>
                                        <p className="text-sm">{t('landing.after2')}</p>
                                    </div>
                                    <div className="flex items-start gap-2">
                                        <span className="text-green-500 mt-1">✅</span>
                                        <p className="text-sm">{t('landing.after3')}</p>
                                    </div>
                                    <div className="flex items-start gap-2">
                                        <span className="text-green-500 mt-1">✅</span>
                                        <p className="text-sm">{t('landing.after4')}</p>
                                    </div>
                                    <div className="flex items-start gap-2">
                                        <span className="text-green-500 mt-1">✅</span>
                                        <p className="text-sm">{t('landing.after5')}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
            <div className="container mx-auto px-4 py-12 bg-muted/50">
                <div className="max-w-3xl mx-auto text-center">
                    <h2 className="text-2xl font-bold mb-6">{t('landing.targetTitle')}</h2>
                    <div className="flex flex-wrap justify-center gap-3">
                        {[1,2,3,4,5].map(i => (
                            <span key={i} className="px-4 py-2 bg-background rounded-full text-sm">{t(`landing.target${i}`)}</span>
                        ))}
                    </div>
                </div>
            </div>

            <div className="container mx-auto px-4 py-12 bg-muted/30">
                <div className="max-w-4xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-8">{t('landing.faqTitle')}</h2>
                    <div className="space-y-4">
                        <details className="group p-4 bg-background rounded-lg border">
                            <summary className="font-semibold cursor-pointer list-none flex items-center justify-between">
                                <span>{t('landing.faq1Q')}</span>
                                <span className="transition group-open:rotate-180">\u25bc</span>
                            </summary>
                            <p className="mt-3 text-sm text-muted-foreground">{t('landing.faq1A')}</p>
                        </details>
                        <details className="group p-4 bg-background rounded-lg border">
                            <summary className="font-semibold cursor-pointer list-none flex items-center justify-between">
                                <span>{t('landing.faq2Q')}</span>
                                <span className="transition group-open:rotate-180">\u25bc</span>
                            </summary>
                            <p className="mt-3 text-sm text-muted-foreground">{t('landing.faq2A')}</p>
                        </details>
                        <details className="group p-4 bg-background rounded-lg border">
                            <summary className="font-semibold cursor-pointer list-none flex items-center justify-between">
                                <span>{t('landing.faq3Q')}</span>
                                <span className="transition group-open:rotate-180">\u25bc</span>
                            </summary>
                            <p className="mt-3 text-sm text-muted-foreground">{t('landing.faq3A')}</p>
                        </details>
                        <details className="group p-4 bg-background rounded-lg border">
                            <summary className="font-semibold cursor-pointer list-none flex items-center justify-between">
                                <span>{t('landing.faq4Q')}</span>
                                <span className="transition group-open:rotate-180">\u25bc</span>
                            </summary>
                            <p className="mt-3 text-sm text-muted-foreground">{t('landing.faq4A')}</p>
                        </details>
                        <details className="group p-4 bg-background rounded-lg border">
                            <summary className="font-semibold cursor-pointer list-none flex items-center justify-between">
                                <span>{t('landing.faq5Q')}</span>
                                <span className="transition group-open:rotate-180">\u25bc</span>
                            </summary>
                            <p className="mt-3 text-sm text-muted-foreground">{t('landing.faq5A')}</p>
                        </details>
                    </div>
                </div>
            </div>

            <div className="container mx-auto px-4 py-16">
                <div className="max-w-2xl mx-auto text-center">
                    <h2 className="text-3xl font-bold mb-4">{t('landing.ctaTitle')}</h2>
                    <p className="text-muted-foreground mb-8">{t('landing.ctaDesc')}</p>
                    <Button size="lg" className="text-lg px-8 py-6" onClick={onGetStarted}>{t('landing.ctaButton')}</Button>
                </div>
            </div>

            <footer className="border-t py-8">
                <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
                    <p>AI Cycling Coach \u2022 Powered by Intervals.icu Integration</p>
                </div>
            </footer>
        </div>
    );
}
