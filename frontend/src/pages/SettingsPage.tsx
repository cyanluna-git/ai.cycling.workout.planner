import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import { useAuth } from '@/contexts/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL || ''

interface Settings {
    ftp: number
    max_hr: number
    lthr: number
    training_goal: string
}

interface ApiKeysCheck {
    intervals_configured: boolean
    llm_configured: boolean
    llm_provider: string
}

export function SettingsPage({ onBack }: { onBack: () => void }) {
    const { session, signOut } = useAuth()
    const [settings, setSettings] = useState<Settings>({
        ftp: 200,
        max_hr: 190,
        lthr: 170,
        training_goal: '지구력 강화',
    })
    const [apiKeys, setApiKeys] = useState({
        intervals_api_key: '',
        athlete_id: '',
        llm_provider: 'gemini',
        llm_api_key: '',
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
                setApiKeys({ ...apiKeys, intervals_api_key: '', llm_api_key: '' })
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

                {/* Profile Settings */}
                <Card>
                    <CardHeader>
                        <CardTitle>⚙️ 프로필 설정</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-3 gap-4">
                            <div className="space-y-2">
                                <Label>FTP (W)</Label>
                                <Input
                                    type="number"
                                    value={settings.ftp}
                                    onChange={(e) =>
                                        setSettings({ ...settings, ftp: parseInt(e.target.value) })
                                    }
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>최대 심박수</Label>
                                <Input
                                    type="number"
                                    value={settings.max_hr}
                                    onChange={(e) =>
                                        setSettings({ ...settings, max_hr: parseInt(e.target.value) })
                                    }
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>젖산역치 심박수</Label>
                                <Input
                                    type="number"
                                    value={settings.lthr}
                                    onChange={(e) =>
                                        setSettings({ ...settings, lthr: parseInt(e.target.value) })
                                    }
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>훈련 목표</Label>
                            <Input
                                value={settings.training_goal}
                                onChange={(e) =>
                                    setSettings({ ...settings, training_goal: e.target.value })
                                }
                            />
                        </div>
                        <Button onClick={saveSettings} disabled={saving}>
                            {saving ? '저장 중...' : '프로필 저장'}
                        </Button>
                    </CardContent>
                </Card>

                {/* API Keys */}
                <Card>
                    <CardHeader>
                        <CardTitle>🔑 API 키 설정</CardTitle>
                        {apiKeysCheck && (
                            <div className="text-sm text-muted-foreground">
                                Intervals.icu: {apiKeysCheck.intervals_configured ? '✅' : '❌'} |
                                LLM: {apiKeysCheck.llm_configured ? '✅' : '❌'}
                            </div>
                        )}
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label>Intervals.icu API Key</Label>
                            <Input
                                type="password"
                                placeholder={apiKeysCheck?.intervals_configured ? '••••••••' : '입력 필요'}
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
                        <div className="space-y-2">
                            <Label>LLM Provider</Label>
                            <Select
                                value={apiKeys.llm_provider}
                                onValueChange={(v) => setApiKeys({ ...apiKeys, llm_provider: v })}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="gemini">Gemini</SelectItem>
                                    <SelectItem value="openai">OpenAI (GPT)</SelectItem>
                                    <SelectItem value="anthropic">Anthropic (Claude)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>LLM API Key</Label>
                            <Input
                                type="password"
                                placeholder={apiKeysCheck?.llm_configured ? '••••••••' : '입력 필요'}
                                value={apiKeys.llm_api_key}
                                onChange={(e) =>
                                    setApiKeys({ ...apiKeys, llm_api_key: e.target.value })
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
