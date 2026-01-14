import { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Plus, Eye, Pencil, Trash2, Inbox } from 'lucide-react';
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
    FormInput,
    FormSelect,
} from './UI';

interface Issue {
    id: number;
    code: string;
    status: string;
    requested_by?: number;
    approved_by?: number;
    issued_at?: string;
    note?: string;
    created_at?: string;
    updated_at?: string;
}

interface IssueItem {
    id: number;
    issue_id: number;
    item_id: number;
    qty: number;
    item_code?: string;
    serial_number?: string;
    item_name?: string;
    unit_symbol?: string;
}

interface User {
    id: number;
    name: string;
}

interface Statistics {
    total: number;
    status_breakdown: {
        draft: { count: number; percentage: number };
        approved: { count: number; percentage: number };
        issued: { count: number; percentage: number };
        cancelled: { count: number; percentage: number };
    };
}

interface IssueDetails {
    issue: Issue;
    items: IssueItem[];
}

function Dashboard() {
    const { user, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();
    const [issues, setIssues] = useState<Issue[]>([]);
    const [statistics, setStatistics] = useState<Statistics | null>(null);
    const [searchInput, setSearchInput] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [statsLoading, setStatsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [selectedIssue, setSelectedIssue] = useState<IssueDetails | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalIssues, setTotalIssues] = useState(0);
    const [pageSize] = useState(10);
    const [sortConfig, setSortConfig] = useState<{ key: keyof Issue; direction: 'asc' | 'desc' }>({
        key: 'id',
        direction: 'desc',
    });
    const [userNameMap, setUserNameMap] = useState<Record<number, string>>({});
    const [filters, setFilters] = useState({
        status: 'all',
        requestedBy: '',
        approvedBy: '',
        issuedFrom: '',
        issuedTo: '',
        note: '',
    });

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    useEffect(() => {
        if (!authLoading && !user) {
            navigate('/login');
        }
    }, [authLoading, user, navigate]);

    const fetchUserData = useCallback(async (userId: number): Promise<User | null> => {
        if (!token) return null;
        try {
            const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (!response.ok) throw new Error('Failed to fetch user');
            return await response.json();
        } catch (err) {
            console.error('Error fetching user:', err);
            return null;
        }
    }, [token, API_BASE_URL]);

    useEffect(() => {
        const userIds = new Set<number>();
        issues.forEach((issue) => {
            if (issue.requested_by) userIds.add(issue.requested_by);
            if (issue.approved_by) userIds.add(issue.approved_by);
        });

        const missingIds = Array.from(userIds).filter((id) => !userNameMap[id]);
        if (missingIds.length === 0) return;

        let mounted = true;
        (async () => {
            const entries = await Promise.all(
                missingIds.map(async (id) => {
                    const user = await fetchUserData(id);
                    return [id, user?.name || ''] as const;
                })
            );
            if (!mounted) return;
            setUserNameMap((prev) => {
                const next = { ...prev };
                entries.forEach(([id, name]) => {
                    next[id] = name;
                });
                return next;
            });
        })();

        return () => {
            mounted = false;
        };
    }, [issues, userNameMap, fetchUserData]);

    const fetchStatistics = useCallback(async () => {
        if (!token) return;
        setStatsLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/issues/stats`, {
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (!response.ok) throw new Error('Failed to fetch statistics');
            const data = await response.json();
            setStatistics(data);
        } catch (err) {
            console.error('Error fetching statistics:', err);
        } finally {
            setStatsLoading(false);
        }
    }, [token, API_BASE_URL]);

    const fetchIssues = useCallback(async () => {
        if (!token) return;
        setIsLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams({
                page: currentPage.toString(),
                page_size: pageSize.toString(),
            });
            if (debouncedSearch.trim()) params.append('search', debouncedSearch.trim());
            if (filters.status !== 'all') params.append('status_filter', filters.status.toUpperCase());

            const response = await fetch(`${API_BASE_URL}/issues?${params}`, {
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (!response.ok) throw new Error('Failed to fetch issues');
            const data = await response.json();
            setIssues(data.issues || []);
            setTotalIssues(data.total || 0);
            setTotalPages(Math.ceil((data.total || 0) / pageSize));
        } catch (err) {
            setError((err as Error).message || 'Failed to load issues');
        } finally {
            setIsLoading(false);
        }
    }, [token, API_BASE_URL, currentPage, pageSize, debouncedSearch, filters.status]);

    const fetchIssueDetails = async (issueId: number) => {
        if (!token) return;
        try {
            const [issueRes, itemsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/issues/${issueId}`, {
                    headers: { 'Authorization': `Bearer ${token}` },
                }),
                fetch(`${API_BASE_URL}/issue-items/issue/${issueId}`, {
                    headers: { 'Authorization': `Bearer ${token}` },
                }),
            ]);

            if (!issueRes.ok || !itemsRes.ok) throw new Error('Failed to fetch issue details');

            const issueData = await issueRes.json();
            const itemsData = await itemsRes.json();

            setSelectedIssue({
                issue: issueData.issue ?? issueData,
                items: Array.isArray(itemsData) ? itemsData : (itemsData.items || []),
            });
        } catch (err) {
            setError((err as Error).message || 'Failed to load issue details');
        }
    };

    const handleDeleteIssue = async (issueId: number) => {
        if (!token || !window.confirm('Delete this issue?')) return;
        try {
            const response = await fetch(`${API_BASE_URL}/issues/${issueId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to delete issue');
            }
            setSuccess('Issue deleted successfully');
            fetchIssues();
        } catch (err) {
            setError((err as Error).message || 'Failed to delete issue');
        }
    };

    useEffect(() => {
        fetchIssues();
        fetchStatistics();
    }, [fetchIssues, fetchStatistics]);

    useEffect(() => {
        const timer = window.setTimeout(() => {
            setDebouncedSearch(searchInput);
            setCurrentPage(1);
        }, 300);
        return () => window.clearTimeout(timer);
    }, [searchInput]);

    const getUserNameById = (userId?: number) => {
        if (!userId) return '-';
        return userNameMap[userId] || `User #${userId}`;
    };

    const getStatusColor = (status: string): 'warning' | 'success' | 'info' | 'secondary' | 'danger' => {
        switch (status?.toUpperCase()) {
            case 'DRAFT': return 'warning';
            case 'APPROVED': return 'info';
            case 'ISSUED': return 'success';
            case 'CANCELLED': return 'secondary';
            default: return 'danger';
        }
    };

    const filteredIssues = useMemo(() => {
        return issues.filter((issue) => {
            if (debouncedSearch && !issue.code.toLowerCase().includes(debouncedSearch.toLowerCase())) return false;
            if (filters.requestedBy) {
                const requestedName = issue.requested_by ? (userNameMap[issue.requested_by] || '') : '';
                if (!requestedName.toLowerCase().includes(filters.requestedBy.toLowerCase())) return false;
            }
            if (filters.approvedBy) {
                const approvedName = issue.approved_by ? (userNameMap[issue.approved_by] || '') : '';
                if (!approvedName.toLowerCase().includes(filters.approvedBy.toLowerCase())) return false;
            }
            if (filters.note && !(issue.note ?? '').toLowerCase().includes(filters.note.toLowerCase())) return false;
            if (filters.issuedFrom || filters.issuedTo) {
                const issuedDate = issue.issued_at ? new Date(issue.issued_at) : null;
                if (filters.issuedFrom && issuedDate && issuedDate < new Date(filters.issuedFrom)) return false;
                if (filters.issuedTo) {
                    const to = new Date(filters.issuedTo);
                    to.setHours(23, 59, 59, 999);
                    if (issuedDate && issuedDate > to) return false;
                }
            }
            return true;
        });
    }, [issues, filters, userNameMap, debouncedSearch]);

    const sortedIssues = useMemo(() => {
        const data = [...filteredIssues];
        data.sort((a, b) => {
            const aValue = a[sortConfig.key];
            const bValue = b[sortConfig.key];
            let result = 0;
            if (sortConfig.key === 'issued_at') {
                const aDate = aValue ? new Date(aValue as string).getTime() : 0;
                const bDate = bValue ? new Date(bValue as string).getTime() : 0;
                result = aDate - bDate;
            } else if (typeof aValue === 'number' && typeof bValue === 'number') {
                result = aValue - bValue;
            } else {
                result = String(aValue || '').localeCompare(String(bValue || ''));
            }
            return sortConfig.direction === 'asc' ? result : -result;
        });
        return data;
    }, [filteredIssues, sortConfig]);

    const handleSort = (key: keyof Issue) => {
        setSortConfig((prev) => ({
            key,
            direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
        }));
    };

    const getSortIndicator = (key: keyof Issue) => {
        if (sortConfig.key !== key) return '';
        return sortConfig.direction === 'asc' ? '▲' : '▼';
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
            <div className="px-4 py-6 max-w-7xl mx-auto">
                {/* Welcome Card */}
                <Card className="mb-6">
                    <CardBody>
                        <h5 className="text-xl font-bold mb-3">
                            Welcome, <span className="text-blue-600">{user?.name}</span>
                        </h5>
                        <div className="flex gap-2">
                            <Badge variant="primary">{user?.role}</Badge>
                            <Badge variant={user?.active ? 'success' : 'danger'}>
                                {user?.active ? 'Active' : 'Inactive'}
                            </Badge>
                        </div>
                    </CardBody>
                </Card>

                {/* Statistics Section */}
                {!statsLoading && statistics && (
                    <div className="mb-6">
                        <h4 className="text-2xl font-bold mb-4">Issues Statistics</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                            {/* Total */}
                            <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                                <CardBody>
                                    <div className="text-4xl mb-2">📊</div>
                                    <p className="text-sm text-gray-600 mb-1">Total Issues</p>
                                    <p className="text-3xl font-bold text-gray-900">{statistics.total}</p>
                                </CardBody>
                            </Card>

                            {/* Draft */}
                            <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
                                <CardBody>
                                    <div className="text-4xl mb-2">📝</div>
                                    <p className="text-sm text-gray-600 mb-1">Draft</p>
                                    <p className="text-3xl font-bold text-gray-900">{statistics.status_breakdown.draft.count}</p>
                                    <div className="mt-2">
                                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                                            <span>{statistics.status_breakdown.draft.percentage}%</span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-1">
                                            <div
                                                className="bg-yellow-500 h-1 rounded-full"
                                                style={{ width: `${statistics.status_breakdown.draft.percentage}%` }}
                                            />
                                        </div>
                                    </div>
                                </CardBody>
                            </Card>

                            {/* Approved */}
                            <Card className="bg-gradient-to-br from-cyan-50 to-cyan-100 border-cyan-200">
                                <CardBody>
                                    <div className="text-4xl mb-2">✅</div>
                                    <p className="text-sm text-gray-600 mb-1">Approved</p>
                                    <p className="text-3xl font-bold text-gray-900">{statistics.status_breakdown.approved.count}</p>
                                    <div className="mt-2">
                                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                                            <span>{statistics.status_breakdown.approved.percentage}%</span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-1">
                                            <div
                                                className="bg-cyan-500 h-1 rounded-full"
                                                style={{ width: `${statistics.status_breakdown.approved.percentage}%` }}
                                            />
                                        </div>
                                    </div>
                                </CardBody>
                            </Card>

                            {/* Issued */}
                            <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
                                <CardBody>
                                    <div className="text-4xl mb-2">📦</div>
                                    <p className="text-sm text-gray-600 mb-1">Issued</p>
                                    <p className="text-3xl font-bold text-gray-900">{statistics.status_breakdown.issued.count}</p>
                                    <div className="mt-2">
                                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                                            <span>{statistics.status_breakdown.issued.percentage}%</span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-1">
                                            <div
                                                className="bg-green-500 h-1 rounded-full"
                                                style={{ width: `${statistics.status_breakdown.issued.percentage}%` }}
                                            />
                                        </div>
                                    </div>
                                </CardBody>
                            </Card>

                            {/* Cancelled */}
                            <Card className="bg-gradient-to-br from-gray-50 to-gray-100 border-gray-200">
                                <CardBody>
                                    <div className="text-4xl mb-2">❌</div>
                                    <p className="text-sm text-gray-600 mb-1">Cancelled</p>
                                    <p className="text-3xl font-bold text-gray-900">{statistics.status_breakdown.cancelled.count}</p>
                                    <div className="mt-2">
                                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                                            <span>{statistics.status_breakdown.cancelled.percentage}%</span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-1">
                                            <div
                                                className="bg-gray-500 h-1 rounded-full"
                                                style={{ width: `${statistics.status_breakdown.cancelled.percentage}%` }}
                                            />
                                        </div>
                                    </div>
                                </CardBody>
                            </Card>
                        </div>
                    </div>
                )}

                {/* Issues Management Section */}
                <Card>
                    <CardHeader>
                        <div className="flex justify-between items-center">
                            <div>
                                <h5 className="text-xl font-bold">Issues Management</h5>
                                <p className="text-sm text-gray-600 mt-1">View and manage all issues</p>
                            </div>
                            {(user?.role === 'ADMIN' || user?.role === 'STAFF') && (
                                <Button variant="primary" onClick={() => navigate('/issues/new')}>
                                    <Plus className="w-4 h-4 mr-2" />
                                    New Issue
                                </Button>
                            )}
                        </div>
                    </CardHeader>

                    <CardBody>
                        {/* Alerts */}
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

                        {/* Search & Filters */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 mb-4">
                            <FormInput
                                label="Search Code"
                                placeholder="ISS-001"
                                value={searchInput}
                                onChange={(e) => {
                                    setSearchInput(e.target.value);
                                }}
                            />
                            <FormSelect
                                label="Status"
                                options={[
                                    { value: 'all', label: 'All' },
                                    { value: 'draft', label: 'DRAFT' },
                                    { value: 'approved', label: 'APPROVED' },
                                    { value: 'issued', label: 'ISSUED' },
                                    { value: 'cancelled', label: 'CANCELLED' },
                                ]}
                                value={filters.status}
                                onChange={(e) => {
                                    setFilters((prev) => ({ ...prev, status: e.target.value }));
                                    setCurrentPage(1);
                                }}
                            />
                            <FormInput
                                label="Requested By"
                                placeholder="User name"
                                value={filters.requestedBy}
                                onChange={(e) => setFilters((prev) => ({ ...prev, requestedBy: e.target.value }))}
                            />
                            <FormInput
                                label="Approved By"
                                placeholder="User name"
                                value={filters.approvedBy}
                                onChange={(e) => setFilters((prev) => ({ ...prev, approvedBy: e.target.value }))}
                            />
                            <FormInput
                                label="Issued From"
                                type="date"
                                value={filters.issuedFrom}
                                onChange={(e) => setFilters((prev) => ({ ...prev, issuedFrom: e.target.value }))}
                            />
                            <FormInput
                                label="Issued To"
                                type="date"
                                value={filters.issuedTo}
                                onChange={(e) => setFilters((prev) => ({ ...prev, issuedTo: e.target.value }))}
                            />
                        </div>

                        {/* Table */}
                        {sortedIssues.length === 0 ? (
                            <div className="text-center text-gray-500 py-12">
                                <Inbox className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                                <p className="text-lg">No issues found</p>
                            </div>
                        ) : (
                            <div className="table-responsive">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200"
                                                onClick={() => handleSort('code')}
                                            >
                                                Code {getSortIndicator('code')}
                                            </th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200"
                                                onClick={() => handleSort('status')}
                                            >
                                                Status {getSortIndicator('status')}
                                            </th>
                                            <th>Requested By</th>
                                            <th>Approved By</th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200"
                                                onClick={() => handleSort('issued_at')}
                                            >
                                                Issued At {getSortIndicator('issued_at')}
                                            </th>
                                            <th>Note</th>
                                            <th className="w-64">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sortedIssues.map((issue) => (
                                            <tr
                                                key={issue.id}
                                                className="hover:bg-gray-50 cursor-pointer"
                                                onClick={() => fetchIssueDetails(issue.id)}
                                            >
                                                <td>
                                                    <code className="text-blue-600 font-mono text-sm">{issue.code}</code>
                                                </td>
                                                <td>
                                                    <Badge variant={getStatusColor(issue.status)}>{issue.status}</Badge>
                                                </td>
                                                <td className="text-sm">{getUserNameById(issue.requested_by)}</td>
                                                <td className="text-sm">{getUserNameById(issue.approved_by)}</td>
                                                <td className="text-sm">
                                                    {issue.issued_at ? new Date(issue.issued_at).toLocaleDateString() : '-'}
                                                </td>
                                                <td className="text-sm max-w-xs truncate">{issue.note || '-'}</td>
                                                <td onClick={(e) => e.stopPropagation()}>
                                                    <div className="flex gap-2">
                                                        <Button
                                                            variant="outline-secondary"
                                                            size="sm"
                                                            onClick={() => navigate(`/issues/${issue.id}/items`)}
                                                        >
                                                            <Eye className="w-4 h-4 mr-1" />
                                                            View
                                                        </Button>
                                                        {(user?.role === 'ADMIN' || user?.role === 'STAFF') && (
                                                            <>
                                                                <Button
                                                                    variant="outline-primary"
                                                                    size="sm"
                                                                    onClick={() => navigate(`/issues/${issue.id}/edit`)}
                                                                >
                                                                    <Pencil className="w-4 h-4 mr-1" />
                                                                    Edit
                                                                </Button>
                                                                {user?.role === 'ADMIN' && (
                                                                    <Button
                                                                        variant="outline-danger"
                                                                        size="sm"
                                                                        onClick={() => handleDeleteIssue(issue.id)}
                                                                    >
                                                                        <Trash2 className="w-4 h-4 mr-1" />
                                                                        Delete
                                                                    </Button>
                                                                )}
                                                            </>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </CardBody>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
                            <PaginationInfo currentPage={currentPage} pageSize={pageSize} totalItems={totalIssues} />
                            <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
                        </div>
                    )}
                </Card>
            </div>

            {/* Issue Details Modal */}
            <Modal show={!!selectedIssue} onHide={() => setSelectedIssue(null)} size="lg">
                {selectedIssue && (
                    <>
                        <ModalHeader>
                            <h5 className="text-xl font-bold">Issue Details - {selectedIssue.issue.code}</h5>
                        </ModalHeader>
                        <ModalBody>
                            <h6 className="font-semibold mb-3">Issue Information</h6>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                                <div>
                                    <p className="text-sm text-gray-600">Code</p>
                                    <code className="text-blue-600 font-mono">{selectedIssue.issue.code}</code>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-600">Status</p>
                                    <Badge variant={getStatusColor(selectedIssue.issue.status)}>
                                        {selectedIssue.issue.status}
                                    </Badge>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-600">Requested By</p>
                                    <p>{getUserNameById(selectedIssue.issue.requested_by)}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-600">Approved By</p>
                                    <p>{getUserNameById(selectedIssue.issue.approved_by)}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-600">Issued At</p>
                                    <p>
                                        {selectedIssue.issue.issued_at
                                            ? new Date(selectedIssue.issue.issued_at).toLocaleString()
                                            : '-'}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-600">Note</p>
                                    <p>{selectedIssue.issue.note || '-'}</p>
                                </div>
                            </div>

                            <h6 className="font-semibold mb-3">Issue Items ({selectedIssue.items.length})</h6>
                            {selectedIssue.items.length === 0 ? (
                                <p className="text-center text-gray-500 py-4">No items in this issue</p>
                            ) : (
                                <div className="table-responsive">
                                    <table className="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Item Code</th>
                                                <th>Item Name</th>
                                                <th>Serial Number</th>
                                                <th>Quantity</th>
                                                <th>Unit</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {selectedIssue.items.map((item) => (
                                                <tr key={item.id}>
                                                    <td>
                                                        <code className="text-blue-600 text-xs">{item.item_code || '-'}</code>
                                                    </td>
                                                    <td className="text-sm">{item.item_name || '-'}</td>
                                                    <td className="text-sm">{item.serial_number || '-'}</td>
                                                    <td className="text-sm">{item.qty ? parseFloat(item.qty.toString()).toFixed(1) : '0.0'}</td>
                                                    <td className="text-sm">{item.unit_symbol || '-'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </ModalBody>
                        <ModalFooter>
                            <Button variant="secondary" onClick={() => setSelectedIssue(null)}>
                                Close
                            </Button>
                        </ModalFooter>
                    </>
                )}
            </Modal>
        </div>
    );
}

export default Dashboard;
