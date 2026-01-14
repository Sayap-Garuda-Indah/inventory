import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft } from 'lucide-react';
import {
    Button,
    Card,
    CardHeader,
    CardBody,
    CardFooter,
    Alert,
    Spinner,
    FormInput,
    FormTextarea,
} from './UI';

interface User {
    id: number;
    name: string;
    email: string;
}

interface IssueFormState {
    code: string;
    status: string;
    requested_by: string;
    approved_by: string;
    issued_at: string;
    note: string;
}

function IssueFormPage() {
    const { issueId } = useParams<{ issueId: string }>();
    const isEdit = Boolean(issueId);
    const navigate = useNavigate();
    const { user, isLoading: authLoading } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [users, setUsers] = useState<User[]>([]);
    const [form, setForm] = useState<IssueFormState>({
        code: '',
        status: 'DRAFT',
        requested_by: '',
        approved_by: '',
        issued_at: '',
        note: '',
    });

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    useEffect(() => {
        if (!authLoading && !user) {
            navigate('/login');
        }
    }, [authLoading, user, navigate]);

    useEffect(() => {
        if (!token) return;

        const loadUsers = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/users?page=1&page_size=100`, {
                    headers: { 'Authorization': `Bearer ${token}` },
                });
                if (response.ok) {
                    const data = await response.json();
                    setUsers(Array.isArray(data) ? data : (data.users || []));
                }
            } catch (err) {
                console.error('Error loading users:', err);
            }
        };

        loadUsers();
    }, [API_BASE_URL, token]);

    useEffect(() => {
        if (!isEdit || !token) return;

        const loadIssue = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const response = await fetch(`${API_BASE_URL}/issues/${issueId}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });
                if (!response.ok) throw new Error('Failed to load issue');

                const data = await response.json();
                const issueData = data.issue ?? data;

                setForm({
                    code: issueData.code || '',
                    status: issueData.status || 'DRAFT',
                    requested_by: issueData.requested_by ? String(issueData.requested_by) : '',
                    approved_by: issueData.approved_by ? String(issueData.approved_by) : '',
                    issued_at: issueData.issued_at ? issueData.issued_at.split('T')[0] : '',
                    note: issueData.note || '',
                });
            } catch (err) {
                setError((err as Error).message || 'Failed to load issue');
            } finally {
                setIsLoading(false);
            }
        };

        loadIssue();
    }, [API_BASE_URL, issueId, isEdit, token]);

    const handleChange = (field: keyof IssueFormState, value: string) => {
        setForm((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token) return;

        setIsLoading(true);
        setError(null);

        const payload = {
            code: form.code.trim(),
            status: form.status,
            requested_by: form.requested_by ? Number(form.requested_by) : null,
            approved_by: form.approved_by ? Number(form.approved_by) : null,
            issued_at: form.issued_at ? new Date(form.issued_at).toISOString() : null,
            note: form.note.trim() || null,
        };

        try {
            const response = await fetch(
                isEdit ? `${API_BASE_URL}/issues/${issueId}` : `${API_BASE_URL}/issues`,
                {
                    method: isEdit ? 'PUT' : 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                }
            );

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to save issue');
            }

            navigate('/dashboard');
        } catch (err) {
            setError((err as Error).message || 'Failed to save issue');
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading || isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Spinner size="lg" />
            </div>
        );
    }

    return (
        <div className="w-full h-full">
            <div className="px-4 py-6 max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-6 flex items-center gap-4">
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="text-blue-600 hover:text-blue-700 transition-colors"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900">
                            {isEdit ? 'Edit Issue' : 'Create New Issue'}
                        </h2>
                        <p className="text-gray-600 mt-1">Fill in the details below</p>
                    </div>
                </div>

                {error && (
                    <Alert variant="danger" dismissible onClose={() => setError(null)} className="mb-6">
                        {error}
                    </Alert>
                )}

                <Card>
                    <CardHeader>
                        <h5 className="font-bold">Issue Information</h5>
                    </CardHeader>
                    <CardBody>
                        <form onSubmit={handleSubmit}>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <FormInput
                                    label="Issue Code"
                                    placeholder="e.g., ISS-001"
                                    value={form.code}
                                    onChange={(e) => handleChange('code', e.target.value)}
                                    required
                                />
                                <div>
                                    <label className="form-label">Status</label>
                                    <select
                                        className="form-select"
                                        value={form.status}
                                        onChange={(e) => handleChange('status', e.target.value)}
                                        required
                                    >
                                        <option value="DRAFT">Draft</option>
                                        <option value="APPROVED">Approved</option>
                                        <option value="ISSUED">Issued</option>
                                        <option value="CANCELLED">Cancelled</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="form-label">Requested By</label>
                                    <select
                                        className="form-select"
                                        value={form.requested_by}
                                        onChange={(e) => handleChange('requested_by', e.target.value)}
                                    >
                                        <option value="">Select user</option>
                                        {users.map((u) => (
                                            <option key={u.id} value={u.id}>
                                                {u.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="form-label">Approved By</label>
                                    <select
                                        className="form-select"
                                        value={form.approved_by}
                                        onChange={(e) => handleChange('approved_by', e.target.value)}
                                    >
                                        <option value="">Select user</option>
                                        {users.map((u) => (
                                            <option key={u.id} value={u.id}>
                                                {u.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <FormInput
                                    label="Issued At"
                                    type="date"
                                    value={form.issued_at}
                                    onChange={(e) => handleChange('issued_at', e.target.value)}
                                />
                            </div>

                            <div className="grid grid-cols-1 gap-4 mb-6">
                                <FormTextarea
                                    label="Note"
                                    placeholder="Add issue notes..."
                                    value={form.note}
                                    onChange={(e) => handleChange('note', e.target.value)}
                                    rows={4}
                                />
                            </div>

                            <CardFooter className="bg-gray-50 flex justify-end gap-2">
                                <Button variant="secondary" onClick={() => navigate('/dashboard')}>
                                    Cancel
                                </Button>
                                <Button variant="primary" type="submit" disabled={isLoading}>
                                    {isLoading ? (
                                        <>
                                            <Spinner size="sm" className="mr-2" />
                                            {isEdit ? 'Saving...' : 'Creating...'}
                                        </>
                                    ) : (
                                        <>{isEdit ? 'Save Changes' : 'Create Issue'}</>
                                    )}
                                </Button>
                            </CardFooter>
                        </form>
                    </CardBody>
                </Card>
            </div>
        </div>
    );
}

export default IssueFormPage;
