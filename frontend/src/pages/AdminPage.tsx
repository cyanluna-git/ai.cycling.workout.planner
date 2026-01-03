/**
 * Admin Dashboard Page
 * 
 * Protected page for admin users to view statistics, API logs, and system monitoring.
 */

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

// Types
interface OverviewStats {
    total_users: number;
    workouts_today: number;
    api_calls_today: number;
    api_calls_week: number;
    avg_response_time_ms: number;
}

interface ApiLog {
    id: string;
    user_id: string | null;
    method: string;
    path: string;
    status_code: number | null;
    response_time_ms: number | null;
    ip_address: string | null;
    error_message: string | null;
    created_at: string;
}

interface AuditLog {
    id: string;
    event_type: string;
    user_id: string | null;
    details: Record<string, unknown>;
    ip_address: string | null;
    created_at: string;
}

interface AdminPageProps {
    onBack: () => void;
}

const API_BASE = import.meta.env.VITE_API_URL || '';

export function AdminPage({ onBack }: AdminPageProps) {
    const { session } = useAuth();
    const [activeTab, setActiveTab] = useState<'overview' | 'api-logs' | 'audit-logs'>('overview');

    // Overview stats
    const [stats, setStats] = useState<OverviewStats | null>(null);
    const [statsLoading, setStatsLoading] = useState(true);

    // API logs
    const [apiLogs, setApiLogs] = useState<ApiLog[]>([]);
    const [apiLogsLoading, setApiLogsLoading] = useState(false);
    const [apiLogsPage, setApiLogsPage] = useState(1);
    const [apiLogsTotal, setApiLogsTotal] = useState(0);

    // Audit logs
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
    const [auditLogsLoading, setAuditLogsLoading] = useState(false);
    const [auditLogsPage, setAuditLogsPage] = useState(1);
    const [auditLogsTotal, setAuditLogsTotal] = useState(0);

    // Weekly workout stats
    const [weeklyWorkouts, setWeeklyWorkouts] = useState<Record<string, number>>({});

    // User workout stats
    const [userStats, setUserStats] = useState<{ user_id: string; email: string; count: number }[]>([]);
    const [topUser, setTopUser] = useState<{ user_id: string; email: string; count: number } | null>(null);
    const [uniqueUsers, setUniqueUsers] = useState(0);

    const getHeaders = useCallback(() => ({
        'Authorization': `Bearer ${session?.access_token}`,
        'Content-Type': 'application/json',
    }), [session?.access_token]);

    // Fetch overview stats
    const fetchStats = useCallback(async () => {
        if (!session?.access_token) return;

        setStatsLoading(true);
        try {
            // Fetch overview stats
            const response = await fetch(`${API_BASE}/api/admin/stats/overview`, {
                headers: getHeaders(),
            });

            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }

            // Fetch weekly workout stats (with user stats)
            const workoutResponse = await fetch(`${API_BASE}/api/admin/stats/workouts?days=7`, {
                headers: getHeaders(),
            });

            if (workoutResponse.ok) {
                const workoutData = await workoutResponse.json();
                setWeeklyWorkouts(workoutData.daily_workouts || {});
                setUserStats(workoutData.user_stats || []);
                setTopUser(workoutData.top_user || null);
                setUniqueUsers(workoutData.unique_users || 0);
            }
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        } finally {
            setStatsLoading(false);
        }
    }, [session?.access_token, getHeaders]);

    // Fetch API logs
    const fetchApiLogs = useCallback(async (page: number = 1) => {
        if (!session?.access_token) return;

        setApiLogsLoading(true);
        try {
            const response = await fetch(`${API_BASE}/api/admin/api-logs?page=${page}&page_size=20`, {
                headers: getHeaders(),
            });

            if (response.ok) {
                const data = await response.json();
                setApiLogs(data.logs);
                setApiLogsTotal(data.total);
                setApiLogsPage(page);
            }
        } catch (error) {
            console.error('Failed to fetch API logs:', error);
        } finally {
            setApiLogsLoading(false);
        }
    }, [session?.access_token, getHeaders]);

    // Fetch Audit logs
    const fetchAuditLogs = useCallback(async (page: number = 1) => {
        if (!session?.access_token) return;

        setAuditLogsLoading(true);
        try {
            const response = await fetch(`${API_BASE}/api/admin/audit-logs?page=${page}&page_size=20`, {
                headers: getHeaders(),
            });

            if (response.ok) {
                const data = await response.json();
                setAuditLogs(data.logs);
                setAuditLogsTotal(data.total);
                setAuditLogsPage(page);
            }
        } catch (error) {
            console.error('Failed to fetch audit logs:', error);
        } finally {
            setAuditLogsLoading(false);
        }
    }, [session?.access_token, getHeaders]);

    // Initial load
    useEffect(() => {
        fetchStats();
    }, [fetchStats]);

    // Load data when tab changes
    useEffect(() => {
        if (activeTab === 'api-logs' && apiLogs.length === 0) {
            fetchApiLogs(1);
        } else if (activeTab === 'audit-logs' && auditLogs.length === 0) {
            fetchAuditLogs(1);
        }
    }, [activeTab, apiLogs.length, auditLogs.length, fetchApiLogs, fetchAuditLogs]);

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const getStatusColor = (status: number | null) => {
        if (!status) return 'text-gray-500';
        if (status >= 200 && status < 300) return 'text-green-600';
        if (status >= 400 && status < 500) return 'text-yellow-600';
        if (status >= 500) return 'text-red-600';
        return 'text-gray-500';
    };

    const getMethodColor = (method: string) => {
        switch (method) {
            case 'GET': return 'bg-blue-100 text-blue-700';
            case 'POST': return 'bg-green-100 text-green-700';
            case 'PUT': return 'bg-yellow-100 text-yellow-700';
            case 'PATCH': return 'bg-orange-100 text-orange-700';
            case 'DELETE': return 'bg-red-100 text-red-700';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b">
                <div className="container mx-auto px-4 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" onClick={onBack}>
                            ← 뒤로
                        </Button>
                        <div>
                            <h1 className="text-2xl font-bold">🔧 Admin Dashboard</h1>
                            <p className="text-muted-foreground text-sm">시스템 모니터링 및 통계</p>
                        </div>
                    </div>
                    <Button variant="outline" onClick={fetchStats}>
                        🔄 새로고침
                    </Button>
                </div>
            </header>

            {/* Tabs */}
            <div className="container mx-auto px-4 py-4">
                <div className="flex gap-2 mb-6">
                    <Button
                        variant={activeTab === 'overview' ? 'default' : 'outline'}
                        onClick={() => setActiveTab('overview')}
                    >
                        📊 개요
                    </Button>
                    <Button
                        variant={activeTab === 'api-logs' ? 'default' : 'outline'}
                        onClick={() => setActiveTab('api-logs')}
                    >
                        📝 API 로그
                    </Button>
                    <Button
                        variant={activeTab === 'audit-logs' ? 'default' : 'outline'}
                        onClick={() => setActiveTab('audit-logs')}
                    >
                        📋 Audit 로그
                    </Button>
                </div>

                {/* Overview Tab */}
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        {/* Stats Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            <Card>
                                <CardHeader className="pb-2">
                                    <CardDescription>총 사용자</CardDescription>
                                    <CardTitle className="text-3xl">
                                        {statsLoading ? '...' : stats?.total_users ?? 0}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">가입된 전체 사용자 수</p>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="pb-2">
                                    <CardDescription>오늘 워크아웃</CardDescription>
                                    <CardTitle className="text-3xl text-green-600">
                                        {statsLoading ? '...' : stats?.workouts_today ?? 0}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">오늘 생성된 워크아웃</p>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="pb-2">
                                    <CardDescription>오늘 API 호출</CardDescription>
                                    <CardTitle className="text-3xl text-blue-600">
                                        {statsLoading ? '...' : stats?.api_calls_today ?? 0}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">
                                        이번 주: {stats?.api_calls_week ?? 0}
                                    </p>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="pb-2">
                                    <CardDescription>평균 응답시간</CardDescription>
                                    <CardTitle className="text-3xl text-purple-600">
                                        {statsLoading ? '...' : `${stats?.avg_response_time_ms ?? 0}ms`}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">오늘 API 평균</p>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Weekly Workout Stats Table */}
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-lg">📅 주간 워크아웃 생성</CardTitle>
                                <CardDescription>최근 7일 일별 생성 개수</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {statsLoading ? (
                                    <div className="text-center py-4 text-muted-foreground">로딩 중...</div>
                                ) : (
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="border-b">
                                                    {(() => {
                                                        const days = [];
                                                        for (let i = 6; i >= 0; i--) {
                                                            const date = new Date();
                                                            date.setDate(date.getDate() - i);
                                                            const dateStr = date.toISOString().split('T')[0];
                                                            const dayName = date.toLocaleDateString('ko-KR', { weekday: 'short' });
                                                            days.push(
                                                                <th key={dateStr} className="py-2 px-3 text-center">
                                                                    <div className="text-xs text-muted-foreground">{dayName}</div>
                                                                    <div className="text-xs">{dateStr.slice(5)}</div>
                                                                </th>
                                                            );
                                                        }
                                                        return days;
                                                    })()}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr>
                                                    {(() => {
                                                        const cells = [];
                                                        for (let i = 6; i >= 0; i--) {
                                                            const date = new Date();
                                                            date.setDate(date.getDate() - i);
                                                            const dateStr = date.toISOString().split('T')[0];
                                                            const count = weeklyWorkouts[dateStr] || 0;
                                                            cells.push(
                                                                <td key={dateStr} className="py-3 px-3 text-center">
                                                                    <span className={`text-lg font-bold ${count > 0 ? 'text-green-600' : 'text-muted-foreground'}`}>
                                                                        {count}
                                                                    </span>
                                                                </td>
                                                            );
                                                        }
                                                        return cells;
                                                    })()}
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* User Workout Stats Card */}
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-lg">👤 사용자별 워크아웃 생성</CardTitle>
                                <CardDescription>최근 7일간 사용자별 생성 횟수 (총 {uniqueUsers}명)</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {statsLoading ? (
                                    <div className="text-center py-4 text-muted-foreground">로딩 중...</div>
                                ) : (
                                    <>
                                        {/* Top User Highlight */}
                                        {topUser && (
                                            <div className="mb-4 p-4 rounded-lg bg-gradient-to-r from-yellow-100 to-orange-100 dark:from-yellow-900/30 dark:to-orange-900/30 border border-yellow-200 dark:border-yellow-800">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-2xl">🏆</span>
                                                    <div>
                                                        <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">최다 생성 유저</p>
                                                        <p className="text-lg font-bold text-yellow-900 dark:text-yellow-100">
                                                            {topUser.email} - {topUser.count}회
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* User Stats Table */}
                                        {userStats.length > 0 ? (
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-sm">
                                                    <thead>
                                                        <tr className="border-b">
                                                            <th className="py-2 px-3 text-left">순위</th>
                                                            <th className="py-2 px-3 text-left">이메일</th>
                                                            <th className="py-2 px-3 text-right">생성 횟수</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {userStats.slice(0, 10).map((user, index) => (
                                                            <tr key={user.user_id} className="border-b hover:bg-muted/50">
                                                                <td className="py-2 px-3 text-muted-foreground">
                                                                    {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}`}
                                                                </td>
                                                                <td className="py-2 px-3 font-mono text-xs">
                                                                    {user.email}
                                                                </td>
                                                                <td className="py-2 px-3 text-right font-bold text-green-600">
                                                                    {user.count}회
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        ) : (
                                            <div className="text-center py-4 text-muted-foreground">
                                                최근 7일간 생성된 워크아웃이 없습니다.
                                            </div>
                                        )}
                                    </>
                                )}
                            </CardContent>
                        </Card>

                        {/* Quick Actions */}
                        <Card>
                            <CardHeader>
                                <CardTitle>빠른 액션</CardTitle>
                            </CardHeader>
                            <CardContent className="flex gap-4">
                                <Button variant="outline" onClick={() => setActiveTab('api-logs')}>
                                    API 로그 보기 →
                                </Button>
                                <Button variant="outline" onClick={() => setActiveTab('audit-logs')}>
                                    Audit 로그 보기 →
                                </Button>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* API Logs Tab */}
                {activeTab === 'api-logs' && (
                    <Card>
                        <CardHeader>
                            <CardTitle>API 요청 로그</CardTitle>
                            <CardDescription>
                                총 {apiLogsTotal}개 ({apiLogsPage} 페이지)
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {apiLogsLoading ? (
                                <div className="text-center py-8 text-muted-foreground">로딩 중...</div>
                            ) : (
                                <>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="border-b">
                                                    <th className="py-2 px-3 text-left">시간</th>
                                                    <th className="py-2 px-3 text-left">메소드</th>
                                                    <th className="py-2 px-3 text-left">경로</th>
                                                    <th className="py-2 px-3 text-left">상태</th>
                                                    <th className="py-2 px-3 text-left">응답시간</th>
                                                    <th className="py-2 px-3 text-left">IP</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {apiLogs.map((log) => (
                                                    <tr key={log.id} className="border-b hover:bg-muted/50">
                                                        <td className="py-2 px-3 text-muted-foreground">
                                                            {formatDate(log.created_at)}
                                                        </td>
                                                        <td className="py-2 px-3">
                                                            <span className={`px-2 py-1 rounded text-xs font-medium ${getMethodColor(log.method)}`}>
                                                                {log.method}
                                                            </span>
                                                        </td>
                                                        <td className="py-2 px-3 font-mono text-xs max-w-[300px] truncate">
                                                            {log.path}
                                                        </td>
                                                        <td className={`py-2 px-3 font-medium ${getStatusColor(log.status_code)}`}>
                                                            {log.status_code ?? '-'}
                                                        </td>
                                                        <td className="py-2 px-3 text-muted-foreground">
                                                            {log.response_time_ms ? `${log.response_time_ms}ms` : '-'}
                                                        </td>
                                                        <td className="py-2 px-3 text-muted-foreground font-mono text-xs">
                                                            {log.ip_address ?? '-'}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>

                                    {/* Pagination */}
                                    <div className="flex justify-center gap-2 mt-4">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            disabled={apiLogsPage <= 1}
                                            onClick={() => fetchApiLogs(apiLogsPage - 1)}
                                        >
                                            ← 이전
                                        </Button>
                                        <span className="flex items-center px-4 text-sm text-muted-foreground">
                                            {apiLogsPage} / {Math.ceil(apiLogsTotal / 20)}
                                        </span>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            disabled={apiLogsPage * 20 >= apiLogsTotal}
                                            onClick={() => fetchApiLogs(apiLogsPage + 1)}
                                        >
                                            다음 →
                                        </Button>
                                    </div>
                                </>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Audit Logs Tab */}
                {activeTab === 'audit-logs' && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Audit 로그</CardTitle>
                            <CardDescription>
                                총 {auditLogsTotal}개 ({auditLogsPage} 페이지)
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {auditLogsLoading ? (
                                <div className="text-center py-8 text-muted-foreground">로딩 중...</div>
                            ) : (
                                <>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="border-b">
                                                    <th className="py-2 px-3 text-left">시간</th>
                                                    <th className="py-2 px-3 text-left">이벤트 타입</th>
                                                    <th className="py-2 px-3 text-left">사용자 ID</th>
                                                    <th className="py-2 px-3 text-left">상세</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {auditLogs.map((log) => (
                                                    <tr key={log.id} className="border-b hover:bg-muted/50">
                                                        <td className="py-2 px-3 text-muted-foreground">
                                                            {formatDate(log.created_at)}
                                                        </td>
                                                        <td className="py-2 px-3">
                                                            <span className="px-2 py-1 rounded text-xs font-medium bg-primary/10 text-primary">
                                                                {log.event_type}
                                                            </span>
                                                        </td>
                                                        <td className="py-2 px-3 font-mono text-xs text-muted-foreground">
                                                            {log.user_id ? log.user_id.slice(0, 8) + '...' : '-'}
                                                        </td>
                                                        <td className="py-2 px-3 text-muted-foreground max-w-[300px] truncate">
                                                            {JSON.stringify(log.details).slice(0, 100)}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>

                                    {/* Pagination */}
                                    <div className="flex justify-center gap-2 mt-4">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            disabled={auditLogsPage <= 1}
                                            onClick={() => fetchAuditLogs(auditLogsPage - 1)}
                                        >
                                            ← 이전
                                        </Button>
                                        <span className="flex items-center px-4 text-sm text-muted-foreground">
                                            {auditLogsPage} / {Math.ceil(auditLogsTotal / 20)}
                                        </span>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            disabled={auditLogsPage * 20 >= auditLogsTotal}
                                            onClick={() => fetchAuditLogs(auditLogsPage + 1)}
                                        >
                                            다음 →
                                        </Button>
                                    </div>
                                </>
                            )}
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
}
