import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Plus, Pencil, Trash2, Inbox } from 'lucide-react';
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
} from './UI';

interface User {
    id: number;
    email: string;
    name: string;
    role: string;
    active: number;
    created_at: string;
}

interface UserListResponse {
    users: User[];
    total: number;
    page: number;
    page_size: number;
}

function UsersPage() {
    const { user: currentUser, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();
    const [users, setUsers] = useState<User[]>([]);
    const [searchInput, setSearchInput] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [activeOnly, setActiveOnly] = useState(true);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalUsers, setTotalUsers] = useState(0);
    const [pageSize] = useState(10);
    const [selectedUser, setSelectedUser] = useState<User | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [sortConfig, setSortConfig] = useState<{ key: keyof User; direction: 'asc' | 'desc' } | null>(null);

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    useEffect(() => {
        if (!authLoading && !currentUser) {
            navigate('/login');
        }
    }, [authLoading, currentUser, navigate]);

    useEffect(() => {
        fetchUsers();
    }, [currentPage, debouncedSearch, activeOnly]);

    useEffect(() => {
        const timer = window.setTimeout(() => {
            setDebouncedSearch(searchInput);
            setCurrentPage(1);
        }, 300);
        return () => window.clearTimeout(timer);
    }, [searchInput]);

    const fetchUsers = async () => {
        if (!token) return;

        setIsLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams({
                page: currentPage.toString(),
                page_size: pageSize.toString(),
                active_only: activeOnly ? '1' : '0',
            });

            if (debouncedSearch.trim()) {
                params.append('search', debouncedSearch.trim());
            }

            const response = await fetch(`${API_BASE_URL}/users?${params}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch users');
            }

            const data: UserListResponse = await response.json();
            setUsers(data.users);
            setTotalUsers(data.total);
            setTotalPages(Math.ceil(data.total / pageSize));
        } catch (err) {
            setError((err as Error).message || 'Failed to load users');
            console.error('Error fetching users:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleActiveFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setActiveOnly(e.target.checked);
        setCurrentPage(1);
    };

    const handleRowClick = (user: User) => {
        setSelectedUser(user);
        setShowModal(true);
    };

    const handleDeleteUser = async (userId: number) => {
        if (!token) return;
        if (!window.confirm('Delete this user?')) return;

        try {
            const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to delete user');
            }
            fetchUsers();
            setShowModal(false);
        } catch (err) {
            setError((err as Error).message || 'Failed to delete user');
        }
    };

    const getRoleBadgeColor = (role: string): 'primary' | 'success' | 'info' => {
        switch (role) {
            case 'ADMIN':
                return 'primary';
            case 'STAFF':
                return 'success';
            case 'AUDITOR':
                return 'info';
            default:
                return 'info';
        }
    };

    const handleSort = (key: keyof User) => {
        setSortConfig((prev) => {
            if (prev?.key === key) {
                return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' };
            }
            return { key, direction: 'asc' };
        });
    };

    const getSortIndicator = (key: keyof User) => {
        if (sortConfig?.key !== key) return '';
        return sortConfig.direction === 'asc' ? '▲' : '▼';
    };

    const filteredUsers = useMemo(() => {
        const term = debouncedSearch.trim().toLowerCase();
        if (!term) return users;
        return users.filter((user) => (
            user.name.toLowerCase().includes(term) ||
            user.email.toLowerCase().includes(term)
        ));
    }, [users, debouncedSearch]);

    const sortedUsers = useMemo(() => {
        if (!sortConfig) return filteredUsers;
        const data = [...filteredUsers];
        data.sort((a, b) => {
            const aValue = a[sortConfig.key];
            const bValue = b[sortConfig.key];
            let result = 0;

            if (sortConfig.key === 'created_at') {
                const aDate = aValue ? new Date(String(aValue)).getTime() : 0;
                const bDate = bValue ? new Date(String(bValue)).getTime() : 0;
                result = aDate - bDate;
            } else if (typeof aValue === 'number' && typeof bValue === 'number') {
                result = aValue - bValue;
            } else {
                result = String(aValue).localeCompare(String(bValue));
            }
            return sortConfig.direction === 'asc' ? result : -result;
        });
        return data;
    }, [filteredUsers, sortConfig]);

    const displayTotal = debouncedSearch.trim() ? sortedUsers.length : totalUsers;

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
                {/* Header */}
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                            <span>👥</span>
                            Users Management
                        </h2>
                        <p className="text-gray-600 mt-1">Manage system users and their roles</p>
                    </div>
                    {currentUser?.role === 'ADMIN' && (
                        <Button variant="primary" onClick={() => navigate('/users/new')}>
                            <Plus className="w-4 h-4 mr-2" />
                            New User
                        </Button>
                    )}
                </div>

                {/* Search & Filter */}
                <Card className="mb-6">
                    <CardBody>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormInput
                                label="Search"
                                placeholder="Search by name or email..."
                                value={searchInput}
                                onChange={(e) => setSearchInput(e.target.value)}
                            />
                            <div className="flex items-end">
                                <div className="flex items-center">
                                    <input
                                        type="checkbox"
                                        id="active-filter"
                                        checked={activeOnly}
                                        onChange={handleActiveFilterChange}
                                        className="w-4 h-4 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                                    />
                                    <label htmlFor="active-filter" className="ml-2 text-sm text-gray-700 cursor-pointer">
                                        Show active users only
                                    </label>
                                </div>
                            </div>
                        </div>
                    </CardBody>
                </Card>

                {error && (
                    <Alert variant="danger" dismissible onClose={() => setError(null)} className="mb-4">
                        {error}
                    </Alert>
                )}

                {/* Users Table */}
                <Card>
                    <CardHeader>
                        <h5 className="font-bold text-lg">
                            Users ({displayTotal})
                        </h5>
                    </CardHeader>
                    <CardBody className="p-0">
                        {sortedUsers.length === 0 ? (
                            <div className="text-center text-gray-500 py-12">
                                <Inbox className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                                <p className="text-lg">No users found</p>
                            </div>
                        ) : (
                            <div className="table-responsive">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200 w-20"
                                                onClick={() => handleSort('id')}
                                            >
                                                ID {getSortIndicator('id')}
                                            </th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200"
                                                onClick={() => handleSort('name')}
                                            >
                                                Name {getSortIndicator('name')}
                                            </th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200"
                                                onClick={() => handleSort('email')}
                                            >
                                                Email {getSortIndicator('email')}
                                            </th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200 w-32"
                                                onClick={() => handleSort('role')}
                                            >
                                                Role {getSortIndicator('role')}
                                            </th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200 w-32"
                                                onClick={() => handleSort('active')}
                                            >
                                                Status {getSortIndicator('active')}
                                            </th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200 w-40"
                                                onClick={() => handleSort('created_at')}
                                            >
                                                Created At {getSortIndicator('created_at')}
                                            </th>
                                            <th className="w-48">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sortedUsers.map((user) => (
                                            <tr
                                                key={user.id}
                                                className="cursor-pointer hover:bg-gray-50"
                                                onClick={() => handleRowClick(user)}
                                            >
                                                <td>
                                                    <code className="text-blue-600 font-mono text-sm">{user.id}</code>
                                                </td>
                                                <td className="font-semibold">{user.name}</td>
                                                <td>{user.email}</td>
                                                <td>
                                                    <Badge variant={getRoleBadgeColor(user.role)}>
                                                        {user.role}
                                                    </Badge>
                                                </td>
                                                <td>
                                                    <Badge variant={user.active ? 'success' : 'danger'}>
                                                        {user.active ? 'Active' : 'Inactive'}
                                                    </Badge>
                                                </td>
                                                <td>
                                                    {new Date(user.created_at).toLocaleDateString()}
                                                </td>
                                                <td onClick={(e) => e.stopPropagation()}>
                                                    {currentUser?.role === 'ADMIN' && (
                                                        <div className="flex gap-2">
                                                            <Button
                                                                variant="outline-primary"
                                                                size="sm"
                                                                onClick={() => navigate(`/users/${user.id}/edit`)}
                                                            >
                                                                <Pencil className="w-4 h-4 mr-1" />
                                                                Edit
                                                            </Button>
                                                            <Button
                                                                variant="outline-danger"
                                                                size="sm"
                                                                onClick={() => handleDeleteUser(user.id)}
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
                            <PaginationInfo currentPage={currentPage} pageSize={pageSize} totalItems={totalUsers} />
                            <Pagination
                                currentPage={currentPage}
                                totalPages={totalPages}
                                onPageChange={setCurrentPage}
                            />
                        </div>
                    )}
                </Card>
            </div>

            {/* User Details Modal */}
            <Modal show={showModal} onHide={() => setShowModal(false)}>
                <ModalHeader onClose={() => setShowModal(false)}>
                    User Details
                </ModalHeader>
                <ModalBody>
                    {selectedUser && (
                        <div className="space-y-4">
                            <div>
                                <strong>ID:</strong>
                                <p>{selectedUser.id}</p>
                            </div>
                            <div>
                                <strong>Name:</strong>
                                <p>{selectedUser.name}</p>
                            </div>
                            <div>
                                <strong>Email:</strong>
                                <p>{selectedUser.email}</p>
                            </div>
                            <div>
                                <strong>Role:</strong>
                                <p>
                                    <Badge variant={getRoleBadgeColor(selectedUser.role)}>
                                        {selectedUser.role}
                                    </Badge>
                                </p>
                            </div>
                            <div>
                                <strong>Status:</strong>
                                <p>
                                    <Badge variant={selectedUser.active ? 'success' : 'danger'}>
                                        {selectedUser.active ? 'Active' : 'Inactive'}
                                    </Badge>
                                </p>
                            </div>
                            <div>
                                <strong>Created At:</strong>
                                <p>{new Date(selectedUser.created_at).toLocaleString()}</p>
                            </div>
                        </div>
                    )}
                </ModalBody>
                <ModalFooter>
                    <Button variant="secondary" onClick={() => setShowModal(false)}>
                        Close
                    </Button>
                </ModalFooter>
            </Modal>
        </div>
    );
}

export default UsersPage;
