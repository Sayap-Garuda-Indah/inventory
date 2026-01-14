import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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

interface TransactionFormState {
    item_id: string;
    location_id: string;
    tx_type: string;
    qty: string;
    ref: string;
    note: string;
}

function TransactionFormPage() {
    const navigate = useNavigate();
    const { user, isLoading: authLoading } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [locations, setLocations] = useState<Location[]>([]);
    const [items, setItems] = useState<Item[]>([]);
    const [form, setForm] = useState<TransactionFormState>({
        item_id: '',
        location_id: '',
        tx_type: 'IN',
        qty: '',
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

        const loadMetadata = async () => {
            try {
                const [locRes, itemRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/locations?page=1&page_size=200`, {
                        headers: { 'Authorization': `Bearer ${token}` },
                    }),
                    fetch(`${API_BASE_URL}/items?page=1&page_size=200`, {
                        headers: { 'Authorization': `Bearer ${token}` },
                    }),
                ]);

                if (locRes.ok) {
                    const locData = await locRes.json();
                    setLocations(locData || []);
                }
                if (itemRes.ok) {
                    const itemData = await itemRes.json();
                    setItems(itemData.items || []);
                }
            } catch (err) {
                console.error('Error loading metadata:', err);
            }
        };

        loadMetadata();
    }, [API_BASE_URL, token]);

    const handleChange = (field: keyof TransactionFormState, value: string) => {
        setForm((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token) return;

        setIsLoading(true);
        setError(null);

        const payload = {
            item_id: Number(form.item_id),
            location_id: Number(form.location_id),
            tx_type: form.tx_type,
            qty: Number(form.qty),
            ref: form.ref.trim() || null,
            note: form.note.trim() || null,
        };

        try {
            const response = await fetch(`${API_BASE_URL}/stock-transactions`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to create transaction');
            }

            navigate('/transactions');
        } catch (err) {
            setError((err as Error).message || 'Failed to create transaction');
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Spinner size="lg" />
            </div>
        );
    }

    const itemOptions = [
        { value: '', label: 'Select item' },
        ...items.map((item) => ({
            value: String(item.id),
            label: `${item.item_code} - ${item.name}`,
        })),
    ];

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
                        <h2 className="text-3xl font-bold text-gray-900">New Stock Transaction</h2>
                        <p className="text-gray-600 mt-1">Record a stock transaction</p>
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
                                <FormSelect
                                    label="Item"
                                    options={itemOptions}
                                    value={form.item_id}
                                    onChange={(e) => handleChange('item_id', e.target.value)}
                                    required
                                />
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
                        <Button
                            variant="primary"
                            onClick={handleSubmit}
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <Spinner size="sm" className="mr-2" />
                                    Saving...
                                </>
                            ) : (
                                <>Save Transaction</>
                            )}
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        </div>
    );
}

export default TransactionFormPage;
