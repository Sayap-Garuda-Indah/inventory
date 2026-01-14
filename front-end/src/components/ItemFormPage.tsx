import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft } from 'lucide-react';
import Select from 'react-select';
import {
    Alert,
    Button,
    Card,
    CardBody,
    CardFooter,
    CardHeader,
    FormCheckbox,
    FormInput,
    FormSelect,
    FormTextarea,
    Spinner,
} from './UI';

interface Category {
    id: number;
    name: string;
}

interface Unit {
    id: number;
    name: string;
    symbol: string;
}

interface UserOption {
    id: number;
    name: string;
    email: string;
}

interface IssueOption {
    id: number;
    code: string;
    status: string;
}

interface IssueSelectOption {
    value: string;
    label: string;
}

interface ItemFormState {
    item_code: string;
    name: string;
    category_id: string;
    unit_id: string;
    owner_user_id: string;
    qrcode: string;
    description: string;
    min_stock: string;
    image_url: string;
    active: boolean;
}

function ItemFormPage() {
    const { itemId } = useParams<{ itemId: string }>();
    const isEdit = Boolean(itemId);
    const navigate = useNavigate();
    const { user, isLoading: authLoading } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [categories, setCategories] = useState<Category[]>([]);
    const [units, setUnits] = useState<Unit[]>([]);
    const [users, setUsers] = useState<UserOption[]>([]);
    const [issues, setIssues] = useState<IssueOption[]>([]);
    const [issueId, setIssueId] = useState('');
    const [form, setForm] = useState<ItemFormState>({
        item_code: '',
        name: '',
        category_id: '',
        unit_id: '',
        owner_user_id: '',
        qrcode: '',
        description: '',
        min_stock: '0',
        image_url: '',
        active: true,
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
                const [categoriesRes, unitsRes, usersRes, issuesRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/categories?page=1&page_size=100`, {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json',
                        },
                    }),
                    fetch(`${API_BASE_URL}/units?page=1&page_size=100`, {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json',
                        },
                    }),
                    fetch(`${API_BASE_URL}/users?page=1&page_size=100&active_only=1`, {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json',
                        },
                    }),
                    fetch(`${API_BASE_URL}/issues?page=1&page_size=100`, {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json',
                        },
                    }),
                ]);

                if (categoriesRes.ok) {
                    const categoriesData = await categoriesRes.json();
                    setCategories(categoriesData || []);
                }
                if (unitsRes.ok) {
                    const unitsData = await unitsRes.json();
                    setUnits(unitsData.units || []);
                }
                if (usersRes.ok) {
                    const usersData = await usersRes.json();
                    setUsers(usersData.users || []);
                }
                if (issuesRes.ok) {
                    const issuesData = await issuesRes.json();
                    const nextIssues = Array.isArray(issuesData) ? issuesData : (issuesData.issues || []);
                    setIssues(nextIssues);
                }
            } catch (err) {
                console.error('Error loading metadata:', err);
            }
        };

        loadMetadata();
    }, [API_BASE_URL, token]);

    useEffect(() => {
        if (!isEdit || !token) return;

        const loadItem = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const response = await fetch(`${API_BASE_URL}/items/${itemId}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });
                if (!response.ok) {
                    throw new Error('Failed to load item');
                }
                const data = await response.json();
                setForm({
                    item_code: data.item_code || '',
                    name: data.name || '',
                    category_id: data.category_id ? String(data.category_id) : '',
                    unit_id: data.unit_id ? String(data.unit_id) : '',
                    owner_user_id: data.owner_user_id ? String(data.owner_user_id) : '',
                    qrcode: data.qrcode || '',
                    description: data.description || '',
                    min_stock: typeof data.min_stock === 'number' ? String(data.min_stock) : '0',
                    image_url: data.image_url || '',
                    active: Boolean(data.active),
                });
            } catch (err) {
                setError((err as Error).message || 'Failed to load item');
            } finally {
                setIsLoading(false);
            }
        };

        loadItem();
    }, [API_BASE_URL, itemId, isEdit, token]);

    const issueLabels = useMemo(() => {
        return issues.map((issue) => ({
            value: String(issue.id),
            label: `${issue.code} (${issue.status})`,
        }));
    }, [issues]);

    const selectedIssueOption = useMemo<IssueSelectOption | null>(() => {
        if (!issueId) return null;
        return issueLabels.find((option) => option.value === issueId) || null;
    }, [issueId, issueLabels]);

    const handleChange = (field: keyof ItemFormState, value: string | boolean) => {
        setForm((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token) return;

        setIsSaving(true);
        setError(null);

        const payload = {
            item_code: form.item_code.trim(),
            name: form.name.trim(),
            category_id: Number(form.category_id),
            unit_id: Number(form.unit_id),
            owner_user_id: form.owner_user_id ? Number(form.owner_user_id) : null,
            qrcode: form.qrcode.trim() || null,
            description: form.description.trim() || null,
            min_stock: Number(form.min_stock || 0),
            image_url: form.image_url.trim() || null,
            active: form.active,
        };

        try {
            const response = await fetch(
                isEdit ? `${API_BASE_URL}/items/${itemId}` : `${API_BASE_URL}/items`,
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
                throw new Error(err.detail || 'Failed to save item');
            }

            const savedItem = await response.json();

            if (issueId) {
                const issueResponse = await fetch(`${API_BASE_URL}/issue-items`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        issue_id: Number(issueId),
                        item_id: savedItem.id,
                        qty: 1,
                    }),
                });

                if (!issueResponse.ok) {
                    const err = await issueResponse.json();
                    throw new Error(err.detail || 'Item saved but failed to link issue');
                }
            }

            navigate('/items');
        } catch (err) {
            setError((err as Error).message || 'Failed to save item');
        } finally {
            setIsSaving(false);
        }
    };

    const categoryOptions = [
        { value: '', label: 'Select category' },
        ...categories.map((cat) => ({ value: String(cat.id), label: cat.name })),
    ];

    const unitOptions = [
        { value: '', label: 'Select unit' },
        ...units.map((unit) => ({ value: String(unit.id), label: `${unit.name} (${unit.symbol})` })),
    ];

    const ownerOptions = [
        { value: '', label: 'Unassigned' },
        ...users.map((u) => ({ value: String(u.id), label: `${u.name} (${u.email})` })),
    ];

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
                <div className="mb-6 flex items-center gap-4">
                    <button
                        onClick={() => navigate('/items')}
                        className="text-blue-600 hover:text-blue-700 transition-colors"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900">
                            {isEdit ? 'Edit Item' : 'Create New Item'}
                        </h2>
                        <p className="text-gray-600 mt-1">Fill in the item details below</p>
                    </div>
                </div>

                {error && (
                    <Alert variant="danger" dismissible onClose={() => setError(null)} className="mb-6">
                        {error}
                    </Alert>
                )}

                <Card>
                    <CardHeader>
                        <h5 className="font-bold">Item Information</h5>
                    </CardHeader>
                    <CardBody>
                        <form onSubmit={handleSubmit}>
                            <div className="grid grid-cols-1 gap-4 mb-6">
                                <div>
                                    <label className="form-label">Issue</label>
                                    <Select
                                        options={issueLabels}
                                        value={selectedIssueOption}
                                        onChange={(option) => setIssueId(option ? option.value : '')}
                                        isClearable
                                        placeholder="Search issue code or status"
                                        classNamePrefix="react-select"
                                    />
                                    <p className="text-sm text-gray-500 mt-1">
                                        Select an issue from the dropdown.
                                    </p>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <FormInput
                                    label="Item Code"
                                    value={form.item_code}
                                    onChange={(e) => handleChange('item_code', e.target.value)}
                                    required
                                />
                                <FormInput
                                    label="Name"
                                    value={form.name}
                                    onChange={(e) => handleChange('name', e.target.value)}
                                    required
                                />
                                <FormSelect
                                    label="Category"
                                    options={categoryOptions}
                                    value={form.category_id}
                                    onChange={(e) => handleChange('category_id', e.target.value)}
                                    required
                                />
                                <FormSelect
                                    label="Unit"
                                    options={unitOptions}
                                    value={form.unit_id}
                                    onChange={(e) => handleChange('unit_id', e.target.value)}
                                    required
                                />
                                <FormSelect
                                    label="Owner"
                                    options={ownerOptions}
                                    value={form.owner_user_id}
                                    onChange={(e) => handleChange('owner_user_id', e.target.value)}
                                />
                                <FormInput
                                    label="QR Code"
                                    value={form.qrcode}
                                    onChange={(e) => handleChange('qrcode', e.target.value)}
                                />
                            </div>

                            <FormTextarea
                                label="Description"
                                rows={4}
                                value={form.description}
                                onChange={(e) => handleChange('description', e.target.value)}
                            />

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                                <FormInput
                                    label="Min Stock"
                                    type="number"
                                    step="1"
                                    min="0"
                                    value={form.min_stock}
                                    onChange={(e) => handleChange('min_stock', e.target.value)}
                                />
                                <FormInput
                                    label="Image URL"
                                    value={form.image_url}
                                    onChange={(e) => handleChange('image_url', e.target.value)}
                                />
                            </div>

                            <div className="mt-4">
                                <FormCheckbox
                                    id="item-active"
                                    label="Active"
                                    checked={form.active}
                                    onChange={(e) => handleChange('active', e.target.checked)}
                                />
                            </div>

                            <CardFooter className="bg-gray-50 flex justify-end gap-2 mt-6">
                                <Button variant="secondary" onClick={() => navigate('/items')}>
                                    Cancel
                                </Button>
                                <Button variant="primary" type="submit" disabled={isSaving}>
                                    {isSaving ? (
                                        <>
                                            <Spinner size="sm" className="mr-2" />
                                            {isEdit ? 'Saving...' : 'Creating...'}
                                        </>
                                    ) : (
                                        <>{isEdit ? 'Save Changes' : 'Create Item'}</>
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

export default ItemFormPage;
