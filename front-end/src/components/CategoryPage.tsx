import { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Plus, Pencil, Trash2, Inbox } from 'lucide-react';
import {
    Button,
    Card,
    CardHeader,
    CardBody,
    Alert,
    Spinner,
    Modal,
    ModalHeader,
    ModalBody,
    ModalFooter,
    FormInput,
} from './UI';

interface Category {
    id: number;
    name: string;
}

function CategoryPage() {
    const { user: currentUser, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();
    const [categories, setCategories] = useState<Category[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [editingCategory, setEditingCategory] = useState<Category | null>(null);
    const [formName, setFormName] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [sortConfig, setSortConfig] = useState<{ key: keyof Category; direction: 'asc' | 'desc' }>({
        key: 'id',
        direction: 'asc',
    });

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    useEffect(() => {
        if (!authLoading && !currentUser) {
            navigate('/login');
        }
    }, [authLoading, currentUser, navigate]);

    const fetchCategories = useCallback(async () => {
        if (!token) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/categories?page=1&page_size=100`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch categories');
            }

            const data: Category[] = await response.json();
            setCategories(data);
        } catch (err) {
            setError((err as Error).message || 'Failed to load categories');
            console.error('Error fetching categories:', err);
        } finally {
            setIsLoading(false);
        }
    }, [API_BASE_URL, token]);

    useEffect(() => {
        fetchCategories();
    }, [fetchCategories]);

    const handleOpenModal = (category?: Category) => {
        if (category) {
            setEditingCategory(category);
            setFormName(category.name);
        } else {
            setEditingCategory(null);
            setFormName('');
        }
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setEditingCategory(null);
        setFormName('');
        setError(null);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token) return;

        setError(null);
        setSuccess(null);

        try {
            const url = editingCategory
                ? `${API_BASE_URL}/categories/${editingCategory.id}`
                : `${API_BASE_URL}/categories`;

            const method = editingCategory ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: formName.trim() }),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to save category');
            }

            setSuccess(editingCategory ? 'Category updated successfully' : 'Category created successfully');
            handleCloseModal();
            fetchCategories();
        } catch (err) {
            setError((err as Error).message || 'Failed to save category');
        }
    };

    const handleDelete = async (categoryId: number) => {
        if (!token) return;
        if (!window.confirm('Are you sure you want to delete this category?')) return;

        setError(null);
        setSuccess(null);

        try {
            const response = await fetch(`${API_BASE_URL}/categories/${categoryId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to delete category');
            }

            setSuccess('Category deleted successfully');
            fetchCategories();
        } catch (err) {
            setError((err as Error).message || 'Failed to delete category');
        }
    };

    const filteredCategories = useMemo(() => {
        if (!searchTerm) return categories;
        return categories.filter(cat =>
            cat.name.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [categories, searchTerm]);

    const sortedCategories = useMemo(() => {
        const data = [...filteredCategories];
        data.sort((a, b) => {
            const aValue = a[sortConfig.key];
            const bValue = b[sortConfig.key];
            const result = String(aValue).localeCompare(String(bValue));
            return sortConfig.direction === 'asc' ? result : -result;
        });
        return data;
    }, [filteredCategories, sortConfig]);

    const handleSort = (key: keyof Category) => {
        setSortConfig((prev) => ({
            key,
            direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
        }));
    };

    const getSortIndicator = (key: keyof Category) => {
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
                {/* Header */}
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900">Categories</h2>
                        <p className="text-sm text-gray-500 mt-1">Manage item categories</p>
                    </div>
                    {(currentUser?.role === 'ADMIN' || currentUser?.role === 'STAFF') && (
                        <Button variant="primary" onClick={() => handleOpenModal()}>
                            <Plus className="w-4 h-4 mr-2" />
                            Add Category
                        </Button>
                    )}
                </div>

                {/* Search */}
                <Card className="mb-6 shadow-sm">
                    <CardBody>
                        <FormInput
                            label="Search Categories"
                            placeholder="Search by name..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </CardBody>
                </Card>

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

                {/* Categories Table */}
                <Card className="shadow-sm">
                    <CardHeader className="bg-gray-50">
                        <h5 className="text-sm font-semibold text-gray-900">
                            Categories ({sortedCategories.length})
                        </h5>
                    </CardHeader>
                    <CardBody className="p-0">
                        {sortedCategories.length === 0 ? (
                            <div className="text-center text-gray-500 py-12">
                                <Inbox className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                                <p className="text-lg">No categories found</p>
                            </div>
                        ) : (
                            <div className="table-responsive">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200 w-24 text-xs uppercase tracking-wide text-gray-500"
                                                onClick={() => handleSort('id')}
                                            >
                                                ID {getSortIndicator('id')}
                                            </th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200 text-xs uppercase tracking-wide text-gray-500"
                                                onClick={() => handleSort('name')}
                                            >
                                                Name {getSortIndicator('name')}
                                            </th>
                                            <th className="w-48 text-right text-xs uppercase tracking-wide text-gray-500">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sortedCategories.map((category) => (
                                            <tr key={category.id}>
                                                <td>
                                                    <code className="text-primary font-mono text-sm">
                                                        {category.id}
                                                    </code>
                                                </td>
                                                <td className="font-semibold">{category.name}</td>
                                                <td className="text-right">
                                                    {(currentUser?.role === 'ADMIN' || currentUser?.role === 'STAFF') && (
                                                        <div className="flex gap-2 justify-end">
                                                            <Button
                                                                variant="outline-primary"
                                                                size="sm"
                                                                className="text-xs"
                                                                onClick={() => handleOpenModal(category)}
                                                            >
                                                                <Pencil className="w-4 h-4 mr-1" />
                                                                Edit
                                                            </Button>
                                                            {currentUser?.role === 'ADMIN' && (
                                                                <Button
                                                                    variant="outline-danger"
                                                                    size="sm"
                                                                    className="text-xs"
                                                                    onClick={() => handleDelete(category.id)}
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
                </Card>
            </div>

            {/* Add/Edit Modal */}
            <Modal show={showModal} onHide={handleCloseModal}>
                <ModalHeader onClose={handleCloseModal}>
                    {editingCategory ? 'Edit Category' : 'Add Category'}
                </ModalHeader>
                <form onSubmit={handleSubmit}>
                    <ModalBody>
                        <div>
                            <label className="form-label">Category Name</label>
                            <input
                                type="text"
                                className="form-control"
                                placeholder="Enter category name"
                                value={formName}
                                onChange={(e) => setFormName(e.target.value)}
                                required
                                autoFocus
                            />
                        </div>
                    </ModalBody>
                    <ModalFooter>
                        <Button variant="secondary" onClick={handleCloseModal} type="button">
                            Cancel
                        </Button>
                        <Button variant="primary" type="submit">
                            {editingCategory ? 'Save Changes' : 'Create Category'}
                        </Button>
                    </ModalFooter>
                </form>
            </Modal>
        </div>
    );
}

export default CategoryPage;
