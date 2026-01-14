import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft } from 'lucide-react';
import {
    Button,
    Card,
    CardHeader,
    CardBody,
    Alert,
    Spinner,
    Badge,
    FormSelect,
} from './UI';

interface IssueItem {
    id: number;
    issue_id: number;
    item_id: number;
    qty: number;
    item_code?: string;
    item_name?: string;
    category_id?: number;
    category_name?: string | { id: number; name: string };
    unit_id?: number;
    unit_name?: string;
    unit_symbol?: string;
    description?: string;
    active?: boolean;
}

interface Issue {
    id: number;
    code: string;
    status: string;
    requested_by?: number | string | { id: number; name?: string };
    approved_by?: number | string | { id: number; name?: string };
    issued_at?: string;
    note?: string;
    created_at?: string;
    updated_at?: string;
}

interface IssueDetailsData {
    issue: Issue;
    items: IssueItem[];
    total_qty: number;
    total_items: number;
}

function IssueDetailsPage() {
    const { issueId } = useParams<{ issueId: string }>();
    const navigate = useNavigate();
    const { user, isLoading: authLoading } = useAuth();
    const [issueDetails, setIssueDetails] = useState<IssueDetailsData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [sortBy, setSortBy] = useState<'name' | 'item_code' | 'qty' | 'category'>('name');
    const [filterCategory, setFilterCategory] = useState<string>('all');
    const [requestedByName, setRequestedByName] = useState<string>('');
    const [approvedByName, setApprovedByName] = useState<string>('');

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    useEffect(() => {
        if (!authLoading && !user) {
            navigate('/login');
        }
    }, [authLoading, user, navigate]);

    useEffect(() => {
        if (issueId && token) {
            fetchIssueDetails();
        }
    }, [issueId, token]);

    useEffect(() => {
        const loadUserNames = async () => {
            if (!issueDetails) return;

            const requestedBy = issueDetails.issue.requested_by;
            if (requestedBy && typeof requestedBy === 'object') {
                setRequestedByName(requestedBy.name || `User #${requestedBy.id ?? ''}`.trim());
            } else if (requestedBy && typeof requestedBy === 'number') {
                const userData = await fetchUserData(requestedBy);
                if (userData) {
                    setRequestedByName(userData.name || `User #${requestedBy}`);
                }
            } else {
                setRequestedByName('');
            }

            const approvedBy = issueDetails.issue.approved_by;
            if (approvedBy && typeof approvedBy === 'object') {
                setApprovedByName(approvedBy.name || `User #${approvedBy.id ?? ''}`.trim());
            } else if (approvedBy && typeof approvedBy === 'number') {
                const userData = await fetchUserData(approvedBy);
                if (userData) {
                    setApprovedByName(userData.name || `User #${approvedBy}`);
                }
            } else {
                setApprovedByName('');
            }
        };
        loadUserNames();
    }, [issueDetails]);

    const fetchIssueDetails = async () => {
        if (!issueId || !token) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(
                `${API_BASE_URL}/issues/${issueId}/items`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to fetch issue details');
            }

            const data = await response.json();

            if (data.issue && data.items !== undefined) {
                setIssueDetails(data);
            } else {
                throw new Error('Invalid response format');
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to load issue details';
            setError(errorMessage);
            console.error('Error fetching issue details:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchUserData = async (userId: number | string) => {
        if (!token) return null;

        try {
            const response = await fetch(
                `${API_BASE_URL}/users/${userId}`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                }
            );

            if (!response.ok) {
                throw new Error('Failed to fetch user data');
            }

            const data = await response.json();
            return data;
        } catch (err) {
            console.error('Error fetching user data:', err);
            return null;
        }
    };

    const getCategoryName = (cat: unknown): string => {
        if (!cat && cat !== 0) return '';
        if (typeof cat === 'object' && cat !== null) {
            const record = cat as { name?: string; id?: number | string };
            return record.name ?? String(record.id ?? '');
        }
        return String(cat);
    };

    const getStatusColor = (status: string): 'warning' | 'success' | 'info' | 'secondary' | 'danger' => {
        switch (status?.toUpperCase()) {
            case 'DRAFT':
                return 'warning';
            case 'APPROVED':
                return 'info';
            case 'ISSUED':
                return 'success';
            case 'CANCELLED':
                return 'secondary';
            default:
                return 'secondary';
        }
    };

    const getUserDisplay = (userValue: unknown, userName: string | null): string => {
        if (!userValue) return '-';
        if (userName) return userName;
        if (typeof userValue === 'number') return `User #${userValue}`;
        if (typeof userValue === 'string') return userValue;
        if (typeof userValue === 'object' && userValue !== null) {
            const record = userValue as { name?: string; id?: number | string };
            return record.name ?? `User #${record.id ?? ''}`.trim();
        }
        return '-';
    };

    const categories = useMemo(() => {
        if (!issueDetails?.items) return [];
        const map = new Map<string, string>();
        issueDetails.items.forEach((item) => {
            const name = getCategoryName(item.category_name);
            const id = item.category_id ? String(item.category_id) : name;
            if (name) map.set(id, name);
        });
        return Array.from(map.entries())
            .map(([id, name]) => ({ id, name }))
            .sort((a, b) => a.name.localeCompare(b.name));
    }, [issueDetails]);

    const sortedItems = useMemo(() => {
        if (!issueDetails?.items) return [];

        let filtered = issueDetails.items;

        if (filterCategory !== 'all') {
            filtered = filtered.filter((item) => getCategoryName(item.category_name) === filterCategory);
        }

        const sorted = [...filtered];
        switch (sortBy) {
            case 'name':
                sorted.sort((a, b) => (a.item_name || '').localeCompare(b.item_name || ''));
                break;
            case 'item_code':
                sorted.sort((a, b) => (a.item_code || '').localeCompare(b.item_code || ''));
                break;
            case 'qty':
                sorted.sort((a, b) => b.qty - a.qty);
                break;
            case 'category':
                sorted.sort((a, b) =>
                    getCategoryName(a.category_name).localeCompare(getCategoryName(b.category_name))
                );
                break;
        }

        return sorted;
    }, [issueDetails, sortBy, filterCategory]);

    if (authLoading || isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Spinner size="lg" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="px-4 py-6 max-w-5xl mx-auto">
                <Alert variant="danger" dismissible onClose={() => setError(null)}>
                    <div className="space-y-3">
                        <p className="font-semibold">Error Loading Issue</p>
                        <p>{error}</p>
                        <Button variant="danger" onClick={() => navigate('/dashboard')}>
                            Back to Dashboard
                        </Button>
                    </div>
                </Alert>
            </div>
        );
    }

    if (!issueDetails) {
        return (
            <div className="px-4 py-6 max-w-5xl mx-auto">
                <Alert variant="warning">
                    <div className="space-y-3">
                        <p className="font-semibold">Issue Not Found</p>
                        <Button variant="secondary" onClick={() => navigate('/dashboard')}>
                            Back to Dashboard
                        </Button>
                    </div>
                </Alert>
            </div>
        );
    }

    const sortOptions = [
        { value: 'name', label: 'Item Name' },
        { value: 'item_code', label: 'Item Code' },
        { value: 'qty', label: 'Quantity' },
        { value: 'category', label: 'Category' },
    ];

    const categoryOptions = [
        { value: 'all', label: 'All Categories' },
        ...categories.map((cat) => ({ value: cat.name, label: cat.name })),
    ];

    return (
        <div className="w-full h-full">
            <div className="px-4 py-6 max-w-6xl mx-auto">
                <div className="mb-6 flex items-center gap-4">
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="text-blue-600 hover:text-blue-700 transition-colors"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900">Issue Details</h2>
                        <p className="text-gray-600 mt-1">Issue code: {issueDetails.issue.code}</p>
                    </div>
                </div>

                <Card className="mb-6">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <h5 className="font-bold">Issue Information</h5>
                            <Badge variant={getStatusColor(issueDetails.issue.status)}>
                                {issueDetails.issue.status}
                            </Badge>
                        </div>
                    </CardHeader>
                    <CardBody>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            <div>
                                <p className="text-sm text-gray-500">Issue Code</p>
                                <p className="font-mono text-blue-600">{issueDetails.issue.code}</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">Status</p>
                                <p>{issueDetails.issue.status}</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">Requested By</p>
                                <p>{getUserDisplay(issueDetails.issue.requested_by, requestedByName)}</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">Approved By</p>
                                <p>{getUserDisplay(issueDetails.issue.approved_by, approvedByName)}</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">Issued At</p>
                                <p>
                                    {issueDetails.issue.issued_at
                                        ? new Date(issueDetails.issue.issued_at).toLocaleString()
                                        : '-'}
                                </p>
                            </div>
                        </div>

                        {issueDetails.issue.note && (
                            <div className="pt-4 mt-4 border-t border-gray-200">
                                <p className="text-sm text-gray-500">Note</p>
                                <p>{issueDetails.issue.note}</p>
                            </div>
                        )}
                    </CardBody>
                </Card>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <Card>
                        <CardBody className="text-center">
                            <p className="text-sm text-gray-500">Total Items</p>
                            <p className="text-3xl font-bold text-gray-900">{issueDetails.total_items || 0}</p>
                        </CardBody>
                    </Card>
                    <Card>
                        <CardBody className="text-center">
                            <p className="text-sm text-gray-500">Total Quantity</p>
                            <p className="text-3xl font-bold text-gray-900">
                                {issueDetails?.total_qty
                                    ? parseFloat(issueDetails.total_qty.toString()).toFixed(2)
                                    : '0.00'}
                            </p>
                        </CardBody>
                    </Card>
                    <Card>
                        <CardBody className="text-center">
                            <p className="text-sm text-gray-500">Categories</p>
                            <p className="text-3xl font-bold text-gray-900">{categories.length || 0}</p>
                        </CardBody>
                    </Card>
                </div>

                <Card className="mb-6">
                    <CardBody>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormSelect
                                label="Sort By"
                                options={sortOptions}
                                value={sortBy}
                                onChange={(e) =>
                                    setSortBy(e.target.value as 'name' | 'item_code' | 'qty' | 'category')
                                }
                            />
                            <FormSelect
                                label="Filter Category"
                                options={categoryOptions}
                                value={filterCategory}
                                onChange={(e) => setFilterCategory(e.target.value)}
                            />
                        </div>
                    </CardBody>
                </Card>

                <Card>
                    <CardHeader>
                        <h5 className="font-bold text-lg">Items ({sortedItems.length})</h5>
                    </CardHeader>
                    <CardBody className="p-0">
                        {sortedItems.length === 0 ? (
                            <div className="text-center text-gray-500 py-12">
                                <p className="text-lg">No items found for this issue</p>
                            </div>
                        ) : (
                            <div className="table-responsive">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>Item Code</th>
                                            <th>Item Name</th>
                                            <th>Category</th>
                                            <th>Quantity</th>
                                            <th>Unit</th>
                                            <th>Description</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sortedItems.map((item) => (
                                            <tr key={`item-${item.id}`}>
                                                <td>
                                                    <code className="text-blue-600 font-mono text-sm">
                                                        {item.item_code || '-'}
                                                    </code>
                                                </td>
                                                <td>{item.item_name || '-'}</td>
                                                <td>
                                                    {item.category_name ? (
                                                        <Badge variant="secondary">
                                                            {getCategoryName(item.category_name)}
                                                        </Badge>
                                                    ) : (
                                                        <span className="text-gray-500">-</span>
                                                    )}
                                                </td>
                                                <td className="font-semibold">
                                                    {item.qty
                                                        ? parseFloat(item.qty.toString()).toFixed(2)
                                                        : '0.00'}
                                                </td>
                                                <td title={item.unit_name || ''}>
                                                    {item.unit_symbol ? (
                                                        <span>{item.unit_symbol}</span>
                                                    ) : (
                                                        <span className="text-gray-500">-</span>
                                                    )}
                                                </td>
                                                <td className="text-sm text-gray-600">
                                                    <span className="block max-w-xs truncate" title={item.description || '-'}>
                                                        {item.description
                                                            ? item.description.substring(0, 40) +
                                                              (item.description.length > 40 ? '...' : '')
                                                            : '-'}
                                                    </span>
                                                </td>
                                                <td>
                                                    <Badge variant={item.active ? 'success' : 'danger'}>
                                                        {item.active ? 'Active' : 'Inactive'}
                                                    </Badge>
                                                </td>
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

export default IssueDetailsPage;
