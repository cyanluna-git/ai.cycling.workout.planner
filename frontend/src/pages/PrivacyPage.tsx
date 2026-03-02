export function PrivacyPage() {
    return (
        <div className="min-h-screen bg-background">
            <div className="container mx-auto px-4 py-12 max-w-3xl">
                <h1 className="text-3xl font-bold mb-2">Privacy Policy</h1>
                <p className="text-sm text-muted-foreground mb-10">Last updated: March 2, 2026</p>

                <div className="space-y-8 text-sm leading-relaxed">

                    <section>
                        <h2 className="text-lg font-semibold mb-3">1. Overview</h2>
                        <p className="text-muted-foreground">
                            AI Cycling Coach ("we", "our", or "us") is a personalized cycling workout planning
                            platform. This Privacy Policy explains what data we collect, how we use it, and your
                            choices regarding that data. By using our service you agree to the practices described here.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold mb-3">2. Data We Collect</h2>
                        <div className="text-muted-foreground space-y-3">
                            <p><strong className="text-foreground">Account data</strong> — Email address and
                            authentication credentials managed by Supabase (our database provider).</p>
                            <p><strong className="text-foreground">Fitness & activity data</strong> — When you connect
                            your Intervals.icu account we access your cycling activity history, wellness metrics
                            (HRV, resting heart rate, sleep), and fitness metrics (CTL / ATL / TSB / FTP). This
                            data is fetched on-demand and used solely to generate personalised workouts.</p>
                            <p><strong className="text-foreground">User preferences</strong> — Settings you configure
                            inside the app (workout style, duration preferences, language).</p>
                            <p><strong className="text-foreground">Usage data</strong> — Standard server logs
                            (request timestamps, error codes). No personal identifiers are stored in logs.</p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold mb-3">3. How We Use Your Data</h2>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2">
                            <li>Generate AI-powered cycling workout recommendations tailored to your current fitness state.</li>
                            <li>Display your weekly training calendar and fitness trend charts inside the dashboard.</li>
                            <li>Export workouts to Zwift (.zwo format) and register them to your Intervals.icu calendar.</li>
                            <li>Improve the service through aggregate, anonymised usage analytics.</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold mb-3">4. Third-Party Services & Data Sharing</h2>
                        <div className="text-muted-foreground space-y-3">
                            <p>We do <strong className="text-foreground">not</strong> sell your personal data to any
                            third party. The following processors receive limited data strictly to operate the service:</p>
                            <div className="overflow-x-auto">
                                <table className="w-full text-xs border-collapse mt-2">
                                    <thead>
                                        <tr className="border-b">
                                            <th className="text-left py-2 pr-4 text-foreground font-semibold">Service</th>
                                            <th className="text-left py-2 pr-4 text-foreground font-semibold">Purpose</th>
                                            <th className="text-left py-2 text-foreground font-semibold">Data shared</th>
                                        </tr>
                                    </thead>
                                    <tbody className="space-y-1">
                                        <tr className="border-b">
                                            <td className="py-2 pr-4 font-medium text-foreground">Supabase</td>
                                            <td className="py-2 pr-4">Auth & database</td>
                                            <td className="py-2">Email, settings</td>
                                        </tr>
                                        <tr className="border-b">
                                            <td className="py-2 pr-4 font-medium text-foreground">Intervals.icu</td>
                                            <td className="py-2 pr-4">Athlete data source</td>
                                            <td className="py-2">Your own data (read/write via your API key)</td>
                                        </tr>
                                        <tr className="border-b">
                                            <td className="py-2 pr-4 font-medium text-foreground">Groq (LLM)</td>
                                            <td className="py-2 pr-4">Workout AI selection</td>
                                            <td className="py-2">Anonymous fitness metrics (CTL/ATL/TSB/FTP, no name/email)</td>
                                        </tr>
                                        <tr className="border-b">
                                            <td className="py-2 pr-4 font-medium text-foreground">Google Gemini</td>
                                            <td className="py-2 pr-4">LLM fallback</td>
                                            <td className="py-2">Same anonymous fitness metrics as Groq</td>
                                        </tr>
                                        <tr>
                                            <td className="py-2 pr-4 font-medium text-foreground">Vercel</td>
                                            <td className="py-2 pr-4">Frontend hosting & AI gateway</td>
                                            <td className="py-2">Standard request metadata</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            <p className="mt-2">LLM prompts sent to Groq / Google Gemini contain only numerical
                            fitness metrics. No names, email addresses, or personally identifiable information
                            are included in AI prompts.</p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold mb-3">5. Data Retention</h2>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2">
                            <li>Account data is retained until you delete your account.</li>
                            <li>Cached fitness data is refreshed on each session and not persisted beyond your Supabase account.</li>
                            <li>Generated workouts are stored in your Intervals.icu calendar (governed by Intervals.icu's own privacy policy).</li>
                            <li>Server logs are retained for up to 30 days for debugging purposes, then purged.</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold mb-3">6. Data Security</h2>
                        <p className="text-muted-foreground">
                            All data in transit is encrypted using TLS. Supabase enforces row-level security so
                            users can only access their own data. Your Intervals.icu API key is stored encrypted
                            and never logged or exposed to the client after initial setup.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold mb-3">7. Your Rights</h2>
                        <p className="text-muted-foreground">
                            You may request access to, correction of, or deletion of your personal data at any
                            time by contacting us at the email below. To delete your account and all associated
                            data, send a deletion request to the contact email.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold mb-3">8. Cookies</h2>
                        <p className="text-muted-foreground">
                            We use only functional cookies required for authentication (Supabase session token).
                            We do not use advertising or tracking cookies.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold mb-3">9. Changes to This Policy</h2>
                        <p className="text-muted-foreground">
                            We may update this policy periodically. Material changes will be announced within
                            the app. Continued use of the service after changes constitutes acceptance of the
                            updated policy.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-lg font-semibold mb-3">10. Contact</h2>
                        <p className="text-muted-foreground">
                            For privacy-related questions or data requests, please contact:{" "}
                            <a
                                href="mailto:pjy8412@gmail.com"
                                className="text-primary underline underline-offset-2"
                            >
                                pjy8412@gmail.com
                            </a>
                        </p>
                    </section>

                </div>

                <div className="mt-12 pt-6 border-t">
                    <a
                        href="/"
                        className="text-sm text-muted-foreground hover:text-primary transition-colors"
                    >
                        ← Back to AI Cycling Coach
                    </a>
                </div>
            </div>
        </div>
    );
}
