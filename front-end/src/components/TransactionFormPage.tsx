import { useState, useEffect, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft } from 'lucide-react';
import Select from 'react-select';
import {
    Button,
    Card,
    CardHeader,
    CardBody,
    CardFooter,
    Alert,
    Spinner,
    FormInput,
    FormSelect,
    FormTextarea,
} from './UI';

interface Location {
    id: number;
    name: string;
    code: string;
}

interface Item {
    id: number;
    item_code: string;
    name: string;
}

interface ItemSelectOption {
    value: string;
    label: string;
}

interface UserOption {
    id: number;
    name: string;
    email: string;
    role?: string;
    active?: boolean;
}

interface TransactionDetailResponse {
    id: number;
    item_id: number;
    location_id: number;
    tx_type: string;
    qty: number;
    user_id: number;
    ref?: string | null;
    note?: string | null;
}

interface TransactionFormState {
    item_id: string;
    location_id: string;
    tx_type: string;
    qty: string;
    user_id: string;
    ref: string;
    note: string;
}

function formatApiErrorDetail(detail: unknown, fallback: string): string {
    if (!detail) return fallback;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        return detail
            .map((entry) => {
                if (typeof entry === 'string') return entry;
                if (entry && typeof entry === 'object') {
                    const msg = 'msg' in entry ? String((entry as { msg?: unknown }).msg) : '';
                    const loc = 'loc' in entry && Array.isArray((entry as { loc?: unknown[] }).loc)
                        ? (entry as { loc?: unknown[] }).loc?.join('.')
                        : '';
                    return loc ? `${loc}: ${msg}` : msg;
                }
                return String(entry);
            })
            .filter(Boolean)
            .join('; ') || fallback;
    }
    if (typeof detail === 'object') {
        try {
            return JSON.stringify(detail);
        } catch {
            return fallback;
        }
    }
    return String(detail);
}

