import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/contexts/AuthContext'

type AuthMode = 'login' | 'signup' | 'reset' | 'verify-sent' | 'reset-sent'

export function AuthPage() {
    const [mode, setMode] = useState<AuthMode>('login')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)

    const { signIn, signUp, signInWithGoogle, resetPassword } = useAuth()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError(null)
        setLoading(true)

        try {
            if (mode === 'login') {
                const { error } = await signIn(email, password)
                if (error) {
                    // Handle unconfirmed email
                    if (error.message.includes('Email not confirmed')) {
                        setError('이메일 인증이 필요합니다. 메일함을 확인해주세요.')
                    } else {
                        setError(error.message)
                    }
                }
            } else if (mode === 'signup') {
                const { error, needsConfirmation } = await signUp(email, password)
                if (error) {
                    setError(error.message)
                } else if (needsConfirmation) {
                    setMode('verify-sent')
                }
            } else if (mode === 'reset') {
                const { error } = await resetPassword(email)
                if (error) {
                    setError(error.message)
                } else {
                    setMode('reset-sent')
                }
            }
        } catch (err) {
            setError('오류가 발생했습니다')
        } finally {
            setLoading(false)
        }
    }

    const handleGoogleLogin = async () => {
        setError(null)
        const { error } = await signInWithGoogle()
        if (error) {
            setError(error.message)
        }
    }

    // Email verification sent screen
    if (mode === 'verify-sent') {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center p-4">
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center">
                        <CardTitle className="text-2xl">📧 인증 메일 발송 완료!</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4 text-center">
                        <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900 rounded-lg p-4">
                            <p className="text-green-800 dark:text-green-300">
                                <strong>{email}</strong>로 인증 메일을 발송했습니다.
                            </p>
                            <p className="text-sm text-green-700 dark:text-green-400 mt-2">
                                메일함을 확인하고 인증 링크를 클릭해주세요.
                            </p>
                        </div>
                        <p className="text-sm text-muted-foreground">
                            메일이 안 오셨나요? 스팸 폴더를 확인해보세요.
                        </p>
                        <Button
                            variant="outline"
                            onClick={() => {
                                setMode('login')
                                setEmail('')
                                setPassword('')
                            }}
                        >
                            로그인으로 돌아가기
                        </Button>
                    </CardContent>
                </Card>
            </div>
        )
    }

    // Password reset sent screen
    if (mode === 'reset-sent') {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center p-4">
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center">
                        <CardTitle className="text-2xl">🔑 비밀번호 재설정 메일 발송!</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4 text-center">
                        <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 rounded-lg p-4">
                            <p className="text-blue-800 dark:text-blue-300">
                                <strong>{email}</strong>로 비밀번호 재설정 링크를 발송했습니다.
                            </p>
                            <p className="text-sm text-blue-700 dark:text-blue-400 mt-2">
                                메일함을 확인하고 링크를 클릭해주세요.
                            </p>
                        </div>
                        <Button
                            variant="outline"
                            onClick={() => {
                                setMode('login')
                                setEmail('')
                            }}
                        >
                            로그인으로 돌아가기
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
                    <CardTitle className="text-2xl">🚴 AI Cycling Coach</CardTitle>
                    <p className="text-muted-foreground text-sm">
                        {mode === 'login' && '로그인하여 시작하세요'}
                        {mode === 'signup' && '새 계정을 만드세요'}
                        {mode === 'reset' && '비밀번호를 재설정하세요'}
                    </p>
                </CardHeader>
                <CardContent className="space-y-4">
                    {mode !== 'reset' && (
                        <>
                            {/* Google Login */}
                            <Button
                                variant="outline"
                                className="w-full"
                                onClick={handleGoogleLogin}
                            >
                                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                                    <path
                                        fill="currentColor"
                                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                    />
                                    <path
                                        fill="currentColor"
                                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                    />
                                    <path
                                        fill="currentColor"
                                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                    />
                                    <path
                                        fill="currentColor"
                                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                    />
                                </svg>
                                Google로 계속하기
                            </Button>

                            <div className="relative">
                                <div className="absolute inset-0 flex items-center">
                                    <span className="w-full border-t" />
                                </div>
                                <div className="relative flex justify-center text-xs uppercase">
                                    <span className="bg-background px-2 text-muted-foreground">
                                        또는
                                    </span>
                                </div>
                            </div>
                        </>
                    )}

                    {/* Email/Password Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="email">이메일</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="your@email.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>

                        {mode !== 'reset' && (
                            <div className="space-y-2">
                                <Label htmlFor="password">비밀번호</Label>
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
                        )}

                        {error && (
                            <div className="text-destructive text-sm text-center bg-destructive/10 p-2 rounded">
                                ❌ {error}
                            </div>
                        )}

                        <Button type="submit" className="w-full" disabled={loading}>
                            {loading ? '처리 중...' :
                                mode === 'login' ? '로그인' :
                                    mode === 'signup' ? '회원가입' :
                                        '비밀번호 재설정 링크 보내기'}
                        </Button>
                    </form>

                    {/* Mode Toggle */}
                    <div className="text-center text-sm space-y-2">
                        {mode === 'login' && (
                            <>
                                <div>
                                    <span className="text-muted-foreground">계정이 없으신가요?</span>{' '}
                                    <button
                                        type="button"
                                        className="text-primary hover:underline"
                                        onClick={() => {
                                            setMode('signup')
                                            setError(null)
                                        }}
                                    >
                                        회원가입
                                    </button>
                                </div>
                                <div>
                                    <button
                                        type="button"
                                        className="text-muted-foreground hover:text-primary hover:underline"
                                        onClick={() => {
                                            setMode('reset')
                                            setError(null)
                                        }}
                                    >
                                        비밀번호를 잊으셨나요?
                                    </button>
                                </div>
                            </>
                        )}
                        {mode === 'signup' && (
                            <div>
                                <span className="text-muted-foreground">이미 계정이 있으신가요?</span>{' '}
                                <button
                                    type="button"
                                    className="text-primary hover:underline"
                                    onClick={() => {
                                        setMode('login')
                                        setError(null)
                                    }}
                                >
                                    로그인
                                </button>
                            </div>
                        )}
                        {mode === 'reset' && (
                            <div>
                                <button
                                    type="button"
                                    className="text-primary hover:underline"
                                    onClick={() => {
                                        setMode('login')
                                        setError(null)
                                    }}
                                >
                                    로그인으로 돌아가기
                                </button>
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
