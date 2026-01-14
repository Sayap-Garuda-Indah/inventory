import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Inbox, Plus, ArrowLeftRight, Pencil, Trash2 } from 'lucide-react';
import {
    Button,
    Card,
    CardHeader,
    CardBody,
    Alert,
    Spinner,
    Badge,
    Pagination,
    PaginationInfo,
    FormInput,
} from './UI';

interface Transaction {
    id: number;
    item_id: number;
    item_code?: string;
    item_name?: string;
    location_id: number;
    location_name?: string;
    tx_type: string;
    qty: number;
    qty_on_hand?: number;
    ref?: string | null;
    note?: string | null;
    tx_at: string;
    user_id: number;
}

interface TransactionListResponse {
    txs: Transaction[];
    total: number;
    page: number;
    page_size: number;
}

interface ItemOption {
    id: number;
    item_code: string;
    name: string;
}

interface LocationOption {
    id: number;
    name: string;
}

function TransactionsPage() {
    const { user: currentUser, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [items, setItems] = useState<ItemOption[]>([]);
    const [locations, setLocations] = useState<LocationOption[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalItems, setTotalItems] = useState(0);
    const [pageSize] = useState(50);
    const [filters, setFilters] = useState({
        search: '',
        tx_type: 'all',
        item_id: '',
        location_id: '',
    });
    const [searchInput, setSearchInput] = useState('');

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    useEffect(() => {
        if (!authLoading && !currentUser) {
            navigate('/login');
        }
    }, [authLoading, currentUser, navigate]);

    useEffect(() => {
        if (!token) return;
        fetchTransactions();
    }, [currentPage, filters, token]);

    useEffect(() => {
        if (!token) return;
        fetchMetadata();
    }, [token]);

    useEffect(() => {
        setCurrentPage(1);
    }, [filters]);

    useEffect(() => {
        const timer = window.setTimeout(() => {
            setFilters((prev) => ({ ...prev, search: searchInput }));
        }, 300);
        return () => window.clearTimeout(timer);
    }, [searchInput]);

    const fetchMetadata = async () => {
        if (!token) return;
        try {
            const [itemsRes, locationsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/items?page=1&page_size=100&active_only=1`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                }),
                fetch(`${API_BASE_URL}/locations?page=1&page_size=100&active_only=1`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                }),
            ]);

            if (itemsRes.ok) {
                const data = await itemsRes.json();
                setItems(data.items || []);
            }
            if (locationsRes.ok) {
                const data = await locationsRes.json();
                setLocations(data || []);
            }
        } catch (err) {
            console.error('Error fetching metadata:', err);
        }
    };

    const fetchTransactions = async () => {
        if (!token) return;

        setIsLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams({
                page: currentPage.toString(),
                page_size: pageSize.toString(),
            });
            if (filters.search.trim()) params.append('search', filters.search.trim());
            if (filters.tx_type !== 'all') params.append('tx_type', filters.tx_type);
            if (filters.item_id) params.append('item_id', filters.item_id);
            if (filters.location_id) params.append('location_id', filters.location_id);

            const response = await fetch(`${API_BASE_URL}/transactions?${params.toString()}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch transactions');
            }

            const data: TransactionListResponse = await response.json();
            setTransactions(data.txs || []);
            setTotalItems(data.total);
            setTotalPages(Math.ceil(data.total / pageSize));
        } catch (err) {
            setError((err as Error).message || 'Failed to load transactions');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (txId: number) => {
        if (!token) return;
        if (!window.confirm('Delete this transaction?')) return;

        try {
            const response = await fetch(`${API_BASE_URL}/transactions/${txId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to delete transaction');
            }
            fetchTransactions();
        } catch (err) {
            setError((err as Error).message || 'Failed to delete transaction');
        }
    };

    const getTxBadge = (txType: string): 'success' | 'danger' | 'warning' | 'secondary' => {
        switch (txType) {
            case 'IN':
                return 'success';
            case 'OUT':
                return 'danger';
            case 'ADJ':
                return 'warning';
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

    return (
        <div className="w-full h-full">
            <div className="px-4 py-6 w-full">
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                            <ArrowLeftRight className="w-6 h-6" />
                            Stock Transactions
                        </h2>
                        <p className="text-gray-600 mt-1">Track stock movements and adjustments</p>
                    </div>
                    {(currentUser?.role === 'ADMIN' || currentUser?.role === 'STAFF') && (
                        <Button variant="primary" onClick={() => navigate('/transactions/new')}>
                            <Plus className="w-4 h-4 mr-2" />
                            New Transaction
                        </Button>
                    )}
                </div>

                {error && (
                    <Alert variant="danger" dismissible onClose={() => setError(null)} className="mb-4">
                        {error}
                    </Alert>
                )}

                <Card className="mb-6">
                    <CardBody>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <FormInput
                                label="Search"
                                placeholder="Item, location, ref, note..."
                                value={searchInput}
                                onChange={(e) => setSearchInput(e.target.value)}
                            />
                            <div>
                                <label className="form-label">Type</label>
                                <select
                                    className="form-select"
                                    value={filters.tx_type}
                                    onChange={(e) => setFilters((prev) => ({ ...prev, tx_type: e.target.value }))}
                                >
                                    <option value="all">All</option>
                                    <option value="IN">IN</option>
                                    <option value="OUT">OUT</option>
                                    <option value="ADJ">ADJ</option>
                                    <option value="XFER">XFER</option>
                                </select>
                            </div>
                            <div>
                                <label className="form-label">Item</label>
                                <select
                                    className="form-select"
                                    value={filters.item_id}
                                    onChange={(e) => setFilters((prev) => ({ ...prev, item_id: e.target.value }))}
                                >
                                    <option value="">All Items</option>
                                    {items.map((item) => (
                                        <option key={item.id} value={item.id}>
                                            {item.item_code} - {item.name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="form-label">Location</label>
                                <select
                                    className="form-select"
                                    value={filters.location_id}
                                    onChange={(e) => setFilters((prev) => ({ ...prev, location_id: e.target.value }))}
                                >
                                    <option value="">All Locations</option>
                                    {locations.map((loc) => (
                                        <option key={loc.id} value={loc.id}>
                                            {loc.name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </CardBody>
                </Card>

                <Card>
                    <CardHeader>
                        <h5 className="font-bold text-lg">Transactions ({totalItems})</h5>
                    </CardHeader>
                    <CardBody className="p-0">
                        {transactions.length === 0 ? (
                            <div className="text-center text-gray-500 py-12">
                                <Inbox className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                                <p className="text-lg">No transactions found</p>
                            </div>
                        ) : (
                            <div className="table-responsive">
                                <table className="table table-compact">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Item Code</th>
                                            <th>Item Name</th>
                                            <th>Location</th>
                                            <th>Type</th>
                                            <th>Qty</th>
                                            <th>On Hand</th>
                                            <th>Ref</th>
                                            <th>Note</th>
                                            <th className="w-48">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {transactions.map((tx) => (
                                            <tr key={tx.id}>
                                                <td>{new Date(tx.tx_at).toLocaleString()}</td>
                                                <td>
                                                    <code className="text-blue-600 font-mono text-sm">
                                                        {tx.item_code || '-'}
                                                    </code>
                                                </td>
                                                <td>{tx.item_name || '-'}</td>
                                                <td>{tx.location_name || '-'}</td>
                                                <td>
                                                    <Badge variant={getTxBadge(tx.tx_type)}>
                                                        {tx.tx_type}
                                                    </Badge>
                                                </td>
                                                <td>{Number(tx.qty).toFixed(1)}</td>
                                                <td>
                                                    {tx.qty_on_hand !== null && tx.qty_on_hand !== undefined
                                                        ? Number(tx.qty_on_hand).toFixed(1)
                                                        : '-'}
                                                </td>
                                                <td>{tx.ref || '-'}</td>
                                                <td className="text-sm text-gray-600">
                                                    <span className="block max-w-xs truncate">{tx.note || '-'}</span>
                                                </td>
                                                <td>
                                                    {(currentUser?.role === 'ADMIN' || currentUser?.role === 'STAFF') && (
                                                        <div className="flex gap-2">
                                                            <Button
                                                                variant="outline-primary"
                                                                size="sm"
                                                                onClick={() => navigate(`/transactions/${tx.id}/edit`)}
                                                            >
                                                                <Pencil className="w-4 h-4 mr-1" />
                                                                Edit
                                                            </Button>
                                                            <Button
                                                                variant="outline-danger"
                                                                size="sm"
                                                                onClick={() => handleDelete(tx.id)}
                                                            >
                                                                <Trash2 className="w-4 h-4 mr-1" />
                                                                Delete
                                                            </Button>
                                                        </div>
                                                    )}
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
                            <PaginationInfo currentPage={currentPage} pageSize={pageSize} totalItems={totalItems} />
                            <Pagination
                                currentPage={currentPage}
                                totalPages={totalPages}
                                onPageChange={setCurrentPage}
                            />
                        </div>
                    )}
                </Card>
            </div>
        </div>
    );
}

export default TransactionsPage;
