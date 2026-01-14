import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
    Alert,
    Badge,
    Button,
    Card,
    CardBody,
    CardHeader,
    FormTextarea,
    Spinner,
} from './UI';

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

interface AuditItemSummary {
    item_id: number;
    item_code: string;
    name: string;
    active: boolean | number;
    qty_on_hand?: number | null;
    note?: string | null;
}

interface AuditReconciliationResponse {
    session_id: number;
    expected_count: number;
    scanned_count: number;
    found_count: number;
    missing_count: number;
    unexpected_count: number;
    unknown_count: number;
    found: AuditItemSummary[];
    missing: AuditItemSummary[];
    unexpected: AuditItemSummary[];
}

interface AuditScanResponse {
    id: number;
    session_id: number;
    scanned_at: string;
    scanned_by: number;
    scanned_code?: string | null;
    item_id?: number | null;
    location_id: number;
    result: string;
    note?: string | null;
}

function AuditSessionDetailPage() {
    const { user, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();
    const { sessionId } = useParams<{ sessionId: string }>();
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    const [session, setSession] = useState<AuditSession | null>(null);
    const [reconciliation, setReconciliation] = useState<AuditReconciliationResponse | null>(null);
    const [notes, setNotes] = useState<Record<string, string>>({});
    const [scanHistory, setScanHistory] = useState<AuditScanResponse[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isClosing, setIsClosing] = useState(false);
    const [isSavingNotes, setIsSavingNotes] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const isAuditor = user?.role === 'ADMIN' || user?.role === 'AUDITOR';

    useEffect(() => {
        if (!authLoading && !user) {
            navigate('/login');
        }
    }, [authLoading, user, navigate]);

    useEffect(() => {
        if (isAuditor) {
            fetchSession();
            fetchReconciliation();
            fetchScans();
        }
    }, [isAuditor]);

    const saveNote = (key: string, value: string) => {
        setNotes((prev) => ({ ...prev, [key]: value }));
    };

    const fetchSession = async () => {
        if (!token || !sessionId) return;
        setIsLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE_URL}/audit/sessions/${sessionId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) throw new Error('Failed to load session');
            const data: AuditSession = await res.json();
            setSession(data);
        } catch {
            setError('Failed to load audit session');
        } finally {
            setIsLoading(false);
        }
    };

    const fetchReconciliation = async () => {
        if (!token || !sessionId) return;
        try {
            const res = await fetch(`${API_BASE_URL}/audit/sessions/${sessionId}/reconciliation`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) {
                const payload = await res.json().catch(() => ({}));
                const detail = payload.detail || `Failed to load reconciliation (${res.status})`;
                throw new Error(detail);
            }
            const data: AuditReconciliationResponse = await res.json();
            setReconciliation(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load reconciliation');
        }
    };

    const fetchScans = async () => {
        if (!token || !sessionId) return;
        try {
            const res = await fetch(`${API_BASE_URL}/audit/sessions/${sessionId}/scans?page=1&page_size=100`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) throw new Error('Failed to load scans');
            const data = await res.json();
            const list = Array.isArray(data) ? data : (data.scans || []);
            setScanHistory(list);
        } catch {
            setError('Failed to load scan history');
        }
    };

    useEffect(() => {
        if (!reconciliation && scanHistory.length === 0) return;
        setNotes((prev) => {
            if (Object.keys(prev).length > 0) return prev;
            const next: Record<string, string> = {};
            reconciliation?.missing?.forEach((item) => {
                if (item.note) next[`missing:${item.item_id}`] = item.note;
            });
            reconciliation?.unexpected?.forEach((item) => {
                if (item.note) next[`unexpected:${item.item_id}`] = item.note;
            });
            scanHistory
                .filter((scan) => scan.result === 'UNKNOWN')
                .forEach((scan) => {
                    if (scan.note) next[`unknown:${scan.id}`] = scan.note;
                });
            return next;
        });
    }, [reconciliation, scanHistory]);

    const handleCloseSession = async () => {
        if (!token || !sessionId) return;
        if (!window.confirm('Close this audit session?')) return;

        setIsClosing(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE_URL}/audit/sessions/${sessionId}/close`, {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) throw new Error('Failed to close session');
            await fetchSession();
            await fetchReconciliation();
        } catch {
            setError('Failed to close audit session');
        } finally {
            setIsClosing(false);
        }
    };

    const handleSaveNotes = async () => {
        if (!token || !sessionId || !reconciliation) return;
        setIsSavingNotes(true);
        setError(null);
        setSuccess(null);
        try {
            const missingNotes = reconciliation.missing.map((item) => ({
                item_id: item.item_id,
                note: (notes[`missing:${item.item_id}`] || '').trim() || null,
            }));
            const unexpectedNotes = reconciliation.unexpected.map((item) => ({
                item_id: item.item_id,
                note: (notes[`unexpected:${item.item_id}`] || '').trim() || null,
            }));
            const unknownNotes = scanHistory
                .filter((scan) => scan.result === 'UNKNOWN')
                .map((scan) => ({
                    scan_id: scan.id,
                    note: (notes[`unknown:${scan.id}`] || '').trim() || null,
                }));

            const res = await fetch(`${API_BASE_URL}/audit/sessions/${sessionId}/notes`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    missing_notes: missingNotes,
                    unexpected_notes: unexpectedNotes,
                    unknown_notes: unknownNotes,
                }),
            });
            if (!res.ok) {
                const payload = await res.json().catch(() => ({}));
                const detail = payload.detail || `Failed to save notes (${res.status})`;
                throw new Error(detail);
            }
            setSuccess('Audit notes saved.');
            await fetchReconciliation();
            await fetchScans();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save notes');
        } finally {
            setIsSavingNotes(false);
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

    const unknownScans = useMemo(
        () => scanHistory.filter((scan) => scan.result === 'UNKNOWN'),
        [scanHistory]
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

    if (!session) {
        return (
            <div className="px-4 py-6 max-w-4xl mx-auto">
                <Alert variant="danger">Audit session not found.</Alert>
            </div>
        );
    }

    return (
        <div className="w-full h-full">
            <div className="px-4 py-6 max-w-6xl mx-auto">
                <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900">Audit Session #{session.id}</h2>
                        <p className="text-sm text-gray-600 mt-1">
                            {session.location_name} ({session.location_code})
                        </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        <Button
                            variant="outline-secondary"
                            onClick={() => {
                                if (window.history.length > 1) {
                                    navigate(-1);
                                } else {
                                    navigate('/audit');
                                }
                            }}
                        >
                            Back
                        </Button>
                        <Button
                            variant="outline-primary"
                            onClick={handleSaveNotes}
                            isLoading={isSavingNotes}
                        >
                            Save Notes
                        </Button>
                        <Badge variant={statusBadge(session.status)}>{session.status}</Badge>
                        {session.status === 'OPEN' && (
                            <>
                                <Button variant="outline-secondary" onClick={() => navigate(`/audit/${session.id}/scan`)}>
                                    Scan Mode
                                </Button>
                                <Button variant="outline-primary" onClick={() => navigate(`/audit/${session.id}/report`)}>
                                    Report
                                </Button>
                                <Button variant="danger" onClick={handleCloseSession} isLoading={isClosing}>
                                    Close Session
                                </Button>
                            </>
                        )}
                        {session.status !== 'OPEN' && (
                            <Button variant="outline-primary" onClick={() => navigate(`/audit/${session.id}/report`)}>
                                Report
                            </Button>
                        )}
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
                        <h5 className="text-lg font-semibold text-gray-900">Reconciliation Summary</h5>
                    </CardHeader>
                    <CardBody>
                        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-center">
                            <div className="p-3 bg-gray-50 rounded-lg">
                                <div className="text-xs text-gray-500">Expected</div>
                                <div className="text-2xl font-bold">{reconciliation?.expected_count ?? 0}</div>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-lg">
                                <div className="text-xs text-gray-500">Scanned</div>
                                <div className="text-2xl font-bold">{reconciliation?.scanned_count ?? 0}</div>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-lg">
                                <div className="text-xs text-gray-500">Found</div>
                                <div className="text-2xl font-bold">{reconciliation?.found_count ?? 0}</div>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-lg">
                                <div className="text-xs text-gray-500">Missing</div>
                                <div className="text-2xl font-bold">{reconciliation?.missing_count ?? 0}</div>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-lg">
                                <div className="text-xs text-gray-500">Unexpected</div>
                                <div className="text-2xl font-bold">{reconciliation?.unexpected_count ?? 0}</div>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-lg">
                                <div className="text-xs text-gray-500">Unknown</div>
                                <div className="text-2xl font-bold">{reconciliation?.unknown_count ?? 0}</div>
                            </div>
                        </div>
                    </CardBody>
                </Card>

                <Card className="mb-6">
                    <CardHeader>
                        <h5 className="text-lg font-semibold text-gray-900">Missing Items</h5>
                    </CardHeader>
                    <CardBody className="p-0">
                        {reconciliation?.missing?.length ? (
                            <div className="table-responsive">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>Item</th>
                                            <th>Qty</th>
                                            <th>Note</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {reconciliation.missing.map((item) => {
                                            const key = `missing:${item.item_id}`;
                                            return (
                                                <tr key={item.item_id}>
                                                    <td>
                                                        <div className="font-semibold">{item.name}</div>
                                                        <div className="text-xs text-gray-500">{item.item_code}</div>
                                                    </td>
                                                    <td className="text-sm">{item.qty_on_hand ?? 0}</td>
                                                    <td className="w-1/2">
                                                        <FormTextarea
                                                            placeholder="Add note (loaned, moved, disposed...)"
                                                            value={notes[key] || ''}
                                                            onChange={(e) => saveNote(key, e.target.value)}
                                                        />
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center text-gray-500 py-8">No missing items</div>
                        )}
                    </CardBody>
                </Card>

                <Card className="mb-6">
                    <CardHeader>
                        <h5 className="text-lg font-semibold text-gray-900">Unexpected Items</h5>
                    </CardHeader>
                    <CardBody className="p-0">
                        {reconciliation?.unexpected?.length ? (
                            <div className="table-responsive">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>Item</th>
                                            <th>Active</th>
                                            <th>Note</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {reconciliation.unexpected.map((item) => {
                                            const key = `unexpected:${item.item_id}`;
                                            return (
                                                <tr key={item.item_id}>
                                                    <td>
                                                        <div className="font-semibold">{item.name}</div>
                                                        <div className="text-xs text-gray-500">{item.item_code}</div>
                                                    </td>
                                                    <td className="text-sm">{item.active ? 'Yes' : 'No'}</td>
                                                    <td className="w-1/2">
                                                        <FormTextarea
                                                            placeholder="Add note (wrong shelf, transferred...)"
                                                            value={notes[key] || ''}
                                                            onChange={(e) => saveNote(key, e.target.value)}
                                                        />
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center text-gray-500 py-8">No unexpected items</div>
                        )}
                    </CardBody>
                </Card>

                <Card>
                    <CardHeader>
                        <h5 className="text-lg font-semibold text-gray-900">Unknown Scans</h5>
                    </CardHeader>
                    <CardBody className="p-0">
                        {unknownScans.length ? (
                            <div className="table-responsive">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>Scanned Code</th>
                                            <th>Time</th>
                                            <th>Note</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {unknownScans.map((scan) => {
                                            const key = `unknown:${scan.scanned_code}`;
                                            return (
                                                <tr key={scan.id}>
                                                    <td className="font-mono text-sm">{scan.scanned_code || '-'}</td>
                                                    <td className="text-sm">
                                                        {new Date(scan.scanned_at).toLocaleString()}
                                                    </td>
                                                    <td className="w-1/2">
                                                        <FormTextarea
                                                            placeholder="Add note for this unknown code"
                                                            value={notes[key] || ''}
                                                            onChange={(e) => saveNote(key, e.target.value)}
                                                        />
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center text-gray-500 py-8">Unknown scan list is empty.</div>
                        )}
                    </CardBody>
                </Card>
            </div>
        </div>
    );
}

export default AuditSessionDetailPage;
