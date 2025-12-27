import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { supabase } from '@/lib/supabase'

interface ResetPasswordPageProps {
    onComplete: () => void;
}

export function ResetPasswordPage({ onComplete: _onComplete }: ResetPasswordPageProps) {
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState(false)
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError(null)

        if (password !== confirmPassword) {
            setError('비밀번호가 일치하지 않습니다')
            return
        }

        if (password.length < 6) {
            setError('비밀번호는 최소 6자 이상이어야 합니다')
            return
        }

        setLoading(true)

        try {
            const { error } = await supabase.auth.updateUser({ password })

            if (error) {
                setError(error.message)
            } else {
                setSuccess(true)
            }
        } catch (err) {
            setError('오류가 발생했습니다')
        } finally {
            setLoading(false)
        }
    }

    if (success) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center p-4">
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center">
                        <CardTitle className="text-2xl">✅ 비밀번호 변경 완료!</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4 text-center">
                        <p className="text-muted-foreground">
                            새 비밀번호로 로그인할 수 있습니다.
                        </p>
                        <Button onClick={() => {
                            // Clear URL hash and go home
                            window.location.hash = '';
                            window.location.href = '/';
                        }}>
                            홈으로 이동
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
                    <CardTitle className="text-2xl">🔑 새 비밀번호 설정</CardTitle>
                    <p className="text-muted-foreground text-sm">
                        새로운 비밀번호를 입력해주세요
                    </p>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="password">새 비밀번호</Label>
                            <Input
                                id="password"
                                type="password"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                minLength={6}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="confirmPassword">비밀번호 확인</Label>
                            <Input
                                id="confirmPassword"
                                type="password"
                                placeholder="••••••••"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                                minLength={6}
                            />
                        </div>

                        {error && (
                            <div className="text-destructive text-sm text-center bg-destructive/10 p-2 rounded">
                                ❌ {error}
                            </div>
                        )}

                        <Button type="submit" className="w-full" disabled={loading}>
                            {loading ? '처리 중...' : '비밀번호 변경'}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    )
}
