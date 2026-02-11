import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { supabase } from '@/lib/supabase'

interface ResetPasswordPageProps {
    onComplete: () => void;
}

export function ResetPasswordPage({ onComplete: _onComplete }: ResetPasswordPageProps) {
    const { t } = useTranslation()
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState(false)
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError(null)
        if (password !== confirmPassword) { setError(t('resetPassword.mismatch')); return }
        if (password.length < 6) { setError(t('resetPassword.tooShort')); return }
        setLoading(true)
        try {
            const { error } = await supabase.auth.updateUser({ password })
            if (error) { setError(error.message) } else { setSuccess(true) }
        } catch (err) { setError(t('common.error')) } finally { setLoading(false) }
    }

    if (success) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center p-4">
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center">
                        <CardTitle className="text-2xl">{t('resetPassword.completeTitle')}</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4 text-center">
                        <p className="text-muted-foreground">{t('resetPassword.completeMessage')}</p>
                        <Button onClick={() => { window.location.hash = ''; window.location.href = '/'; }}>
                            {t('resetPassword.goHome')}
                        </Button>
                    </CardContent>
                </Card>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center">
                    <CardTitle className="text-2xl">{t('resetPassword.title')}</CardTitle>
                    <p className="text-muted-foreground text-sm">{t('resetPassword.subtitle')}</p>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="password">{t('resetPassword.newPassword')}</Label>
                            <Input id="password" type="password" placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="confirmPassword">{t('resetPassword.confirmPassword')}</Label>
                            <Input id="confirmPassword" type="password" placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={6} />
                        </div>
                        {error && <div className="text-destructive text-sm text-center bg-destructive/10 p-2 rounded">\u274c {error}</div>}
                        <Button type="submit" className="w-full" disabled={loading}>
                            {loading ? t('common.processing') : t('resetPassword.changePassword')}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    )
}
