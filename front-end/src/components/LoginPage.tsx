import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Alert, Button, Card, CardBody, FormInput, Spinner } from './UI';

function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await login(email, password);
            navigate('/dashboard');
        } catch (err) {
            setError((err as Error).message || 'Login failed. Please check your email and password.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100 relative overflow-hidden">
            <div className="absolute -top-24 -left-24 w-72 h-72 bg-blue-200/40 rounded-full blur-3xl" />
            <div className="absolute bottom-10 right-10 w-96 h-96 bg-blue-300/20 rounded-full blur-3xl" />

            <div className="w-full max-w-md px-4 relative z-10">
                <Card className="shadow-xl border border-gray-100">
                    <CardBody className="p-8 sm:p-10">
                        <div className="text-center mb-8">
                            <h1 className="text-2xl font-bold text-gray-900 mb-2 tracking-tight">
                                Inventory Management
                                <br />
                                System
                            </h1>
                            <p className="text-sm text-gray-500">Sign in to your account</p>
                        </div>

                        {error && (
                            <Alert variant="danger" dismissible onClose={() => setError('')} className="mb-6">
                                {error}
                            </Alert>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-6">
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
                            <Button variant="primary" type="submit" className="w-full" disabled={isLoading}>
                                {isLoading ? (
                                    <span className="inline-flex items-center">
                                        <Spinner size="sm" className="mr-2" />
                                        Signing in...
                                    </span>
                                ) : (
                                    'Sign In'
                                )}
                            </Button>
                        </form>

                        <p className="text-center mt-6 text-sm text-gray-500">
                            Don't have an account?{' '}
                            <Link to="/register" className="text-blue-600 hover:text-blue-700 font-medium">
                                Register here
                            </Link>
                        </p>
                    </CardBody>
                </Card>
            </div>
        </div>
    );
}

export default LoginPage;
