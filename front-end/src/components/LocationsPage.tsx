import { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Plus, Pencil, Trash2, Inbox, MapPin } from 'lucide-react';
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
    FormSelect,
    Form,
    Badge,
} from './UI';

interface Location {
    id: number;
    name: string;
    code: string;
    active: number;
}

interface LocationForm {
    name: string;
    code: string;
    active: string;
}

function LocationsPage() {
    const { user: currentUser, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();
    const [locations, setLocations] = useState<Location[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [editingLocation, setEditingLocation] = useState<Location | null>(null);
    const [form, setForm] = useState<LocationForm>({
        name: '',
        code: '',
        active: '1',
    });
    const [searchTerm, setSearchTerm] = useState('');
    const [sortConfig, setSortConfig] = useState<{ key: keyof Location; direction: 'asc' | 'desc' }>({
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

    const fetchLocations = useCallback(async () => {
        if (!token) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/locations?page=1&page_size=200&active_only=0`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch locations');
            }

            const data = await response.json();
            setLocations(Array.isArray(data) ? data : []);
        } catch (err) {
            setError((err as Error).message || 'Failed to load locations');
            console.error('Error fetching locations:', err);
        } finally {
            setIsLoading(false);
        }
    }, [API_BASE_URL, token]);

    useEffect(() => {
        fetchLocations();
    }, [fetchLocations]);

    const handleOpenModal = (location?: Location) => {
        if (location) {
            setEditingLocation(location);
            setForm({
                name: location.name,
                code: location.code,
                active: location.active ? '1' : '0',
            });
        } else {
            setEditingLocation(null);
            setForm({
                name: '',
                code: '',
                active: '1',
            });
        }
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setEditingLocation(null);
        setForm({
            name: '',
            code: '',
            active: '1',
        });
        setError(null);
    };

    const handleChange = (field: keyof LocationForm, value: string) => {
        setForm((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token) return;

        setError(null);
        setSuccess(null);

        try {
            const url = editingLocation
                ? `${API_BASE_URL}/locations/${editingLocation.id}`
                : `${API_BASE_URL}/locations`;
            const method = editingLocation ? 'PUT' : 'POST';
            const payload = {
                name: form.name.trim(),
                code: form.code.trim(),
                active: Number(form.active),
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
                throw new Error(err.detail || 'Failed to save location');
            }

            setSuccess(editingLocation ? 'Location updated successfully' : 'Location created successfully');
            handleCloseModal();
            fetchLocations();
        } catch (err) {
            setError((err as Error).message || 'Failed to save location');
        }
    };

    const handleDelete = async (locationId: number) => {
        if (!token) return;
        if (!window.confirm('Are you sure you want to delete this location?')) return;

        setError(null);
        setSuccess(null);

        try {
            const response = await fetch(`${API_BASE_URL}/locations/${locationId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to delete location');
            }

            setSuccess('Location deleted successfully');
            fetchLocations();
        } catch (err) {
            setError((err as Error).message || 'Failed to delete location');
        }
    };

    const filteredLocations = useMemo(() => {
        if (!searchTerm) return locations;
        const term = searchTerm.toLowerCase();
        return locations.filter((location) =>
            location.name.toLowerCase().includes(term) ||
            location.code.toLowerCase().includes(term)
        );
    }, [locations, searchTerm]);

    const sortedLocations = useMemo(() => {
        const data = [...filteredLocations];
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
    }, [filteredLocations, sortConfig]);

    const handleSort = (key: keyof Location) => {
        setSortConfig((prev) => ({
            key,
            direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
        }));
    };

    const getSortIndicator = (key: keyof Location) => {
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
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                            <MapPin className="w-7 h-7 text-blue-600" />
                            Locations
                        </h2>
                        <p className="text-gray-600 mt-1">Manage stock locations for transactions</p>
                    </div>
                    {currentUser?.role === 'ADMIN' && (
                        <Button variant="primary" onClick={() => handleOpenModal()}>
                            <Plus className="w-4 h-4 mr-2" />
                            New Location
                        </Button>
                    )}
                </div>

                <Card className="mb-6 shadow-sm">
                    <CardBody>
                        <FormInput
                            label="Search Locations"
                            placeholder="Search by name or code..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </CardBody>
                </Card>

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

                <Card className="shadow-sm">
                    <CardHeader className="bg-gray-50">
                        <h5 className="text-sm font-semibold text-gray-900">
                            Locations ({sortedLocations.length})
                        </h5>
                    </CardHeader>
                    <CardBody className="p-0">
                        {sortedLocations.length === 0 ? (
                            <div className="text-center text-gray-500 py-12">
                                <Inbox className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                                <p className="text-lg">No locations found</p>
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
                                                onClick={() => handleSort('code')}
                                            >
                                                Code {getSortIndicator('code')}
                                            </th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200 text-xs uppercase tracking-wide text-gray-500"
                                                onClick={() => handleSort('name')}
                                            >
                                                Name {getSortIndicator('name')}
                                            </th>
                                            <th
                                                className="cursor-pointer hover:bg-gray-200 text-xs uppercase tracking-wide text-gray-500"
                                                onClick={() => handleSort('active')}
                                            >
                                                Status {getSortIndicator('active')}
                                            </th>
                                            <th className="w-56 text-right text-xs uppercase tracking-wide text-gray-500">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sortedLocations.map((location) => (
                                            <tr key={location.id}>
                                                <td>
                                                    <code className="text-blue-600 font-mono text-sm">
                                                        {location.id}
                                                    </code>
                                                </td>
                                                <td>
                                                    <code className="text-gray-600 font-mono">{location.code}</code>
                                                </td>
                                                <td className="font-semibold">{location.name}</td>
                                                <td>
                                                    <Badge variant={location.active ? 'success' : 'secondary'}>
                                                        {location.active ? 'Active' : 'Inactive'}
                                                    </Badge>
                                                </td>
                                                <td className="text-right">
                                                    {currentUser?.role === 'ADMIN' && (
                                                        <div className="flex gap-2 justify-end">
                                                            <Button
                                                                variant="outline-primary"
                                                                size="sm"
                                                                onClick={() => handleOpenModal(location)}
                                                            >
                                                                <Pencil className="w-4 h-4 mr-1" />
                                                                Edit
                                                            </Button>
                                                            <Button
                                                                variant="outline-danger"
                                                                size="sm"
                                                                onClick={() => handleDelete(location.id)}
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

            <Modal show={showModal} onHide={handleCloseModal}>
                <ModalHeader onClose={handleCloseModal}>
                    {editingLocation ? 'Edit Location' : 'Add Location'}
                </ModalHeader>
                <Form onSubmit={handleSubmit}>
                    <ModalBody>
                        <div className="grid grid-cols-1 gap-4">
                            <FormInput
                                label="Location Name"
                                placeholder="e.g., Main Warehouse"
                                value={form.name}
                                onChange={(e) => handleChange('name', e.target.value)}
                                required
                                autoFocus
                            />
                            <FormInput
                                label="Location Code"
                                placeholder="e.g., WH-MAIN"
                                value={form.code}
                                onChange={(e) => handleChange('code', e.target.value)}
                                required
                            />
                            <FormSelect
                                label="Status"
                                options={[
                                    { value: '1', label: 'Active' },
                                    { value: '0', label: 'Inactive' },
                                ]}
                                value={form.active}
                                onChange={(e) => handleChange('active', e.target.value)}
                                required
                            />
                        </div>
                    </ModalBody>
                    <ModalFooter>
                        <Button variant="secondary" onClick={handleCloseModal} type="button">
                            Cancel
                        </Button>
                        <Button variant="primary" type="submit">
                            {editingLocation ? 'Save Changes' : 'Create Location'}
                        </Button>
                    </ModalFooter>
                </Form>
            </Modal>
        </div>
    );
}

export default LocationsPage;
