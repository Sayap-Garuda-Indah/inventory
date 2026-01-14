import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Alert, Button, Card, CardBody, FormInput, Spinner } from './UI';

function RegisterPage() {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        if (password.length < 8) {
            setError('Password must be at least 8 characters long.');
            return;
        }

        setIsLoading(true);

        try {
            await register(email, password, name);
            navigate('/dashboard');
        } catch (err) {
            setError((err as Error).message || 'Registration failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
            <div className="w-full max-w-lg">
                <Card className="shadow-xl border border-gray-100">
                    <CardBody className="p-8 md:p-10">
                        <div className="text-center mb-8">
                            <h1 className="text-3xl font-bold text-gray-900 tracking-tight mb-2">
                                Create Account
                            </h1>
                            <p className="text-sm text-gray-500">
                                Register to access the Inventory Management System
                            </p>
                        </div>

                        {error && (
                            <Alert variant="danger" dismissible onClose={() => setError('')} className="mb-6">
                                {error}
                            </Alert>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-6">
                            <FormInput
                                label="Full Name"
                                type="text"
                                placeholder="Your full name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                                minLength={1}
                                maxLength={120}
                                disabled={isLoading}
                            />
                            <FormInput
                                label="Email"
                                type="email"
                                placeholder="you@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={isLoading}
                            />
                            <FormInput
                                label="Password"
                                type="password"
                                placeholder="Enter your password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                minLength={8}
                                disabled={isLoading}
                            />
                            <FormInput
                                label="Confirm Password"
                                type="password"
                                placeholder="Re-enter your password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                                minLength={8}
                                disabled={isLoading}
                            />

                            <Button variant="primary" type="submit" className="w-full" disabled={isLoading}>
                                {isLoading ? (
                                    <span className="inline-flex items-center">
                                        <Spinner size="sm" className="mr-2" />
                                        Registering...
                                    </span>
                                ) : (
                                    'Register'
                                )}
                            </Button>
                        </form>

                        <p className="text-center mt-6 text-sm text-gray-500">
                            Already have an account?{' '}
                            <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium">
                                Login here
                            </Link>
                        </p>
                    </CardBody>
                </Card>
            </div>
        </div>
    );
}

export default RegisterPage;
