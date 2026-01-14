import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
    Alert,
    Badge,
    Button,
    Card,
    CardBody,
    CardHeader,
    FormInput,
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
    scanned_count: number;
    expected_count: number;
    missing_count: number;
    unexpected_count: number;
    unknown_count: number;
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

function AuditScanPage() {
    const { user, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();
    const { sessionId } = useParams<{ sessionId: string }>();
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    const [session, setSession] = useState<AuditSession | null>(null);
    const [scannedCode, setScannedCode] = useState('');
    const [note, setNote] = useState('');
    const [scanHistory, setScanHistory] = useState<AuditScanResponse[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const [cameraActive, setCameraActive] = useState(false);
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const zxingReaderRef = useRef<any>(null);

    const isAuditor = user?.role === 'ADMIN' || user?.role === 'AUDITOR';

    useEffect(() => {
        if (!authLoading && !user) {
            navigate('/login');
        }
    }, [authLoading, user, navigate]);

    useEffect(() => {
        if (isAuditor) {
            fetchSession();
            fetchScans();
        }
    }, [isAuditor]);

    useEffect(() => {
        return () => {
            stopCamera();
        };
    }, []);

    const normalizeScannedCode = (value: string) => {
        const trimmed = value.trim();
        if (!trimmed) return '';
        try {
            const parsed = JSON.parse(trimmed);
            if (parsed && typeof parsed === 'object') {
                const itemCode = typeof parsed.item_code === 'string' ? parsed.item_code.trim() : '';
                const serialNumber = typeof parsed.serial_number === 'string' ? parsed.serial_number.trim() : '';
                if (itemCode) return itemCode;
                if (serialNumber) return serialNumber;
            }
        } catch {
            // ignore JSON parse errors
        }
        return trimmed.slice(0, 64);
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

    const handleSubmitScan = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token || !sessionId || !scannedCode.trim()) return;
        const normalizedCode = normalizeScannedCode(scannedCode);
        if (!normalizedCode) return;

        setIsSubmitting(true);
        setError(null);
        setSuccess(null);

        try {
            const res = await fetch(`${API_BASE_URL}/audit/sessions/${sessionId}/scans`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ scanned_code: normalizedCode, note: note.trim() || null }),
            });
            if (!res.ok) throw new Error('Scan failed');

            setScannedCode('');
            setNote('');
            setSuccess('Scan submitted');
            fetchSession();
            fetchScans();
        } catch {
            setError('Failed to submit scan');
        } finally {
            setIsSubmitting(false);
        }
    };

    const startCamera = async () => {
        setError(null);
        setSuccess(null);
        if ('BarcodeDetector' in window) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'environment' },
                });
                streamRef.current = stream;
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    videoRef.current.muted = true;
                    await videoRef.current.play();
                }
                setCameraActive(true);
                scanLoop();
                return;
            } catch {
                setError('Unable to access camera.');
                return;
            }
        }

        try {
            const { BrowserQRCodeReader } = await import('@zxing/browser');
            const reader = new BrowserQRCodeReader();
            zxingReaderRef.current = reader;
            const videoElement = videoRef.current;
            if (!videoElement) {
                setError('Camera element not ready.');
                return;
            }
            setCameraActive(true);
            await reader.decodeFromVideoDevice(undefined, videoElement, (result) => {
                if (result) {
                    setScannedCode(result.getText());
                    setSuccess('QR code detected');
                    stopCamera();
                }
            });
        } catch {
            setError('Camera scanning is not supported in this browser.');
        }
    };

    const stopCamera = () => {
        if (zxingReaderRef.current) {
            zxingReaderRef.current.reset();
            zxingReaderRef.current = null;
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((t) => t.stop());
            streamRef.current = null;
        }
        setCameraActive(false);
    };

    const scanLoop = async () => {
        if (!cameraActive || !videoRef.current) return;
        const BarcodeDetectorCtor = (window as any).BarcodeDetector;
        const detector = new BarcodeDetectorCtor({ formats: ['qr_code'] });

        const detectFrame = async () => {
            if (!cameraActive || !videoRef.current) return;
            try {
                const barcodes = await detector.detect(videoRef.current);
                if (barcodes && barcodes.length > 0) {
                    const value = barcodes[0].rawValue || '';
                    if (value) {
                        setScannedCode(value);
                        stopCamera();
                        return;
                    }
                }
            } catch {
                // ignore frame errors
            }
            requestAnimationFrame(detectFrame);
        };

        requestAnimationFrame(detectFrame);
    };

    const handleFileScan = async (file: File | null) => {
        if (!file) return;
        setError(null);
        setSuccess(null);
        if ('BarcodeDetector' in window) {
            try {
                const BarcodeDetectorCtor = (window as any).BarcodeDetector;
                const detector = new BarcodeDetectorCtor({ formats: ['qr_code'] });
                const bitmap = await createImageBitmap(file);
                const barcodes = await detector.detect(bitmap);
                if (barcodes && barcodes.length > 0) {
                    setScannedCode(barcodes[0].rawValue || '');
                    setSuccess('QR code detected from image');
                } else {
                    setError('No QR code found in image');
                }
            } catch {
                setError('Failed to read QR from image');
            }
            return;
        }

        try {
            const { BrowserQRCodeReader } = await import('@zxing/browser');
            const reader = new BrowserQRCodeReader();
            const imageUrl = URL.createObjectURL(file);
            const img = new Image();
            img.src = imageUrl;
            await img.decode();
            const result = await reader.decodeFromImageElement(img);
            URL.revokeObjectURL(imageUrl);
            if (result?.getText()) {
                setScannedCode(result.getText());
                setSuccess('QR code detected from image');
            } else {
                setError('No QR code found in image');
            }
        } catch {
            setError('Failed to read QR from image');
        }
    };

    const statusBadge = (status: string) => {
        switch (status) {
            case 'FOUND':
                return 'success';
            case 'UNKNOWN':
                return 'warning';
            case 'WRONG_LOCATION':
                return 'danger';
            case 'INACTIVE':
                return 'secondary';
            case 'DUPLICATE':
                return 'info';
            default:
                return 'secondary';
        }
    };

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
                        <h2 className="text-2xl font-bold text-gray-900">Scan Mode</h2>
                        <p className="text-sm text-gray-600 mt-1">
                            Session #{session.id} · {session.location_name} ({session.location_code})
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline-secondary" onClick={() => navigate(`/audit/${session.id}`)}>
                            View Details
                        </Button>
                        {session.status !== 'OPEN' && (
                            <Badge variant="secondary">{session.status}</Badge>
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
                        <h5 className="text-lg font-semibold text-gray-900">Counters</h5>
                    </CardHeader>
                    <CardBody>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
                            <div className="p-3 bg-gray-50 rounded-lg">
                                <div className="text-xs text-gray-500">Scanned</div>
                                <div className="text-2xl font-bold">{session.scanned_count}</div>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-lg">
                                <div className="text-xs text-gray-500">Expected</div>
                                <div className="text-2xl font-bold">{session.expected_count}</div>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-lg">
                                <div className="text-xs text-gray-500">Missing</div>
                                <div className="text-2xl font-bold">{session.missing_count}</div>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-lg">
                                <div className="text-xs text-gray-500">Unexpected</div>
                                <div className="text-2xl font-bold">{session.unexpected_count}</div>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-lg">
                                <div className="text-xs text-gray-500">Unknown</div>
                                <div className="text-2xl font-bold">{session.unknown_count}</div>
                            </div>
                        </div>
                    </CardBody>
                </Card>

                <Card className="mb-6">
                    <CardHeader>
                        <h5 className="text-lg font-semibold text-gray-900">Scan Input</h5>
                    </CardHeader>
                    <CardBody>
                        <form onSubmit={handleSubmitScan} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormInput
                                label="Scanned Code"
                                placeholder="Scan or paste QR code value"
                                value={scannedCode}
                                onChange={(e) => setScannedCode(e.target.value)}
                                required
                            />
                            <FormTextarea
                                label="Note (optional)"
                                placeholder="Observed condition or note"
                                value={note}
                                onChange={(e) => setNote(e.target.value)}
                            />
                            <div className="md:col-span-2 flex flex-wrap gap-2">
                                <Button type="submit" variant="primary" isLoading={isSubmitting} disabled={!scannedCode.trim()}>
                                    Submit Scan
                                </Button>
                                {!cameraActive ? (
                                    <Button type="button" variant="outline-primary" onClick={startCamera}>
                                        Start Camera Scan
                                    </Button>
                                ) : (
                                    <Button type="button" variant="outline-danger" onClick={stopCamera}>
                                        Stop Camera
                                    </Button>
                                )}
                                <label className="inline-flex items-center gap-2 text-sm text-gray-600">
                                    <input
                                        type="file"
                                        accept="image/*"
                                        onChange={(e) => handleFileScan(e.target.files ? e.target.files[0] : null)}
                                    />
                                    Upload QR image
                                </label>
                            </div>
                            <div className={`md:col-span-2 ${cameraActive ? '' : 'hidden'}`}>
                                <video
                                    ref={videoRef}
                                    className="w-full rounded-lg border border-gray-200"
                                    playsInline
                                    autoPlay
                                    muted
                                />
                            </div>
                        </form>
                    </CardBody>
                </Card>

                <Card>
                    <CardHeader>
                        <h5 className="text-lg font-semibold text-gray-900">Scan History</h5>
                    </CardHeader>
                    <CardBody className="p-0">
                        {scanHistory.length === 0 ? (
                            <div className="text-center text-gray-500 py-12">No scans yet</div>
                        ) : (
                            <div className="table-responsive">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>Time</th>
                                            <th>Code</th>
                                            <th>Result</th>
                                            <th>Note</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {scanHistory.map((scan) => (
                                            <tr key={scan.id}>
                                                <td className="text-sm">{new Date(scan.scanned_at).toLocaleString()}</td>
                                                <td className="text-sm font-mono">{scan.scanned_code || '-'}</td>
                                                <td>
                                                    <Badge variant={statusBadge(scan.result)}>{scan.result}</Badge>
                                                </td>
                                                <td className="text-sm">{scan.note || '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </CardBody>
                </Card>
            </div>
        </div>
    );
}

export default AuditScanPage;
