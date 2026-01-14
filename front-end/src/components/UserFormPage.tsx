import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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
    FormCheckbox,
} from './UI';

interface UserFormState {
    name: string;
    email: string;
    password: string;
    confirm_password: string;
    role: string;
    active: boolean;
}

function UserFormPage() {
    const { userId } = useParams<{ userId: string }>();
    const isEdit = Boolean(userId);
    const navigate = useNavigate();
    const { user, isLoading: authLoading } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [form, setForm] = useState<UserFormState>({
        name: '',
        email: '',
        password: '',
        confirm_password: '',
        role: 'STAFF',
        active: true,
    });

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('authToken');

    useEffect(() => {
        if (!authLoading && user?.role !== 'ADMIN') {
            navigate('/dashboard');
        }
    }, [authLoading, user, navigate]);

    useEffect(() => {
        if (!isEdit || !token) return;

        const loadUser = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });
                if (!response.ok) throw new Error('Failed to load user');

                const data = await response.json();
                setForm({
                    name: data.name || '',
                    email: data.email || '',
                    password: '',
                    confirm_password: '',
                    role: data.role || 'STAFF',
                    active: Boolean(data.active),
                });
            } catch (err) {
                setError((err as Error).message || 'Failed to load user');
            } finally {
                setIsLoading(false);
            }
        };

        loadUser();
    }, [API_BASE_URL, userId, isEdit, token]);

    const handleChange = (field: keyof UserFormState, value: string | boolean) => {
        setForm((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token) return;

        if (form.password !== form.confirm_password) {
            setError('Passwords do not match');
            return;
        }

        setIsLoading(true);
        setError(null);

        const payload: any = {
            name: form.name.trim(),
            email: form.email.trim(),
            role: form.role,
            active: form.active,
        };

        if (form.password) {
            payload.password = form.password;
        }

        try {
            const response = await fetch(
                isEdit ? `${API_BASE_URL}/users/${userId}` : `${API_BASE_URL}/users`,
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
                throw new Error(err.detail || 'Failed to save user');
            }

            navigate('/users');
        } catch (err) {
            setError((err as Error).message || 'Failed to save user');
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading || (isEdit && isLoading)) {
        return (
            <div className="flex items-center justify-center py-12">
                <Spinner size="lg" />
            </div>
        );
    }

    return (
        <div className="w-full h-full">
            <div className="px-4 py-6 max-w-2xl mx-auto">
                {/* Header */}
                <div className="mb-6 flex items-center gap-4">
                    <button
                        onClick={() => navigate('/users')}
                        className="text-blue-600 hover:text-blue-700 transition-colors"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900">
                            {isEdit ? 'Edit User' : 'Create New User'}
                        </h2>
                        <p className="text-gray-600 mt-1">Fill in the details below</p>
                    </div>
                </div>

                {error && (
                    <Alert variant="danger" dismissible onClose={() => setError(null)} className="mb-6">
                        {error}
                    </Alert>
                )}

                <Card>
                    <CardHeader>
                        <h5 className="font-bold">User Information</h5>
                    </CardHeader>
                    <CardBody>
                        <form onSubmit={handleSubmit}>
                            <div className="grid grid-cols-1 gap-4 mb-4">
                                <FormInput
                                    label="Full Name"
                                    placeholder="Enter full name"
                                    value={form.name}
                                    onChange={(e) => handleChange('name', e.target.value)}
                                    required
                                />
                                <FormInput
                                    label="Email"
                                    type="email"
                                    placeholder="user@example.com"
                                    value={form.email}
                                    onChange={(e) => handleChange('email', e.target.value)}
                                    required
                                />
                                <FormInput
                                    label={isEdit ? 'New Password (Leave blank to keep current)' : 'Password'}
                                    type="password"
                                    placeholder="Enter password"
                                    value={form.password}
                                    onChange={(e) => handleChange('password', e.target.value)}
                                    required={!isEdit}
                                />
                                <FormInput
                                    label="Confirm Password"
                                    type="password"
                                    placeholder="Confirm password"
                                    value={form.confirm_password}
                                    onChange={(e) => handleChange('confirm_password', e.target.value)}
                                    required={!isEdit || !!form.password}
                                />
                                <div>
                                    <label className="form-label">Role</label>
                                    <select
                                        className="form-select"
                                        value={form.role}
                                        onChange={(e) => handleChange('role', e.target.value)}
                                        required
                                    >
                                        <option value="STAFF">Staff</option>
                                        <option value="ADMIN">Admin</option>
                                        <option value="AUDITOR">Auditor</option>
                                    </select>
                                </div>
                                <div>
                                    <FormCheckbox
                                        id="user-active"
                                        label="Active"
                                        checked={form.active}
                                        onChange={(e) => handleChange('active', e.target.checked)}
                                    />
                                </div>
                            </div>
                        </form>
                    </CardBody>
                    <CardFooter className="bg-gray-50 flex justify-end gap-2">
                        <Button variant="secondary" onClick={() => navigate('/users')}>
                            Cancel
                        </Button>
                        <Button variant="primary" onClick={handleSubmit} disabled={isLoading}>
                            {isLoading ? (
                                <>
                                    <Spinner size="sm" className="mr-2" />
                                    {isEdit ? 'Saving...' : 'Creating...'}
                                </>
                            ) : (
                                <>{isEdit ? 'Save Changes' : 'Create User'}</>
                            )}
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        </div>
    );
}

export default UserFormPage;
