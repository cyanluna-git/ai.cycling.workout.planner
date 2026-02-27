/**
 * ProfileDetailModal — Full profile view with Zwift chart and all 24 columns
 */

import { useState, useMemo } from 'react';
import useSWR from 'swr';
import { useAuth } from '@/contexts/AuthContext';
import { createAuthFetcher, defaultSWRConfig } from '@/lib/swr';
import { Button } from '@/components/ui/button';
import { ProfileChart } from './ProfileChart';

interface ProfileDetailModalProps {
    profileId: number;
    onClose: () => void;
    onDeleted: () => void;
}

export function ProfileDetailModal({ profileId, onClose, onDeleted }: ProfileDetailModalProps) {
    const { session } = useAuth();
    const [showZwo, setShowZwo] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [confirmDelete, setConfirmDelete] = useState(false);
    const [deleteError, setDeleteError] = useState<string | null>(null);

    const authFetcher = useMemo(
        () => createAuthFetcher(session?.access_token),
        [session?.access_token]
    );

    const { data: profile, isLoading } = useSWR(
        session?.access_token ? `/api/profiles/${profileId}` : null,
        authFetcher,
        defaultSWRConfig
    );

    const handleDelete = async () => {
        if (!confirmDelete) {
            setConfirmDelete(true);
            setDeleteError(null);
            return;
        }
        setDeleting(true);
        setDeleteError(null);
        try {
            const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const res = await fetch(`${API_BASE}/api/profiles/${profileId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${session?.access_token}`,
                },
            });
            if (res.ok) {
                onDeleted();
            } else {
                setDeleteError(`Failed to delete (${res.status})`);
            }
        } catch {
            setDeleteError('Network error');
        } finally {
            setDeleting(false);
            setConfirmDelete(false);
        }
    };

    const renderValue = (val: unknown) => {
        if (val === null || val === undefined) return <span className="text-muted-foreground">-</span>;
        if (typeof val === 'boolean') return val ? 'Yes' : 'No';
        if (typeof val === 'number') return String(val);
        if (typeof val === 'string') return val;
        return JSON.stringify(val);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
            <div
                className="bg-background rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="sticky top-0 bg-background border-b px-6 py-4 flex justify-between items-center z-10">
                    <h2 className="text-lg font-bold truncate">
                        {isLoading ? 'Loading...' : profile?.name || `Profile #${profileId}`}
                    </h2>
                    <Button variant="ghost" size="sm" onClick={onClose}>
                        Close
                    </Button>
                </div>

                {isLoading ? (
                    <div className="p-8 text-center text-muted-foreground">Loading profile...</div>
                ) : profile ? (
                    <div className="p-6 space-y-6">
                        {/* Chart */}
                        <ProfileChart stepsJson={profile.steps_json} height={200} />

                        {/* Basic Info */}
                        <Section title="Basic Info">
                            <Field label="ID" value={profile.id} />
                            <Field label="Name" value={profile.name} />
                            <Field label="Slug" value={profile.slug} />
                            <Field label="Category" value={profile.category} />
                            <Field label="Subcategory" value={profile.subcategory} />
                            <Field label="Difficulty" value={profile.difficulty} />
                            <Field label="Source" value={profile.source} />
                            {profile.source_url && (
                                <div className="col-span-2">
                                    <span className="text-xs text-muted-foreground">Source URL</span>
                                    <div>
                                        <a
                                            href={profile.source_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-500 hover:underline text-sm break-all"
                                        >
                                            {profile.source_url}
                                        </a>
                                    </div>
                                </div>
                            )}
                        </Section>

                        {/* Training Data */}
                        <Section title="Training Data">
                            <Field label="Target Zone" value={profile.target_zone} />
                            <Field label="Interval Type" value={profile.interval_type} />
                            <Field label="Interval Length" value={profile.interval_length} />
                            <Field label="Duration" value={profile.duration_minutes ? `${profile.duration_minutes} min` : null} />
                            <Field label="Est. TSS" value={profile.estimated_tss?.toFixed(1)} />
                            <Field label="Est. IF" value={profile.estimated_if?.toFixed(2)} />
                            <Field label="Fatigue Impact" value={profile.fatigue_impact} />
                            <Field label="Min FTP" value={profile.min_ftp} />
                        </Section>

                        {/* Tags */}
                        {profile.tags && (Array.isArray(profile.tags) ? profile.tags.length > 0 : true) && (
                            <Section title="Tags">
                                <div className="col-span-2 flex flex-wrap gap-1">
                                    {(Array.isArray(profile.tags) ? profile.tags : []).map((tag: string, i: number) => (
                                        <span key={i} className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full">
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </Section>
                        )}

                        {/* Description */}
                        {profile.description && (
                            <Section title="Description">
                                <div className="col-span-2 text-sm text-muted-foreground whitespace-pre-wrap">
                                    {profile.description}
                                </div>
                            </Section>
                        )}

                        {/* Coach Notes */}
                        {profile.coach_notes && (
                            <Section title="Coach Notes">
                                <div className="col-span-2 text-xs font-mono bg-muted p-3 rounded overflow-x-auto">
                                    {JSON.stringify(profile.coach_notes, null, 2)}
                                </div>
                            </Section>
                        )}

                        {/* ZWO XML */}
                        {profile.zwo_xml && (
                            <Section title="ZWO XML">
                                <div className="col-span-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setShowZwo(!showZwo)}
                                    >
                                        {showZwo ? 'Hide XML' : 'Show XML'}
                                    </Button>
                                    {showZwo && (
                                        <pre className="mt-2 text-xs font-mono bg-muted p-3 rounded overflow-x-auto max-h-64 overflow-y-auto">
                                            {profile.zwo_xml}
                                        </pre>
                                    )}
                                </div>
                            </Section>
                        )}

                        {/* System */}
                        <Section title="System">
                            <Field label="Active" value={renderValue(profile.is_active)} />
                            <Field label="Created" value={profile.created_at ? new Date(profile.created_at).toLocaleString('ko-KR') : null} />
                            <Field label="Updated" value={profile.updated_at ? new Date(profile.updated_at).toLocaleString('ko-KR') : null} />
                        </Section>

                        {/* Delete */}
                        <div className="border-t pt-4 flex justify-end items-center gap-2">
                            {deleteError && (
                                <span className="text-red-500 text-sm mr-auto">{deleteError}</span>
                            )}
                            {confirmDelete && (
                                <Button variant="outline" size="sm" onClick={() => setConfirmDelete(false)}>
                                    Cancel
                                </Button>
                            )}
                            <Button
                                variant="destructive"
                                size="sm"
                                onClick={handleDelete}
                                disabled={deleting}
                            >
                                {deleting ? 'Deleting...' : confirmDelete ? 'Confirm Delete' : 'Delete Profile'}
                            </Button>
                        </div>
                    </div>
                ) : (
                    <div className="p-8 text-center text-muted-foreground">Profile not found</div>
                )}
            </div>
        </div>
    );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">{title}</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {children}
            </div>
        </div>
    );
}

function Field({ label, value }: { label: string; value: unknown }) {
    return (
        <div>
            <span className="text-xs text-muted-foreground">{label}</span>
            <div className="text-sm font-medium truncate">
                {value === null || value === undefined ? (
                    <span className="text-muted-foreground">-</span>
                ) : (
                    String(value)
                )}
            </div>
        </div>
    );
}