function TransactionFormPage() {
    const navigate = useNavigate();
    const { txId } = useParams<{ txId?: string }>();
    const isEditMode = Boolean(txId);
    const { user, isLoading: authLoading } = useAuth();
    const isStaff = user?.role === 'STAFF';
    const [isLoading, setIsLoading] = useState(false);
    const [isPageLoading, setIsPageLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [locations, setLocations] = useState<Location[]>([]);
    const [items, setItems] = useState<Item[]>([]);
    const [users, setUsers] = useState<UserOption[]>([]);
    const [form, setForm] = useState<TransactionFormState>({
        item_id: '',
        location_id: '',
        tx_type: 'IN',
        qty: '',
        user_id: '',
        ref: '',
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

        const loadFormData = async () => {
            setIsPageLoading(true);
            try {
                const requests: Promise<Response>[] = [
                    fetch(`${API_BASE_URL}/locations?page=1&page_size=200`, {
                        headers: { 'Authorization': `Bearer ${token}` },
                    }),
                    fetch(`${API_BASE_URL}/items?page=1&page_size=100&active_only=1`, {
                        headers: { 'Authorization': `Bearer ${token}` },
                    }),
                    fetch(`${API_BASE_URL}/users?page=1&page_size=100&active_only=1`, {
                        headers: { 'Authorization': `Bearer ${token}` },
                    }),
                ];

                if (isEditMode && txId) {
                    requests.push(
                        fetch(`${API_BASE_URL}/transactions/${txId}`, {
                            headers: { 'Authorization': `Bearer ${token}` },
                        })
                    );
                }

                const responses = await Promise.all(requests);
                const [locRes, itemRes, usersRes, txRes] = responses;

                if (!locRes.ok) {
                    const err = await locRes.json().catch(() => ({}));
                    throw new Error(formatApiErrorDetail(err.detail, 'Failed to load locations'));
                }
                if (!itemRes.ok) {
                    const err = await itemRes.json().catch(() => ({}));
                    throw new Error(formatApiErrorDetail(err.detail, 'Failed to load items'));
                }
                if (!usersRes.ok) {
                    const err = await usersRes.json().catch(() => ({}));
                    throw new Error(formatApiErrorDetail(err.detail, 'Failed to load users'));
                }
                if (txRes && !txRes.ok) {
                    const err = await txRes.json().catch(() => ({}));
                    throw new Error(formatApiErrorDetail(err.detail, 'Failed to load transaction'));
                }

                const [locData, itemData, usersData] = await Promise.all([
                    locRes.json(),
                    itemRes.json(),
                    usersRes.json(),
                ]);

                setLocations(locData || []);
                setItems(itemData.items || []);

                const nextUsers: UserOption[] = Array.isArray(usersData) ? usersData : (usersData.users || []);
                setUsers(nextUsers);

                if (txRes) {
                    const txData: TransactionDetailResponse = await txRes.json();
                    setForm({
                        item_id: String(txData.item_id ?? ''),
                        location_id: String(txData.location_id ?? ''),
                        tx_type: txData.tx_type || 'IN',
                        qty: txData.qty !== undefined && txData.qty !== null ? String(txData.qty) : '',
                        user_id: txData.user_id ? String(txData.user_id) : '',
                        ref: txData.ref || '',
                        note: txData.note || '',
                    });
                } else if (user?.id) {
                    setForm((prev) => ({
                        ...prev,
                        user_id: prev.user_id || String(user.id),
                    }));
                }
            } catch (err) {
                setError((err as Error).message || 'Failed to load form data');
                console.error('Error loading metadata:', err);
            } finally {
                setIsPageLoading(false);
            }
        };

        loadFormData();
    }, [API_BASE_URL, token, isEditMode, txId, user?.id]);

    useEffect(() => {
        if (!user?.id) return;
        setForm((prev) => ({
            ...prev,
            user_id: prev.user_id || String(user.id),
        }));
    }, [user?.id]);

    const handleChange = (field: keyof TransactionFormState, value: string) => {
        setForm((prev) => ({ ...prev, [field]: value }));
    };

    const itemOptions = useMemo<ItemSelectOption[]>(
        () =>
            items.map((item) => ({
                value: String(item.id),
                label: `${item.item_code} - ${item.name}`,
            })),
        [items]
    );
    const selectedItemOption = useMemo<ItemSelectOption | null>(() => {
        if (!form.item_id) return null;
        return itemOptions.find((option) => option.value === form.item_id) || null;
    }, [form.item_id, itemOptions]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token) return;

        setIsLoading(true);
        setError(null);

        const payload: {
            item_id: number;
            location_id: number;
            tx_type: string;
            qty: number;
            user_id: number;
            ref: string | null;
            note: string | null;
        } = {
            item_id: Number(form.item_id),
            location_id: Number(form.location_id),
            tx_type: form.tx_type,
            qty: Number(form.qty),
            user_id: Number(form.user_id),
            ref: form.ref.trim() || null,
            note: form.note.trim() || null,
        };

        try {
            const response = await fetch(
                isEditMode && txId ? `${API_BASE_URL}/transactions/${txId}` : `${API_BASE_URL}/transactions`,
                {
                method: isEditMode ? 'PUT' : 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
                }
            );

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || `Failed to ${isEditMode ? 'update' : 'create'} transaction`);
            }

            navigate('/transactions');
        } catch (err) {
            setError((err as Error).message || `Failed to ${isEditMode ? 'update' : 'create'} transaction`);
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading || isPageLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Spinner size="lg" />
            </div>
        );
    }

    const locationOptions = [
        { value: '', label: 'Select location' },
        ...locations.map((location) => ({
            value: String(location.id),
            label: `${location.code} - ${location.name}`,
        })),
    ];

    const typeOptions = [
        { value: 'IN', label: 'IN (Receive)' },
        { value: 'OUT', label: 'OUT (Issue)' },
        { value: 'ADJ', label: 'ADJ (Adjust)' },
        { value: 'XFER', label: 'XFER (Transfer)' },
    ];

    const ownerOptions = [
        { value: '', label: 'Select owner' },
        ...users.map((owner) => ({
            value: String(owner.id),
            label: owner.name,
        })),
    ];

    return (
        <div className="w-full h-full">
            <div className="px-4 py-6 max-w-2xl mx-auto">
                <div className="mb-6 flex items-center gap-4">
                    <button
                        onClick={() => navigate('/transactions')}
                        className="text-blue-600 hover:text-blue-700 transition-colors"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900">
                            {isEditMode ? 'Edit Stock Transaction' : 'New Stock Transaction'}
                        </h2>
                        <p className="text-gray-600 mt-1">
                            {isEditMode ? 'Update a stock transaction' : 'Record a stock transaction'}
                        </p>
                        {isStaff && (
                            <p className="text-xs text-amber-700 mt-1">
                                You can create transactions only for items assigned to you.
                            </p>
                        )}
                    </div>
                </div>

                {error && (
                    <Alert variant="danger" dismissible onClose={() => setError(null)} className="mb-6">
                        {error}
                    </Alert>
                )}

                <Card>
                    <CardHeader>
                        <h5 className="font-bold">Transaction Details</h5>
                    </CardHeader>
                    <CardBody>
                        <form onSubmit={handleSubmit}>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label className="form-label">Item</label>
                                    <Select
                                        options={itemOptions}
                                        value={selectedItemOption}
                                        onChange={(option) => handleChange('item_id', option ? option.value : '')}
                                        isClearable
                                        placeholder="Search item code or name"
                                        classNamePrefix="react-select"
                                    />
                                    {isStaff && (
                                        <p className="text-xs text-gray-500 mt-1">Showing your owned items only.</p>
                                    )}
                                </div>
                                <FormSelect
                                    label="Location"
                                    options={locationOptions}
                                    value={form.location_id}
                                    onChange={(e) => handleChange('location_id', e.target.value)}
                                    required
                                />
                                <FormSelect
                                    label="Transaction Type"
                                    options={typeOptions}
                                    value={form.tx_type}
                                    onChange={(e) => handleChange('tx_type', e.target.value)}
                                    required
                                />
                                <FormSelect
                                    label="Assigned to"
                                    options={ownerOptions}
                                    value={form.user_id}
                                    onChange={(e) => handleChange('user_id', e.target.value)}
                                    required
                                />
                                <FormInput
                                    label="Quantity"
                                    type="number"
                                    min="1"
                                    step="1"
                                    placeholder="Enter quantity"
                                    value={form.qty}
                                    onChange={(e) => handleChange('qty', e.target.value)}
                                    required
                                />
                            </div>
                            <div className="grid grid-cols-1 gap-4">
                                <FormInput
                                    label="Reference"
                                    placeholder="PO, invoice, or ticket number"
                                    value={form.ref}
                                    onChange={(e) => handleChange('ref', e.target.value)}
                                />
                                <FormTextarea
                                    label="Note"
                                    placeholder="Add an optional note"
                                    rows={4}
                                    value={form.note}
                                    onChange={(e) => handleChange('note', e.target.value)}
                                />
                            </div>
                        </form>
                    </CardBody>
                    <CardFooter className="bg-gray-50 flex justify-end gap-2">
                        <Button variant="secondary" onClick={() => navigate('/transactions')}>
                            Cancel
                        </Button>
                        <Button variant="primary" onClick={handleSubmit} disabled={isLoading}>
                            {isLoading ? (
                                <>
                                    <Spinner size="sm" className="mr-2" />
                                    Saving...
                                </>
                            ) : (
                                <>{isEditMode ? 'Save Changes' : 'Save Transaction'}</>
                            )}
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        </div>
    );
}

export default TransactionFormPage;
