import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import Dashboard from './components/Dashboard';
import IssueDetailsPage from './components/IssueDetailsPage';
import Layout from './components/Layout';
import UsersPage from './components/UsersPage';
import ItemsPage from './components/ItemsPage';
import IssueFormPage from './components/IssueFormPage';
import ItemFormPage from './components/ItemFormPage';
import UserFormPage from './components/UserFormPage';
import SettingsPage from './components/SettingsPage';
import CategoryPage from './components/CategoryPage';
import UnitPage from './components/UnitPage';
import TransactionsPage from './components/TransactionsPage';
import TransactionFormPage from './components/TransactionFormPage';
import LocationsPage from './components/LocationsPage';
import AuditSessionsPage from './components/AuditSessionsPage';
import AuditSessionDetailPage from './components/AuditSessionDetailPage';
import AuditScanPage from './components/AuditScanPage';
import AuditReportPage from './components/AuditReportPage';

function PrivateRoute({ children, allowedRoles }: { children: React.ReactNode; allowedRoles?: string[] }) {
    const { user, isLoading } = useAuth();

    if (isLoading) {
        return <div>Loading...</div>;
    }

    if (!user) {
        return <Navigate to="/login" />;
    }

    if (allowedRoles && !allowedRoles.includes(user.role)) {
        return <Navigate to="/dashboard" />;
    }

    return <Layout>{children}</Layout>;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
    const { user, isLoading } = useAuth();

    if (isLoading) {
        return <div>Loading...</div>;
    }

    return user ? <Navigate to="/dashboard" /> : <>{children}</>;
}

function AppRoutes() {
    return (
        <Routes>
            <Route
                path="/login"
                element={
                    <PublicRoute>
                        <LoginPage />
                    </PublicRoute>
                }
            />
            <Route
                path="/register"
                element={
                    <PublicRoute>
                        <RegisterPage />
                    </PublicRoute>
                }
            />
            <Route
                path="/dashboard"
                element={
                    <PrivateRoute>
                        <Dashboard />
                    </PrivateRoute>
                }
            />
            <Route
                path="/issues/:issueId/items"
                element={
                    <PrivateRoute>
                        <IssueDetailsPage />
                    </PrivateRoute>
                }
            />
            <Route 
                path="/users"
                element={
                    <PrivateRoute>
                        <UsersPage />
                    </PrivateRoute>
                }
            />
            <Route 
                path="/items"
                element={
                    <PrivateRoute>
                        <ItemsPage />
                    </PrivateRoute>
                }
            />
            <Route 
                path="/categories"
                element={
                    <PrivateRoute>
                        <CategoryPage />
                    </PrivateRoute>
                }
            />
            <Route 
                path="/units"
                element={
                    <PrivateRoute>
                        <UnitPage />
                    </PrivateRoute>
                }
            />
            <Route
                path="/transactions"
                element={
                    <PrivateRoute>
                        <TransactionsPage />
                    </PrivateRoute>
                }
            />
            <Route
                path="/transactions/new"
                element={
                    <PrivateRoute>
                        <TransactionFormPage />
                    </PrivateRoute>
                }
            />
            <Route
                path="/transactions/:txId/edit"
                element={
                    <PrivateRoute>
                        <TransactionFormPage />
                    </PrivateRoute>
                }
            />
            <Route
                path="/locations"
                element={
                    <PrivateRoute allowedRoles={['ADMIN']}>
                        <LocationsPage />
                    </PrivateRoute>
                }
            />
            <Route
                path="/issues/new"
                element={
                    <PrivateRoute>
                        <IssueFormPage />
                    </PrivateRoute>
                }
            />
            <Route
                path="/issues/:issueId/edit"
                element={
                    <PrivateRoute>
                        <IssueFormPage />
                    </PrivateRoute>
                }
            />
            <Route
                path="/items/new"
                element={
                    <PrivateRoute>
                        <ItemFormPage />
                    </PrivateRoute>
                }
            />
            <Route
                path="/items/:itemId/edit"
                element={
                    <PrivateRoute>
                        <ItemFormPage />
                    </PrivateRoute>
                }
            />
            <Route
                path="/users/new"
                element={
                    <PrivateRoute>
                        <UserFormPage />
                    </PrivateRoute>
                }
            />
            <Route
                path="/users/:userId/edit"
                element={
                    <PrivateRoute>
                        <UserFormPage />
                    </PrivateRoute>
                }
            />
            <Route
                path="/settings"
                element={
                    <PrivateRoute>
                        <SettingsPage />
                    </PrivateRoute>
                }
            />

            <Route
                path="/audit"
                element={
                    <PrivateRoute allowedRoles={['ADMIN', 'AUDITOR']}>
                        <AuditSessionsPage />
                    </PrivateRoute>
                }
            />

            <Route
                path="/audit/:sessionId"
                element={
                    <PrivateRoute allowedRoles={['ADMIN', 'AUDITOR']}>
                        <AuditSessionDetailPage />
                    </PrivateRoute>
                }
            />

            <Route
                path="/audit/:sessionId/scan"
                element={
                    <PrivateRoute allowedRoles={['ADMIN', 'AUDITOR']}>
                        <AuditScanPage />
                    </PrivateRoute>
                }
            />

            <Route
                path="/audit/:sessionId/report"
                element={
                    <PrivateRoute allowedRoles={['ADMIN', 'AUDITOR']}>
                        <AuditReportPage />
                    </PrivateRoute>
                }
            />

            <Route
                path="/audit-sessions"
                element={
                    <PrivateRoute allowedRoles={['ADMIN', 'AUDITOR']}>
                        <AuditSessionsPage />
                    </PrivateRoute>
                }
            />

            <Route
                path="/audit-sessions/:sessionId"
                element={
                    <PrivateRoute allowedRoles={['ADMIN', 'AUDITOR']}>
                        <AuditSessionDetailPage />
                    </PrivateRoute>
                }
            />

            <Route
                path="/audit-sessions/:sessionId/scan"
                element={
                    <PrivateRoute allowedRoles={['ADMIN', 'AUDITOR']}>
                        <AuditScanPage />
                    </PrivateRoute>
                }
            />

            <Route
                path="/audit-sessions/:sessionId/report"
                element={
                    <PrivateRoute allowedRoles={['ADMIN', 'AUDITOR']}>
                        <AuditReportPage />
                    </PrivateRoute>
                }
            />

            <Route
                path="/audit/:sessionId/report"
                element={
                    <PrivateRoute allowedRoles={['ADMIN', 'AUDITOR']}>
                        <AuditReportPage />
                    </PrivateRoute>
                }
            />

            <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
    );
}

function App() {
    return (
        <AuthProvider>
            <AppRoutes />
        </AuthProvider>
    );
}

export default App;
