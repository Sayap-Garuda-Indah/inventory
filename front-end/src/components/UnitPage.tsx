import { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Pencil, Trash2, Inbox } from 'lucide-react';
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
    Form,
} from './UI';

interface Unit {
    id: number;
    name: string;
    symbol: string;
    multiplier: number;
}

interface UnitForm {
    name: string;
    symbol: string;
    multiplier: string;
}

function UnitPage() {
    const { user: currentUser, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();
    const [units, setUnits] = useState<Unit[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [editingUnit, setEditingUnit] = useState<Unit | null>(null);
    const [form, setForm] = useState<UnitForm>({
        name: '',
        symbol: '',
        multiplier: '1',
    });
    const [searchTerm, setSearchTerm] = useState('');
    const [sortConfig, setSortConfig] = useState<{ key: keyof Unit; direction: 'asc' | 'desc' }>({
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

    const fetchUnits = useCallback(async () => {
        if (!token) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/units?page=1&page_size=100`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch units');
            }

            const data = await response.json();
            setUnits(data.units || []);
        } catch (err) {
            setError((err as Error).message || 'Failed to load units');
            console.error('Error fetching units:', err);
        } finally {
            setIsLoading(false);
        }
    }, [API_BASE_URL, token]);

    useEffect(() => {
        fetchUnits();
    }, [fetchUnits]);

    const handleOpenModal = (unit?: Unit) => {
        if (unit) {
            setEditingUnit(unit);
            setForm({
                name: unit.name,
                symbol: unit.symbol,
                multiplier: unit.multiplier.toString(),
            });
        } else {
            setEditingUnit(null);
            setForm({
                name: '',
                symbol: '',
                multiplier: '1',
            });
        }
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setEditingUnit(null);
        setForm({
            name: '',
            symbol: '',
            multiplier: '1',
        });
        setError(null);
    };

    const handleChange = (field: keyof UnitForm, value: string) => {
        setForm((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token) return;

        setError(null);
        setSuccess(null);

        try {
            const url = editingUnit
                ? `${API_BASE_URL}/units/${editingUnit.id}`
                : `${API_BASE_URL}/units`;

            const method = editingUnit ? 'PUT' : 'POST';

            const payload = {
                name: form.name.trim(),
                symbol: form.symbol.trim(),
                multiplier: Number(form.multiplier),
            };

            const response = await fetch(url, {
                method,
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to save unit');
            }

            setSuccess(editingUnit ? 'Unit updated successfully' : 'Unit created successfully');
            handleCloseModal();
            fetchUnits();
        } catch (err) {
            setError((err as Error).message || 'Failed to save unit');
        }
    };

    const handleDelete = async (unitId: number) => {
        if (!token) return;
        if (!window.confirm('Are you sure you want to delete this unit?')) return;

        setError(null);
        setSuccess(null);

        try {
            const response = await fetch(`${API_BASE_URL}/units/${unitId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to delete unit');
            }

            setSuccess('Unit deleted successfully');
            fetchUnits();
        } catch (err) {
            setError((err as Error).message || 'Failed to delete unit');
        }
    };

    const filteredUnits = useMemo(() => {
        if (!searchTerm) return units;
        return units.filter(unit =>
            unit.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            unit.symbol.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [units, searchTerm]);

    const sortedUnits = useMemo(() => {
        const data = [...filteredUnits];
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
    }, [filteredUnits, sortConfig]);

    const handleSort = (key: keyof Unit) => {
        setSortConfig((prev) => ({
            key,
            direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
        }));
    };

    const getSortIndicator = (key: keyof Unit) => {
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
                        <h2 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                            <span>📏</span>
                            Units of Measurement
                        </h2>
                        <p className="text-gray-600 mt-1">Manage units for inventory items</p>
                    </div>
                    {currentUser?.role === 'ADMIN' && (
                        <Button variant="primary" onClick={() => handleOpenModal()}>
                            <Plus className="w-4 h-4 mr-2" />
                            New Unit
                        </Button>
                    )}
                </div>

                {/* Search */}
                <Card className="mb-6">
                    <CardBody>
                        <div>
                            <label className="form-label">Search Units</label>
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input
                                    type="text"
                                    className="form-control pl-10"
                                    placeholder="Search by name or symbol..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </div>
                        </div>
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

                {/* Units Table */}
                <Card>
                    <CardHeader>
                        <h5 className="font-bold text-lg">
                            Units ({sortedUnits.length})
                        </h5>
                    </CardHeader>
                    <CardBody className="p-0">
                        {sortedUnits.length === 0 ? (
                            <div className="text-center text-gray-500 py-12">
                                <Inbox className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                                <p className="text-lg">No units found</p>
                            </div>
                        ) : (
                            <div className="table-responsive">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200 w-24"
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
                                                className="cursor-pointer hover:bg-gray-200 w-40"
                                                onClick={() => handleSort('symbol')}
                                            >
                                                Symbol {getSortIndicator('symbol')}
                                            </th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200 w-40"
                                                onClick={() => handleSort('multiplier')}
                                            >
                                                Multiplier {getSortIndicator('multiplier')}
                                            </th>
                                            <th className="w-56">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sortedUnits.map((unit) => (
                                            <tr key={unit.id}>
                                                <td>
                                                    <code className="text-blue-600 font-mono text-sm">
                                                        {unit.id}
                                                    </code>
                                                </td>
                                                <td className="font-semibold">{unit.name}</td>
                                                <td>
                                                    <code className="text-gray-600 font-mono">{unit.symbol}</code>
                                                </td>
                                                <td>{unit.multiplier}</td>
                                                <td>
                                                    {currentUser?.role === 'ADMIN' && (
                                                        <div className="flex gap-2">
                                                            <Button
                                                                variant="outline-primary"
                                                                size="sm"
                                                                onClick={() => handleOpenModal(unit)}
                                                            >
                                                                <Pencil className="w-4 h-4 mr-1" />
                                                                Edit
                                                            </Button>
                                                            <Button
                                                                variant="outline-danger"
                                                                size="sm"
                                                                onClick={() => handleDelete(unit.id)}
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
                </Card>
            </div>

            {/* Add/Edit Modal */}
            <Modal show={showModal} onHide={handleCloseModal}>
                <ModalHeader onClose={handleCloseModal}>
                    {editingUnit ? 'Edit Unit' : 'Add Unit'}
                </ModalHeader>
                <Form onSubmit={handleSubmit}>
                    <ModalBody>
                        <div className="grid grid-cols-1 gap-4">
                            <FormInput
                                label="Unit Name"
                                placeholder="e.g., Kilogram, Meter, Piece"
                                value={form.name}
                                onChange={(e) => handleChange('name', e.target.value)}
                                required
                                autoFocus
                            />
                            <FormInput
                                label="Symbol"
                                placeholder="e.g., kg, m, pcs"
                                value={form.symbol}
                                onChange={(e) => handleChange('symbol', e.target.value)}
                                required
                            />
                            <FormInput
                                label="Multiplier"
                                type="number"
                                step="0.000001"
                                min="0"
                                value={form.multiplier}
                                onChange={(e) => handleChange('multiplier', e.target.value)}
                                required
                                helperText="Conversion factor (e.g., 1000 for kg to g)"
                            />
                        </div>
                    </ModalBody>
                    <ModalFooter>
                        <Button variant="secondary" onClick={handleCloseModal} type="button">
                            Cancel
                        </Button>
                        <Button variant="primary" type="submit">
                            {editingUnit ? 'Save Changes' : 'Create Unit'}
                        </Button>
                    </ModalFooter>
                </Form>
            </Modal>
        </div>
    );
}

export default UnitPage;
