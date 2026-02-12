/**
 * Admin Dashboard Page
 * 
 * Protected page for admin users to view statistics, API logs, and system monitoring.
 */

import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CURRENT_VERSION } from '@/lib/version';

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

interface DeploymentInfo {
    frontend_version: string;
    frontend_build_time: string;
    backend_version: string;
    backend_git_commit: string;
    backend_git_commit_date: string;
    backend_started_at: string;
}

interface AdminPageProps {
    onBack: () => void;
}

const API_BASE = import.meta.env.VITE_API_URL || '';

export function AdminPage({ onBack }: AdminPageProps) {
    const { session } = useAuth();
    const { t } = useTranslation();
    const [activeTab, setActiveTab] = useState<'overview' | 'api-logs' | 'audit-logs'>('overview');

    // Overview stats
    const [stats, setStats] = useState<OverviewStats | null>(null);
    const [deployInfo, setDeployInfo] = useState<DeploymentInfo | null>(null);
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
    const [userStatsDays, setUserStatsDays] = useState<1 | 7 | 30>(7);

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
            const workoutResponse = await fetch(`${API_BASE}/api/admin/stats/workouts?days=${userStatsDays}`, {
                headers: getHeaders(),
            });

            if (workoutResponse.ok) {
                const workoutData = await workoutResponse.json();
                setWeeklyWorkouts(workoutData.daily_workouts || {});
                setUserStats(workoutData.user_stats || []);
                setTopUser(workoutData.top_user || null);
                setUniqueUsers(workoutData.unique_users || 0);
            }

            // Fetch backend health info
            const healthResponse = await fetch(`${API_BASE}/api/health`);
            if (healthResponse.ok) {
                const healthData = await healthResponse.json();
                setDeployInfo({
                    frontend_version: CURRENT_VERSION,
                    frontend_build_time: __BUILD_TIME__,
                    backend_version: healthData.version || 'unknown',
                    backend_git_commit: healthData.git_commit || 'unknown',
                    backend_git_commit_date: healthData.git_commit_date || 'unknown',
                    backend_started_at: healthData.started_at || 'unknown',
                });
            }
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        } finally {
            setStatsLoading(false);
        }
    }, [session?.access_token, getHeaders, userStatsDays]);

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
                            {t("admin.back")}
                        </Button>
                        <div>
                            <h1 className="text-2xl font-bold">🔧 Admin Dashboard</h1>
                            <p className="text-muted-foreground text-sm">{t('admin.subtitle')}</p>
                        </div>
                    </div>
                    <Button variant="outline" onClick={fetchStats}>
                        {t("admin.refresh")}
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
                        {t("admin.overviewTab")}
                    </Button>
                    <Button
                        variant={activeTab === 'api-logs' ? 'default' : 'outline'}
                        onClick={() => setActiveTab('api-logs')}
                    >
                        {t("admin.apiLogsTab")}
                    </Button>
                    <Button
                        variant={activeTab === 'audit-logs' ? 'default' : 'outline'}
                        onClick={() => setActiveTab('audit-logs')}
                    >
                        {t("admin.auditLogsTab")}
                    </Button>
                </div>

                {/* Overview Tab */}
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        {/* Stats Cards */}
                        {/* Deployment Info */}
                        {deployInfo && (
                            <Card>
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-lg">🚀 Deployment Info</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                        <div>
                                            <h4 className="font-semibold mb-2">Frontend</h4>
                                            <div className="space-y-1 text-muted-foreground">
                                                <p>Version: <span className="font-mono text-foreground">{deployInfo.frontend_version}</span></p>
                                                <p>Built: <span className="font-mono text-foreground">{new Date(deployInfo.frontend_build_time).toLocaleString('ko-KR')}</span></p>
                                            </div>
                                        </div>
                                        <div>
                                            <h4 className="font-semibold mb-2">Backend</h4>
                                            <div className="space-y-1 text-muted-foreground">
                                                <p>Version: <span className="font-mono text-foreground">{deployInfo.backend_version}</span></p>
                                                <p>Commit: <span className="font-mono text-foreground">{deployInfo.backend_git_commit}</span></p>
                                                <p>Commit Date: <span className="font-mono text-foreground">{new Date(deployInfo.backend_git_commit_date).toLocaleString('ko-KR')}</span></p>
                                                <p>Started: <span className="font-mono text-foreground">{new Date(deployInfo.backend_started_at).toLocaleString('ko-KR')}</span></p>
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            <Card>
                                <CardHeader className="pb-2">
                                    <CardDescription>{t('admin.totalUsers')}</CardDescription>
                                    <CardTitle className="text-3xl">
                                        {statsLoading ? '...' : stats?.total_users ?? 0}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">{t('admin.totalUsersDesc')}</p>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="pb-2">
                                    <CardDescription>{t('admin.todayWorkouts')}</CardDescription>
                                    <CardTitle className="text-3xl text-green-600">
                                        {statsLoading ? '...' : stats?.workouts_today ?? 0}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">{t('admin.todayWorkoutsDesc')}</p>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="pb-2">
                                    <CardDescription>{t('admin.todayApiCalls')}</CardDescription>
                                    <CardTitle className="text-3xl text-blue-600">
                                        {statsLoading ? '...' : stats?.api_calls_today ?? 0}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">
                                        {t('admin.thisWeek', { count: stats?.api_calls_week ?? 0 })}
                                    </p>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="pb-2">
                                    <CardDescription>{t('admin.avgResponseTime')}</CardDescription>
                                    <CardTitle className="text-3xl text-purple-600">
                                        {statsLoading ? '...' : `${stats?.avg_response_time_ms ?? 0}ms`}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">{t('admin.avgResponseTimeDesc')}</p>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Weekly Workout Stats Table */}
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-lg">{t('admin.weeklyWorkoutsTitle')}</CardTitle>
                                <CardDescription>{t('admin.weeklyWorkoutsDesc')}</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {statsLoading ? (
                                    <div className="text-center py-4 text-muted-foreground">{t('common.loading')}</div>
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
                                <div className="flex justify-between items-start">
                                    <div>
                                        <CardTitle className="text-lg">{t('admin.userStatsTitle')}</CardTitle>
                                        <CardDescription>
                                            {userStatsDays === 1 ? t('admin.userStatsDescToday', { count: uniqueUsers }) : userStatsDays === 7 ? t('admin.userStatsDescWeek', { count: uniqueUsers }) : t('admin.userStatsDescMonth', { count: uniqueUsers })}
                                        </CardDescription>
                                    </div>
                                    <div className="flex gap-1">
                                        <Button
                                            variant={userStatsDays === 1 ? 'default' : 'outline'}
                                            size="sm"
                                            onClick={() => setUserStatsDays(1)}
                                        >{t("admin.daily")}</Button>
                                        <Button
                                            variant={userStatsDays === 7 ? 'default' : 'outline'}
                                            size="sm"
                                            onClick={() => setUserStatsDays(7)}
                                        >{t("admin.weekly")}</Button>
                                        <Button
                                            variant={userStatsDays === 30 ? 'default' : 'outline'}
                                            size="sm"
                                            onClick={() => setUserStatsDays(30)}
                                        >{t("admin.monthly")}</Button>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                {statsLoading ? (
                                    <div className="text-center py-4 text-muted-foreground">{t('common.loading')}</div>
                                ) : (
                                    <>
                                        {/* Top User Highlight */}
                                        {topUser && (
                                            <div className="mb-4 p-4 rounded-lg bg-gradient-to-r from-yellow-100 to-orange-100 dark:from-yellow-900/30 dark:to-orange-900/30 border border-yellow-200 dark:border-yellow-800">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-2xl">🏆</span>
                                                    <div>
                                                        <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">{t('admin.topUser')}</p>
                                                        <p className="text-lg font-bold text-yellow-900 dark:text-yellow-100">
                                                            {topUser.email} - {topUser.count}{t("common.times")}
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
                                                            <th className="py-2 px-3 text-left">{t('admin.rank')}</th>
                                                            <th className="py-2 px-3 text-left">{t('common.email')}</th>
                                                            <th className="py-2 px-3 text-right">{t('admin.creationCount')}</th>
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
                                                                    {user.count}{t("common.times")}
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        ) : (
                                            <div className="text-center py-4 text-muted-foreground">
                                                {t("admin.noWorkoutsRecent")}
                                            </div>
                                        )}
                                    </>
                                )}
                            </CardContent>
                        </Card>

                        {/* Quick Actions */}
                        <Card>
                            <CardHeader>
                                <CardTitle>{t('admin.quickActions')}</CardTitle>
                            </CardHeader>
                            <CardContent className="flex gap-4">
                                <Button variant="outline" onClick={() => setActiveTab('api-logs')}>
                                    {t("admin.viewApiLogs")}
                                </Button>
                                <Button variant="outline" onClick={() => setActiveTab('audit-logs')}>
                                    {t("admin.viewAuditLogs")}
                                </Button>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* API Logs Tab */}
                {activeTab === 'api-logs' && (
                    <Card>
                        <CardHeader>
                            <CardTitle>{t('admin.apiLogsTitle')}</CardTitle>
                            <CardDescription>
                                {t("admin.totalCount", { total: apiLogsTotal, page: apiLogsPage })}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {apiLogsLoading ? (
                                <div className="text-center py-8 text-muted-foreground">{t('common.loading')}</div>
                            ) : (
                                <>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="border-b">
                                                    <th className="py-2 px-3 text-left">{t('admin.time')}</th>
                                                    <th className="py-2 px-3 text-left">{t('admin.method')}</th>
                                                    <th className="py-2 px-3 text-left">{t('admin.path')}</th>
                                                    <th className="py-2 px-3 text-left">{t('admin.status')}</th>
                                                    <th className="py-2 px-3 text-left">{t('admin.responseTime')}</th>
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
                                            {t("admin.prevPage")}
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
                                            {t("admin.nextPage")}
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
                            <CardTitle>{t('admin.auditLogsTitle')}</CardTitle>
                            <CardDescription>
                                {t("admin.totalCount", { total: auditLogsTotal, page: auditLogsPage })}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {auditLogsLoading ? (
                                <div className="text-center py-8 text-muted-foreground">{t('common.loading')}</div>
                            ) : (
                                <>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="border-b">
                                                    <th className="py-2 px-3 text-left">{t('admin.time')}</th>
                                                    <th className="py-2 px-3 text-left">{t('admin.eventType')}</th>
                                                    <th className="py-2 px-3 text-left">{t('admin.userId')}</th>
                                                    <th className="py-2 px-3 text-left">{t('admin.details')}</th>
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
                                            {t("admin.prevPage")}
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
                                            {t("admin.nextPage")}
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
