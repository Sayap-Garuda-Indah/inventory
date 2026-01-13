import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Alert, Badge, Button, Card, CardBody, CardHeader, Spinner } from './UI';

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

function AuditReportPage() {
    const { user, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();
    const { sessionId } = useParams<{ sessionId: string }>();
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    const [session, setSession] = useState<AuditSession | null>(null);
    const [reconciliation, setReconciliation] = useState<AuditReconciliationResponse | null>(null);
    const [scans, setScans] = useState<AuditScanResponse[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

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
            const res = await fetch(`${API_BASE_URL}/audit/sessions/${sessionId}/scans?page=1&page_size=200`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) throw new Error('Failed to load scans');
            const data = await res.json();
            const list = Array.isArray(data) ? data : (data.scans || []);
            setScans(list);
        } catch {
            setError('Failed to load scan history');
        }
    };

    const unknownScans = useMemo(
        () => scans.filter((scan) => scan.result === 'UNKNOWN'),
        [scans]
    );

    const handlePrint = () => window.print();

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
            <style>{`
                @media print {
                    .no-print { display: none !important; }
                    .print-card { box-shadow: none !important; }
                }
            `}</style>

            <div className="px-4 py-6 max-w-5xl mx-auto">
                <div className="flex items-center justify-between mb-6 no-print">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900">Audit Report</h2>
                        <p className="text-sm text-gray-600">
                            Session #{session.id} · {session.location_name} ({session.location_code})
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant="outline-secondary"
                            onClick={() => {
                                if (window.history.length > 1) {
                                    navigate(-1);
                                } else {
                                    navigate(`/audit/${session.id}`);
                                }
                            }}
                        >
                            Back
                        </Button>
                        <Button variant="primary" onClick={handlePrint}>Print</Button>
                    </div>
                </div>

                {error && (
                    <Alert variant="danger" dismissible onClose={() => setError(null)} className="mb-4 no-print">
                        {error}
                    </Alert>
                )}

                <Card className="mb-6 print-card">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <h5 className="text-lg font-semibold text-gray-900">Summary</h5>
                            <Badge variant="secondary">{session.status}</Badge>
                        </div>
                    </CardHeader>
                    <CardBody>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                            <div>
                                <div className="text-xs text-gray-500">Started At</div>
                                <div>{new Date(session.started_at).toLocaleString()}</div>
                            </div>
                            <div>
                                <div className="text-xs text-gray-500">Started By</div>
                                <div>{session.started_by_name || session.started_by}</div>
                            </div>
                            <div>
                                <div className="text-xs text-gray-500">Note</div>
                                <div>{session.note || '-'}</div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-center mt-6">
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

                <Card className="mb-6 print-card">
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
                                        {reconciliation.missing.map((item) => (
                                            <tr key={item.item_id}>
                                                <td>
                                                    <div className="font-semibold">{item.name}</div>
                                                    <div className="text-xs text-gray-500">{item.item_code}</div>
                                                </td>
                                                <td className="text-sm">{item.qty_on_hand ?? 0}</td>
                                                <td className="text-sm">{item.note || '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center text-gray-500 py-6">No missing items</div>
                        )}
                    </CardBody>
                </Card>

                <Card className="mb-6 print-card">
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
                                        {reconciliation.unexpected.map((item) => (
                                            <tr key={item.item_id}>
                                                <td>
                                                    <div className="font-semibold">{item.name}</div>
                                                    <div className="text-xs text-gray-500">{item.item_code}</div>
                                                </td>
                                                <td className="text-sm">{item.active ? 'Yes' : 'No'}</td>
                                                <td className="text-sm">{item.note || '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center text-gray-500 py-6">No unexpected items</div>
                        )}
                    </CardBody>
                </Card>

                <Card className="print-card">
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
                                        {unknownScans.map((scan) => (
                                            <tr key={scan.id}>
                                                <td className="font-mono text-sm">{scan.scanned_code || '-'}</td>
                                                <td className="text-sm">{new Date(scan.scanned_at).toLocaleString()}</td>
                                                <td className="text-sm">{scan.note || '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center text-gray-500 py-6">No unknown scans</div>
                        )}
                    </CardBody>
                </Card>
            </div>
        </div>
    );
}

export default AuditReportPage;
