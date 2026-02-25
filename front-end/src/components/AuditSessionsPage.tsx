import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Eye, ScanLine } from 'lucide-react';
import {
    Alert,
    Badge,
    Button,
    Card,
    CardBody,
    CardHeader,
    FormSelect,
    FormTextarea,
    Pagination,
    PaginationInfo,
    Spinner,
} from './UI';

interface Location {
    id: number;
    name: string;
    code: string;
    active: number;
}

interface AuditSession {
    id: number;
    location_id: number;
    location_name?: string;
    location_code?: string;
    status: string;
    started_at: string;
    started_by: number;
    started_by_name?: string;
    closed_at?: string | null;
    closed_by?: number | null;
    closed_by_name?: string | null;
    note?: string | null;
    scanned_count: number;
    expected_count: number;
    missing_count: number;
    unexpected_count: number;
    unknown_count: number;
}

interface AuditSessionListResponse {
    sessions: AuditSession[];
    total: number;
    page: number;
    page_size: number;
}

function AuditSessionsPage() {
    const { user, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    const [locations, setLocations] = useState<Location[]>([]);
    const [sessions, setSessions] = useState<AuditSession[]>([]);
    const [statusFilter, setStatusFilter] = useState('all');
    const [locationId, setLocationId] = useState('');
    const [note, setNote] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalSessions, setTotalSessions] = useState(0);
    const pageSize = 10;

    const isAuditor = user?.role === 'ADMIN' || user?.role === 'AUDITOR';

    useEffect(() => {
        if (!authLoading && !user) {
            navigate('/login');
        }
    }, [authLoading, user, navigate]);

    useEffect(() => {
        if (isAuditor) {
            fetchLocations();
        }
    }, [isAuditor]);

    useEffect(() => {
        if (isAuditor) {
            fetchSessions();
        }
    }, [currentPage, statusFilter, locationId, isAuditor]);

    const fetchLocations = async () => {
        if (!token) return;
        try {
            const res = await fetch(`${API_BASE_URL}/locations?page=1&page_size=100&active_only=1`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            const data = await res.json();
            setLocations(Array.isArray(data) ? data : []);
        } catch (err) {
            setError('Failed to load locations');
        }
    };

    const fetchSessions = async () => {
        if (!token) return;
        setIsLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams({
                page: currentPage.toString(),
                page_size: pageSize.toString(),
            });
            if (statusFilter !== 'all') params.append('session_status', statusFilter);
            if (locationId) params.append('location_id', locationId);

            const res = await fetch(`${API_BASE_URL}/audit/sessions?${params}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) throw new Error('Failed to load sessions');
            const data: AuditSessionListResponse = await res.json();
            setSessions(data.sessions || []);
            setTotalSessions(data.total || 0);
            setTotalPages(Math.ceil((data.total || 0) / pageSize));
        } catch (err) {
            setError('Failed to load audit sessions');
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreateSession = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token || !locationId) return;

        setIsCreating(true);
        setError(null);
        setSuccess(null);

        try {
            const res = await fetch(`${API_BASE_URL}/audit/sessions`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    location_id: Number(locationId),
                    note: note.trim() || null,
                }),
            });
            if (!res.ok) throw new Error('Failed to create session');
            const data: AuditSession = await res.json();
            setSuccess('Audit session created');
            setNote('');
            navigate(`/audit/${data.id}/scan`);
        } catch (err) {
            setError('Failed to create audit session');
        } finally {
            setIsCreating(false);
        }
    };

    const statusBadge = (status: string) => {
        switch (status) {
            case 'OPEN':
                return 'success';
            case 'CLOSED':
                return 'secondary';
            case 'CANCELLED':
                return 'danger';
            default:
                return 'info';
        }
    };

    const locationOptions = useMemo(
        () => locations.map((loc) => ({ value: loc.id, label: `${loc.name} (${loc.code})` })),
        [locations]
    );

    if (authLoading || isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Spinner size="lg" />
            </div>
        );
    }

    if (!isAuditor) {
        return (
            <div className="px-4 py-6 max-w-4xl mx-auto">
                <Alert variant="danger">You do not have access to Audit pages.</Alert>
            </div>
        );
    }

    return (
        <div className="w-full h-full">
            <div className="px-4 py-6 max-w-7xl mx-auto">
                <div className="flex items-start justify-between mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900">Audit Sessions</h2>
                        <p className="text-sm text-gray-600 mt-1">Create and manage audit sessions</p>
                    </div>
                </div>

                {error && (
                    <Alert variant="danger" dismissible onClose={() => setError(null)} className="mb-4">
                        {error}
                    </Alert>
                )}
                {success && (
                    <Alert variant="success" dismissible onClose={() => setSuccess(null)} className="mb-4">
                        {success}
                    </Alert>
                )}

                <Card className="mb-6">
                    <CardHeader>
                        <h5 className="text-lg font-semibold text-gray-900">Create Audit Session</h5>
                    </CardHeader>
                    <CardBody>
                        <form onSubmit={handleCreateSession} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormSelect
                                label="Location"
                                options={locationOptions}
                                value={locationId}
                                onChange={(e) => setLocationId(e.target.value)}
                                required
                            />
                            <FormTextarea
                                label="Note"
                                placeholder="Optional note (e.g., Quarterly audit Q1)"
                                value={note}
                                onChange={(e) => setNote(e.target.value)}
                            />
                            <div className="md:col-span-2">
                                <Button type="submit" variant="primary" isLoading={isCreating} disabled={!locationId}>
                                    Create Session
                                </Button>
                            </div>
                        </form>
                    </CardBody>
                </Card>

                <Card>
                    <CardHeader>
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                            <div>
                                <h5 className="text-lg font-semibold text-gray-900">Sessions</h5>
                                <p className="text-sm text-gray-600">Recent audit sessions</p>
                            </div>
                            <div className="flex flex-col sm:flex-row gap-3">
                                <FormSelect
                                    label="Status"
                                    options={[
                                        { value: 'all', label: 'All' },
                                        { value: 'OPEN', label: 'OPEN' },
                                        { value: 'CLOSED', label: 'CLOSED' },
                                        { value: 'CANCELLED', label: 'CANCELLED' },
                                    ]}
                                    value={statusFilter}
                                    onChange={(e) => {
                                        setStatusFilter(e.target.value);
                                        setCurrentPage(1);
                                    }}
                                />
                                <FormSelect
                                    label="Location"
                                    options={[{ value: '', label: 'All Locations' }, ...locationOptions]}
                                    value={locationId}
                                    onChange={(e) => {
                                        setLocationId(e.target.value);
                                        setCurrentPage(1);
                                    }}
                                />
                            </div>
                        </div>
                    </CardHeader>
                    <CardBody className="p-0">
                        {sessions.length === 0 ? (
                            <div className="text-center text-gray-500 py-12">No sessions found</div>
                        ) : (
                            <div className="table-responsive">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Location</th>
                                            <th>Status</th>
                                            <th>Started</th>
                                            <th>Scanned / Expected</th>
                                            <th className="w-24 text-center">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sessions.map((session) => (
                                            <tr key={session.id}>
                                                <td className="font-mono text-sm">#{session.id}</td>
                                                <td>
                                                    <div className="font-semibold">{session.location_name}</div>
                                                    <div className="text-xs text-gray-500">{session.location_code}</div>
                                                </td>
                                                <td>
                                                    <Badge variant={statusBadge(session.status)}>
                                                        {session.status}
                                                    </Badge>
                                                </td>
                                                <td className="text-sm">
                                                    {new Date(session.started_at).toLocaleString()}
                                                </td>
                                                <td className="text-sm">
                                                    {session.scanned_count} / {session.expected_count}
                                                </td>
                                                <td className="text-center">
                                                    <div className="flex gap-1 justify-center">
                                                        <Button
                                                            variant="outline-primary"
                                                            size="sm"
                                                            className="px-2"
                                                            title="View audit session"
                                                            aria-label="View audit session"
                                                            onClick={() => navigate(`/audit/${session.id}`)}
                                                        >
                                                            <Eye className="w-4 h-4" />
                                                        </Button>
                                                        {session.status === 'OPEN' && (
                                                            <Button
                                                                variant="primary"
                                                                size="sm"
                                                                className="px-2"
                                                                title="Scan audit session"
                                                                aria-label="Scan audit session"
                                                                onClick={() => navigate(`/audit/${session.id}/scan`)}
                                                            >
                                                                <ScanLine className="w-4 h-4" />
                                                            </Button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </CardBody>
                    {totalPages > 1 && (
                        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
                            <PaginationInfo currentPage={currentPage} pageSize={pageSize} totalItems={totalSessions} />
                            <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
                        </div>
                    )}
                </Card>
            </div>
        </div>
    );
}

export default AuditSessionsPage;
