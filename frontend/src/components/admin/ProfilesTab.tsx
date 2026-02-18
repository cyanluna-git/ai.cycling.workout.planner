/**
 * ProfilesTab — Profile list with filters, search, pagination, and stats
 */

import { useState, useMemo, useCallback } from 'react';
import useSWR from 'swr';
import { useAuth } from '@/contexts/AuthContext';
import { createAuthFetcher, defaultSWRConfig } from '@/lib/swr';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ProfileDetailModal } from './ProfileDetailModal';

interface ProfileListItem {
    id: number;
    name: string;
    slug: string;
    category: string;
    subcategory: string | null;
    target_zone: string | null;
    duration_minutes: number | null;
    estimated_tss: number | null;
    estimated_if: number | null;
    difficulty: string | null;
    source: string | null;
    is_active: boolean | number;
}

interface ProfileStats {
    total: number;
    by_source: Record<string, number>;
    by_category: Record<string, number>;
    by_difficulty: Record<string, number>;
}

const PAGE_SIZE = 50;

export function ProfilesTab() {
    const { session } = useAuth();
    const [offset, setOffset] = useState(0);
    const [category, setCategory] = useState('');
    const [difficulty, setDifficulty] = useState('');
    const [source, setSource] = useState('');
    const [search, setSearch] = useState('');
    const [searchInput, setSearchInput] = useState('');
    const [selectedId, setSelectedId] = useState<number | null>(null);

    const authFetcher = useMemo(
        () => createAuthFetcher(session?.access_token),
        [session?.access_token]
    );

    // Build query string
    const queryParams = useMemo(() => {
        const params = new URLSearchParams();
        params.set('offset', String(offset));
        params.set('limit', String(PAGE_SIZE));
        if (category) params.set('category', category);
        if (difficulty) params.set('difficulty', difficulty);
        if (source) params.set('source', source);
        if (search) params.set('search', search);
        return params.toString();
    }, [offset, category, difficulty, source, search]);

    // Profiles list
    const { data: listData, isLoading, mutate: mutateList } = useSWR<{ items: ProfileListItem[]; total: number }>(
        session?.access_token ? `/api/profiles?${queryParams}` : null,
        authFetcher,
        defaultSWRConfig
    );

    // Stats
    const { data: statsData } = useSWR<ProfileStats>(
        session?.access_token ? '/api/profiles/stats' : null,
        authFetcher,
        defaultSWRConfig
    );

    const items = listData?.items || [];
    const total = listData?.total || 0;
    const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
    const totalPages = Math.ceil(total / PAGE_SIZE);

    const handleSearch = useCallback(() => {
        setSearch(searchInput);
        setOffset(0);
    }, [searchInput]);

    const handleFilterChange = useCallback((setter: (v: string) => void, value: string) => {
        setter(value);
        setOffset(0);
    }, []);

    const handleDeleted = useCallback(() => {
        setSelectedId(null);
        mutateList();
    }, [mutateList]);

    return (
        <div className="space-y-4">
            {/* Stats Bar */}
            {statsData && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <Card>
                        <CardHeader className="pb-1 pt-3 px-4">
                            <CardTitle className="text-2xl">{statsData.total}</CardTitle>
                        </CardHeader>
                        <CardContent className="px-4 pb-3">
                            <p className="text-xs text-muted-foreground">Total Profiles</p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-1 pt-3 px-4">
                            <CardTitle className="text-2xl">{Object.keys(statsData.by_category || {}).length}</CardTitle>
                        </CardHeader>
                        <CardContent className="px-4 pb-3">
                            <p className="text-xs text-muted-foreground">Categories</p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-1 pt-3 px-4">
                            <CardTitle className="text-2xl">{Object.keys(statsData.by_source || {}).length}</CardTitle>
                        </CardHeader>
                        <CardContent className="px-4 pb-3">
                            <p className="text-xs text-muted-foreground">Sources</p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-1 pt-3 px-4">
                            <CardTitle className="text-2xl">{Object.keys(statsData.by_difficulty || {}).length}</CardTitle>
                        </CardHeader>
                        <CardContent className="px-4 pb-3">
                            <p className="text-xs text-muted-foreground">Difficulty Levels</p>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Filters */}
            <Card>
                <CardContent className="py-3 px-4">
                    <div className="flex flex-wrap gap-3 items-end">
                        <div>
                            <label className="text-xs text-muted-foreground block mb-1">Category</label>
                            <select
                                className="h-9 rounded-md border bg-background px-3 text-sm"
                                value={category}
                                onChange={(e) => handleFilterChange(setCategory, e.target.value)}
                            >
                                <option value="">All</option>
                                {Object.entries(statsData?.by_category || {}).map(([cat, count]) => (
                                    <option key={cat} value={cat}>{cat} ({String(count)})</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="text-xs text-muted-foreground block mb-1">Difficulty</label>
                            <select
                                className="h-9 rounded-md border bg-background px-3 text-sm"
                                value={difficulty}
                                onChange={(e) => handleFilterChange(setDifficulty, e.target.value)}
                            >
                                <option value="">All</option>
                                {Object.entries(statsData?.by_difficulty || {}).map(([diff, count]) => (
                                    <option key={diff} value={diff}>{diff} ({String(count)})</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="text-xs text-muted-foreground block mb-1">Source</label>
                            <select
                                className="h-9 rounded-md border bg-background px-3 text-sm"
                                value={source}
                                onChange={(e) => handleFilterChange(setSource, e.target.value)}
                            >
                                <option value="">All</option>
                                {Object.entries(statsData?.by_source || {}).map(([src, count]) => (
                                    <option key={src} value={src}>{src} ({String(count)})</option>
                                ))}
                            </select>
                        </div>
                        <div className="flex-1 min-w-[200px]">
                            <label className="text-xs text-muted-foreground block mb-1">Search</label>
                            <div className="flex gap-1">
                                <input
                                    type="text"
                                    className="h-9 flex-1 rounded-md border bg-background px-3 text-sm"
                                    placeholder="Search by name..."
                                    value={searchInput}
                                    onChange={(e) => setSearchInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                />
                                <Button variant="outline" size="sm" className="h-9" onClick={handleSearch}>
                                    Search
                                </Button>
                                {(search || category || difficulty || source) && (
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="h-9"
                                        onClick={() => {
                                            setSearch('');
                                            setSearchInput('');
                                            setCategory('');
                                            setDifficulty('');
                                            setSource('');
                                            setOffset(0);
                                        }}
                                    >
                                        Clear
                                    </Button>
                                )}
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Table */}
            <Card>
                <CardContent className="p-0">
                    {isLoading ? (
                        <div className="text-center py-8 text-muted-foreground">Loading profiles...</div>
                    ) : items.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">No profiles found</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b bg-muted/50">
                                        <th className="py-2 px-3 text-left w-12">ID</th>
                                        <th className="py-2 px-3 text-left">Name</th>
                                        <th className="py-2 px-3 text-left">Category</th>
                                        <th className="py-2 px-3 text-left">Zone</th>
                                        <th className="py-2 px-3 text-right">Dur</th>
                                        <th className="py-2 px-3 text-right">TSS</th>
                                        <th className="py-2 px-3 text-right">IF</th>
                                        <th className="py-2 px-3 text-left">Diff</th>
                                        <th className="py-2 px-3 text-left">Source</th>
                                        <th className="py-2 px-3 text-center">Active</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {items.map((item: ProfileListItem) => (
                                        <tr
                                            key={item.id}
                                            className="border-b hover:bg-muted/50 cursor-pointer transition-colors"
                                            onClick={() => setSelectedId(item.id)}
                                        >
                                            <td className="py-2 px-3 text-muted-foreground">{item.id}</td>
                                            <td className="py-2 px-3 font-medium max-w-[250px] truncate">{item.name}</td>
                                            <td className="py-2 px-3">
                                                <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full">
                                                    {item.category}
                                                </span>
                                            </td>
                                            <td className="py-2 px-3 text-muted-foreground">{item.target_zone || '-'}</td>
                                            <td className="py-2 px-3 text-right">{item.duration_minutes ? `${item.duration_minutes}m` : '-'}</td>
                                            <td className="py-2 px-3 text-right">{item.estimated_tss?.toFixed(0) ?? '-'}</td>
                                            <td className="py-2 px-3 text-right">{item.estimated_if?.toFixed(2) ?? '-'}</td>
                                            <td className="py-2 px-3">
                                                <DifficultyBadge difficulty={item.difficulty} />
                                            </td>
                                            <td className="py-2 px-3 text-muted-foreground text-xs">{item.source || '-'}</td>
                                            <td className="py-2 px-3 text-center">
                                                {item.is_active ? (
                                                    <span className="text-green-600">On</span>
                                                ) : (
                                                    <span className="text-red-500">Off</span>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Pagination */}
                    {total > PAGE_SIZE && (
                        <div className="flex justify-between items-center px-4 py-3 border-t">
                            <span className="text-sm text-muted-foreground">
                                {offset + 1}-{Math.min(offset + PAGE_SIZE, total)} of {total}
                            </span>
                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={offset === 0}
                                    onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                                >
                                    Prev
                                </Button>
                                <span className="flex items-center px-3 text-sm text-muted-foreground">
                                    {currentPage} / {totalPages}
                                </span>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={offset + PAGE_SIZE >= total}
                                    onClick={() => setOffset(offset + PAGE_SIZE)}
                                >
                                    Next
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Detail Modal */}
            {selectedId !== null && (
                <ProfileDetailModal
                    profileId={selectedId}
                    onClose={() => setSelectedId(null)}
                    onDeleted={handleDeleted}
                />
            )}
        </div>
    );
}

function DifficultyBadge({ difficulty }: { difficulty: string | null }) {
    if (!difficulty) return <span className="text-muted-foreground">-</span>;

    const colors: Record<string, string> = {
        beginner: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
        intermediate: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
        advanced: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    };

    return (
        <span className={`px-2 py-0.5 text-xs rounded-full ${colors[difficulty] || 'bg-gray-100 text-gray-700'}`}>
            {difficulty}
        </span>
    );
}
