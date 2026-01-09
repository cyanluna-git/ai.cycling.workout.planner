import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/contexts/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL || ''

interface Settings {
    ftp: number
    max_hr: number
    lthr: number
    training_goal: string
    exclude_barcode_workouts?: boolean
}

interface ApiKeysCheck {
    intervals_configured: boolean
}

export function SettingsPage({ onBack }: { onBack: () => void }) {
    const { session, signOut } = useAuth()
    const [settings, setSettings] = useState<Settings>({
        ftp: 200,
        max_hr: 190,
        lthr: 170,
        training_goal: '지구력 강화',
        exclude_barcode_workouts: false,
    })
    const [apiKeys, setApiKeys] = useState({
        intervals_api_key: '',
        athlete_id: '',
    })
    const [apiKeysCheck, setApiKeysCheck] = useState<ApiKeysCheck | null>(null)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState<string | null>(null)

    useEffect(() => {
        if (session?.access_token) {
            fetchSettings()
            checkApiKeys()
        }
    }, [session])

    const fetchSettings = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/settings`, {
                headers: { Authorization: `Bearer ${session?.access_token}` },
            })
            if (res.ok) {
                const data = await res.json()
                setSettings(data.settings)
            }
        } catch (e) {
            console.error('Failed to fetch settings', e)
        }
    }

    const checkApiKeys = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/settings/api-keys/check`, {
                headers: { Authorization: `Bearer ${session?.access_token}` },
            })
            if (res.ok) {
                setApiKeysCheck(await res.json())
            }
        } catch (e) {
            console.error('Failed to check API keys', e)
        }
    }

    const saveSettings = async () => {
        setSaving(true)
        setMessage(null)
        try {
            const res = await fetch(`${API_BASE}/api/settings`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${session?.access_token}`,
                },
                body: JSON.stringify(settings),
            })
            if (res.ok) {
                setMessage('✅ 설정이 저장되었습니다')
            }
        } catch (e) {
            setMessage('❌ 저장 실패')
        } finally {
            setSaving(false)
        }
    }

    const saveApiKeys = async () => {
        setSaving(true)
        setMessage(null)
        try {
            const res = await fetch(`${API_BASE}/api/settings/api-keys`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${session?.access_token}`,
                },
                body: JSON.stringify(apiKeys),
            })
            if (res.ok) {
                setMessage('✅ API 키가 저장되었습니다')
                checkApiKeys()
                setApiKeys({ ...apiKeys, intervals_api_key: '' })
            }
        } catch (e) {
            setMessage('❌ 저장 실패')
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="min-h-screen bg-background p-4">
            <div className="container mx-auto max-w-2xl space-y-6">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <Button variant="ghost" onClick={onBack}>
                        ← 돌아가기
                    </Button>
                    <Button variant="outline" onClick={signOut}>
                        로그아웃
                    </Button>
                </div>

                {message && (
                    <div className="p-3 rounded bg-muted text-center">{message}</div>
                )}

                {/* Training Goal Settings */}
                <Card>
                    <CardHeader>
                        <CardTitle>🎯 훈련 목표</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-sm text-muted-foreground">
                            FTP, 최대 심박수, 역치 심박수는 Intervals.icu에서 자동으로 가져옵니다.
                        </p>
                        <div className="space-y-2">
                            <Label>훈련 목표</Label>
                            <Input
                                value={settings.training_goal}
                                onChange={(e) =>
                                    setSettings({ ...settings, training_goal: e.target.value })
                                }
                                placeholder="예: 지구력 강화, 스프린트 파워 향상"
                            />
                        </div>
                        <div className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                id="exclude_barcode"
                                checked={settings.exclude_barcode_workouts ?? false}
                                onChange={(e) =>
                                    setSettings({ ...settings, exclude_barcode_workouts: e.target.checked })
                                }
                                className="h-4 w-4 rounded border-gray-300"
                            />
                            <div>
                                <label htmlFor="exclude_barcode" className="text-sm font-medium cursor-pointer">
                                    바코드형 인터벌 워크아웃 제외 (40/20, 30/30 등)
                                </label>
                                <p className="text-xs text-muted-foreground">
                                    ERG 반응이 느린 스마트 롤러 등에 권장
                                </p>
                            </div>
                        </div>
                        <Button onClick={saveSettings} disabled={saving}>
                            {saving ? '저장 중...' : '목표 저장'}
                        </Button>
                    </CardContent>
                </Card>

                {/* API Keys */}
                <Card>
                    <CardHeader>
                        <CardTitle>🔑 Intervals.icu 연동</CardTitle>
                        {apiKeysCheck && (
                            <div className="text-sm text-muted-foreground">
                                연동 상태: {apiKeysCheck.intervals_configured ? '✅ 완료' : '❌ 미설정'}
                            </div>
                        )}
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Guide Section */}
                        <div className="p-4 rounded-lg bg-muted/50 border border-border">
                            <h4 className="font-medium mb-2">📌 API 키 발급 방법</h4>
                            <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
                                <li>
                                    <a
                                        href="https://intervals.icu/settings"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-primary hover:underline"
                                    >
                                        Intervals.icu Settings
                                    </a>
                                    {' '}페이지로 이동
                                </li>
                                <li>"Developer" 탭 클릭</li>
                                <li>"API Key" 섹션에서 키 복사</li>
                                <li>페이지 상단의 Athlete ID도 함께 확인 (예: i123456)</li>
                            </ol>
                        </div>

                        <div className="space-y-2">
                            <Label>Intervals.icu API Key</Label>
                            <Input
                                type="password"
                                placeholder={apiKeysCheck?.intervals_configured ? '••••••••' : 'API 키 입력'}
                                value={apiKeys.intervals_api_key}
                                onChange={(e) =>
                                    setApiKeys({ ...apiKeys, intervals_api_key: e.target.value })
                                }
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Athlete ID</Label>
                            <Input
                                placeholder="예: i123456"
                                value={apiKeys.athlete_id}
                                onChange={(e) =>
                                    setApiKeys({ ...apiKeys, athlete_id: e.target.value })
                                }
                            />
                        </div>
                        <Button onClick={saveApiKeys} disabled={saving}>
                            {saving ? '저장 중...' : 'API 키 저장'}
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
