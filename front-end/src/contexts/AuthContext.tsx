import { createContext, useState, useEffect, useContext } from 'react';
import type { ReactNode } from 'react';
import type { User, AuthContextType } from './authTypes';

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    
    useEffect(() => {
        // Check for existing token on mount
        const storedToken = localStorage.getItem('authToken');
        if (storedToken) {
            setToken(storedToken);
            fetchUserInfo(storedToken);
        } else {
            setIsLoading(false);
        }
    }, []);

    const fetchUserInfo = async (authToken: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch user info');
            }

            const data = await response.json();
            setUser(data);
        } catch (error) {
            console.error('Failed to fetch user info:', error);
            localStorage.removeItem('authToken');
            setToken(null);
        } finally {
            setIsLoading(false);
        }
    };

    const buildNetworkError = () => {
        return `Unable to reach API at ${API_BASE_URL}. Please check the server is running and accessible.`;
    };

    const login = async (email: string, password: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            const accessToken = data.access_token;

            localStorage.setItem('authToken', accessToken);
            setToken(accessToken);

            await fetchUserInfo(accessToken);
        } catch (error) {
            console.error('Login failed:', error);
            if (error instanceof TypeError || (error instanceof Error && error.message === 'Failed to fetch')) {
                throw new Error(buildNetworkError());
            }
            if (error instanceof Error) {
                throw error;
            }
            throw new Error('Login failed. Please try again.');
        }
    };

    const register = async (email: string, password: string, name: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    email, 
                    password, 
                    name,
                    role: 'STAFF',
                    active: 1 
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Registration failed');
            }

            // Auto-login after registration
            await login(email, password);
        } catch (error) {
            console.error('Registration failed:', error);
            if (error instanceof TypeError || (error instanceof Error && error.message === 'Failed to fetch')) {
                throw new Error(buildNetworkError());
            }
            if (error instanceof Error) {
                throw error;
            }
            throw new Error('Registration failed. Please try again.');
        }
    };

    const logout = () => {
        localStorage.removeItem('authToken');
        setUser(null);
        setToken(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, register, logout, isLoading }}>
            {children}
        </AuthContext.Provider>
    );
};
