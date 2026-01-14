import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Pencil, Trash2, Inbox, Download } from 'lucide-react';
import QRCode from 'qrcode';
import { downloadQRCodesPDF } from '../utils/qrPdfGenerators';
import {
    Button,
    Card,
    CardHeader,
    CardBody,
    Badge,
    Alert,
    Spinner,
    Modal,
    ModalHeader,
    ModalBody,
    ModalFooter,
    Pagination,
    PaginationInfo,
} from './UI';

interface Item {
    id: number;
    item_code: string;
    name: string;
    description: string | null;
    category_id: number;
    unit_id: number;
    owner_user_id: number | null;
    qrcode: string | null;
    min_stock: number;
    image_url: string | null;
    active: number;
    created_at: string;
    updated_at: string;
}

interface ItemListResponse {
    items: Item[];
    total: number;
    page: number;
    page_size: number;
}

interface Category {
    id: number;
    name: string;
}

interface Unit {
    id: number;
    name: string;
    symbol: string;
}

interface User {
    id: number;
    name: string;
}

interface BulkQRCode {
    item_code: string;
    name: string;
    dataUrl: string;
}

interface QRPreview {
    item: Item;
    dataUrl: string;
}

function ItemsPage() {
    const { user: currentUser, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();
    const [items, setItems] = useState<Item[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [units, setUnits] = useState<Unit[]>([]);
    const [users, setUsers] = useState<User[]>([]);

    const [searchInput, setSearchInput] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalItems, setTotalItems] = useState(0);
    const [pageSize] = useState(10);
    const [selectedItem, setSelectedItem] = useState<Item | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [showBulkQRModal, setShowBulkQRModal] = useState(false);
    const [bulkQRCodes, setBulkQRCodes] = useState<BulkQRCode[]>([]);
    const [isGeneratingBulk, setIsGeneratingBulk] = useState(false);
    const [isDownloadingAll, setIsDownloadingAll] = useState(false);
    const [qrPreview, setQrPreview] = useState<QRPreview | null>(null);
    const [sortConfig, setSortConfig] = useState<{ key: keyof Item; direction: 'asc' | 'desc' } | null>(null);

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    useEffect(() => {
        if (!authLoading && !currentUser) {
            navigate('/login');
        }
    }, [authLoading, currentUser, navigate]);

    useEffect(() => {
        fetchMetadata();
    }, []);

    useEffect(() => {
        const timer = window.setTimeout(() => {
            setDebouncedSearch(searchInput);
            setCurrentPage(1);
        }, 300);
        return () => window.clearTimeout(timer);
    }, [searchInput]);

    useEffect(() => {
        fetchItems();
    }, [currentPage, debouncedSearch, statusFilter]);

    const fetchMetadata = async () => {
        if (!token) return;

        try {
            const [categoriesRes, unitsRes, usersRes] = await Promise.all([
                fetch(`${API_BASE_URL}/categories?page=1&page_size=100`, {
                    headers: { 'Authorization': `Bearer ${token}` },
                }),
                fetch(`${API_BASE_URL}/units?page=1&page_size=100`, {
                    headers: { 'Authorization': `Bearer ${token}` },
                }),
                fetch(`${API_BASE_URL}/users?page=1&page_size=100&active_only=1`, {
                    headers: { 'Authorization': `Bearer ${token}` },
                }),
            ]);

            const catData = await categoriesRes.json();
            const unitData = await unitsRes.json();
            const userData = await usersRes.json();

            setCategories(Array.isArray(catData) ? catData : []);
            setUnits(unitData.units || []);
            setUsers(Array.isArray(userData) ? userData : (userData.users || []));
        } catch (error) {
            console.error('Error fetching metadata:', error);
        }
    };

    const fetchItems = async () => {
        if (!token) return;

        setIsLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams({
                page: currentPage.toString(),
                page_size: pageSize.toString(),
            });

            if (debouncedSearch.trim()) {
                params.append('search', debouncedSearch.trim());
            }

            const response = await fetch(`${API_BASE_URL}/items?${params}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to fetch items');
            }

            const data: ItemListResponse = await response.json();
            setItems(data.items);
            setTotalItems(data.total);
            setTotalPages(Math.ceil(data.total / pageSize));
        } catch (err) {
            setError((err as Error).message || 'Failed to load items');
        } finally {
            setIsLoading(false);
        }
    };

    const getCategoryName = (categoryId: number): string => {
        const category = categories.find(c => c.id === categoryId);
        return category ? category.name : 'Unknown';
    };

    const getUserName = (userId: number | null): string => {
        if (!userId) return 'Unassigned';
        const user = users.find(u => u.id === userId);
        return user ? user.name : 'Unknown';
    };

    const buildQrPayload = (item: Item) => JSON.stringify({
        item_id: item.id,
        item_code: item.item_code,
        name: item.name,
        category: getCategoryName(item.category_id),
        owner: getUserName(item.owner_user_id),
        status: item.active ? 'Active' : 'Inactive',
    }, null, 2);

    const createQrDataUrl = (payload: string) => {
        return QRCode.toDataURL(payload, {
            width: 300,
            margin: 2,
            color: { dark: '#000000', light: '#FFFFFF' },
        });
    };

    const handleGenerateQR = async (item: Item) => {
        try {
            const dataUrl = await createQrDataUrl(buildQrPayload(item));
            setQrPreview({ item, dataUrl });
        } catch (error) {
            console.error('Error generating QR code:', error);
            setError('Failed to generate QR code');
        }
    };

    const handleGenerateBulkQR = async () => {
        setIsGeneratingBulk(true);
        try {
            const qrPromises = sortedItems.map(async (item) => {
                const dataUrl = await createQrDataUrl(buildQrPayload(item));

                return { item_code: item.item_code, name: item.name, dataUrl };
            });

            const qrItems = await Promise.all(qrPromises);
            setBulkQRCodes(qrItems);
            setShowBulkQRModal(true);
        } catch (error) {
            console.error('Error generating bulk QR codes:', error);
            setError('Failed to generate bulk QR codes');
        } finally {
            setIsGeneratingBulk(false);
        }
    };

    const fetchAllItems = async () => {
        if (!token) return [];

        const allItems: Item[] = [];
        let page = 1;
        let total = 0;

        do {
            const params = new URLSearchParams({
                page: page.toString(),
                page_size: '100',
            });

            const response = await fetch(`${API_BASE_URL}/items?${params}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to fetch items');
            }

            const data: ItemListResponse = await response.json();
            total = data.total;
            if (data.items.length === 0) {
                break;
            }
            allItems.push(...data.items);
            page += 1;
        } while (allItems.length < total);

        return allItems;
    };

    const handleDownloadAllPDF = async () => {
        setIsDownloadingAll(true);
        setError(null);
        try {
            const allItems = await fetchAllItems();
            if (allItems.length === 0) {
                setError('No items available to export.');
                return;
            }

            const qrItems = await Promise.all(allItems.map(async (item) => ({
                item_code: item.item_code,
                name: item.name,
                dataUrl: await createQrDataUrl(buildQrPayload(item)),
            })));

            downloadQRCodesPDF(qrItems, undefined, {
                cols: 5,
                rows: 6,
                showGrid: true,
            });
        } catch (error) {
            console.error('Error downloading all QR codes:', error);
            setError('Failed to download all QR codes');
        } finally {
            setIsDownloadingAll(false);
        }
    };

    const handleDownloadBulkPDF = () => {
        downloadQRCodesPDF(bulkQRCodes, undefined, {
            cols: 5,
            rows: 6,
            showGrid: true,
        });
    };

    const handleDeleteItem = async (itemId: number) => {
        if (!token) return;
        if (!window.confirm('Delete this item?')) return;

        try {
            const response = await fetch(`${API_BASE_URL}/items/${itemId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });
            if (!response.ok) {
                throw new Error('Failed to delete item');
            }
            fetchItems();
            setShowModal(false);
        } catch (err) {
            setError((err as Error).message || 'Failed to delete item');
        }
    };

    const handleRowClick = (item: Item) => {
        setSelectedItem(item);
        setShowModal(true);
    };

    const handleSort = (key: keyof Item) => {
        setSortConfig((prev) => {
            if (prev?.key === key) {
                return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' };
            }
            return { key, direction: 'asc' };
        });
    };

    const getSortIndicator = (key: keyof Item) => {
        if (sortConfig?.key !== key) return '';
        return sortConfig.direction === 'asc' ? '▲' : '▼';
    };

    const filteredItems = useMemo(() => {
        let filtered = items;
        const term = debouncedSearch.trim().toLowerCase();

        if (term) {
            filtered = filtered.filter((item) => {
                return (
                    item.item_code.toLowerCase().includes(term) ||
                    item.name.toLowerCase().includes(term) ||
                    (item.description?.toLowerCase().includes(term) ?? false)
                );
            });
        }

        if (statusFilter !== 'all') {
            const isActive = statusFilter === 'active';
            filtered = filtered.filter(item => Boolean(item.active) === isActive);
        }

        return filtered;
    }, [items, debouncedSearch, statusFilter]);

    const sortedItems = useMemo(() => {
        if (!sortConfig) return filteredItems;
        const data = [...filteredItems];
        data.sort((a, b) => {
            const aValue = a[sortConfig.key];
            const bValue = b[sortConfig.key];
            let result = 0;

            if (typeof aValue === 'number' && typeof bValue === 'number') {
                result = aValue - bValue;
            } else {
                result = String(aValue).localeCompare(String(bValue));
            }
            return sortConfig.direction === 'asc' ? result : -result;
        });
        return data;
    }, [filteredItems, sortConfig]);

    if (authLoading || isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Spinner size="lg" />
            </div>
        );
    }

    return (
        <div className="w-full h-full">
            <div className="px-4 py-6 max-w-7xl mx-auto">
                <div className="sm:flex sm:items-center sm:justify-between mb-8">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900">Items Management</h2>
                        <p className="mt-1 text-sm text-gray-500">Manage inventory items and stock levels.</p>
                    </div>
                    <div className="mt-4 sm:mt-0 flex flex-wrap gap-3">
                        {items.length > 0 && (
                            <Button
                                variant="outline-secondary"
                                onClick={handleGenerateBulkQR}
                                disabled={isGeneratingBulk || sortedItems.length === 0}
                                className="bg-white"
                            >
                                {isGeneratingBulk ? (
                                    <>
                                        <Spinner size="sm" className="mr-2" />
                                        Generating...
                                    </>
                                ) : (
                                    'Generate All QR Codes'
                                )}
                            </Button>
                        )}
                        {totalItems > 0 && (
                            <Button
                                variant="outline-secondary"
                                onClick={handleDownloadAllPDF}
                                className="bg-white"
                                disabled={isDownloadingAll || totalItems === 0}
                            >
                                {isDownloadingAll ? 'Preparing PDF...' : 'Download All as PDF'}
                            </Button>
                        )}
                        {(currentUser?.role === 'ADMIN' || currentUser?.role === 'STAFF') && (
                            <Button variant="primary" onClick={() => navigate('/items/new')}>
                                <Plus className="w-4 h-4 mr-2" />
                                Add Item
                            </Button>
                        )}
                    </div>
                </div>

                {error && (
                    <Alert variant="danger" dismissible onClose={() => setError(null)} className="mb-4">
                        {error}
                    </Alert>
                )}

                <Card className="shadow-sm mb-6">
                    <CardHeader className="bg-gray-50">
                        <h5 className="text-lg font-semibold text-gray-900">
                            Items ({sortedItems.length} / {totalItems})
                        </h5>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                            <div>
                                <label className="form-label">Search</label>
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input
                                        type="text"
                                        className="form-control pl-10"
                                        placeholder="Search by code, name, or description"
                                        value={searchInput}
                                        onChange={(e) => {
                                            setSearchInput(e.target.value);
                                        }}
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="form-label">Status</label>
                                <select
                                    className="form-select"
                                    value={statusFilter}
                                    onChange={(e) => {
                                        setStatusFilter(e.target.value);
                                        setCurrentPage(1);
                                    }}
                                >
                                    <option value="all">All Statuses</option>
                                    <option value="active">Active</option>
                                    <option value="inactive">Inactive</option>
                                </select>
                            </div>
                        </div>
                    </CardHeader>
                    <CardBody className="p-0">
                        {sortedItems.length === 0 ? (
                            <div className="text-center text-gray-500 py-12">
                                <Inbox className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                                <p className="text-lg">No items found</p>
                            </div>
                        ) : (
                        <div className="table-responsive">
                            <table className="table">
                                    <thead>
                                        <tr>
                                            <th className="w-32 text-xs uppercase tracking-wide text-gray-500">QR Code</th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200 text-xs uppercase tracking-wide text-gray-500"
                                                onClick={() => handleSort('item_code')}
                                            >
                                                Item Code {getSortIndicator('item_code')}
                                            </th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200 text-xs uppercase tracking-wide text-gray-500"
                                                onClick={() => handleSort('name')}
                                            >
                                                Name {getSortIndicator('name')}
                                            </th>
                                            <th className="text-xs uppercase tracking-wide text-gray-500">Description</th>
                                            <th className="text-center text-xs uppercase tracking-wide text-gray-500">Min Stock</th>
                                            <th className="text-center text-xs uppercase tracking-wide text-gray-500">Status</th>
                                            <th className="w-56 text-right text-xs uppercase tracking-wide text-gray-500">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sortedItems.map((item) => (
                                            <tr
                                                key={item.id}
                                                className="cursor-pointer hover:bg-gray-50"
                                                onClick={() => handleRowClick(item)}
                                            >
                                                <td onClick={(e) => e.stopPropagation()}>
                                                    <Button
                                                        variant="outline-secondary"
                                                        size="sm"
                                                        className="text-xs"
                                                        onClick={() => handleGenerateQR(item)}
                                                    >
                                                        Generate
                                                    </Button>
                                                </td>
                                                <td>
                                                    <code className="text-primary font-mono text-sm">
                                                        {item.item_code}
                                                    </code>
                                                </td>
                                                <td className="font-semibold text-gray-900">{item.name}</td>
                                                <td className="text-sm text-gray-500">
                                                    {item.description || '-'}
                                                </td>
                                                <td className="text-center">
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                        {item.min_stock.toFixed(1)}
                                                    </span>
                                                </td>
                                                <td className="text-center">
                                                    <Badge variant={item.active ? 'success' : 'danger'}>
                                                        {item.active ? 'Active' : 'Inactive'}
                                                    </Badge>
                                                </td>
                                                <td onClick={(e) => e.stopPropagation()} className="text-right">
                                                    {(currentUser?.role === 'ADMIN' || currentUser?.role === 'STAFF') && (
                                                        <div className="flex gap-2 justify-end">
                                                            <Button
                                                                variant="outline-primary"
                                                                size="sm"
                                                                className="text-xs"
                                                                onClick={() => navigate(`/items/${item.id}/edit`)}
                                                            >
                                                                <Pencil className="w-4 h-4 mr-1" />
                                                                Edit
                                                            </Button>
                                                            {currentUser?.role === 'ADMIN' && (
                                                                <Button
                                                                    variant="outline-danger"
                                                                    size="sm"
                                                                    className="text-xs"
                                                                    onClick={() => handleDeleteItem(item.id)}
                                                                >
                                                                    <Trash2 className="w-4 h-4 mr-1" />
                                                                    Delete
                                                                </Button>
                                                            )}
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

            {/* Bulk QR Modal */}
            <Modal show={showBulkQRModal} onHide={() => setShowBulkQRModal(false)} size="lg">
                <ModalHeader onClose={() => setShowBulkQRModal(false)}>
                    Generated QR Codes
                </ModalHeader>
                <ModalBody>
                    <div className="grid grid-cols-3 gap-4">
                        {bulkQRCodes.map((item) => (
                            <div key={item.item_code} className="text-center">
                                <img src={item.dataUrl} alt={`QR for ${item.item_code}`} className="w-full mb-2" />
                                <p className="text-sm font-semibold">{item.item_code}</p>
                                <p className="text-xs text-gray-500">{item.name}</p>
                            </div>
                        ))}
                    </div>
                </ModalBody>
                <ModalFooter>
                    <Button variant="secondary" onClick={() => setShowBulkQRModal(false)}>
                        Close
                    </Button>
                    <Button variant="primary" onClick={handleDownloadBulkPDF}>
                        <Download className="w-4 h-4 mr-2" />
                        Download PDF ({bulkQRCodes.length})
                    </Button>
                </ModalFooter>
            </Modal>

            {/* QR Preview Modal */}
            <Modal show={Boolean(qrPreview)} onHide={() => setQrPreview(null)} size="md">
                <ModalHeader onClose={() => setQrPreview(null)}>
                    QR Code Preview
                </ModalHeader>
                <ModalBody>
                    {qrPreview && (
                        <div className="space-y-4">
                            <img
                                src={qrPreview.dataUrl}
                                alt={`QR for ${qrPreview.item.item_code}`}
                                className="w-full max-w-xs mx-auto"
                            />
                            <div className="text-sm text-gray-600 space-y-2">
                                <div>
                                    <span className="font-semibold text-gray-900">Item Code:</span>{' '}
                                    <span className="font-mono text-primary">{qrPreview.item.item_code}</span>
                                </div>
                                <div>
                                    <span className="font-semibold text-gray-900">Name:</span> {qrPreview.item.name}
                                </div>
                                <div>
                                    <span className="font-semibold text-gray-900">Category:</span>{' '}
                                    {getCategoryName(qrPreview.item.category_id)}
                                </div>
                                <div>
                                    <span className="font-semibold text-gray-900">Owner:</span>{' '}
                                    {getUserName(qrPreview.item.owner_user_id)}
                                </div>
                                <div>
                                    <span className="font-semibold text-gray-900">Status:</span>{' '}
                                    {qrPreview.item.active ? 'Active' : 'Inactive'}
                                </div>
                            </div>
                        </div>
                    )}
                </ModalBody>
                <ModalFooter>
                    <Button variant="secondary" onClick={() => setQrPreview(null)}>
                        Close
                    </Button>
                </ModalFooter>
            </Modal>

            {/* Item Details Modal */}
            <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
                <ModalHeader onClose={() => setShowModal(false)}>
                    Item Details
                </ModalHeader>
                <ModalBody>
                    {selectedItem && (
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <strong>Item Code:</strong>
                                <p className="text-blue-600 font-mono">{selectedItem.item_code}</p>
                            </div>
                            <div>
                                <strong>Status:</strong>
                                <p>
                                    <Badge variant={selectedItem.active ? 'success' : 'danger'}>
                                        {selectedItem.active ? 'Active' : 'Inactive'}
                                    </Badge>
                                </p>
                            </div>
                            <div className="col-span-2">
                                <strong>Name:</strong>
                                <p className="font-semibold">{selectedItem.name}</p>
                            </div>
                            <div className="col-span-2">
                                <strong>Description:</strong>
                                <p>{selectedItem.description || '-'}</p>
                            </div>
                            <div>
                                <strong>Category:</strong>
                                <p>{getCategoryName(selectedItem.category_id)}</p>
                            </div>
                            <div>
                                <strong>Unit:</strong>
                                <p>{units.find(u => u.id === selectedItem.unit_id)?.name || '-'}</p>
                            </div>
                            <div>
                                <strong>Min Stock:</strong>
                                <p>{selectedItem.min_stock.toFixed(2)}</p>
                            </div>
                            <div>
                                <strong>Owner:</strong>
                                <p>{getUserName(selectedItem.owner_user_id)}</p>
                            </div>
                            {selectedItem.image_url && (
                                <div className="col-span-2">
                                    <strong>Image:</strong>
                                    <a
                                        href={selectedItem.image_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:underline"
                                    >
                                        View Image
                                    </a>
                                </div>
                            )}
                        </div>
                    )}
                </ModalBody>
                <ModalFooter>
                    {selectedItem && (currentUser?.role === 'ADMIN' || currentUser?.role === 'STAFF') && (
                        <>
                            <Button
                                variant="outline-primary"
                                onClick={() => {
                                    navigate(`/items/${selectedItem.id}/edit`);
                                    setShowModal(false);
                                }}
                            >
                                <Pencil className="w-4 h-4 mr-2" />
                                Edit
                            </Button>
                            {currentUser?.role === 'ADMIN' && (
                                <Button
                                    variant="outline-danger"
                                    onClick={() => handleDeleteItem(selectedItem.id)}
                                >
                                    <Trash2 className="w-4 h-4 mr-2" />
                                    Delete
                                </Button>
                            )}
                        </>
                    )}
                    <Button variant="secondary" onClick={() => setShowModal(false)}>
                        Close
                    </Button>
                </ModalFooter>
            </Modal>
        </div>
    );
}

export default ItemsPage;
